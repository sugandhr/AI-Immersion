import uuid
import datetime
from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.middleware.auth_middleware import token_required
from backend.middleware.role_middleware import require_role
from backend.services.supabase_service import db

lab_bp = Blueprint('lab', __name__, url_prefix='/api/lab-tests')

@lab_bp.route('', methods=['GET'])
@token_required
def get_lab_orders():
    user = request.current_user
    user_id = user['id']
    role = user.get('role', 'patient')

    if role == 'patient':
        orders = db.get_lab_orders(patient_id=user_id)
    else:
        orders = db.get_lab_orders()
    return api_response(orders)

@lab_bp.route('/<order_id>', methods=['GET'])
@token_required
def get_lab_order_by_id(order_id):
    order = db.get_lab_order_by_id(order_id)
    if order:
        return api_response(order)
    return api_error("Lab order not found", status_code=404)

@lab_bp.route('', methods=['POST'])
@token_required
@require_role(['doctor', 'staff', 'admin'])
def create_lab_order():
    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    test_name = data.get('test_name')
    if not patient_id or not test_name:
        return api_error("Missing patient_id or test_name", status_code=400)

    patient = db.get_profile_by_id(patient_id)
    doc_id = request.current_user['id']
    doc_name = request.current_user['full_name']

    new_order = {
        "id": str(uuid.uuid4()),
        "patient_id": str(patient_id),
        "patient_name": patient["full_name"] if patient else "Patient",
        "doctor_id": doc_id,
        "doctor_name": doc_name,
        "test_name": test_name,
        "status": "ordered",
        "ordered_at": datetime.datetime.utcnow().isoformat() + "Z",
        "sample_collected_at": None,
        "processing_at": None,
        "report_ready_at": None,
        "report_reference": f"LAB-REF-{str(uuid.uuid4())[:8].upper()}",
        "notes": data.get('notes', 'Routine lab investigation.')
    }
    # Inserts into Supabase table lab_orders
    db.create_lab_order(new_order)

    # Notification saved to Supabase
    db.create_notification({
        "id": str(uuid.uuid4()),
        "user_id": str(patient_id),
        "title": "Lab Test Ordered",
        "message": f"New test prescribed: {test_name}. Please visit the Laboratory counter for sample collection.",
        "type": "lab",
        "is_read": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })

    return api_response(new_order, message="Lab test ordered successfully", status_code=201)

@lab_bp.route('/<order_id>/status', methods=['PUT'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def update_lab_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ('ordered', 'sample_collected', 'processing', 'report_ready'):
        return api_error("Invalid status", status_code=400)

    order = db.get_lab_order_by_id(order_id)
    if not order:
        return api_error("Lab order not found", status_code=404)

    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    updates = {"status": new_status}
    if new_status == 'sample_collected' and not order.get('sample_collected_at'):
        updates['sample_collected_at'] = now_iso
    elif new_status == 'processing' and not order.get('processing_at'):
        updates['processing_at'] = now_iso
    elif new_status == 'report_ready':
        updates['report_ready_at'] = now_iso
        db.create_notification({
            "id": str(uuid.uuid4()),
            "user_id": order['patient_id'],
            "title": "Lab Report Ready!",
            "message": f"Your diagnostic report for '{order['test_name']}' is now available online.",
            "type": "lab",
            "is_read": False,
            "created_at": now_iso
        })

    # Update in Supabase
    updated = db.update_lab_order(order_id, updates)
    return api_response(updated or order, message=f"Lab order status updated to {new_status}")
