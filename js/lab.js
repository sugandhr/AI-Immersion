/**
 * SmartCare Queue AI - Diagnostic Lab Tests Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['patient', 'staff', 'doctor', 'admin'])) return;

  await loadLabOrders();
});

async function loadLabOrders() {
  const container = document.getElementById('lab-orders-container');
  if (!container) return;

  try {
    const res = await window.api.get('/lab-tests');
    const orders = res.data || [];

    if (orders.length === 0) {
      container.innerHTML = `
        <div class="card text-center" style="padding: 3rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔬</div>
          <h3>No Diagnostic Tests Found</h3>
          <p>You have no pending or completed laboratory tests.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = orders.map(o => {
      const isStaff = ['staff', 'doctor', 'admin'].includes(window.Auth.getUser()?.role);
      const stages = [
        { key: 'ordered', label: 'Test Ordered' },
        { key: 'sample_collected', label: 'Sample Collected' },
        { key: 'processing', label: 'Processing' },
        { key: 'report_ready', label: 'Report Ready' }
      ];

      const stageIndex = stages.findIndex(s => s.key === o.status);

      return `
        <div class="card mb-3">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <h3 style="margin-bottom: 0.25rem;">${o.test_name}</h3>
              <p style="font-size: 0.85rem; color: var(--text-muted);">
                Patient: <strong>${o.patient_name || 'Patient'}</strong> • Prescribed by: <strong>${o.doctor_name || 'Attending Doctor'}</strong>
              </p>
              <div style="font-size: 0.78rem; color: var(--text-light); margin-top: 0.25rem;">
                Ref ID: <code>${o.report_reference || 'LAB-DEMO'}</code>
              </div>
            </div>
            <div>
              <span class="badge ${o.status === 'report_ready' ? 'badge-success' : 'badge-warning'}">
                ${o.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>

          <!-- Progress Stepper -->
          <div style="display: flex; justify-content: space-between; position: relative; margin: 1.5rem 0; padding: 0 1rem;">
            ${stages.map((stage, idx) => {
              const isCompleted = idx <= stageIndex;
              const isCurrent = idx === stageIndex;
              return `
                <div style="display: flex; flex-direction: column; align-items: center; z-index: 2; flex: 1;">
                  <div style="width: 28px; height: 28px; border-radius: 50%; background: ${isCompleted ? 'var(--primary)' : 'var(--surface-border)'}; color: #FFF; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; border: 3px solid var(--surface); box-shadow: ${isCurrent ? '0 0 0 3px var(--primary-glow)' : 'none'};">
                    ${isCompleted ? '✓' : (idx + 1)}
                  </div>
                  <div style="font-size: 0.75rem; font-weight: ${isCurrent ? '700' : '500'}; color: ${isCurrent ? 'var(--primary)' : 'var(--text-muted)'}; margin-top: 0.35rem; text-align: center;">
                    ${stage.label}
                  </div>
                </div>
              `;
            }).join('')}
          </div>

          <div style="background: var(--surface-alt); border-radius: var(--radius-md); padding: 0.85rem 1rem; font-size: 0.85rem; color: var(--text-muted); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <span>ℹ️ Notes: ${o.notes || 'Automated sample processing in Central Laboratory block.'}</span>
            ${o.status === 'report_ready' ? `
              <button class="btn btn-secondary btn-sm" onclick="viewDemoReport('${o.report_reference}', '${o.test_name}')">📄 View Report</button>
            ` : ''}
          </div>

          ${isStaff ? `
            <div style="margin-top: 1rem; border-top: 1px solid var(--surface-border); padding-top: 0.75rem; display: flex; gap: 0.5rem; align-items: center;">
              <span style="font-size: 0.8rem; font-weight: 600;">Update Status:</span>
              <button class="btn btn-outline btn-sm" onclick="updateTestStatus('${o.id}', 'sample_collected')">Collected</button>
              <button class="btn btn-outline btn-sm" onclick="updateTestStatus('${o.id}', 'processing')">Processing</button>
              <button class="btn btn-success btn-sm" onclick="updateTestStatus('${o.id}', 'report_ready')">Report Ready</button>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
  } catch (err) {
    window.api.showToast('Failed to load lab orders: ' + err.message, 'danger');
  }
}

async function updateTestStatus(orderId, newStatus) {
  try {
    const res = await window.api.put(`/lab-tests/${orderId}/status`, { status: newStatus });
    if (res.success) {
      window.api.showToast(`Lab status updated to ${newStatus}`, 'success');
      await loadLabOrders();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.updateTestStatus = updateTestStatus;

function viewDemoReport(ref, testName) {
  alert(`[SmartCare Demo Diagnostic Report]\n\nReference: ${ref}\nInvestigation: ${testName}\nResult: Normal physiological findings.\nVerified by: Chief Biochemist & Pathologist\n\n(Fictional demonstration report for college project evaluation)`);
}
window.viewDemoReport = viewDemoReport;
