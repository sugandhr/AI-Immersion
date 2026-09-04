/**
 * SmartCare Queue AI - Appointments Controller
 */

let allDoctors = [];
let allDepartments = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['patient', 'doctor', 'staff', 'admin'])) return;

  await loadAppointmentsData();
  setupAppointmentBookingModal();
});

async function loadAppointmentsData() {
  try {
    const [appRes, deptRes, docRes] = await Promise.all([
      window.api.get('/appointments'),
      window.api.get('/departments'),
      window.api.get('/doctors')
    ]);

    allDepartments = deptRes.data || [];
    allDoctors = docRes.data || [];

    renderAppointmentsList(appRes.data || []);
    populateModalDropdowns();
  } catch (err) {
    window.api.showToast('Failed to load appointments: ' + err.message, 'danger');
  }
}

function renderAppointmentsList(appointments) {
  const container = document.getElementById('appointments-list-container');
  if (!container) return;

  if (appointments.length === 0) {
    container.innerHTML = `
      <div class="card text-center" style="padding: 2.5rem 1rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📅</div>
        <h3>No Appointments Scheduled</h3>
        <p style="margin-bottom: 1rem;">Book a scheduled doctor appointment to guarantee consultation slots.</p>
        <button class="btn btn-primary btn-sm" onclick="openBookModal()">Schedule Appointment</button>
      </div>
    `;
    return;
  }

  container.innerHTML = appointments.map(a => `
    <div class="card mb-2">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem;">
        <div>
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
            <h4 style="margin: 0;">${a.doctor_name || 'Specialist Doctor'}</h4>
            <span class="badge ${a.status === 'confirmed' ? 'badge-success' : 'badge-warning'}">${a.status}</span>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">
            Department: <strong>${a.department_name}</strong> • Reason: <em>${a.reason || 'General Consultation'}</em>
          </p>
          <div style="display: flex; gap: 1rem; font-size: 0.85rem; font-weight: 600;">
            <span>🗓️ ${a.appointment_date}</span>
            <span>⏰ ${a.appointment_time}</span>
          </div>
        </div>

        <div>
          ${a.status === 'confirmed' ? `
            <button class="btn btn-outline btn-sm" style="color:var(--danger); border-color:var(--danger);" onclick="cancelAppointment('${a.id}')">Cancel</button>
          ` : ''}
        </div>
      </div>
    </div>
  `).join('');
}

function populateModalDropdowns() {
  const deptSelect = document.getElementById('book-dept-select');
  const docSelect = document.getElementById('book-doctor-select');
  if (!deptSelect || !docSelect) return;

  deptSelect.innerHTML = '<option value="">Select Department</option>' + 
    allDepartments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');

  deptSelect.addEventListener('change', (e) => {
    const deptId = e.target.value;
    const filteredDocs = deptId ? allDoctors.filter(d => d.department_id === deptId) : allDoctors;
    docSelect.innerHTML = '<option value="">Select Doctor</option>' + 
      filteredDocs.map(doc => `<option value="${doc.id}">${doc.full_name} (${doc.specialization})</option>`).join('');
  });
}

function setupAppointmentBookingModal() {
  const form = document.getElementById('book-appointment-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const deptId = document.getElementById('book-dept-select').value;
    const docId = document.getElementById('book-doctor-select').value;
    const date = document.getElementById('book-date-input').value;
    const time = document.getElementById('book-time-select').value;
    const reason = document.getElementById('book-reason-input').value;

    if (!deptId || !docId || !date || !time) {
      window.api.showToast('Please fill all required appointment fields.', 'warning');
      return;
    }

    try {
      const res = await window.api.post('/appointments', {
        department_id: deptId,
        doctor_id: docId,
        appointment_date: date,
        appointment_time: time,
        reason: reason
      });

      if (res.success) {
        window.api.showToast('Appointment booked successfully!', 'success');
        closeBookModal();
        await loadAppointmentsData();
      }
    } catch (err) {
      window.api.showToast(err.message, 'danger');
    }
  });
}

function openBookModal() {
  const modal = document.getElementById('book-appointment-modal');
  if (modal) modal.classList.add('active');
}
window.openBookModal = openBookModal;

function closeBookModal() {
  const modal = document.getElementById('book-appointment-modal');
  if (modal) modal.classList.remove('active');
}
window.closeBookModal = closeBookModal;

async function cancelAppointment(appId) {
  if (!confirm('Are you sure you want to cancel this appointment?')) return;
  try {
    const res = await window.api.del(`/appointments/${appId}`);
    if (res.success) {
      window.api.showToast('Appointment cancelled', 'info');
      await loadAppointmentsData();
    }
  } catch (err) {
    window.api.showToast(err.message, 'danger');
  }
}
window.cancelAppointment = cancelAppointment;
