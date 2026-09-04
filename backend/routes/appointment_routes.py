import uuid
import datetime
from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.utils.validators import validate_required_fields
from backend.middleware.auth_middleware import token_required
from backend.services.supabase_service import db

appointment_bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')

@appointment_bp.route('', methods=['GET'])
@token_required
def get_appointments():
    user = request.current_user
    user_id = user['id']
    role = user.get('role', 'patient')

    if role == 'patient':
        user_apps = db.get_appointments(patient_id=user_id)
    elif role == 'doctor':
        doc = next((d for d in db.get_doctors() if d.get('profile_id') == user_id), None)
        if doc:
            user_apps = db.get_appointments(doctor_id=doc['id'])
        else:
            user_apps = db.get_appointments()
    else:
        user_apps = db.get_appointments()

    return api_response(user_apps)

@appointment_bp.route('', methods=['POST'])
@token_required
def create_appointment():
    data = request.get_json() or {}
    ok, err = validate_required_fields(data, ['doctor_id', 'department_id', 'appointment_date', 'appointment_time'])
    if not ok:
        return api_error(err, status_code=400)

    patient_id = request.current_user['id']
    patient = db.get_profile_by_id(patient_id)
    doc = db.get_doctor_by_id(data['doctor_id'])
    dept = db.get_department_by_id(data['department_id'])

    new_app = {
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "patient_name": patient["full_name"] if patient else "Patient",
        "doctor_id": str(data['doctor_id']),
        "doctor_name": doc["full_name"] if doc else "Doctor",
        "department_id": str(data['department_id']),
        "department_name": dept["name"] if dept else "Department",
        "appointment_date": data['appointment_date'],
        "appointment_time": data['appointment_time'],
        "reason": data.get('reason', 'General Consultation'),
        "status": "confirmed",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

    # Stored directly in Supabase table appointments
    db.create_appointment(new_app)

    # Dispatch notification to Supabase table notifications
    db.create_notification({
        "id": str(uuid.uuid4()),
        "user_id": patient_id,
        "title": "Appointment Confirmed",
        "message": f"Appointment with {new_app['doctor_name']} ({new_app['department_name']}) confirmed for {new_app['appointment_date']} at {new_app['appointment_time']}.",
        "type": "appointment",
        "is_read": False,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })

    return api_response(new_app, message="Appointment booked successfully", status_code=201)

@appointment_bp.route('/<app_id>', methods=['PUT'])
@token_required
def update_appointment(app_id):
    data = request.get_json() or {}
    updates = {}
    if 'status' in data:
        updates['status'] = data['status']
    if 'appointment_date' in data:
        updates['appointment_date'] = data['appointment_date']
    if 'appointment_time' in data:
        updates['appointment_time'] = data['appointment_time']
    if 'reason' in data:
        updates['reason'] = data['reason']

    updated = db.update_appointment(app_id, updates)
    if updated:
        return api_response(updated, message="Appointment updated")
    return api_error("Appointment not found", status_code=404)

@appointment_bp.route('/<app_id>', methods=['DELETE'])
@token_required
def cancel_appointment(app_id):
    updated = db.update_appointment(app_id, {"status": "cancelled"})
    if updated:
        return api_response(updated, message="Appointment cancelled")
    return api_error("Appointment not found", status_code=404)
