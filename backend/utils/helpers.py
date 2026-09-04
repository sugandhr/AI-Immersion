from flask import jsonify

def api_response(data=None, message="Operation successful", status_code=200, success=True):
    """
    Standardized API response structure as specified in requirements:
    {
        "success": true,
        "data": {},
        "message": "Operation successful"
    }
    """
    response_body = {
        "success": success,
        "message": message
    }
    if data is not None:
        response_body["data"] = data
        
    return jsonify(response_body), status_code

def api_error(message="An error occurred", status_code=400, errors=None):
    """
    Standardized API error structure:
    {
        "success": false,
        "message": "Error description"
    }
    """
    response_body = {
        "success": False,
        "message": message
    }
    if errors:
        response_body["errors"] = errors
        
    return jsonify(response_body), status_code
