from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.middleware.auth_middleware import token_required
from backend.middleware.role_middleware import require_role
from backend.services.supabase_service import db

doctor_bp = Blueprint('doctors', __name__, url_prefix='/api/doctors')

@doctor_bp.route('', methods=['GET'])
def get_doctors():
    department_id = request.args.get('department_id')
    docs = db.doctors
    if department_id:
        docs = [d for d in docs if d.get('department_id') == str(department_id)]
    return api_response(docs)

@doctor_bp.route('/<doc_id>', methods=['GET'])
def get_doctor_by_id(doc_id):
    for d in db.doctors:
        if d['id'] == str(doc_id):
            return api_response(d)
    return api_error("Doctor not found", status_code=404)

@doctor_bp.route('/<doc_id>/status', methods=['PUT'])
@token_required
@require_role(['doctor', 'staff', 'admin'])
def update_doctor_status(doc_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ('available', 'busy', 'offline'):
        return api_error("Invalid status. Must be 'available', 'busy', or 'offline'.", status_code=400)

    for d in db.doctors:
        if d['id'] == str(doc_id):
            d['status'] = new_status
            return api_response(d, message="Doctor status updated successfully")
    return api_error("Doctor not found", status_code=404)
