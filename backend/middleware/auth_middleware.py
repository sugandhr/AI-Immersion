import functools
import jwt
from flask import request
from backend.config import Config
from backend.utils.helpers import api_error
from backend.services.supabase_service import db

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return api_error("Missing Authorization header. Bearer token required.", status_code=401)
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return api_error("Invalid Authorization format. Expected 'Bearer <token>'.", status_code=401)
        
        token = parts[1].strip()

        # If live Supabase client is available, attempt to get user from auth
        if db.is_configured and db.client:
            try:
                user_res = db.client.auth.get_user(token)
                if user_res and user_res.user:
                    auth_uid = user_res.user.id
                    profile = db.get_profile_by_auth_uid(auth_uid)
                    if not profile:
                        # Auto-create profile if missing
                        email = user_res.user.email
                        meta = user_res.user.user_metadata or {}
                        full_name = meta.get('full_name', email.split('@')[0].title())
                        role = meta.get('role', 'patient')
                        profile = db.create_profile({
                            "auth_user_id": auth_uid,
                            "email": email,
                            "full_name": full_name,
                            "role": role
                        })
                    request.current_user = profile
                    return f(*args, **kwargs)
            except Exception as e:
                # Fall through to local token verification
                pass

        # Verification for local/demo tokens
        try:
            # Check if token is signed with our secret
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            profile_id = payload.get("sub") or payload.get("profile_id")
            profile = db.get_profile_by_id(profile_id)
            if not profile:
                return api_error("User profile not found", status_code=401)
            request.current_user = profile
            return f(*args, **kwargs)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass

        # Demo fallback tokens for instant evaluation
        if token.startswith("demo_token_"):
            role = token.replace("demo_token_", "")
            for p in db.profiles:
                if p["role"] == role:
                    request.current_user = p
                    return f(*args, **kwargs)

        return api_error("Invalid or expired authentication token. Please log in again.", status_code=401)

    return decorated
