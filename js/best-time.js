/**
 * SmartCare Queue AI - Best Time to Visit Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth()) return;

  await loadBestTimeRecommendations();
  setupDepartmentFilter();
});

async function loadBestTimeRecommendations(deptId = null) {
  try {
    const url = deptId ? `/ai/best-time/${deptId}` : '/ai/best-time';
    const res = await window.api.get(url);
    const data = res.data || {};

    // Render Highlights
    const recWindowEl = document.getElementById('rec-window');
    const recWaitEl = document.getElementById('rec-wait');
    const recLevelEl = document.getElementById('rec-level');
    const peakWindowEl = document.getElementById('peak-window');
    const peakWaitEl = document.getElementById('peak-wait');
    const disclaimerEl = document.getElementById('best-time-disclaimer');

    if (recWindowEl) recWindowEl.textContent = data.recommended_window || '2:00 PM – 3:00 PM';
    if (recWaitEl) recWaitEl.textContent = data.recommended_wait || '~15 minutes';
    if (recLevelEl) recLevelEl.textContent = data.recommended_level || 'Low';
    if (peakWindowEl) peakWindowEl.textContent = data.peak_window || '10:00 AM – 12:00 PM';
    if (peakWaitEl) peakWaitEl.textContent = data.peak_wait || '40-50 minutes';
    if (disclaimerEl) disclaimerEl.textContent = data.disclaimer || 'Predictions are operational estimates and may vary.';

    // Render Hourly Chart
    renderHourlySchedule(data.hourly_schedule || []);
  } catch (err) {
    window.api.showToast('Failed to load visit recommendations: ' + err.message, 'danger');
  }
}

function renderHourlySchedule(schedule) {
  const container = document.getElementById('hourly-schedule-container');
  if (!container) return;

  container.innerHTML = schedule.map(item => {
    let barColor = 'var(--success)';
    if (item.load_score > 70) barColor = 'var(--danger)';
    else if (item.load_score > 45) barColor = 'var(--warning)';

    return `
      <div style="margin-bottom: 1rem; background: var(--surface); padding: 0.85rem 1rem; border-radius: var(--radius-md); border: 1px solid var(--surface-border); ${item.recommended ? 'border-left: 4px solid var(--success);' : ''}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <div>
            <span style="font-weight: 600; font-size: 0.95rem;">${item.slot}</span>
            ${item.recommended ? '<span class="badge badge-success" style="margin-left:0.5rem;">🌟 AI Recommended</span>' : ''}
          </div>
          <div style="font-size: 0.85rem; color: var(--text-muted);">
            Traffic: <strong>${item.traffic}</strong> (${item.wait_estimate})
          </div>
        </div>
        <div style="height: 10px; background: var(--surface-alt); border-radius: var(--radius-full); overflow: hidden;">
          <div style="height: 100%; width: ${item.load_score}%; background: ${barColor}; border-radius: var(--radius-full); transition: width 0.6s ease;"></div>
        </div>
      </div>
    `;
  }).join('');
}

async function setupDepartmentFilter() {
  const selectEl = document.getElementById('best-time-dept-select');
  if (!selectEl) return;

  try {
    const res = await window.api.get('/departments');
    const depts = res.data || [];
    selectEl.innerHTML = '<option value="">All Hospital OPDs</option>' + 
      depts.map(d => `<option value="${d.id}">${d.name}</option>`).join('');

    selectEl.addEventListener('change', (e) => {
      loadBestTimeRecommendations(e.target.value);
    });
  } catch (err) {
    console.warn(err);
  }
}
