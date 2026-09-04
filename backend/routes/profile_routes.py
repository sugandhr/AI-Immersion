from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.middleware.auth_middleware import token_required
from backend.services.supabase_service import db

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@profile_bp.route('/me', methods=['GET'])
@token_required
def get_current_profile():
    # Fresh fetch from database
    user_id = request.current_user['id']
    profile = db.get_profile_by_id(user_id)
    return api_response(profile or request.current_user)

@profile_bp.route('/me', methods=['PUT'])
@token_required
def update_current_profile():
    data = request.get_json() or {}
    user_id = request.current_user['id']
    profile = db.get_profile_by_id(user_id)
    if not profile:
        return api_error("User profile not found", status_code=404)

    updates = {}
    if 'full_name' in data and data['full_name'].strip():
        updates['full_name'] = data['full_name'].strip()
    if 'phone' in data:
        updates['phone'] = data['phone'].strip()
    if 'gender' in data:
        updates['gender'] = data['gender']
    if 'date_of_birth' in data:
        updates['date_of_birth'] = data['date_of_birth']

    # Update in Supabase profiles table
    updated_profile = db.update_profile(user_id, updates)

    return api_response(updated_profile or profile, message="Profile updated successfully")
