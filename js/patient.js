/**
 * SmartCare Queue AI - Patient Dashboard Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['patient'])) return;

  await loadPatientDashboardData();

  // Polling for live queue updates every 8 seconds
  setInterval(loadActiveQueue, 8000);
});

async function loadPatientDashboardData() {
  await Promise.all([
    loadActiveQueue(),
    loadPatientSummaryMetrics()
  ]);
}

async function loadActiveQueue() {
  const container = document.getElementById('active-queue-container');
  if (!container) return;

  try {
    const res = await window.api.get('/queue-entry/active');
    if (res.success && res.data) {
      renderActiveQueueCard(res.data);
    } else {
      renderEmptyQueueState();
    }
  } catch (err) {
    console.error('Error loading active queue:', err);
  }
}

function renderActiveQueueCard(data) {
  const container = document.getElementById('active-queue-container');
  if (!container) return;

  const entry = data.entry;
  const dept = data.department || {};
  const currentServing = data.current_serving || 'None';
  const ahead = data.patients_ahead || 0;
  const waitTime = entry.estimated_wait_minutes || 15;

  let statusClass = 'status-waiting';
  let statusText = 'Waiting in Queue';
  if (entry.status === 'called') {
    statusClass = 'status-called';
    statusText = 'Token Called! Please Proceed';
  } else if (entry.status === 'serving') {
    statusClass = 'status-serving';
    statusText = 'Currently Serving';
  }

  container.innerHTML = `
    <div class="active-queue-banner">
      <div class="queue-banner-info">
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
          <span class="badge ${statusClass}">
            <span class="pulse-dot"></span> ${statusText}
          </span>
          <span class="ai-badge">🤖 AI Predicted</span>
        </div>
        <h2>${dept.name || 'Department'} Queue</h2>
        <p>Service: <strong>${entry.service_type || 'Consultation'}</strong> • Room: <strong>${entry.counter_number || dept.location || 'OPD'}</strong></p>
        
        <div class="banner-metrics">
          <div class="banner-metric-item">
            <div class="banner-metric-label">Now Serving</div>
            <div class="banner-metric-value">${currentServing}</div>
          </div>
          <div class="banner-metric-item">
            <div class="banner-metric-label">Patients Ahead</div>
            <div class="banner-metric-value">${ahead}</div>
          </div>
          <div class="banner-metric-item">
            <div class="banner-metric-label">Est. Wait Time</div>
            <div class="banner-metric-value">${waitTime} min</div>
          </div>
        </div>

        <div style="margin-top: 1.5rem; display: flex; gap: 0.75rem; flex-wrap: wrap;">
          <a href="qr-token.html?id=${entry.id}" class="btn btn-secondary btn-sm">📱 View Digital QR</a>
          <a href="hospital-map.html?dept=${dept.id || ''}" class="btn btn-outline btn-sm" style="background:#FFF; color:#1E293B;">🗺️ Route Map</a>
          <button onclick="requestPriority('${entry.id}')" class="btn btn-outline btn-sm" style="background:rgba(255,255,255,0.2); color:#FFF; border-color:#FFF;">⚡ Request Priority</button>
          <button onclick="cancelQueueEntry('${entry.id}')" class="btn btn-sm" style="background:rgba(220,38,38,0.2); color:#FFF; border:1px solid rgba(255,255,255,0.4);">Cancel</button>
        </div>
      </div>

      <div class="token-badge-large">
        <div class="token-badge-label">Your Digital Token</div>
        <div class="token-badge-code">${entry.token_code}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted);">Joined at ${new Date(entry.joined_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</div>
      </div>
    </div>
  `;
}

function renderEmptyQueueState() {
  const container = document.getElementById('active-queue-container');
  if (!container) return;

  container.innerHTML = `
    <div class="card text-center" style="padding: 2.5rem 1.5rem; border: 1.5px dashed var(--surface-border);">
      <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏥</div>
      <h3 style="margin-bottom: 0.35rem;">No Active Queue Token</h3>
      <p style="margin-bottom: 1.25rem;">You are not currently in any hospital queue. Join digitally to skip the waiting room!</p>
      <a href="queue.html" class="btn btn-primary">Join a Queue Now</a>
    </div>
  `;
}

async function loadPatientSummaryMetrics() {
  try {
    const [appsRes, billsRes, notesRes] = await Promise.all([
      window.api.get('/appointments'),
      window.api.get('/bills'),
      window.api.get('/notifications')
    ]);

    const appCount = (appsRes.data || []).filter(a => a.status === 'confirmed').length;
    const pendingBills = (billsRes.data || []).filter(b => b.payment_status === 'unpaid').length;
    const unreadNotes = (notesRes.data || []).filter(n => !n.is_read).length;

    const appEl = document.getElementById('stat-appointments-count');
    const billEl = document.getElementById('stat-bills-count');
    const noteEl = document.getElementById('stat-notifications-count');

    if (appEl) appEl.textContent = appCount;
    if (billEl) billEl.textContent = pendingBills;
    if (noteEl) noteEl.textContent = unreadNotes;

    // Header notification badge
    const headerBadge = document.getElementById('header-notif-badge');
    if (headerBadge) {
      if (unreadNotes > 0) {
        headerBadge.style.display = 'flex';
        headerBadge.textContent = unreadNotes;
      } else {
        headerBadge.style.display = 'none';
      }
    }
  } catch (err) {
    console.warn('Metrics loading error:', err);
  }
}

async function cancelQueueEntry(entryId) {
  if (!confirm('Are you sure you want to cancel your queue position?')) return;
  try {
    const res = await window.api.post(`/queue-entry/${entryId}/cancel`);
    if (res.success) {
      window.api.showToast('Queue entry cancelled', 'info');
      await loadActiveQueue();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}

async function requestPriority(entryId) {
  const reason = prompt('Please specify the reason for priority (e.g. Senior Citizen, Mobility Impairment, Acute Discomfort):');
  if (!reason) return;

  try {
    const res = await window.api.post(`/queue-entry/${entryId}/priority`, { reason });
    if (res.success) {
      window.api.showToast('Priority request submitted for staff verification.', 'success');
      await loadActiveQueue();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
