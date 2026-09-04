/**
 * SmartCare Queue AI - Departments Directory Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth()) return;

  await loadDepartmentsDirectory();
});

async function loadDepartmentsDirectory() {
  const container = document.getElementById('departments-directory-grid');
  if (!container) return;

  try {
    const [deptRes, docsRes] = await Promise.all([
      window.api.get('/departments'),
      window.api.get('/doctors')
    ]);

    const departments = deptRes.data || [];
    const doctors = docsRes.data || [];

    container.innerHTML = departments.map(d => {
      const deptDocs = doctors.filter(doc => doc.department_id === d.id);
      return `
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div>
              <h3 style="margin-bottom: 0.2rem;">${d.name}</h3>
              <span style="font-size: 0.8rem; color: var(--text-muted);">📍 ${d.location} (${d.floor})</span>
            </div>
            <span class="badge badge-primary">Prefix: ${d.code_prefix}</span>
          </div>
          <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1rem;">${d.description || ''}</p>
          
          <div style="border-top: 1px solid var(--surface-border); padding-top: 0.75rem; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.35rem;">Assigned Specialists (${deptDocs.length}):</div>
            ${deptDocs.length > 0 ? deptDocs.map(doc => `
              <div style="font-size: 0.82rem; color: var(--text-muted);">👨‍⚕️ ${doc.full_name} - ${doc.specialization} (${doc.room_number})</div>
            `).join('') : '<div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">Duty medical officers available.</div>'}
          </div>

          <div style="display: flex; gap: 0.5rem;">
            <a href="queue.html" class="btn btn-primary btn-sm btn-block">Join Queue</a>
            <a href="hospital-map.html?dest=${encodeURIComponent(d.name)}" class="btn btn-outline btn-sm">Map</a>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    window.api.showToast('Failed to load departments: ' + err.message, 'danger');
  }
}
