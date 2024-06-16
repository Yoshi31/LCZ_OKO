const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const clearButton = document.getElementById('clear-button');
const fileUploadInfo = document.getElementById('file-upload-info');
const uploadedImages = document.getElementById('uploaded-images');

uploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    handleFiles(fileInput.files);
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('highlight');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('highlight');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('highlight');
    handleFiles(e.dataTransfer.files);
});

clearButton.addEventListener('click', () => {
    clearFiles();
});

function handleFiles(files) {
    const existingFiles = Array.from(fileInput.files);
    const newFiles = Array.from(files);
    const allFiles = existingFiles.concat(newFiles);

    const dt = new DataTransfer();
    allFiles.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;

    updateFileDisplay();
}

function updateFileDisplay() {
    uploadedImages.innerHTML = '';
    const files = Array.from(fileInput.files);
    if (files.length === 0) {
        fileUploadInfo.innerText = 'No file upload';
    } else {
        fileUploadInfo.innerText = `Upload ${files.length} ${files.length === 1 ? 'file' : 'files'}`;
    }

    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.className = 'image-container';
            div.innerHTML = `
                <img src="${e.target.result}" alt="${file.name}">
                <button class="remove-button">Delete</button>
            `;
            div.querySelector('.remove-button').addEventListener('click', () => {
                removeFile(file.name);
            });
            uploadedImages.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

function removeFile(filename) {
    const dt = new DataTransfer();
    const files = Array.from(fileInput.files).filter(file => file.name !== filename);
    files.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;

    updateFileDisplay();
}

function clearFiles() {
    fetch('/clear', { method: 'POST' })
        .then(() => {
            fileUploadInfo.innerText = 'No file upload';
            uploadedImages.innerHTML = '';
            fileInput.value = null;
        });
}

updateFileDisplay();
