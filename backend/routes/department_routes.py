from flask import Blueprint
from backend.utils.helpers import api_response, api_error
from backend.services.supabase_service import db

dept_bp = Blueprint('departments', __name__, url_prefix='/api/departments')

@dept_bp.route('', methods=['GET'])
def get_departments():
    active_depts = [d for d in db.departments if d.get('active', True)]
    return api_response(active_depts)

@dept_bp.route('/<dept_id>', methods=['GET'])
def get_department(dept_id):
    for d in db.departments:
        if d['id'] == str(dept_id):
            return api_response(d)
    return api_error("Department not found", status_code=404)
