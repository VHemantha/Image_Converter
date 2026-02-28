/**
 * PDF Converter — Frontend logic for the Image to PDF converter.
 * Handles file selection, previews, upload, and download.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ─── State ───────────────────────────────────────────────────────────────
    let selectedFiles = [];

    // ─── DOM references ───────────────────────────────────────────────────────
    const dropZone              = document.getElementById('pdfDropZone');
    const fileInput             = document.getElementById('pdfFileInput');
    const filePreviewContainer  = document.getElementById('pdfFilePreviewContainer');
    const filePreviewGrid       = document.getElementById('pdfFilePreviewGrid');
    const fileCountLabel        = document.getElementById('pdfFileCount');
    const infoBox               = document.getElementById('pdfInfoBox');
    const convertBtn            = document.getElementById('pdfConvertBtn');
    const convertBtnText        = document.getElementById('pdfConvertBtnText');
    const convertBtnSpinner     = document.getElementById('pdfConvertBtnSpinner');
    const resultsContainer      = document.getElementById('pdfResultsContainer');
    const toast                 = document.getElementById('pdfToast');
    const toastMessage          = document.getElementById('pdfToastMessage');

    // ─── Drag-and-drop ────────────────────────────────────────────────────────
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-red-500', 'bg-red-50', 'dark:bg-red-900/10');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-red-500', 'bg-red-50', 'dark:bg-red-900/10');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-red-500', 'bg-red-50', 'dark:bg-red-900/10');
        handleFiles(e.dataTransfer.files);
    });

    // Click on drop zone also opens file picker (unless user clicks the button)
    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON') {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', () => {
        handleFiles(fileInput.files);
        // Reset input so same files can be re-selected after removal
        fileInput.value = '';
    });

    // ─── File handling ────────────────────────────────────────────────────────
    function handleFiles(files) {
        const imageFiles = Array.from(files).filter((f) => f.type.startsWith('image/'));
        const rejected   = Array.from(files).length - imageFiles.length;

        if (rejected > 0) {
            showToast(`${rejected} file(s) skipped — only image files are supported.`, 'error');
        }

        const oversized = imageFiles.filter((f) => f.size > 50 * 1024 * 1024);
        if (oversized.length > 0) {
            showToast(`${oversized.length} file(s) exceed the 50 MB limit and were skipped.`, 'error');
        }

        const validFiles = imageFiles.filter((f) => f.size <= 50 * 1024 * 1024);
        selectedFiles = [...selectedFiles, ...validFiles];

        renderPreviews();
        updateUI();
    }

    function renderPreviews() {
        if (selectedFiles.length === 0) {
            filePreviewContainer.classList.add('hidden');
            infoBox.classList.add('hidden');
            return;
        }

        filePreviewContainer.classList.remove('hidden');
        infoBox.classList.remove('hidden');
        fileCountLabel.textContent = `(${selectedFiles.length} image${selectedFiles.length !== 1 ? 's' : ''})`;
        filePreviewGrid.innerHTML = '';

        selectedFiles.forEach((file, index) => {
            const card = document.createElement('div');
            card.className = 'relative bg-gray-50 dark:bg-gray-700 rounded-xl overflow-hidden shadow-sm slide-in-card';

            const reader = new FileReader();
            reader.onload = (e) => {
                card.innerHTML = `
                    <div class="relative">
                        <img src="${e.target.result}"
                             alt="${escapeHtml(file.name)}"
                             class="w-full h-28 object-cover">
                        <button
                            onclick="window.pdfRemoveFile(${index})"
                            class="absolute top-1 right-1 bg-red-600 hover:bg-red-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs leading-none shadow transition-colors"
                            title="Remove">
                            &times;
                        </button>
                        <span class="absolute bottom-1 left-1 bg-black/50 text-white text-xs px-1.5 py-0.5 rounded">
                            Page ${index + 1}
                        </span>
                    </div>
                    <div class="p-2">
                        <p class="text-xs text-gray-800 dark:text-gray-200 truncate font-medium" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">${formatFileSize(file.size)}</p>
                    </div>
                `;
            };
            reader.readAsDataURL(file);
            filePreviewGrid.appendChild(card);
        });
    }

    window.pdfRemoveFile = function (index) {
        selectedFiles.splice(index, 1);
        renderPreviews();
        updateUI();
    };

    window.clearAllFiles = function () {
        selectedFiles = [];
        renderPreviews();
        updateUI();
        resultsContainer.classList.add('hidden');
    };

    function updateUI() {
        convertBtn.disabled = selectedFiles.length === 0;
    }

    // ─── Conversion ───────────────────────────────────────────────────────────
    convertBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;

        setLoadingState(true);

        const csrfTokenEl = document.querySelector('input[name="csrf_token"]');
        if (!csrfTokenEl) {
            showToast('Security token missing. Please refresh the page.', 'error');
            setLoadingState(false);
            return;
        }

        const formData = new FormData();
        formData.append('csrf_token', csrfTokenEl.value);
        selectedFiles.forEach((file) => formData.append('files', file));

        try {
            const response = await fetch('/upload-pdf', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                showResults(data);
            } else {
                showToast(data.error || 'Conversion failed. Please try again.', 'error');
            }
        } catch (err) {
            showToast('Network error. Please check your connection and try again.', 'error');
        } finally {
            setLoadingState(false);
        }
    });

    function setLoadingState(loading) {
        convertBtn.disabled = loading;
        convertBtnSpinner.classList.toggle('hidden', !loading);
        convertBtnText.textContent = loading ? 'Converting...' : 'Convert to PDF';
    }

    // ─── Results ──────────────────────────────────────────────────────────────
    function showResults(data) {
        resultsContainer.classList.remove('hidden');
        resultsContainer.innerHTML = `
            <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-8 text-center">
                <div class="flex justify-center mb-4">
                    <div class="bg-green-100 dark:bg-green-800 rounded-full p-4">
                        <svg class="h-12 w-12 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                </div>
                <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">PDF Created Successfully!</h3>
                <p class="text-gray-600 dark:text-gray-300 mb-6">
                    Your PDF has <strong>${data.page_count}</strong> page${data.page_count !== 1 ? 's' : ''}
                    &bull; File size: <strong>${formatFileSize(data.file_size)}</strong>
                </p>
                <div class="flex flex-col sm:flex-row justify-center gap-3">
                    <a href="${escapeHtml(data.download_url)}"
                       class="inline-flex items-center justify-center px-8 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-md transition-colors text-lg"
                       download="converted.pdf">
                        <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Download PDF
                    </a>
                    <button
                        onclick="window.clearAllFiles()"
                        class="inline-flex items-center justify-center px-8 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-semibold rounded-xl transition-colors text-lg">
                        Convert More Images
                    </button>
                </div>
            </div>
        `;
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // ─── Toast ────────────────────────────────────────────────────────────────
    let toastTimeout;
    function showToast(message, type = 'info') {
        toast.classList.remove('hidden', 'bg-red-600', 'bg-green-600', 'bg-gray-800');
        toast.classList.add(type === 'error' ? 'bg-red-600' : type === 'success' ? 'bg-green-600' : 'bg-gray-800');
        toastMessage.textContent = message;
        toast.classList.remove('hidden');

        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => toast.classList.add('hidden'), 5000);
    }

    // ─── Helpers ──────────────────────────────────────────────────────────────
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }
});
