/**
 * SmartCare Queue AI - Notifications Center
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth()) return;

  await loadNotifications();
});

async function loadNotifications() {
  const container = document.getElementById('notifications-list-container');
  if (!container) return;

  try {
    const res = await window.api.get('/notifications');
    const notes = res.data || [];

    if (notes.length === 0) {
      container.innerHTML = `
        <div class="card text-center" style="padding: 3rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔔</div>
          <h3>No Notifications</h3>
          <p>You are all caught up!</p>
        </div>
      `;
      return;
    }

    const typeIcons = {
      queue: '🎟️',
      appointment: '🗓️',
      billing: '💳',
      lab: '🔬',
      emergency: '🚨',
      system: '🔔'
    };

    container.innerHTML = notes.map(n => `
      <div class="card mb-2" style="${n.is_read ? 'opacity: 0.85;' : 'border-left: 4px solid var(--primary); background: #F8FAFC;'}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
          <div style="display: flex; gap: 0.85rem;">
            <div style="font-size: 1.5rem;">${typeIcons[n.type] || '🔔'}</div>
            <div>
              <h4 style="margin-bottom: 0.25rem; font-size: 1rem;">${n.title}</h4>
              <p style="font-size: 0.88rem; color: var(--text-main); margin-bottom: 0.35rem;">${n.message}</p>
              <span style="font-size: 0.75rem; color: var(--text-light);">${new Date(n.created_at).toLocaleString()}</span>
            </div>
          </div>
          <div>
            ${!n.is_read ? `
              <button class="btn btn-outline btn-sm" onclick="markAsRead('${n.id}')">Mark Read</button>
            ` : `
              <span style="font-size: 0.75rem; color: var(--text-light);">Read</span>
            `}
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    window.api.showToast('Failed to load notifications: ' + err.message, 'danger');
  }
}

async function markAsRead(noteId) {
  try {
    const res = await window.api.put(`/notifications/${noteId}/read`);
    if (res.success) {
      await loadNotifications();
    }
  } catch (err) {
    console.warn(err);
  }
}
window.markAsRead = markAsRead;

async function markAllNotificationsRead() {
  try {
    const res = await window.api.post('/notifications/read-all');
    if (res.success) {
      window.api.showToast('All notifications marked as read', 'info');
      await loadNotifications();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.markAllNotificationsRead = markAllNotificationsRead;
