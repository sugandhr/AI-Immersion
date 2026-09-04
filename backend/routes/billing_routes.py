import uuid
import datetime
from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.middleware.auth_middleware import token_required
from backend.middleware.role_middleware import require_role
from backend.services.supabase_service import db

billing_bp = Blueprint('billing', __name__, url_prefix='/api/bills')

@billing_bp.route('', methods=['GET'])
@token_required
def get_bills():
    user = request.current_user
    user_id = user['id']
    role = user.get('role', 'patient')

    if role == 'patient':
        bills = db.get_bills(patient_id=user_id)
    else:
        bills = db.get_bills()
    return api_response(bills)

@billing_bp.route('/<bill_id>', methods=['GET'])
@token_required
def get_bill_by_id(bill_id):
    bill = db.get_bill_by_id(bill_id)
    if bill:
        return api_response(bill)
    return api_error("Bill not found", status_code=404)

@billing_bp.route('/<bill_id>/pay', methods=['POST'])
@token_required
def pay_bill(bill_id):
    data = request.get_json() or {}
    payment_method = data.get('payment_method', 'UPI / QR Simulation')
    user_id = request.current_user['id']

    target_bill = db.get_bill_by_id(bill_id)
    if not target_bill:
        return api_error("Bill not found", status_code=404)

    if target_bill.get('payment_status') == 'paid':
        return api_error("This bill has already been settled", status_code=400)

    # Simulated transaction processing
    txn_id = f"TXN_SIM_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:6].upper()}"
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"

    # Updates bill in Supabase table bills
    updated_bill = db.update_bill(bill_id, {"payment_status": "paid"})

    payment_record = {
        "id": str(uuid.uuid4()),
        "bill_id": target_bill['id'],
        "patient_id": user_id,
        "amount": float(target_bill['total_amount']),
        "payment_method": payment_method,
        "transaction_id": txn_id,
        "status": "completed",
        "created_at": now_iso
    }
    # Inserts into Supabase table payments
    db.create_payment(payment_record)

    # Dispatch notification into Supabase table notifications
    db.create_notification({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": "Payment Successful",
        "message": f"Payment of ₹{float(target_bill['total_amount']):.2f} for bill {target_bill['bill_number']} was successful. Ref: {txn_id}.",
        "type": "billing",
        "is_read": False,
        "created_at": now_iso
    })

    return api_response({
        "bill": updated_bill or target_bill,
        "payment": payment_record
    }, message="Payment processed and verified successfully")

@billing_bp.route('', methods=['POST'])
@token_required
@require_role(['staff', 'admin'])
def create_bill():
    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    if not patient_id:
        return api_error("Missing patient_id", status_code=400)

    consultation = float(data.get('consultation_fee', 0))
    lab = float(data.get('lab_fee', 0))
    pharmacy = float(data.get('pharmacy_fee', 0))
    reg = float(data.get('registration_fee', 0))
    other = float(data.get('other_charges', 0))
    total = consultation + lab + pharmacy + reg + other

    all_bills = db.get_bills()
    bill_num = f"INV-2026-{len(all_bills) + 892:04d}"

    new_bill = {
        "id": str(uuid.uuid4()),
        "patient_id": str(patient_id),
        "bill_number": bill_num,
        "consultation_fee": consultation,
        "lab_fee": lab,
        "pharmacy_fee": pharmacy,
        "registration_fee": reg,
        "other_charges": other,
        "total_amount": total,
        "payment_status": "unpaid",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    # Inserts directly into Supabase table bills
    db.create_bill(new_bill)

    db.create_notification({
        "id": str(uuid.uuid4()),
        "user_id": str(patient_id),
        "title": f"New Invoice: {bill_num}",
        "message": f"An invoice for ₹{total:.2f} has been generated. You can pay digitally via the Billing section.",
        "type": "billing",
        "is_read": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })

    return api_response(new_bill, message="Bill generated successfully", status_code=201)
