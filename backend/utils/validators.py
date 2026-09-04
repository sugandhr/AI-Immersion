import re

def is_valid_email(email):
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email.strip()))

def validate_required_fields(data, required_fields):
    if not data or not isinstance(data, dict):
        return False, "Request body must be a valid JSON object"
    missing = [field for field in required_fields if field not in data or data[field] is None or str(data[field]).strip() == '']
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None
