import uuid
import datetime
import threading
from backend.services.supabase_service import db

_queue_lock = threading.Lock()

class QueueService:
    @staticmethod
    def get_departments():
        return db.get_departments(active_only=True)

    @staticmethod
    def get_department_by_id(dept_id):
        return db.get_department_by_id(dept_id)

    @staticmethod
    def get_today_queue(department_id, service_type="Consultation"):
        return db.get_today_queue(department_id, service_type)

    @staticmethod
    def join_queue(patient_id, department_id, service_type="Consultation", doctor_id=None):
        with _queue_lock:
            today = datetime.date.today().isoformat()
            
            # 1. Check for duplicate active entry in this queue
            active_patient_entries = db.get_queue_entries(patient_id=patient_id)
            for e in active_patient_entries:
                if e.get("status") in ('waiting', 'called', 'serving'):
                    q = db.get_today_queue(department_id, service_type)
                    if q and str(q["id"]) == str(e["queue_id"]):
                        return False, "You already have an active token in this queue.", None

            # 2. Retrieve today's queue
            queue = db.get_today_queue(department_id, service_type)
            next_token = int(queue.get("current_token_number", 0)) + 1
            db.update_queue(queue["id"], {"current_token_number": next_token})

            dept = db.get_department_by_id(department_id)
            prefix = dept.get("code_prefix", "Q") if dept else "Q"
            token_code = f"{prefix}-{next_token:02d}"

            # 3. Calculate waiting time & patients ahead
            queue_entries = db.get_queue_entries(queue_id=queue["id"])
            patients_ahead = len([
                e for e in queue_entries 
                if e.get("status") == 'waiting'
            ])

            # Active doctors in department
            all_docs = db.get_doctors(department_id=department_id)
            active_docs = len([
                doc for doc in all_docs 
                if doc.get("status") == "available"
            ])
            if active_docs == 0:
                active_docs = 1

            # Average consultation time
            avg_consult = 15
            for doc in all_docs:
                avg_consult = doc.get("average_consultation_minutes", 15)
                break

            estimated_wait = max(5, int((patients_ahead * avg_consult) / active_docs))

            patient = db.get_profile_by_id(patient_id)
            entry_id = str(uuid.uuid4())
            new_entry = {
                "id": entry_id,
                "queue_id": queue["id"],
                "department_id": str(department_id),
                "department_name": dept["name"] if dept else "General",
                "service_type": service_type,
                "patient_id": str(patient_id),
                "patient_name": patient["full_name"] if patient else "Patient",
                "doctor_id": str(doctor_id) if doctor_id else None,
                "token_number": next_token,
                "token_code": token_code,
                "status": "waiting",
                "priority_requested": False,
                "priority_approved": False,
                "joined_at": datetime.datetime.utcnow().isoformat() + "Z",
                "called_at": None,
                "serving_at": None,
                "completed_at": None,
                "estimated_wait_minutes": estimated_wait,
                "counter_number": None
            }
            # Directly inserts into Supabase table queue_entries
            db.create_queue_entry(new_entry)

            # Auto Notification saved to Supabase table notifications
            db.create_notification({
                "id": str(uuid.uuid4()),
                "user_id": str(patient_id),
                "title": f"Queue Joined: {token_code}",
                "message": f"You joined {dept['name'] if dept else 'Department'} queue. Token: {token_code}. Estimated wait: {estimated_wait} mins.",
                "type": "queue",
                "is_read": False,
                "created_at": datetime.datetime.utcnow().isoformat() + "Z"
            })

            return True, "Successfully joined the queue.", {
                "entry": new_entry,
                "patients_ahead": patients_ahead,
                "estimated_wait_minutes": estimated_wait
            }

    @staticmethod
    def get_active_entry_for_patient(patient_id):
        patient_entries = db.get_queue_entries(patient_id=patient_id)
        active_entries = [
            e for e in patient_entries 
            if e.get("status") in ('waiting', 'called', 'serving')
        ]
        if not active_entries:
            return None

        entry = active_entries[-1]
        all_queues = db.get_all_queues()
        queue = next((q for q in all_queues if str(q["id"]) == str(entry["queue_id"])), None)
        
        # Calculate current serving in this queue
        queue_entries = db.get_queue_entries(queue_id=entry["queue_id"])
        serving_entry = next((
            e for e in queue_entries 
            if e.get("status") in ('serving', 'called')
        ), None)
        
        # Calculate how many waiting patients are ahead of this entry
        ahead_count = len([
            e for e in queue_entries 
            if e.get("status") == 'waiting' and int(e.get("token_number", 0)) < int(entry.get("token_number", 0))
        ])

        dept = db.get_department_by_id(queue["department_id"]) if queue else None

        return {
            "entry": entry,
            "department": dept,
            "current_serving": serving_entry["token_code"] if serving_entry else "None",
            "now_serving_number": serving_entry["token_number"] if serving_entry else 0,
            "patients_ahead": ahead_count,
            "queue_status": queue["status"] if queue else "active"
        }

    @staticmethod
    def get_queue_details(queue_id):
        all_queues = db.get_all_queues()
        queue = next((q for q in all_queues if str(q["id"]) == str(queue_id)), None)
        if not queue:
            return None
        
        entries = db.get_queue_entries(queue_id=queue_id)
        waiting = [e for e in entries if e.get("status") == "waiting"]
        called = [e for e in entries if e.get("status") == "called"]
        serving = [e for e in entries if e.get("status") == "serving"]
        completed = [e for e in entries if e.get("status") == "completed"]
        skipped = [e for e in entries if e.get("status") == "skipped"]

        return {
            "queue": queue,
            "total_tokens": len(entries),
            "waiting_count": len(waiting),
            "serving_token": serving[0] if serving else (called[0] if called else None),
            "waiting_list": waiting,
            "called_list": called,
            "serving_list": serving,
            "completed_list": completed,
            "skipped_list": skipped
        }

    @staticmethod
    def call_next(queue_id, counter_number="Counter 1"):
        with _queue_lock:
            # 1. Complete or finish any currently serving token if appropriate
            queue_entries = db.get_queue_entries(queue_id=queue_id)
            for e in queue_entries:
                if e.get("status") in ('serving', 'called'):
                    db.update_queue_entry(e["id"], {
                        "status": "completed",
                        "completed_at": datetime.datetime.utcnow().isoformat() + "Z"
                    })

            # 2. Pick next waiting entry (prioritizing approved priority requests first)
            waiting_entries = [
                e for e in db.get_queue_entries(queue_id=queue_id)
                if e.get("status") == "waiting"
            ]
            if not waiting_entries:
                return False, "No patients waiting in queue.", None

            waiting_entries.sort(key=lambda x: (not x.get("priority_approved", False), int(x.get("token_number", 0))))
            next_entry = waiting_entries[0]

            now_iso = datetime.datetime.utcnow().isoformat() + "Z"
            updated = db.update_queue_entry(next_entry["id"], {
                "status": "called",
                "called_at": now_iso,
                "counter_number": counter_number
            })

            # Send Notification to Patient and store in Supabase
            db.create_notification({
                "id": str(uuid.uuid4()),
                "user_id": next_entry["patient_id"],
                "title": f"Token {next_entry['token_code']} Called!",
                "message": f"Your token {next_entry['token_code']} is now being called! Please proceed immediately to {counter_number}.",
                "type": "queue",
                "is_read": False,
                "created_at": now_iso
            })

            return True, f"Token {next_entry['token_code']} called successfully.", updated or next_entry

    @staticmethod
    def start_serving(entry_id):
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        updated = db.update_queue_entry(entry_id, {
            "status": "serving",
            "serving_at": now_iso
        })
        if updated:
            return True, f"Now serving token {updated.get('token_code', '')}", updated
        return False, "Queue entry not found", None

    @staticmethod
    def complete_entry(entry_id):
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        updated = db.update_queue_entry(entry_id, {
            "status": "completed",
            "completed_at": now_iso
        })
        if updated:
            db.create_notification({
                "id": str(uuid.uuid4()),
                "user_id": updated["patient_id"],
                "title": "Consultation Completed",
                "message": f"Your consultation for token {updated['token_code']} is completed. Thank you!",
                "type": "queue",
                "is_read": False,
                "created_at": now_iso
            })
            return True, f"Token {updated['token_code']} marked as completed.", updated
        return False, "Queue entry not found", None

    @staticmethod
    def skip_entry(entry_id):
        updated = db.update_queue_entry(entry_id, {"status": "skipped"})
        if updated:
            return True, f"Token {updated.get('token_code', '')} skipped.", updated
        return False, "Queue entry not found", None

    @staticmethod
    def recall_entry(entry_id, counter_number=None):
        updates = {"status": "called"}
        if counter_number:
            updates["counter_number"] = counter_number
        updated = db.update_queue_entry(entry_id, updates)
        if updated:
            db.create_notification({
                "id": str(uuid.uuid4()),
                "user_id": updated["patient_id"],
                "title": f"RECALL: Token {updated['token_code']}",
                "message": f"Final call for token {updated['token_code']} at {updated.get('counter_number', 'Counter 1')}. Please proceed immediately.",
                "type": "queue",
                "is_read": False,
                "created_at": datetime.datetime.utcnow().isoformat() + "Z"
            })
            return True, f"Token {updated['token_code']} recalled.", updated
        return False, "Queue entry not found", None
