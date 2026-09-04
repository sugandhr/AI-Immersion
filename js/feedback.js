/**
 * SmartCare Queue AI - Feedback & Patient Ratings Controller
 */

let selectedRatings = {
  overall: 5,
  waiting: 5,
  staff: 5,
  doctor: 5,
  facility: 5
};

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth()) return;

  setupStarRatings();
  await loadCompletedVisitsForFeedback();
  setupFeedbackForm();
});

function setupStarRatings() {
  const categories = ['overall', 'waiting', 'staff', 'doctor', 'facility'];

  categories.forEach(cat => {
    const starContainer = document.getElementById(`stars-${cat}`);
    if (!starContainer) return;

    starContainer.innerHTML = [1, 2, 3, 4, 5].map(num => `
      <span class="star-btn ${num <= 5 ? 'active' : ''}" data-val="${num}" onclick="setRating('${cat}', ${num})">★</span>
    `).join('');
  });
}

function setRating(category, val) {
  selectedRatings[category] = val;
  const starContainer = document.getElementById(`stars-${category}`);
  if (!starContainer) return;

  const stars = starContainer.querySelectorAll('.star-btn');
  stars.forEach((s, idx) => {
    s.classList.toggle('active', (idx + 1) <= val);
  });
}
window.setRating = setRating;

async function loadCompletedVisitsForFeedback() {
  const selectEl = document.getElementById('feedback-visit-select');
  if (!selectEl) return;

  try {
    const res = await window.api.get('/waiting-history');
    const visits = (res.data || {}).visits || [];

    if (visits.length === 0) {
      selectEl.innerHTML = '<option value="">No completed visits recorded yet</option>';
      return;
    }

    selectEl.innerHTML = '<option value="">Select Visit to Review</option>' + 
      visits.map(v => `<option value="${v.id}" data-dept="${v.department_id || ''}">Token ${v.token_code} - ${v.department_name} (${new Date(v.completed_at || v.joined_at).toLocaleDateString()})</option>`).join('');
  } catch (err) {
    console.warn(err);
  }
}

function setupFeedbackForm() {
  const form = document.getElementById('feedback-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const visitSelect = document.getElementById('feedback-visit-select');
    const selectedOption = visitSelect.options[visitSelect.selectedIndex];
    const visitId = visitSelect.value || null;
    const deptId = selectedOption ? selectedOption.dataset.dept : null;
    const comment = document.getElementById('feedback-comment').value.trim();

    try {
      const res = await window.api.post('/feedback', {
        queue_entry_id: visitId,
        department_id: deptId,
        overall_rating: selectedRatings.overall,
        waiting_rating: selectedRatings.waiting,
        staff_rating: selectedRatings.staff,
        doctor_rating: selectedRatings.doctor,
        facility_rating: selectedRatings.facility,
        comment: comment
      });

      if (res.success) {
        window.api.showToast('Thank you! Your feedback helps improve care quality.', 'success');
        form.reset();
        setupStarRatings();
      }
    } catch (err) {
      window.api.showToast(err.message, 'danger');
    }
  });
}
