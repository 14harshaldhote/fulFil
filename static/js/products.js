/**
 * Products page functionality
 * Handles product listing, filtering, CRUD operations, and bulk delete
 */

const API_BASE = '/api';
let currentPage = 1;
let pageSize = 25;
let totalPages = 1;
let deleteProductId = null;
let isBulkDelete = false;

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadProducts();

    // Add enter key listener to filter inputs
    document.querySelectorAll('.filters-bar input').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') applyFilters();
        });
    });
});

/**
 * Load product statistics
 */
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/products/stats/`);
        const stats = await response.json();

        document.getElementById('totalProducts').textContent = stats.total.toLocaleString();
        document.getElementById('activeProducts').textContent = stats.active.toLocaleString();
        document.getElementById('inactiveProducts').textContent = stats.inactive.toLocaleString();
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Load products with current filters and pagination
 */
async function loadProducts() {
    const params = new URLSearchParams();
    params.append('page', currentPage);

    // Add filters
    const sku = document.getElementById('filterSku').value.trim();
    const name = document.getElementById('filterName').value.trim();
    const status = document.getElementById('filterStatus').value;
    const description = document.getElementById('filterDescription').value.trim();

    if (sku) params.append('sku', sku);
    if (name) params.append('name', name);
    if (status) params.append('is_active', status);
    if (description) params.append('description', description);

    try {
        const response = await fetch(`${API_BASE}/products/?${params}`);
        const data = await response.json();

        renderProducts(data.results);
        renderPagination(data.count, data.next, data.previous);

    } catch (error) {
        console.error('Error loading products:', error);
        showToast('Failed to load products', 'error');
    }
}

/**
 * Render products table
 */
function renderProducts(products) {
    const tbody = document.getElementById('productsTableBody');

    if (products.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">📦</div>
                        <h3 class="empty-state-title">No products found</h3>
                        <p class="empty-state-description">Upload a CSV file or add products manually to get started.</p>
                        <a href="/" class="btn btn-primary">Upload CSV</a>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = products.map(product => `
        <tr>
            <td><strong>${escapeHtml(product.sku)}</strong></td>
            <td>${escapeHtml(product.name)}</td>
            <td class="text-muted">${escapeHtml(product.description || '-')}</td>
            <td>
                <span class="badge ${product.is_active ? 'badge-success' : 'badge-danger'}">
                    ${product.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="text-muted text-sm">${formatDate(product.created_at)}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-sm btn-outline" onclick="editProduct(${product.id})" title="Edit">
                        ✏️
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="confirmDeleteProduct(${product.id})" title="Delete">
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Render pagination controls
 */
function renderPagination(totalCount, nextUrl, prevUrl) {
    totalPages = Math.ceil(totalCount / pageSize);
    const pagination = document.getElementById('pagination');

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // Previous button
    html += `<button class="pagination-btn" onclick="goToPage(${currentPage - 1})" ${!prevUrl ? 'disabled' : ''}>← Prev</button>`;

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        html += `<button class="pagination-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) html += `<span class="pagination-info">...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span class="pagination-info">...</span>`;
        html += `<button class="pagination-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    // Next button
    html += `<button class="pagination-btn" onclick="goToPage(${currentPage + 1})" ${!nextUrl ? 'disabled' : ''}>Next →</button>`;

    // Info
    html += `<span class="pagination-info">${totalCount.toLocaleString()} products</span>`;

    pagination.innerHTML = html;
}

/**
 * Go to specific page
 */
function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadProducts();
}

/**
 * Apply filters
 */
function applyFilters() {
    currentPage = 1;
    loadProducts();
}

/**
 * Clear filters
 */
function clearFilters() {
    document.getElementById('filterSku').value = '';
    document.getElementById('filterName').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterDescription').value = '';
    applyFilters();
}

/**
 * Open product modal for creating a new product
 */
function openProductModal() {
    document.getElementById('modalTitle').textContent = 'Add Product';
    document.getElementById('productId').value = '';
    document.getElementById('productSku').value = '';
    document.getElementById('productName').value = '';
    document.getElementById('productDescription').value = '';
    document.getElementById('productActive').checked = true;
    document.getElementById('productSku').disabled = false;
    document.getElementById('productModal').classList.add('active');
}

/**
 * Edit existing product
 */
async function editProduct(id) {
    try {
        const response = await fetch(`${API_BASE}/products/${id}/`);
        const product = await response.json();

        document.getElementById('modalTitle').textContent = 'Edit Product';
        document.getElementById('productId').value = product.id;
        document.getElementById('productSku').value = product.sku;
        document.getElementById('productName').value = product.name;
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productActive').checked = product.is_active;
        document.getElementById('productSku').disabled = true; // SKU can't be changed
        document.getElementById('productModal').classList.add('active');

    } catch (error) {
        console.error('Error loading product:', error);
        showToast('Failed to load product', 'error');
    }
}

/**
 * Close product modal
 */
function closeProductModal() {
    document.getElementById('productModal').classList.remove('active');
}

/**
 * Save product (create or update)
 */
async function saveProduct() {
    const id = document.getElementById('productId').value;
    const data = {
        sku: document.getElementById('productSku').value.trim(),
        name: document.getElementById('productName').value.trim(),
        description: document.getElementById('productDescription').value.trim(),
        is_active: document.getElementById('productActive').checked
    };

    if (!data.sku || !data.name) {
        showToast('SKU and Name are required', 'error');
        return;
    }

    try {
        const url = id ? `${API_BASE}/products/${id}/` : `${API_BASE}/products/`;
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.sku?.[0] || error.detail || 'Save failed');
        }

        closeProductModal();
        loadProducts();
        loadStats();
        showToast(id ? 'Product updated successfully' : 'Product created successfully');

    } catch (error) {
        console.error('Error saving product:', error);
        showToast(error.message, 'error');
    }
}

/**
 * Confirm delete single product
 */
function confirmDeleteProduct(id) {
    deleteProductId = id;
    isBulkDelete = false;
    document.getElementById('deleteMessage').textContent = 'Are you sure you want to delete this product?';
    document.getElementById('deleteModal').classList.add('active');
}

/**
 * Confirm bulk delete all products
 */
function confirmBulkDelete() {
    isBulkDelete = true;
    document.getElementById('deleteMessage').innerHTML = `
        <strong>⚠️ Warning: This action cannot be undone!</strong><br><br>
        Are you sure you want to delete <strong>ALL</strong> products from the database?
    `;
    document.getElementById('deleteModal').classList.add('active');
}

/**
 * Close delete modal
 */
function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
    deleteProductId = null;
    isBulkDelete = false;
}

/**
 * Execute delete (single or bulk)
 */
async function executeDelete() {
    try {
        let url, method;

        if (isBulkDelete) {
            url = `${API_BASE}/products/bulk_delete/`;
            method = 'DELETE';
        } else {
            url = `${API_BASE}/products/${deleteProductId}/`;
            method = 'DELETE';
        }

        const response = await fetch(url, { method });

        if (!response.ok && response.status !== 204 && response.status !== 202) {
            throw new Error('Delete failed');
        }

        closeDeleteModal();
        loadProducts();
        loadStats();
        showToast(isBulkDelete ? 'All products are being deleted...' : 'Product deleted successfully');

    } catch (error) {
        console.error('Error deleting:', error);
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
        day: 'numeric'
    });
}
