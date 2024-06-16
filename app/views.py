import os
import glob
import mimetypes
import io
import logging
import time
import cv2

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    session,
    wrappers,
    send_from_directory,
    jsonify,
)
from werkzeug.utils import secure_filename
from PIL import Image
from ultralytics import YOLO
from zipfile import ZipFile

logger = logging.getLogger("model_logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")

file_handler = logging.FileHandler("./logs/model.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class DataUtils:
    def __init__(
        self,
        upload_folder: str = "./uploads",
        output_folder: str = "./outputs",
        log_folder: str = "./logs",
        model_path: str = "./models/best10.pt",
    ) -> None:

        self.upload_folder = upload_folder
        self.output_folder = output_folder
        self.log_folder = log_folder
        self.model = YOLO(model_path)

        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

    def _get_txt_name(self, filename: str) -> str:
        txt_name = filename.replace(".jpg", ".txt").replace(".png", ".txt")
        txt_name = txt_name.replace(".jpeg", ".txt").replace(".JPEG", ".txt")

        return txt_name

    def clear_folders(self) -> None:
        try:
            outputs = glob.glob(os.path.join(self.output_folder, "*"))
            uploads = glob.glob(os.path.join(self.upload_folder, "*"))
            logs = glob.glob(os.path.join(self.log_folder, "*"))

            for file in outputs:
                os.remove(file)

            for file in uploads:
                os.remove(file)

            for file in logs:
                os.remove(file)
        except:
            pass

    def save_frame_and_annotation(
        self, frame, frame_count, bboxes, classes, confs, labels, photos
    ):
        for i, new_box in enumerate(bboxes):
            (x, y, ex, ey) = [int(v) for v in new_box]
            cv2.rectangle(frame, (x, y), (ex, ey), (255, 0, 255), 3)

            cv2.putText(
                frame,
                f"conf: {confs[i]}",
                (x, y - 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 255),
                2,
            )
            cv2.putText(
                frame,
                f"class: {classes[i]}",
                (x, y - 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 255),
                2,
            )

        frame_filename = f"{frame_count}.jpg"
        frame_path = os.path.join(photos, frame_filename)
        cv2.imwrite(frame_path, frame)

        txt_filename = f"{frame_count}.txt"
        txt_path = os.path.join(labels, txt_filename)
        with open(txt_path, "w") as txt_file:
            for i, bbox in enumerate(bboxes):
                (x, y, ex, ey) = [int(v) for v in bbox]
                txt_file.write(f"{x}, {y}, {ex}, {ey}, {confs[i]}, {classes[i]}\n")

        return frame

    def process_images(self, filenames: list) -> None:
        for filename in filenames:
            filepath = os.path.join(self.upload_folder, filename)
            img = Image.open(filepath)

            results = self.model.predict(img, verbose=False, device=0)

            detections = results[0].boxes.xywhn.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy()
            speed = results[0].speed

            logger.info("filename: {}, speed: {}".format(filename, speed))

            txt_name = self._get_txt_name(filename)
            txt_path = os.path.join(self.output_folder, txt_name)
            with open(txt_path, "w") as f:
                for det, cls in zip(detections, class_ids):
                    x_center, y_center, width, height = det
                    class_id = int(cls)
                    f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")

    def process_videos(self, filenames: list) -> wrappers.Response:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        new_output_folder = os.path.join(self.output_folder, timestamp)
        os.makedirs(new_output_folder)
        labels = os.path.join(new_output_folder, "labels")
        photos = os.path.join(new_output_folder, "photos")
        os.makedirs(labels)
        os.makedirs(photos)
        for filename in filenames:
            video_path = os.path.join(self.upload_folder, filename)
            cap = cv2.VideoCapture(video_path)
            frame_count = 0
            frames = []
            output_video_path = os.path.join("app/static/files", "processed_video.webm")
            fps = 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            out = cv2.VideoWriter(
                output_video_path, cv2.VideoWriter_fourcc(*"VP80"), fps, (width, height)
            )

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                results = self.model.predict(image, verbose=False, device=0)

                bboxes = []
                classes = []
                confs = []
                for result in results:
                    if len(result.boxes.xyxy.tolist()) != 0:
                        bboxes.append(result.boxes.xyxy.tolist()[0])
                        classes.append(result.boxes.cls.tolist()[0])
                        confs.append(result.boxes.conf.tolist()[0])

                frame = self.save_frame_and_annotation(
                    frame, frame_count, bboxes, classes, confs, labels, photos
                )
                frames.append(frame)
                frame_count += 1
                out.write(frame)

            cap.release()
            out.release()

            return send_file(
                out, download_name="processed_video.webm", as_attachment=True
            )

    def download_labels(self, filenames: list) -> wrappers.Response:
        memory_file = io.BytesIO()
        with ZipFile(memory_file, "w") as zf:
            for filename in filenames:
                base_name = os.path.splitext(filename)[0]
                zf.write(
                    os.path.join(self.output_folder, f"{base_name}.txt"),
                    f"{base_name}.txt",
                )

            zf.write("logs/model.log")
        memory_file.seek(0)

        return send_file(memory_file, download_name="labels.zip", as_attachment=True)


Utils = DataUtils()
main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    if "filenames" not in session:
        session["filenames"] = []

    if request.method == "POST":
        if "clear" in request.form:
            session.pop("filenames", None)
            Utils.clear_folders()
            return redirect(url_for("main.index"))

        files = request.files.getlist("files")

        if not files or files[0].filename == "":
            flash("Plz select files")
            return redirect(request.url)

        image_filenames = []
        video_filenames = []

        for file in files:
            filename = secure_filename(file.filename)
            filepath = os.path.join(Utils.upload_folder, filename)
            file.save(filepath)

            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type and mime_type.startswith("image"):
                image_filenames.append(filename)
            elif mime_type and mime_type.startswith("video"):
                video_filenames.append(filename)

        # Если загрузили что-то кроме видео и фото
        if len(image_filenames) + len(video_filenames) < len(files):
            flash("Click clear and try again")
            return redirect(url_for("main.index"))

        if len(image_filenames) != 0:
            Utils.process_images(image_filenames)
            return Utils.download_labels(image_filenames)

        if len(video_filenames) != 0:
            Utils.process_videos(video_filenames)
            return render_template("video.html")

    return render_template("main.html", filenames=session["filenames"])


@main.route("/get-fps", methods=["GET"])
def get_fps():
    try:
        cap = cv2.VideoCapture(os.path.join("app/static/files", "processed_video.webm"))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return jsonify({"fps": fps}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def get_latest_annotations_dir(base_dir="./outputs"):
    """Возвращает путь к самой новой папке с метками"""
    subdirs = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]
    latest_subdir = max(subdirs, key=os.path.getmtime)
    return os.path.join(latest_subdir, "labels")


@main.route("/frames-with-objects", methods=["GET"])
def get_frames_with_objects():
    frames_with_objects = []
    annotations_dir = get_latest_annotations_dir()
    for filename in os.listdir(annotations_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(annotations_dir, filename)
            with open(filepath, "r") as file:
                lines = file.readlines()
                has_object = any(line.strip() for line in lines)
                if has_object:
                    frame_number = int(os.path.splitext(filename)[0])
                    frames_with_objects.append(frame_number)
    return jsonify(frames_with_objects)


@main.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("public", filename)


@main.route("/clear", methods=["POST"])
def clear_files():
    session.pop("filenames", None)
    Utils.clear_folders()
    return redirect(url_for("main.index"))
