import math
from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.services.supabase_service import db

navigation_bp = Blueprint('navigation', __name__, url_prefix='/api/navigation')

@navigation_bp.route('/locations', methods=['GET'])
def get_locations():
    return api_response(db.hospital_locations)

@navigation_bp.route('/route', methods=['GET'])
def get_route():
    from_id = request.args.get('from')
    to_id = request.args.get('to')
    
    if not from_id or not to_id:
        return api_error("Missing 'from' or 'to' location IDs", status_code=400)

    start_loc = next((loc for loc in db.hospital_locations if loc['id'] == str(from_id)), None)
    end_loc = next((loc for loc in db.hospital_locations if loc['id'] == str(to_id)), None)

    if not start_loc or not end_loc:
        return api_error("One or both location IDs are invalid", status_code=404)

    # Calculate simulated distance based on coordinate Euclidean geometry
    dx = end_loc['x_position'] - start_loc['x_position']
    dy = end_loc['y_position'] - start_loc['y_position']
    raw_dist = math.sqrt(dx * dx + dy * dy)
    
    # Approx 1 canvas pixel = 0.25 meters
    distance_meters = max(15, int(round(raw_dist * 0.25)))
    floor_change = (start_loc['floor'] != end_loc['floor'])
    
    # Average walking speed ~1.2 m/s -> ~72 meters/minute
    walking_minutes = max(1, int(math.ceil(distance_meters / 60.0)) + (2 if floor_change else 0))

    # Route steps with directions
    steps = [
        f"Start from {start_loc['name']} ({start_loc['floor']}).",
        f"Proceed along the main central corridor towards {'Stairs / Elevator to ' + end_loc['floor'] if floor_change else end_loc['location_type'].title() + ' corridor'}.",
        f"Arrive at {end_loc['name']} on {end_loc['floor']} ({end_loc['description']})."
    ]

    return api_response({
        "from": start_loc,
        "to": end_loc,
        "distance_meters": distance_meters,
        "walking_minutes": walking_minutes,
        "floor_change": floor_change,
        "steps": steps,
        "waypoints": [
            {"x": start_loc['x_position'], "y": start_loc['y_position']},
            {"x": (start_loc['x_position'] + end_loc['x_position']) // 2, "y": (start_loc['y_position'] + end_loc['y_position']) // 2},
            {"x": end_loc['x_position'], "y": end_loc['y_position']}
        ]
    })
