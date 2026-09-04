/**
 * SmartCare Queue AI - Centralized HTTP API Client
 * Tagline: "Less Waiting. Better Care."
 */

class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl || (window.CONFIG ? window.CONFIG.API_BASE_URL : 'http://localhost:5001/api');
  }

  getToken() {
    return localStorage.getItem('smartcare_token') || sessionStorage.getItem('smartcare_token');
  }

  getHeaders(customHeaders = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...customHeaders
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const headers = this.getHeaders(options.headers);

    this.showGlobalLoader();

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      const data = await response.json().catch(() => ({
        success: false,
        message: `HTTP Error ${response.status}: Failed to parse JSON response`
      }));

      if (!response.ok) {
        if (response.status === 401) {
          console.warn('[SmartCare API] Unauthorized request - session expired.');
          // If token expired, clear and redirect to login if not already on login
          if (!window.location.pathname.includes('login') && !window.location.pathname.includes('index') && !window.location.pathname.endsWith('/')) {
            this.showToast('Session expired. Please log in again.', 'warning');
            setTimeout(() => {
              window.location.href = 'login.html';
            }, 1200);
          }
        }
        throw new Error(data.message || `Request failed with status ${response.status}`);
      }

      return data;
    } catch (err) {
      console.error(`[SmartCare API Error] ${endpoint}:`, err);
      throw err;
    } finally {
      this.hideGlobalLoader();
    }
  }

  get(endpoint, headers = {}) {
    return this.request(endpoint, { method: 'GET', headers });
  }

  post(endpoint, body = {}, headers = {}) {
    return this.request(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    });
  }

  put(endpoint, body = {}, headers = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body)
    });
  }

  del(endpoint, headers = {}) {
    return this.request(endpoint, { method: 'DELETE', headers });
  }

  // Toast Notification UI Helper
  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'warning') icon = '⚠️';
    if (type === 'danger')  icon = '❌';

    toast.innerHTML = `
      <div style="display:flex; align-items:center; gap:0.5rem;">
        <span>${icon}</span>
        <span>${message}</span>
      </div>
      <button style="background:none; border:none; cursor:pointer; font-size:1.1rem; color:inherit;" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }
    }, 4500);
  }

  showGlobalLoader() {
    let loader = document.getElementById('global-api-loader');
    if (loader) loader.style.display = 'block';
  }

  hideGlobalLoader() {
    let loader = document.getElementById('global-api-loader');
    if (loader) loader.style.display = 'none';
  }
}

window.api = new ApiClient();
