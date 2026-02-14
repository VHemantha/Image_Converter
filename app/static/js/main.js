/**
 * Main JavaScript for Image Converter Pro
 * Handles drag-and-drop, file preview, form submission, and results display
 */

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');
const convertBtn = document.getElementById('convertBtn');
const convertBtnText = document.getElementById('convertBtnText');
const convertBtnSpinner = document.getElementById('convertBtnSpinner');
const filePreviewContainer = document.getElementById('filePreviewContainer');
const filePreviewGrid = document.getElementById('filePreviewGrid');
const resultsContainer = document.getElementById('resultsContainer');
const resultsContent = document.getElementById('resultsContent');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');

// State
let selectedFiles = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
    setupFileInput();
    setupFormSubmit();
});

/**
 * Set up drag and drop functionality
 */
function setupDragAndDrop() {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when dragging over
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    dropZone.classList.add('border-blue-500', 'bg-blue-50', 'dark:bg-blue-900');
}

function unhighlight() {
    dropZone.classList.remove('border-blue-500', 'bg-blue-50', 'dark:bg-blue-900');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

/**
 * Set up file input change listener
 */
function setupFileInput() {
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

/**
 * Handle selected files
 */
function handleFiles(files) {
    selectedFiles = Array.from(files);

    if (selectedFiles.length === 0) {
        filePreviewContainer.classList.add('hidden');
        convertBtn.disabled = true;
        return;
    }

    // Validate files
    const validFiles = selectedFiles.filter(file => {
        // Check if it's an image
        if (!file.type.startsWith('image/')) {
            showToast(`${file.name} is not an image file`, 'error');
            return false;
        }

        // Check file size (50MB max)
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            showToast(`${file.name} exceeds maximum file size (50MB)`, 'error');
            return false;
        }

        return true;
    });

    if (validFiles.length !== selectedFiles.length) {
        selectedFiles = validFiles;
    }

    if (selectedFiles.length > 0) {
        displayFilePreviews();
        convertBtn.disabled = false;
        filePreviewContainer.classList.remove('hidden');
    } else {
        filePreviewContainer.classList.add('hidden');
        convertBtn.disabled = true;
    }
}

/**
 * Display file previews
 */
function displayFilePreviews() {
    filePreviewGrid.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const reader = new FileReader();

        reader.onload = (e) => {
            const previewCard = createPreviewCard(file, e.target.result, index);
            filePreviewGrid.appendChild(previewCard);
        };

        reader.readAsDataURL(file);
    });
}

/**
 * Create preview card for a file
 */
function createPreviewCard(file, dataUrl, index) {
    const card = document.createElement('div');
    card.className = 'relative bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden transition-colors duration-200';

    const img = document.createElement('img');
    img.src = dataUrl;
    img.alt = file.name;
    img.className = 'w-full h-32 object-cover';

    const info = document.createElement('div');
    info.className = 'p-2';

    const name = document.createElement('p');
    name.className = 'text-sm text-gray-900 dark:text-white truncate font-medium';
    name.textContent = file.name;
    name.title = file.name;

    const size = document.createElement('p');
    size.className = 'text-xs text-gray-500 dark:text-gray-400';
    size.textContent = formatFileSize(file.size);

    // Remove button
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full p-1 transition-colors';
    removeBtn.innerHTML = `
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
    `;
    removeBtn.onclick = () => removeFile(index);

    info.appendChild(name);
    info.appendChild(size);
    card.appendChild(img);
    card.appendChild(info);
    card.appendChild(removeBtn);

    return card;
}

/**
 * Remove file from selection
 */
function removeFile(index) {
    selectedFiles.splice(index, 1);

    if (selectedFiles.length === 0) {
        filePreviewContainer.classList.add('hidden');
        convertBtn.disabled = true;
        fileInput.value = '';
    } else {
        displayFilePreviews();
    }
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Set up form submission
 */
function setupFormSubmit() {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Disable button and show loading state
        convertBtn.disabled = true;
        convertBtnText.textContent = 'Converting...';
        convertBtnSpinner.classList.remove('hidden');

        try {
            const formData = new FormData(uploadForm);

            // Clear previous file input and add selected files
            formData.delete('files');
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            // Submit form
            const response = await fetch(uploadForm.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Check if this is an async response (Celery)
                if (result.async) {
                    // Poll for task completion
                    showToast('Conversion started. Checking progress...', 'info');
                    await pollTaskStatus(result.task_id);
                } else {
                    // Synchronous response - results ready immediately
                    displayResults(result);
                    showToast(`Successfully converted ${result.successful} of ${result.total_files} images`, 'success');
                }
            } else {
                showToast(result.error || 'Conversion failed', 'error');
            }

        } catch (error) {
            console.error('Error:', error);
            showToast('An error occurred during conversion', 'error');
        } finally {
            // Re-enable button and hide loading state
            convertBtn.disabled = false;
            convertBtnText.textContent = 'Convert Images';
            convertBtnSpinner.classList.add('hidden');
        }
    });
}

/**
 * Poll task status for async conversions
 */
async function pollTaskStatus(taskId) {
    const maxAttempts = 60; // 60 seconds timeout
    let attempts = 0;

    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`/status/${taskId}`);
            const status = await response.json();

            if (status.state === 'SUCCESS') {
                // Task completed successfully
                const taskResult = status.result;
                displayResults(taskResult);
                showToast(`Successfully converted ${taskResult.successful} of ${taskResult.total_files} images`, 'success');
                return;
            } else if (status.state === 'FAILURE') {
                // Task failed
                showToast(status.error || 'Conversion failed', 'error');
                return;
            } else if (status.state === 'PROGRESS') {
                // Update progress (could add progress bar here)
                console.log(`Progress: ${status.progress}% - ${status.status}`);
            }

            // Wait 1 second before next poll
            await new Promise(resolve => setTimeout(resolve, 1000));
            attempts++;

        } catch (error) {
            console.error('Error polling task status:', error);
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    // Timeout
    showToast('Task timeout - please check results manually', 'error');
}

/**
 * Display conversion results
 */
function displayResults(result) {
    resultsContent.innerHTML = '';

    // Create results summary
    const summary = document.createElement('div');
    summary.className = 'bg-blue-100 dark:bg-blue-900 rounded-lg p-4 mb-4';
    summary.innerHTML = `
        <div class="flex items-center justify-between">
            <div>
                <p class="text-lg font-semibold text-blue-900 dark:text-blue-100">
                    Conversion Complete
                </p>
                <p class="text-sm text-blue-700 dark:text-blue-300">
                    ${result.successful} successful, ${result.failed} failed
                </p>
            </div>
            <svg class="h-12 w-12 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        </div>
    `;
    resultsContent.appendChild(summary);

    // Create results table
    const table = document.createElement('div');
    table.className = 'space-y-3';

    result.results.forEach(item => {
        const row = createResultRow(item, result.task_id);
        table.appendChild(row);
    });

    resultsContent.appendChild(table);
    resultsContainer.classList.remove('hidden');

    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Create result row for a converted file
 */
function createResultRow(item, taskId) {
    const row = document.createElement('div');
    row.className = `bg-white dark:bg-gray-700 rounded-lg p-4 shadow transition-colors duration-200 ${item.success ? '' : 'border-l-4 border-red-500'}`;

    if (item.success) {
        row.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <p class="font-medium text-gray-900 dark:text-white">${item.original_filename}</p>
                    <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400 mt-1">
                        <span>${item.source_format} → ${item.target_format}</span>
                        <span>${item.input_size.toFixed(2)} MB → ${item.output_size.toFixed(2)} MB</span>
                        <span class="${item.compression_ratio > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
                            ${item.compression_ratio > 0 ? '-' : '+'}${Math.abs(item.compression_ratio).toFixed(1)}%
                        </span>
                    </div>
                </div>
                <a href="/download/${taskId}/${item.converted_filename}"
                   class="ml-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center space-x-2"
                   download>
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span>Download</span>
                </a>
            </div>
        `;
    } else {
        row.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <p class="font-medium text-gray-900 dark:text-white">${item.original_filename}</p>
                    <p class="text-sm text-red-600 dark:text-red-400 mt-1">
                        Error: ${item.error}
                    </p>
                </div>
                <svg class="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
        `;
    }

    return row;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    toastMessage.textContent = message;

    // Set color based on type
    if (type === 'error') {
        toast.className = 'fixed bottom-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    } else if (type === 'success') {
        toast.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    } else {
        toast.className = 'fixed bottom-4 right-4 bg-gray-900 dark:bg-gray-700 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    }

    toast.classList.remove('hidden');

    // Hide after 5 seconds
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 5000);
}
