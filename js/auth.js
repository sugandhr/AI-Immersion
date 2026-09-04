/**
 * SmartCare Queue AI - Authentication & Session Manager
 */

const Auth = {
  getToken() {
    return localStorage.getItem('smartcare_token');
  },

  getUser() {
    const raw = localStorage.getItem('smartcare_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  setSession(token, user) {
    localStorage.setItem('smartcare_token', token);
    localStorage.setItem('smartcare_user', JSON.stringify(user));
  },

  clearSession() {
    localStorage.removeItem('smartcare_token');
    localStorage.removeItem('smartcare_user');
  },

  isAuthenticated() {
    return Boolean(this.getToken() && this.getUser());
  },

  async login(email, password) {
    try {
      const res = await window.api.post('/auth/login', { email, password });
      if (res.success && res.data) {
        this.setSession(res.data.token, res.data.user);
        window.api.showToast(`Welcome back, ${res.data.user.full_name}!`, 'success');
        setTimeout(() => {
          window.location.href = res.data.redirect_url || `${res.data.user.role}-dashboard.html`;
        }, 800);
        return res.data;
      }
    } catch (err) {
      window.api.showToast(err.message || 'Login failed', 'danger');
      throw err;
    }
  },

  async register(fullName, email, password, role = 'patient', phone = '') {
    try {
      const res = await window.api.post('/auth/register', {
        full_name: fullName,
        email,
        password,
        role,
        phone
      });
      if (res.success && res.data) {
        this.setSession(res.data.token, res.data.user);
        window.api.showToast('Account registered successfully!', 'success');
        setTimeout(() => {
          window.location.href = res.data.redirect_url || `${res.data.user.role}-dashboard.html`;
        }, 800);
        return res.data;
      }
    } catch (err) {
      window.api.showToast(err.message || 'Registration failed', 'danger');
      throw err;
    }
  },

  logout() {
    this.clearSession();
    window.api.showToast('Logged out successfully.', 'info');
    setTimeout(() => {
      window.location.href = 'login.html';
    }, 500);
  },

  // Page Auth Guard
  requireAuth(allowedRoles = []) {
    const user = this.getUser();
    if (!this.isAuthenticated() || !user) {
      window.location.href = 'login.html';
      return false;
    }

    if (allowedRoles.length > 0) {
      const userRole = user.role || 'patient';
      if (!allowedRoles.includes(userRole) && userRole !== 'admin') {
        window.api.showToast(`Access denied for role: ${userRole}`, 'danger');
        setTimeout(() => {
          window.location.href = `${userRole}-dashboard.html`;
        }, 1000);
        return false;
      }
    }

    // Populate user profile info in top bar if present
    this.renderHeaderUserInfo(user);
    return true;
  },

  renderHeaderUserInfo(user) {
    const nameEl = document.getElementById('header-user-name');
    const roleEl = document.getElementById('header-user-role');
    const avatarEl = document.getElementById('header-user-avatar');

    if (nameEl) nameEl.textContent = user.full_name || user.email;
    if (roleEl) roleEl.textContent = user.role ? user.role.toUpperCase() : 'PATIENT';
    if (avatarEl) {
      const initials = (user.full_name || 'U').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      avatarEl.textContent = initials;
    }
  }
};

window.Auth = Auth;
