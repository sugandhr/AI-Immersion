import functools
from flask import request
from backend.utils.helpers import api_error

def require_role(allowed_roles):
    """
    Decorator to restrict endpoint access by role.
    allowed_roles: string or list of strings ('patient', 'staff', 'doctor', 'admin')
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = getattr(request, 'current_user', None)
            if not current_user:
                return api_error("Unauthorized. User context missing.", status_code=401)
            
            user_role = current_user.get('role', 'patient')
            # Admin has superuser access to all operational endpoints
            if user_role not in allowed_roles and user_role != 'admin':
                return api_error(
                    f"Forbidden. Role '{user_role}' is not authorized to access this resource. Required: {', '.join(allowed_roles)}",
                    status_code=403
                )
            return f(*args, **kwargs)
        return decorated_function
    return decorator
