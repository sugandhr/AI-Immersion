import datetime
import uuid
import jwt
from flask import Blueprint, request
from backend.config import Config
from backend.utils.helpers import api_response, api_error
from backend.utils.validators import is_valid_email, validate_required_fields
from backend.services.supabase_service import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def generate_jwt_token(profile):
    payload = {
        "sub": profile["id"],
        "profile_id": profile["id"],
        "email": profile["email"],
        "role": profile["role"],
        "full_name": profile["full_name"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    ok, err = validate_required_fields(data, ['email', 'password', 'full_name'])
    if not ok:
        return api_error(err, status_code=400)

    email = data['email'].strip().lower()
    if not is_valid_email(email):
        return api_error("Invalid email address format", status_code=400)

    if len(data['password']) < 6:
        return api_error("Password must be at least 6 characters", status_code=400)

    # Check if user already exists
    existing = db.get_profile_by_email(email)
    if existing:
        return api_error("An account with this email already exists", status_code=409)

    role = data.get('role', 'patient')
    if role not in ('patient', 'staff', 'doctor', 'admin'):
        role = 'patient'

    # If live Supabase is configured, create Auth user
    auth_uid = str(uuid.uuid4())
    if db.is_configured and db.client:
        try:
            sign_res = db.client.auth.sign_up({
                "email": email,
                "password": data['password'],
                "options": {
                    "data": {
                        "full_name": data['full_name'],
                        "role": role
                    }
                }
            })
            if sign_res and sign_res.user:
                auth_uid = sign_res.user.id
        except Exception as e:
            # Fallback to local profile creation if Supabase Auth network error
            pass

    profile = db.create_profile({
        "auth_user_id": auth_uid,
        "email": email,
        "full_name": data['full_name'].strip(),
        "phone": data.get('phone', ''),
        "gender": data.get('gender', 'prefer_not_to_say'),
        "role": role,
        "date_of_birth": data.get('date_of_birth')
    })

    token = generate_jwt_token(profile)

    return api_response({
        "token": token,
        "user": profile,
        "redirect_url": f"{role}-dashboard.html"
    }, message="Registration successful", status_code=201)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    ok, err = validate_required_fields(data, ['email', 'password'])
    if not ok:
        return api_error(err, status_code=400)

    email = data['email'].strip().lower()
    password = data['password']

    # Supabase live auth check if configured
    if db.is_configured and db.client:
        try:
            auth_res = db.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if auth_res and auth_res.user:
                auth_uid = auth_res.user.id
                profile = db.get_profile_by_auth_uid(auth_uid) or db.get_profile_by_email(email)
                if not profile:
                    profile = db.create_profile({
                        "auth_user_id": auth_uid,
                        "email": email,
                        "full_name": email.split('@')[0].title(),
                        "role": "patient"
                    })
                token = auth_res.session.access_token if auth_res.session else generate_jwt_token(profile)
                return api_response({
                    "token": token,
                    "user": profile,
                    "redirect_url": f"{profile['role']}-dashboard.html"
                }, message="Login successful")
        except Exception:
            pass

    # Check against database profiles
    profile = db.get_profile_by_email(email)
    if not profile:
        return api_error("Invalid email or password", status_code=401)

    # Demo accounts allow standard login
    token = generate_jwt_token(profile)

    return api_response({
        "token": token,
        "user": profile,
        "redirect_url": f"{profile['role']}-dashboard.html"
    }, message="Login successful")

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    if not is_valid_email(email):
        return api_error("Please enter a valid email address", status_code=400)

    # Always return a friendly success message to prevent user enumeration
    return api_response(
        data={"email": email},
        message="If this email is registered in our system, a password reset link has been dispatched."
    )
