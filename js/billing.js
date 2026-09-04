/**
 * SmartCare Queue AI - Billing & Simulated Digital Payments Controller
 */

let currentBillToPay = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!window.Auth.requireAuth(['patient', 'staff', 'admin'])) return;

  await loadBills();
  setupPaymentModalListeners();
});

async function loadBills() {
  const container = document.getElementById('bills-list-container');
  if (!container) return;

  try {
    const res = await window.api.get('/bills');
    const bills = res.data || [];

    if (bills.length === 0) {
      container.innerHTML = `
        <div class="card text-center" style="padding: 3rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💳</div>
          <h3>No Invoices Found</h3>
          <p>You have no pending hospital billing invoices.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = bills.map(b => `
      <div class="invoice-item-card">
        <div class="invoice-header">
          <div>
            <div class="invoice-number">${b.bill_number}</div>
            <div style="font-size: 0.8rem; color: var(--text-light);">Date: ${new Date(b.created_at).toLocaleDateString()}</div>
          </div>
          <div>
            <span class="badge ${b.payment_status === 'paid' ? 'badge-success' : 'badge-warning'}">
              ${b.payment_status.toUpperCase()}
            </span>
          </div>
        </div>

        <div style="margin-bottom: 1rem;">
          <div class="fee-breakdown-row">
            <span>Doctor Consultation Fee</span>
            <span>₹${Number(b.consultation_fee).toFixed(2)}</span>
          </div>
          <div class="fee-breakdown-row">
            <span>Laboratory & Diagnostics</span>
            <span>₹${Number(b.lab_fee).toFixed(2)}</span>
          </div>
          <div class="fee-breakdown-row">
            <span>Pharmacy Medicines</span>
            <span>₹${Number(b.pharmacy_fee).toFixed(2)}</span>
          </div>
          <div class="fee-breakdown-row">
            <span>Registration & Administrative Charge</span>
            <span>₹${Number(b.registration_fee).toFixed(2)}</span>
          </div>
          <div class="fee-breakdown-row total-row">
            <span>Total Payable Amount</span>
            <span style="color: var(--primary);">₹${Number(b.total_amount).toFixed(2)}</span>
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem;">
          ${b.payment_status !== 'paid' ? `
            <button class="btn btn-primary btn-sm" onclick="openPaymentModal('${b.id}', ${b.total_amount}, '${b.bill_number}')">
              💳 Pay Now (Simulated)
            </button>
          ` : `
            <button class="btn btn-outline btn-sm" onclick="viewReceipt('${b.id}', '${b.bill_number}', ${b.total_amount})">
              🧾 Download Receipt
            </button>
          `}
        </div>
      </div>
    `).join('');
  } catch (err) {
    window.api.showToast('Failed to load bills: ' + err.message, 'danger');
  }
}

function openPaymentModal(billId, amount, billNumber) {
  currentBillToPay = billId;
  const modal = document.getElementById('payment-simulator-modal');
  if (!modal) return;

  document.getElementById('modal-pay-amount').textContent = `₹${Number(amount).toFixed(2)}`;
  document.getElementById('modal-pay-bill-num').textContent = billNumber;

  modal.classList.add('active');
}
window.openPaymentModal = openPaymentModal;

function closePaymentModal() {
  const modal = document.getElementById('payment-simulator-modal');
  if (modal) modal.classList.remove('active');
  currentBillToPay = null;
}
window.closePaymentModal = closePaymentModal;

function setupPaymentModalListeners() {
  const confirmBtn = document.getElementById('confirm-pay-btn');
  if (!confirmBtn) return;

  confirmBtn.addEventListener('click', async () => {
    if (!currentBillToPay) return;

    const selectedMethodEl = document.querySelector('.payment-method-card.selected');
    const method = selectedMethodEl ? selectedMethodEl.dataset.method : 'UPI Simulation';

    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="spinner"></span> Processing Simulated Payment...';

    try {
      const res = await window.api.post(`/bills/${currentBillToPay}/pay`, {
        payment_method: method
      });

      if (res.success) {
        window.api.showToast('Payment confirmed! Receipt generated.', 'success');
        closePaymentModal();
        await loadBills();
      }
    } catch (err) {
      window.api.showToast(err.message, 'danger');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = 'Confirm Simulated Payment';
    }
  });

  // Payment method selection cards
  document.querySelectorAll('.payment-method-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.payment-method-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
    });
  });
}

function viewReceipt(billId, billNumber, amount) {
  alert(`[SmartCare Digital Payment Receipt]\n\nInvoice: ${billNumber}\nAmount Settled: ₹${Number(amount).toFixed(2)}\nStatus: COMPLETED\nGateway: SmartCare Instant OPD Simulator\n\nThank you for choosing SmartCare Queue AI!`);
}
window.viewReceipt = viewReceipt;
