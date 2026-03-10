const TAX_RATE = 0.05;

let poItems = [];
let vendors = [];
let products = [];
let editingItemIndex = null;

async function loadVendors() {
    try {
        vendors = await ERP.apiRequest('/vendors');
        populateVendorDropdown();
    } catch (error) {
        ERP.showToast('Failed to load vendors: ' + error.message, 'danger');
    }
}

async function loadProducts() {
    try {
        products = await ERP.apiRequest('/products');
        populateProductDropdown();
    } catch (error) {
        ERP.showToast('Failed to load products: ' + error.message, 'danger');
    }
}

function populateVendorDropdown() {
    const select = document.getElementById('vendorSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">Select a vendor...</option>';
    vendors.forEach(vendor => {
        const option = document.createElement('option');
        option.value = vendor.id;
        option.textContent = vendor.name;
        select.appendChild(option);
    });
}

function populateProductDropdown() {
    updateProductDropdownInRow();
}

function updateProductDropdownInRow(selectId = 'productSelect') {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    select.innerHTML = '<option value="">Select a product...</option>';
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = `${product.name} (${product.sku}) - ${ERP.formatCurrency(product.unit_price)}`;
        option.dataset.price = product.unit_price;
        select.appendChild(option);
    });
}

function handleProductSelect(selectElement) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const priceInput = document.getElementById('itemPrice');
    
    if (selectedOption && selectedOption.dataset.price) {
        priceInput.value = parseFloat(selectedOption.dataset.price).toFixed(2);
    }
}

function addItem() {
    const productSelect = document.getElementById('productSelect');
    const quantityInput = document.getElementById('itemQuantity');
    const priceInput = document.getElementById('itemPrice');
    
    const productId = parseInt(productSelect.value);
    const quantity = parseInt(quantityInput.value);
    const price = parseFloat(priceInput.value);
    
    // Validation
    if (!productId) {
        ERP.showToast('Please select a product', 'warning');
        return;
    }
    
    if (!quantity || quantity <= 0) {
        ERP.showToast('Please enter a valid quantity', 'warning');
        return;
    }
    
    if (!price || price <= 0) {
        ERP.showToast('Please enter a valid price', 'warning');
        return;
    }
    
    // Check for duplicate product
    const existingIndex = poItems.findIndex(item => item.product_id === productId);
    if (existingIndex !== -1 && editingItemIndex === null) {
        ERP.showToast('Product already added. Edit the existing item instead.', 'warning');
        return;
    }
    
    // Get product details
    const product = products.find(p => p.id === productId);
    
    const item = {
        product_id: productId,
        product_name: product.name,
        product_sku: product.sku,
        quantity: quantity,
        price: price
    };
    
    if (editingItemIndex !== null) {
        // Update existing item
        poItems[editingItemIndex] = item;
        editingItemIndex = null;
        document.getElementById('addItemBtn').textContent = 'Add Item';
    } else {
        // Add new item
        poItems.push(item);
    }
    
    // Clear form
    productSelect.value = '';
    quantityInput.value = '1';
    priceInput.value = '';
    
    // Update display
    renderItemsTable();
    updateTotals();
}

function editItem(index) {
    const item = poItems[index];
    editingItemIndex = index;
    
    document.getElementById('productSelect').value = item.product_id;
    document.getElementById('itemQuantity').value = item.quantity;
    document.getElementById('itemPrice').value = item.price.toFixed(2);
    document.getElementById('addItemBtn').textContent = 'Update Item';
}

function removeItem(index) {
    poItems.splice(index, 1);
    renderItemsTable();
    updateTotals();
}

function renderItemsTable() {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;
    
    if (poItems.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    No items added yet. Add products to your order above.
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = poItems.map((item, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>
                <strong>${item.product_name}</strong>
                <br><small class="text-muted">${item.product_sku}</small>
            </td>
            <td class="text-center">${item.quantity}</td>
            <td class="text-end">${ERP.formatCurrency(item.price)}</td>
            <td class="text-end">${ERP.formatCurrency(item.quantity * item.price)}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editItem(${index})" title="Edit">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="removeItem(${index})" title="Remove">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function updateTotals() {
    const subtotal = poItems.reduce((sum, item) => sum + (item.quantity * item.price), 0);
    const tax = subtotal * TAX_RATE;
    const total = subtotal + tax;
    
    document.getElementById('subtotalAmount').textContent = ERP.formatCurrency(subtotal);
    document.getElementById('taxAmount').textContent = ERP.formatCurrency(tax);
    document.getElementById('totalAmount').textContent = ERP.formatCurrency(total);
}

async function submitPurchaseOrder() {
    const vendorId = parseInt(document.getElementById('vendorSelect').value);
    
    // Validation
    if (!vendorId) {
        ERP.showToast('Please select a vendor', 'warning');
        return;
    }
    
    if (poItems.length === 0) {
        ERP.showToast('Please add at least one item', 'warning');
        return;
    }
    
    // Prepare payload
    const payload = {
        vendor_id: vendorId,
        items: poItems.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            price: item.price
        }))
    };
    
    // Disable submit button
    const submitBtn = document.getElementById('submitPOBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating...';
    
    try {
        const result = await ERP.apiRequest('/purchase-orders', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        ERP.showToast(`Purchase Order ${result.reference_no} created successfully!`, 'success');
        
        // Clear form
        poItems = [];
        document.getElementById('vendorSelect').value = '';
        renderItemsTable();
        updateTotals();
        
        // Redirect to dashboard after delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1500);
        
    } catch (error) {
        ERP.showToast('Failed to create purchase order: ' + error.message, 'danger');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Create Purchase Order';
    }
}

async function loadPurchaseOrders() {
    const tbody = document.getElementById('poTableBody');
    try {
        ERP.showLoading('poTableBody');
        const orders = await ERP.apiRequest('/purchase-orders');
        renderPurchaseOrdersTable(orders);
        updateDashboardStats(orders);
    } catch (error) {
        console.error('Failed to load purchase orders:', error);
        // Show error state in table instead of just toast
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4 text-danger">
                        <i class="bi bi-exclamation-circle me-2"></i>
                        Failed to load orders: ${error.message}
                        <br>
                        <button class="btn btn-sm btn-outline-primary mt-2" onclick="POManager.loadPurchaseOrders()">
                            <i class="bi bi-arrow-clockwise"></i> Retry
                        </button>
                    </td>
                </tr>
            `;
        }
    }
}

function renderPurchaseOrdersTable(orders) {
    const tbody = document.getElementById('poTableBody');
    if (!tbody) return;
    
    if (orders.length === 0) {
        ERP.showEmptyState('poTableBody', 'No purchase orders yet', 'bi-cart');
        return;
    }
    
    tbody.innerHTML = orders.map(order => `
        <tr>
            <td><strong>${order.reference_no}</strong></td>
            <td>${order.vendor ? order.vendor.name : 'N/A'}</td>
            <td>${ERP.formatDate(order.order_date)}</td>
            <td class="text-end">${ERP.formatCurrency(order.subtotal)}</td>
            <td class="text-end">${ERP.formatCurrency(order.tax)}</td>
            <td class="text-end"><strong>${ERP.formatCurrency(order.total_amount)}</strong></td>
            <td>${ERP.getStatusBadge(order.status)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewPurchaseOrder(${order.id})" title="View Details">
                    <i class="bi bi-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function updateDashboardStats(orders) {
    // Count by status
    const stats = {
        total: orders.length,
        totalAmount: orders.reduce((sum, o) => sum + o.total_amount, 0),
        pending: orders.filter(o => o.status === 'pending').length,
        approved: orders.filter(o => o.status === 'approved').length
    };
    
    // Update stat cards if they exist
    const totalOrdersEl = document.getElementById('totalOrders');
    const totalAmountEl = document.getElementById('totalAmount');
    const pendingOrdersEl = document.getElementById('pendingOrders');
    const approvedOrdersEl = document.getElementById('approvedOrders');
    
    if (totalOrdersEl) totalOrdersEl.textContent = stats.total;
    if (totalAmountEl) totalAmountEl.textContent = ERP.formatCurrency(stats.totalAmount);
    if (pendingOrdersEl) pendingOrdersEl.textContent = stats.pending;
    if (approvedOrdersEl) approvedOrdersEl.textContent = stats.approved;
}

async function viewPurchaseOrder(id) {
    try {
        const order = await ERP.apiRequest(`/purchase-orders/${id}`);
        showPurchaseOrderModal(order);
    } catch (error) {
        ERP.showToast('Failed to load order details: ' + error.message, 'danger');
    }
}

function showPurchaseOrderModal(order) {
    const modal = document.getElementById('poDetailModal');
    if (!modal) {
        createPODetailModal();
    }
    
    document.getElementById('modalReferenceNo').textContent = order.reference_no;
    document.getElementById('modalVendor').textContent = order.vendor ? order.vendor.name : 'N/A';
    document.getElementById('modalOrderDate').textContent = ERP.formatDateTime(order.order_date);
    document.getElementById('modalStatus').innerHTML = ERP.getStatusBadge(order.status);
    document.getElementById('modalSubtotal').textContent = ERP.formatCurrency(order.subtotal);
    document.getElementById('modalTax').textContent = ERP.formatCurrency(order.tax);
    document.getElementById('modalTotal').textContent = ERP.formatCurrency(order.total_amount);
    
    const itemsHtml = order.items.map((item, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>${item.product ? item.product.name : 'N/A'}</td>
            <td>${item.product ? item.product.sku : 'N/A'}</td>
            <td class="text-center">${item.quantity}</td>
            <td class="text-end">${ERP.formatCurrency(item.price)}</td>
            <td class="text-end">${ERP.formatCurrency(item.quantity * item.price)}</td>
        </tr>
    `).join('');
    
    document.getElementById('modalItemsBody').innerHTML = itemsHtml;
    
    const bsModal = new bootstrap.Modal(document.getElementById('poDetailModal'));
    bsModal.show();
}

function createPODetailModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'poDetailModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Purchase Order Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <p><strong>Reference:</strong> <span id="modalReferenceNo"></span></p>
                            <p><strong>Vendor:</strong> <span id="modalVendor"></span></p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Date:</strong> <span id="modalOrderDate"></span></p>
                            <p><strong>Status:</strong> <span id="modalStatus"></span></p>
                        </div>
                    </div>
                    
                    <h6 class="mb-3">Items</h6>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Product</th>
                                <th>SKU</th>
                                <th class="text-center">Qty</th>
                                <th class="text-end">Price</th>
                                <th class="text-end">Total</th>
                            </tr>
                        </thead>
                        <tbody id="modalItemsBody"></tbody>
                    </table>
                    
                    <div class="po-summary">
                        <div class="po-summary-row">
                            <span>Subtotal:</span>
                            <span id="modalSubtotal"></span>
                        </div>
                        <div class="po-summary-row">
                            <span>Tax (5%):</span>
                            <span id="modalTax"></span>
                        </div>
                        <div class="po-summary-row">
                            <span>Total:</span>
                            <span id="modalTotal"></span>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

async function initCreatePOPage() {
    if (!ERP.initPage('create-po')) return;
    
    await Promise.all([loadVendors(), loadProducts()]);
    renderItemsTable();
    updateTotals();
}

async function initDashboardPage() {
    if (!ERP.initPage('dashboard')) return;
    
    try {
        await loadPurchaseOrders();
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
    }
}

window.POManager = {
    initCreatePOPage,
    initDashboardPage,
    addItem,
    editItem,
    removeItem,
    submitPurchaseOrder,
    handleProductSelect,
    viewPurchaseOrder,
    loadPurchaseOrders
};
