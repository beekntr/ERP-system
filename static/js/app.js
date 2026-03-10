const API_BASE_URL = '/api';
const GOOGLE_CLIENT_ID = '';

const AppState = {
    user: null,
    token: null,
    googleClientId: null
};

function getToken() {
    return localStorage.getItem('erp_token');
}

function setToken(token) {
    localStorage.setItem('erp_token', token);
    AppState.token = token;
}

function clearAuth() {
    localStorage.removeItem('erp_token');
    localStorage.removeItem('erp_user');
    AppState.token = null;
    AppState.user = null;
}

function getUser() {
    const userData = localStorage.getItem('erp_user');
    return userData ? JSON.parse(userData) : null;
}

function setUser(user) {
    localStorage.setItem('erp_user', JSON.stringify(user));
    AppState.user = user;
}

function isAuthenticated() {
    return !!getToken();
}

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, mergedOptions);
        
        // Handle authentication errors
        if (response.status === 401) {
            clearAuth();
            window.location.href = '/login?error=session_expired';
            throw new Error('Session expired');
        }
        
        // Handle other errors
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }
        
        // Handle No Content response
        if (response.status === 204) {
            return null;
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

function showEmptyState(elementId, message = 'No data found', icon = 'bi-inbox') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="empty-state">
                <i class="bi ${icon}"></i>
                <h5>${message}</h5>
                <p>Create a new item to get started</p>
            </div>
        `;
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusBadge(status) {
    const statusClasses = {
        'draft': 'badge-draft',
        'pending': 'badge-pending',
        'approved': 'badge-approved',
        'ordered': 'badge-ordered',
        'received': 'badge-received',
        'cancelled': 'badge-cancelled'
    };
    
    return `<span class="badge ${statusClasses[status] || 'badge-draft'}">${status.toUpperCase()}</span>`;
}

function getUserInitials(name) {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

function updateUserHeader() {
    const user = getUser();
    const userNameEl = document.getElementById('userName');
    const userAvatarEl = document.getElementById('userAvatar');
    
    if (user && user.name) {
        if (userNameEl) userNameEl.textContent = user.name;
        if (userAvatarEl) userAvatarEl.textContent = getUserInitials(user.name);
    } else {
        // Fallback: try to fetch user info from API
        fetchCurrentUser();
    }
}

async function fetchCurrentUser() {
    try {
        const user = await apiRequest('/auth/me');
        if (user) {
            setUser(user);
            const userNameEl = document.getElementById('userName');
            const userAvatarEl = document.getElementById('userAvatar');
            if (userNameEl) userNameEl.textContent = user.name;
            if (userAvatarEl) userAvatarEl.textContent = getUserInitials(user.name);
        }
    } catch (error) {
        console.error('Failed to fetch user info:', error);
    }
}

async function handleLogout() {
    try {
        await apiRequest('/auth/logout', { method: 'POST' });
    } catch (e) {
    }
    
    clearAuth();
    window.location.href = '/login';
}

function confirmAction(message) {
    return new Promise((resolve) => {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirm Action</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" id="confirmBtn">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        
        modal.querySelector('#confirmBtn').addEventListener('click', () => {
            bsModal.hide();
            resolve(true);
        });
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
            resolve(false);
        });
        
        bsModal.show();
    });
}

async function initGoogleAuth() {
    try {
        const config = await fetch('/api/auth/config').then(r => r.json());
        AppState.googleClientId = config.google_client_id;
        
        if (AppState.googleClientId && window.google) {
            google.accounts.id.initialize({
                client_id: AppState.googleClientId,
                callback: handleGoogleCallback
            });
            
            google.accounts.id.renderButton(
                document.getElementById('googleSignInBtn'),
                { theme: 'outline', size: 'large', width: 280 }
            );
        }
    } catch (error) {
        console.error('Failed to initialize Google Auth:', error);
    }
}

async function handleGoogleCallback(response) {
    try {
        const res = await fetch('/api/auth/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: response.credential })
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Google authentication failed');
        }
        
        const result = await res.json();
        
        if (!result.access_token || !result.user) {
            throw new Error('Invalid response from server');
        }
        
        setToken(result.access_token);
        setUser(result.user);
        
        showToast('Login successful!', 'success');
        window.location.href = '/dashboard';
    } catch (error) {
        console.error('Google login error:', error);
        showToast('Login failed: ' + error.message, 'danger');
    }
}

async function handleDevLogin() {
    try {
        const res = await fetch('/api/auth/dev-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Dev login failed');
        }
        
        const result = await res.json();
        
        setToken(result.access_token);
        setUser(result.user);
        
        showToast('Development login successful!', 'success');
        window.location.href = '/dashboard';
    } catch (error) {
        showToast('Login failed: ' + error.message, 'danger');
    }
}

function setActiveNavItem(page) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `/${page}` || 
            (page === 'dashboard' && link.getAttribute('href') === '/dashboard')) {
            link.classList.add('active');
        }
    });
}

function initPage(pageName) {
    // Check authentication for protected pages
    if (pageName !== 'login' && !requireAuth()) {
        return false;
    }
    
    // Update user info in header
    if (pageName !== 'login') {
        updateUserHeader();
        setActiveNavItem(pageName);
    }
    
    return true;
}

window.ERP = {
    apiRequest,
    showToast,
    showLoading,
    showEmptyState,
    formatCurrency,
    formatDate,
    formatDateTime,
    getStatusBadge,
    confirmAction,
    initPage,
    handleLogout,
    handleDevLogin,
    initGoogleAuth,
    getToken,
    getUser
};
