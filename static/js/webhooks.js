/**
 * Webhooks page functionality
 * Handles webhook listing, CRUD operations, and testing
 */

const API_BASE = '/api';
let eventTypes = [];
let deleteWebhookId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadEventTypes();
    loadWebhooks();
});

/**
 * Load available event types
 */
async function loadEventTypes() {
    try {
        const response = await fetch(`${API_BASE}/webhooks/event_types/`);
        eventTypes = await response.json();

        const select = document.getElementById('webhookEventType');
        select.innerHTML = '<option value="">Select event type...</option>' +
            eventTypes.map(et => `<option value="${et.value}">${et.label}</option>`).join('');

    } catch (error) {
        console.error('Error loading event types:', error);
    }
}

/**
 * Load webhooks list
 */
async function loadWebhooks() {
    try {
        const response = await fetch(`${API_BASE}/webhooks/`);
        const data = await response.json();

        // Handle both paginated and non-paginated responses
        const webhooks = data.results || data;
        renderWebhooks(webhooks);

    } catch (error) {
        console.error('Error loading webhooks:', error);
        showToast('Failed to load webhooks', 'error');
    }
}

/**
 * Render webhooks table
 */
function renderWebhooks(webhooks) {
    const tbody = document.getElementById('webhooksTableBody');

    if (webhooks.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">🔗</div>
                        <h3 class="empty-state-title">No webhooks configured</h3>
                        <p class="empty-state-description">Add webhooks to receive notifications when products are modified.</p>
                        <button class="btn btn-primary" onclick="openWebhookModal()">Add Webhook</button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = webhooks.map(webhook => `
        <tr>
            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">
                <code>${escapeHtml(webhook.url)}</code>
            </td>
            <td>
                <span class="badge badge-info">${escapeHtml(webhook.event_type_display)}</span>
            </td>
            <td>
                <span class="badge ${webhook.is_active ? 'badge-success' : 'badge-danger'}">
                    ${webhook.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="text-muted text-sm">
                ${webhook.last_triggered_at ? formatDate(webhook.last_triggered_at) : 'Never'}
            </td>
            <td>
                ${webhook.last_response_code ? `
                    <span class="badge ${webhook.last_response_code >= 200 && webhook.last_response_code < 300 ? 'badge-success' : 'badge-danger'}">
                        ${webhook.last_response_code}
                    </span>
                    ${webhook.last_response_time_ms ? `<span class="text-sm text-muted">${webhook.last_response_time_ms}ms</span>` : ''}
                ` : '<span class="text-muted">-</span>'}
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-sm btn-success" onclick="testWebhook(${webhook.id})" title="Test">
                        🧪
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="editWebhook(${webhook.id})" title="Edit">
                        ✏️
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="confirmDeleteWebhook(${webhook.id})" title="Delete">
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Open webhook modal for creating
 */
function openWebhookModal() {
    document.getElementById('webhookModalTitle').textContent = 'Add Webhook';
    document.getElementById('webhookId').value = '';
    document.getElementById('webhookUrl').value = '';
    document.getElementById('webhookEventType').value = '';
    document.getElementById('webhookActive').checked = true;
    document.getElementById('webhookModal').classList.add('active');
}

/**
 * Edit existing webhook
 */
async function editWebhook(id) {
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}/`);
        const webhook = await response.json();

        document.getElementById('webhookModalTitle').textContent = 'Edit Webhook';
        document.getElementById('webhookId').value = webhook.id;
        document.getElementById('webhookUrl').value = webhook.url;
        document.getElementById('webhookEventType').value = webhook.event_type;
        document.getElementById('webhookActive').checked = webhook.is_active;
        document.getElementById('webhookModal').classList.add('active');

    } catch (error) {
        console.error('Error loading webhook:', error);
        showToast('Failed to load webhook', 'error');
    }
}

/**
 * Close webhook modal
 */
function closeWebhookModal() {
    document.getElementById('webhookModal').classList.remove('active');
}

/**
 * Save webhook (create or update)
 */
async function saveWebhook() {
    const id = document.getElementById('webhookId').value;
    const data = {
        url: document.getElementById('webhookUrl').value.trim(),
        event_type: document.getElementById('webhookEventType').value,
        is_active: document.getElementById('webhookActive').checked
    };

    if (!data.url || !data.event_type) {
        showToast('URL and Event Type are required', 'error');
        return;
    }

    try {
        const url = id ? `${API_BASE}/webhooks/${id}/` : `${API_BASE}/webhooks/`;
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.url?.[0] || error.detail || 'Save failed');
        }

        closeWebhookModal();
        loadWebhooks();
        showToast(id ? 'Webhook updated successfully' : 'Webhook created successfully');

    } catch (error) {
        console.error('Error saving webhook:', error);
        showToast(error.message, 'error');
    }
}

/**
 * Test a webhook
 */
async function testWebhook(id) {
    try {
        showToast('Testing webhook...', 'success');

        const response = await fetch(`${API_BASE}/webhooks/${id}/test/`, {
            method: 'POST'
        });

        const result = await response.json();
        showTestResult(result);
        loadWebhooks(); // Refresh to show updated last_triggered info

    } catch (error) {
        console.error('Error testing webhook:', error);
        showToast('Failed to test webhook', 'error');
    }
}

/**
 * Show test result in modal
 */
function showTestResult(result) {
    const content = document.getElementById('testResultContent');

    if (result.success) {
        content.innerHTML = `
            <div class="alert alert-success">
                <span class="alert-icon">✅</span>
                <div>
                    <strong>Test Successful!</strong><br>
                    Response Code: ${result.response_code}<br>
                    Response Time: ${result.response_time_ms}ms
                </div>
            </div>
        `;
    } else {
        content.innerHTML = `
            <div class="alert alert-danger">
                <span class="alert-icon">❌</span>
                <div>
                    <strong>Test Failed</strong><br>
                    ${result.error || 'Unknown error'}
                    ${result.response_code ? `<br>Response Code: ${result.response_code}` : ''}
                </div>
            </div>
        `;
    }

    document.getElementById('testResultModal').classList.add('active');
}

/**
 * Close test result modal
 */
function closeTestResultModal() {
    document.getElementById('testResultModal').classList.remove('active');
}

/**
 * Confirm delete webhook
 */
function confirmDeleteWebhook(id) {
    deleteWebhookId = id;
    document.getElementById('deleteWebhookModal').classList.add('active');
}

/**
 * Close delete modal
 */
function closeDeleteWebhookModal() {
    document.getElementById('deleteWebhookModal').classList.remove('active');
    deleteWebhookId = null;
}

/**
 * Execute delete webhook
 */
async function executeDeleteWebhook() {
    try {
        const response = await fetch(`${API_BASE}/webhooks/${deleteWebhookId}/`, {
            method: 'DELETE'
        });

        if (!response.ok && response.status !== 204) {
            throw new Error('Delete failed');
        }

        closeDeleteWebhookModal();
        loadWebhooks();
        showToast('Webhook deleted successfully');

    } catch (error) {
        console.error('Error deleting webhook:', error);
        showToast('Delete failed', 'error');
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

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
