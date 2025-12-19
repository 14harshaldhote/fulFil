/**
 * Upload page functionality
 * Handles CSV file upload with drag-and-drop and real-time progress tracking via SSE
 */

const API_BASE = '/api';
let currentJobId = null;
let eventSource = null;

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressMessage = document.getElementById('progressMessage');
const progressPercent = document.getElementById('progressPercent');
const progressDetails = document.getElementById('progressDetails');
const processedRows = document.getElementById('processedRows');
const totalRows = document.getElementById('totalRows');
const resultSection = document.getElementById('resultSection');
const resultAlert = document.getElementById('resultAlert');

// Upload zone click handler
uploadZone.addEventListener('click', () => {
    if (!uploadZone.classList.contains('uploading')) {
        fileInput.click();
    }
});

// File input change handler
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

// Drag and drop handlers
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    if (!uploadZone.classList.contains('uploading')) {
        uploadZone.classList.add('dragover');
    }
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');

    if (!uploadZone.classList.contains('uploading') && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.name.toLowerCase().endsWith('.csv')) {
            handleFileUpload(file);
        } else {
            showToast('Please upload a CSV file', 'error');
        }
    }
});

/**
 * Handle the file upload process
 */
async function handleFileUpload(file) {
    // Update UI to show uploading state
    uploadZone.classList.add('uploading');
    progressContainer.classList.add('active');
    resultSection.style.display = 'none';

    updateProgress(0, 'Uploading file...');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/products/upload/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.file?.[0] || error.detail || 'Upload failed');
        }

        const job = await response.json();
        currentJobId = job.id;

        // Start listening for progress updates
        startProgressTracking(job.id);

    } catch (error) {
        showError(error.message);
    }
}

/**
 * Start tracking upload progress via SSE
 */
function startProgressTracking(jobId) {
    // Close any existing connection
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`${API_BASE}/products/upload/${jobId}/status/`);

    eventSource.onmessage = (event) => {
        try {
            const job = JSON.parse(event.data);

            if (job.error) {
                throw new Error(job.error);
            }

            // Update progress UI
            const statusMessages = {
                'pending': 'Preparing...',
                'parsing': 'Parsing CSV file...',
                'validating': 'Validating data...',
                'importing': 'Importing products...',
                'completed': 'Import complete!',
                'failed': 'Import failed'
            };

            updateProgress(job.progress_percentage, statusMessages[job.status] || job.status);

            // Show row counts for importing status
            if (job.status === 'importing' && job.total_rows > 0) {
                progressDetails.style.display = 'block';
                processedRows.textContent = job.processed_rows.toLocaleString();
                totalRows.textContent = job.total_rows.toLocaleString();
            }

            // Handle completion
            if (job.is_complete) {
                eventSource.close();

                if (job.status === 'completed') {
                    showSuccess(job);
                } else {
                    showError(job.error_message || 'Import failed');
                }
            }

        } catch (error) {
            console.error('Error parsing SSE data:', error);
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        // Fall back to polling
        pollProgress(jobId);
    };
}

/**
 * Fallback polling for environments that don't support SSE
 */
async function pollProgress(jobId) {
    try {
        const response = await fetch(`${API_BASE}/products/upload/${jobId}/status/`);
        const job = await response.json();

        const statusMessages = {
            'pending': 'Preparing...',
            'parsing': 'Parsing CSV file...',
            'validating': 'Validating data...',
            'importing': 'Importing products...',
            'completed': 'Import complete!',
            'failed': 'Import failed'
        };

        updateProgress(job.progress_percentage, statusMessages[job.status] || job.status);

        if (job.status === 'importing' && job.total_rows > 0) {
            progressDetails.style.display = 'block';
            processedRows.textContent = job.processed_rows.toLocaleString();
            totalRows.textContent = job.total_rows.toLocaleString();
        }

        if (job.is_complete) {
            if (job.status === 'completed') {
                showSuccess(job);
            } else {
                showError(job.error_message || 'Import failed');
            }
        } else {
            // Continue polling
            setTimeout(() => pollProgress(jobId), 1000);
        }

    } catch (error) {
        console.error('Polling error:', error);
        showError('Failed to track upload progress');
    }
}

/**
 * Update progress bar UI
 */
function updateProgress(percent, message) {
    progressFill.style.width = `${percent}%`;
    progressPercent.textContent = `${percent}%`;
    progressMessage.textContent = message;
}

/**
 * Show success result with detailed import summary
 */
function showSuccess(job) {
    uploadZone.classList.remove('uploading');
    resultSection.style.display = 'block';

    const totalImported = job.successful_rows + job.duplicate_rows;
    const hasWarnings = job.failed_rows > 0 || job.skipped_rows > 0;

    let summaryHtml = `
        <div class="alert ${hasWarnings ? 'alert-warning' : 'alert-success'}">
            <span class="alert-icon">${hasWarnings ? '⚠️' : '✅'}</span>
            <div>
                <strong>${hasWarnings ? 'Import Completed with Warnings' : 'Import Successful!'}</strong>
            </div>
        </div>
        
        <div class="import-summary" style="background: var(--bg-secondary); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
            <h4 style="margin: 0 0 1rem 0; font-size: 0.9rem; color: var(--text-secondary);">📊 Import Summary</h4>
            <table style="width: 100%; font-size: 0.9rem;">
                <tr>
                    <td style="padding: 0.25rem 0; color: var(--text-secondary);">Total rows in file:</td>
                    <td style="padding: 0.25rem 0; text-align: right; font-weight: 600;">${job.total_rows.toLocaleString()}</td>
                </tr>
                <tr>
                    <td style="padding: 0.25rem 0; color: var(--text-secondary);">Rows processed:</td>
                    <td style="padding: 0.25rem 0; text-align: right; font-weight: 600;">${job.processed_rows.toLocaleString()}</td>
                </tr>
                <tr style="border-top: 1px solid var(--border-color);">
                    <td style="padding: 0.5rem 0 0.25rem; color: var(--success);">✓ New products imported:</td>
                    <td style="padding: 0.5rem 0 0.25rem; text-align: right; font-weight: 600; color: var(--success);">${job.successful_rows.toLocaleString()}</td>
                </tr>
                <tr>
                    <td style="padding: 0.25rem 0; color: var(--info);">↻ Duplicates overwritten:</td>
                    <td style="padding: 0.25rem 0; text-align: right; font-weight: 600; color: var(--info);">${job.duplicate_rows.toLocaleString()}</td>
                </tr>
                ${job.failed_rows > 0 ? `
                <tr>
                    <td style="padding: 0.25rem 0; color: var(--danger);">✗ Failed (missing SKU):</td>
                    <td style="padding: 0.25rem 0; text-align: right; font-weight: 600; color: var(--danger);">${job.failed_rows.toLocaleString()}</td>
                </tr>
                ` : ''}
                ${job.skipped_rows > 0 ? `
                <tr>
                    <td style="padding: 0.25rem 0; color: var(--warning);">⚠ Skipped (errors):</td>
                    <td style="padding: 0.25rem 0; text-align: right; font-weight: 600; color: var(--warning);">${job.skipped_rows.toLocaleString()}</td>
                </tr>
                ` : ''}
                <tr style="border-top: 1px solid var(--border-color);">
                    <td style="padding: 0.5rem 0 0; font-weight: 600;">Total products in DB:</td>
                    <td style="padding: 0.5rem 0 0; text-align: right; font-weight: 700; font-size: 1.1rem;">${totalImported.toLocaleString()}</td>
                </tr>
            </table>
        </div>
    `;

    resultAlert.innerHTML = summaryHtml;
}

/**
 * Show error result
 */
function showError(message) {
    uploadZone.classList.remove('uploading');
    resultSection.style.display = 'block';

    resultAlert.innerHTML = `
        <div class="alert alert-danger">
            <span class="alert-icon">❌</span>
            <div>
                <strong>Import Failed</strong><br>
                ${message}
            </div>
        </div>
    `;
}

/**
 * Reset upload UI for another file
 */
function resetUpload() {
    uploadZone.classList.remove('uploading');
    progressContainer.classList.remove('active');
    resultSection.style.display = 'none';
    progressDetails.style.display = 'none';
    updateProgress(0, 'Preparing...');
    fileInput.value = '';
    currentJobId = null;

    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${type === 'success' ? '✅' : '❌'}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.2s ease reverse';
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}
