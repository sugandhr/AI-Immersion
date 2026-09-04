/**
 * SmartCare Queue AI - Waiting History & Analytics Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth()) return;

  await loadWaitingHistory();
});

async function loadWaitingHistory() {
  const container = document.getElementById('history-table-body');
  if (!container) return;

  try {
    const res = await window.api.get('/waiting-history');
    const data = res.data || {};

    // Update KPI stats
    const totalVisitsEl = document.getElementById('hist-total-visits');
    const avgWaitEl = document.getElementById('hist-avg-wait');
    const shortestEl = document.getElementById('hist-shortest-wait');
    const longestEl = document.getElementById('hist-longest-wait');

    if (totalVisitsEl) totalVisitsEl.textContent = data.total_visits || 0;
    if (avgWaitEl) avgWaitEl.textContent = `${data.average_wait_minutes || 0} min`;
    if (shortestEl) shortestEl.textContent = `${data.shortest_wait_minutes || 0} min`;
    if (longestEl) longestEl.textContent = `${data.longest_wait_minutes || 0} min`;

    const visits = data.visits || [];
    if (visits.length === 0) {
      container.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 2rem;">No past completed hospital visits found.</td></tr>`;
      return;
    }

    container.innerHTML = visits.map(v => `
      <tr>
        <td><strong>${new Date(v.completed_at || v.joined_at).toLocaleDateString()}</strong></td>
        <td>${v.department_name || 'General OPD'}</td>
        <td>${v.service_type || 'Consultation'}</td>
        <td><span class="badge badge-primary">${v.token_code}</span></td>
        <td>${v.estimated_wait_minutes || 15} minutes</td>
        <td><span class="badge badge-success">Completed</span></td>
      </tr>
    `).join('');
  } catch (err) {
    window.api.showToast('Failed to load waiting history: ' + err.message, 'danger');
  }
}
