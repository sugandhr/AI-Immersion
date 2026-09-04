/**
 * SmartCare Queue AI - Join Queue Controller
 */

let selectedDepartmentId = null;
let allDepartments = [];
let allDoctors = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['patient'])) return;

  await loadDepartmentsAndDoctors();
  setupJoinQueueListeners();
});

async function loadDepartmentsAndDoctors() {
  try {
    const [deptRes, docRes] = await Promise.all([
      window.api.get('/departments'),
      window.api.get('/doctors')
    ]);

    allDepartments = deptRes.data || [];
    allDoctors = docRes.data || [];

    renderDepartmentGrid(allDepartments);
    populateDoctorSelect();
  } catch (err) {
    window.api.showToast('Failed to load departments: ' + err.message, 'danger');
  }
}

function renderDepartmentGrid(departments) {
  const container = document.getElementById('dept-selection-grid');
  if (!container) return;

  const iconsMap = {
    'General Medicine': '🩺',
    'Cardiology': '❤️',
    'Orthopedics': '🦴',
    'Pediatrics': '👶',
    'Dermatology': '✨',
    'Neurology': '🧠',
    'ENT': '👂',
    'Laboratory': '🔬',
    'Pharmacy': '💊',
    'Billing': '💳',
    'Registration': '📋',
    'Emergency': '🚨'
  };

  container.innerHTML = departments.map(d => `
    <div class="dept-card ${selectedDepartmentId === d.id ? 'selected' : ''}" onclick="selectDepartment('${d.id}')">
      <div>
        <div class="dept-icon">${iconsMap[d.name] || '🏥'}</div>
        <div class="dept-title">${d.name}</div>
        <div class="dept-location">📍 ${d.location} (${d.floor})</div>
        <p style="font-size: 0.82rem; color: var(--text-muted);">${d.description || ''}</p>
      </div>
      <div style="margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
        <span class="badge badge-primary">Prefix: ${d.code_prefix}</span>
        <span style="font-size: 0.8rem; font-weight: 600; color: var(--primary);">Select &rarr;</span>
      </div>
    </div>
  `).join('');
}

function selectDepartment(deptId) {
  selectedDepartmentId = deptId;
  renderDepartmentGrid(allDepartments);

  const dept = allDepartments.find(d => d.id === deptId);
  const selectedDisplay = document.getElementById('selected-dept-display');
  if (selectedDisplay) {
    selectedDisplay.textContent = dept ? dept.name : 'None';
  }

  populateDoctorSelect(deptId);
}

function populateDoctorSelect(deptId = null) {
  const selectEl = document.getElementById('doctor-select');
  if (!selectEl) return;

  let filtered = allDoctors;
  if (deptId) {
    filtered = allDoctors.filter(d => d.department_id === deptId);
  }

  selectEl.innerHTML = '<option value="">Any Available Doctor / Specialist</option>' + 
    filtered.map(doc => `<option value="${doc.id}">${doc.full_name} (${doc.specialization} - ${doc.room_number})</option>`).join('');
}

function setupJoinQueueListeners() {
  const form = document.getElementById('join-queue-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!selectedDepartmentId) {
      window.api.showToast('Please select a department first.', 'warning');
      return;
    }

    const serviceType = document.getElementById('service-type-select').value;
    const doctorId = document.getElementById('doctor-select').value || null;

    try {
      const res = await window.api.post('/queues/join', {
        department_id: selectedDepartmentId,
        service_type: serviceType,
        doctor_id: doctorId
      });

      if (res.success && res.data) {
        showTokenConfirmationModal(res.data);
      }
    } catch (err) {
      window.api.showToast(err.message || 'Failed to join queue', 'danger');
    }
  });
}

function showTokenConfirmationModal(data) {
  const modal = document.getElementById('token-confirm-modal');
  const entry = data.entry;
  if (!modal || !entry) {
    window.location.href = 'patient-dashboard.html';
    return;
  }

  document.getElementById('modal-token-code').textContent = entry.token_code;
  document.getElementById('modal-dept-name').textContent = entry.department_name || 'OPD';
  document.getElementById('modal-patients-ahead').textContent = data.patients_ahead || 0;
  document.getElementById('modal-wait-time').textContent = (entry.estimated_wait_minutes || 15) + ' minutes';
  document.getElementById('modal-view-qr-btn').href = `qr-token.html?id=${entry.id}`;

  modal.classList.add('active');
}
