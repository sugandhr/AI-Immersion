import re
from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.services.prediction_service import PredictionService
from backend.services.queue_service import QueueService
from backend.services.supabase_service import db

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@ai_bp.route('/wait-time/<queue_entry_id>', methods=['GET'])
def get_wait_time(queue_entry_id):
    prediction = PredictionService.calculate_wait_time(queue_entry_id)
    return api_response(prediction)

@ai_bp.route('/best-time/<department_id>', methods=['GET'])
def get_best_time_for_dept(department_id):
    recommendation = PredictionService.get_best_time_to_visit(department_id)
    return api_response(recommendation)

@ai_bp.route('/best-time', methods=['GET'])
def get_best_time_general():
    dept_id = request.args.get('department_id')
    recommendation = PredictionService.get_best_time_to_visit(dept_id)
    return api_response(recommendation)

@ai_bp.route('/assistant', methods=['POST'])
def ai_assistant_query():
    data = request.get_json() or {}
    query = data.get('query', '').strip().lower()
    user_id = data.get('user_id')

    if not query:
        return api_error("Query message cannot be empty", status_code=400)

    # 1. MEDICAL SAFETY GUARDRAILS (Strict non-negotiable rule)
    medical_keywords = [
        'diagnose', 'symptom', 'disease', 'medicine', 'prescribe', 'drug',
        'tablet', 'dose', 'pain in chest', 'heart attack', 'stroke', 'bleeding',
        'cure', 'treatment', 'cancer', 'infection', 'fever remedy', 'what disease'
    ]
    if any(k in query for k in medical_keywords):
        return api_response({
            "query": query,
            "response": (
                "⚠️ **Medical Safety Guardrail**: SmartCare AI is strictly an administrative and operational "
                "hospital assistant. I am not certified to provide medical diagnosis, prescribe treatments, "
                "or recommend medications. If you feel unwell or suspect an emergency, please visit our "
                "Emergency Bay on the Ground Floor immediately or speak with one of our licensed physicians."
            ),
            "type": "medical_guardrail"
        })

    # 2. EMERGENCY QUERY
    if 'emergency' in query or 'ambulance' in query or 'trauma' in query:
        return api_response({
            "query": query,
            "response": (
                "🚨 **Emergency Alert**: The Emergency Department is located on the Ground Floor at Gate 2. "
                "Immediate trauma resuscitation and 24x7 medical officers are on standby. "
                "Emergency Helpline: +91 98765 00000. Please proceed directly without waiting for a token."
            ),
            "type": "emergency"
        })

    # 3. QUEUE POSITION / TOKEN INQUIRY
    if any(w in query for w in ['queue', 'token', 'position', 'ahead', 'wait time', 'my turn']):
        active_entry = None
        if user_id:
            active_entry = QueueService.get_active_entry_for_patient(user_id)
        
        # If no authenticated patient user_id passed, check demo default patient
        if not active_entry:
            active_entry = QueueService.get_active_entry_for_patient("c0000000-0000-0000-0000-000000000001")

        if active_entry:
            entry = active_entry["entry"]
            token = entry.get("token_code")
            ahead = active_entry.get("patients_ahead", 0)
            wait = entry.get("estimated_wait_minutes", 15)
            serving = active_entry.get("current_serving", "None")
            dept = active_entry.get("department", {}).get("name", "Cardiology")
            return api_response({
                "query": query,
                "response": (
                    f"Your active token is **{token}** in **{dept}**. "
                    f"Currently serving: **{serving}**. "
                    f"There are **{ahead} patients ahead** of you. "
                    f"Estimated waiting time: approximately **{wait} minutes**."
                ),
                "type": "queue_info"
            })
        else:
            return api_response({
                "query": query,
                "response": (
                    "You do not currently have an active queue token. "
                    "You can easily join an outpatient queue by selecting your desired department on the 'Join Queue' page."
                ),
                "type": "queue_info"
            })

    # 4. LOCATION / INDOOR NAVIGATION INQUIRY
    locations_map = {
        'cardiology': "Cardiology is on the **First Floor, Wing B, Room 204**.",
        'orthopedics': "Orthopedics is located on the **First Floor, Wing B, Room 210**.",
        'laboratory': "The Central Laboratory is on the **Ground Floor, Central Block (Lab 1)** near the main lounge.",
        'lab': "The Central Laboratory is on the **Ground Floor, Central Block (Lab 1)**.",
        'billing': "The Billing Counters (1 to 3) are in the **Ground Floor Main Atrium**.",
        'pharmacy': "The Outpatient Pharmacy is in the **Ground Floor Main Atrium at Counter 4**.",
        'general medicine': "General Medicine OPD is on the **Ground Floor, Wing A (Rooms 101-104)**.",
        'pediatrics': "Pediatrics is on the **Ground Floor, Wing C (Room 105)**.",
        'reception': "Registration and Reception are directly beside the **Main Entrance on the Ground Floor**.",
        'registration': "Registration is at the **Ground Floor Main Entrance**."
    }
    for loc_key, loc_desc in locations_map.items():
        if loc_key in query:
            return api_response({
                "query": query,
                "response": f"📍 {loc_desc} You can also use our interactive **Hospital Map** to get step-by-step walking directions.",
                "type": "navigation_info"
            })

    # 5. BEST TIME TO VISIT INQUIRY
    if any(w in query for w in ['best time', 'less crowd', 'peak hour', 'rush']):
        rec = PredictionService.get_best_time_to_visit()
        return api_response({
            "query": query,
            "response": (
                f"🕒 Based on historical queue patterns, the lowest congestion period is **{rec['recommended_window']}** "
                f"with an expected wait time of **{rec['recommended_wait']}**. "
                f"Peak crowd hours are typically between **{rec['peak_window']}** (wait ~{rec['peak_wait']})."
            ),
            "type": "best_time_info"
        })

    # 6. BILLING / APPOINTMENT / LAB INQUIRIES
    if 'bill' in query or 'fee' in query or 'payment' in query:
        return api_response({
            "query": query,
            "response": (
                "You can view and settle your hospital bills securely via the **Billing & Payments** tab. "
                "Our platform supports digital simulated payment confirmation with instant transaction receipts."
            ),
            "type": "billing_info"
        })

    if 'appointment' in query or 'book' in query or 'doctor' in query:
        return api_response({
            "query": query,
            "response": (
                "To book or manage a scheduled doctor consultation, head to the **Appointments** page where you can "
                "pick your preferred specialist and available time slot."
            ),
            "type": "appointment_info"
        })

    if 'report' in query or 'test' in query:
        return api_response({
            "query": query,
            "response": (
                "Diagnostic reports can be tracked under the **Lab Tests** section. "
                "You will receive an instant notification as soon as your sample report is marked ready."
            ),
            "type": "lab_info"
        })

    # DEFAULT HELPFUL ASSISTANT RESPONSE
    return api_response({
        "query": query,
        "response": (
            "Hello! I am your **SmartCare AI Assistant**. I can assist you with:\n"
            "• Checking your active queue position and estimated wait time\n"
            "• Finding directions to hospital departments, labs, and counters\n"
            "• Identifying the best low-crowd hours to visit\n"
            "• Booking appointments and checking lab order status\n\n"
            "How can I help you today?"
        ),
        "type": "general_help"
    })
