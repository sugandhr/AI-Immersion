/**
 * SmartCare Queue AI - Staff & Doctor Queue Operations Controller
 */

let activeQueueId = null;
let currentCounter = 'Counter 1';

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['staff', 'doctor', 'admin'])) return;

  await loadStaffQueues();
  setupCounterSwitcher();
  setInterval(refreshLiveStaffQueue, 5000);
});

async function loadStaffQueues() {
  try {
    const res = await window.api.get('/queues');
    const queues = res.data || [];

    const selectEl = document.getElementById('staff-queue-select');
    if (selectEl) {
      selectEl.innerHTML = queues.map(q => `
        <option value="${q.queue.id}">${q.queue.department_name} - ${q.queue.service_type} (${q.waiting_count} waiting)</option>
      `).join('');

      if (queues.length > 0) {
        activeQueueId = queues[0].queue.id;
        selectEl.value = activeQueueId;
      }

      selectEl.addEventListener('change', (e) => {
        activeQueueId = e.target.value;
        refreshLiveStaffQueue();
      });
    }

    await refreshLiveStaffQueue();
    await loadStaffDashboardKPIs();
  } catch (err) {
    window.api.showToast('Failed to load queues: ' + err.message, 'danger');
  }
}

async function refreshLiveStaffQueue() {
  if (!activeQueueId) return;

  try {
    const res = await window.api.get(`/queues/${activeQueueId}`);
    if (res.success && res.data) {
      renderStaffQueueData(res.data);
    }
  } catch (err) {
    console.warn('Queue refresh error:', err);
  }
}

function renderStaffQueueData(data) {
  // Current Serving Spotlight
  const servingTokenEl = document.getElementById('staff-serving-token');
  const servingPatientEl = document.getElementById('staff-serving-patient');
  const servingStatusEl = document.getElementById('staff-serving-status');

  const currentServing = data.serving_token;
  if (servingTokenEl) servingTokenEl.textContent = currentServing ? currentServing.token_code : '--';
  if (servingPatientEl) servingPatientEl.textContent = currentServing ? (currentServing.patient_name || 'Patient') : 'No Patient Active';
  if (servingStatusEl) {
    servingStatusEl.textContent = currentServing ? currentServing.status.toUpperCase() : 'IDLE';
    servingStatusEl.className = currentServing ? `badge badge-${currentServing.status === 'called' ? 'warning' : 'success'}` : 'badge badge-info';
  }

  // Waiting Patients Table
  const waitingTableBody = document.getElementById('staff-waiting-table-body');
  if (waitingTableBody) {
    const waitingList = data.waiting_list || [];
    if (waitingList.length === 0) {
      waitingTableBody.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 2rem;">No patients currently waiting in this queue.</td></tr>`;
    } else {
      waitingTableBody.innerHTML = waitingList.map(item => `
        <tr>
          <td><strong style="font-size: 1.1rem; color: var(--primary);">${item.token_code}</strong></td>
          <td>
            <div>${item.patient_name || 'Patient'}</div>
            ${item.priority_approved ? '<span class="priority-badge">⚡ PRIORITY</span>' : ''}
          </td>
          <td>${new Date(item.joined_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</td>
          <td>~${item.estimated_wait_minutes || 15} min</td>
          <td>
            <div style="display: flex; gap: 0.35rem;">
              <button class="btn btn-primary btn-sm" onclick="callSpecificToken('${item.id}')">Call</button>
              <button class="btn btn-outline btn-sm" onclick="skipToken('${item.id}')">Skip</button>
            </div>
          </td>
        </tr>
      `).join('');
    }
  }
}

async function loadStaffDashboardKPIs() {
  try {
    const res = await window.api.get('/analytics/dashboard');
    const d = res.data || {};

    const totalEl = document.getElementById('staff-kpi-total');
    const waitingEl = document.getElementById('staff-kpi-waiting');
    const servedEl = document.getElementById('staff-kpi-served');
    const avgWaitEl = document.getElementById('staff-kpi-avgwait');

    if (totalEl) totalEl.textContent = d.total_patients_today || 0;
    if (waitingEl) waitingEl.textContent = d.waiting_patients || 0;
    if (servedEl) servedEl.textContent = d.completed_patients || 0;
    if (avgWaitEl) avgWaitEl.textContent = `${d.average_wait_minutes || 18} min`;
  } catch (err) {
    console.warn('KPI load error:', err);
  }
}

function setupCounterSwitcher() {
  const counterSelect = document.getElementById('counter-number-select');
  if (counterSelect) {
    counterSelect.addEventListener('change', (e) => {
      currentCounter = e.target.value;
      const display = document.getElementById('current-counter-display');
      if (display) display.textContent = currentCounter;
    });
  }
}

/* Operational Staff Actions */
async function callNextPatient() {
  if (!activeQueueId) return;

  try {
    const res = await window.api.post(`/queues/${activeQueueId}/next`, {
      counter_number: currentCounter
    });

    if (res.success) {
      window.api.showToast(`Called token ${res.data.token_code} to ${currentCounter}`, 'success');
      await refreshLiveStaffQueue();
      await loadStaffDashboardKPIs();
    }
  } catch (err) {
    window.api.showToast(err.message, 'warning');
  }
}
window.callNextPatient = callNextPatient;

async function startServingPatient() {
  const currentTokenEl = document.getElementById('staff-serving-token');
  const tokenCode = currentTokenEl ? currentTokenEl.textContent : '';

  try {
    const qRes = await window.api.get(`/queues/${activeQueueId}`);
    const currentEntry = qRes.data ? (qRes.data.serving_token) : null;

    if (!currentEntry) {
      window.api.showToast('No patient is currently called to serve.', 'warning');
      return;
    }

    const res = await window.api.post(`/queue-entry/${currentEntry.id}/serving`);
    if (res.success) {
      window.api.showToast(`Now serving token ${currentEntry.token_code}`, 'info');
      await refreshLiveStaffQueue();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.startServingPatient = startServingPatient;

async function completeCurrentPatient() {
  try {
    const qRes = await window.api.get(`/queues/${activeQueueId}`);
    const currentEntry = qRes.data ? (qRes.data.serving_token) : null;

    if (!currentEntry) {
      window.api.showToast('No patient currently active to complete.', 'warning');
      return;
    }

    const res = await window.api.post(`/queue-entry/${currentEntry.id}/complete`);
    if (res.success) {
      window.api.showToast(`Completed consultation for token ${currentEntry.token_code}`, 'success');
      await refreshLiveStaffQueue();
      await loadStaffDashboardKPIs();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.completeCurrentPatient = completeCurrentPatient;

async function recallCurrentPatient() {
  try {
    const qRes = await window.api.get(`/queues/${activeQueueId}`);
    const currentEntry = qRes.data ? (qRes.data.serving_token) : null;

    if (!currentEntry) {
      window.api.showToast('No patient currently called to recall.', 'warning');
      return;
    }

    const res = await window.api.post(`/queue-entry/${currentEntry.id}/call`, {
      counter_number: currentCounter
    });
    if (res.success) {
      window.api.showToast(`Recalled token ${currentEntry.token_code}!`, 'info');
      await refreshLiveStaffQueue();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.recallCurrentPatient = recallCurrentPatient;

async function callSpecificToken(entryId) {
  try {
    const res = await window.api.post(`/queue-entry/${entryId}/call`, {
      counter_number: currentCounter
    });
    if (res.success) {
      window.api.showToast(`Called token ${res.data.token_code}`, 'success');
      await refreshLiveStaffQueue();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.callSpecificToken = callSpecificToken;

async function skipToken(entryId) {
  try {
    const res = await window.api.post(`/queue-entry/${entryId}/skip`);
    if (res.success) {
      window.api.showToast('Token skipped', 'info');
      await refreshLiveStaffQueue();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.skipToken = skipToken;
