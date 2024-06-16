import VideoTimeline from 'video-timeline.js'

// Получить ссылки на видеоплеер и кнопки
const videoPlayer = document.getElementById('videoPlayer');
const playButton = document.getElementById('playButton');
const pauseButton = document.getElementById('pauseButton');
const deleteButton = document.getElementById('deleteButton');

// Проверяем наличие обработанного видео файла в папке "outputs"
function checkVideoFile() {
    fetch('/check-video-file')
        .then(response => response.json())
        .then(data => {
            if (data.exists && data.filename === 'processed_test_video.mp4' && data.path === 'outputs') {
                videoPlayer.src = `/Users/apple/Downloads/i_yolo_web_service/outputs/processed_video.mp4`; // Установить путь к обработанному видео файлу
                videoPlayer.style.display = 'block';
                playButton.style.display = 'inline-block';
                pauseButton.style.display = 'inline-block';
                deleteButton.style.display = 'inline-block';

                videoPlayer.addEventListener('canplay', function() {
                    videoPlayer.play();
                });
            }
        })
        .catch(error => {
            console.error('Ошибка при проверке файла видео:', error);
        });
}

// Проверяем наличие файла каждые 2 секунды
const intervalId = setInterval(checkVideoFile, 2000);

// Обработчики событий для кнопок
playButton.addEventListener('click', function() {
    videoPlayer.play();
});

pauseButton.addEventListener('click', function() {
    videoPlayer.pause();
});

deleteButton.addEventListener('click', function() {
    // Добавьте код для удаления видео, если это необходимо
});

checkVideoFile();