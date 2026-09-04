import os
import json
import uuid
import datetime
import threading
from pathlib import Path
from backend.config import Config

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "store.json"

class SupabaseService:
    def __init__(self):
        self.is_configured = Config.IS_SUPABASE_CONFIGURED
        self.client = None
        self.admin_client = None
        self._lock = threading.Lock()

        if self.is_configured and create_client:
            try:
                self.client = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
                if Config.SUPABASE_SERVICE_ROLE_KEY:
                    self.admin_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
                else:
                    self.admin_client = self.client
                print(f"[SmartCare Supabase] Successfully connected to live Supabase: {Config.SUPABASE_URL}")
            except Exception as e:
                print(f"[SmartCare Supabase] Connection warning: {e}")
                self.is_configured = False

        self._init_memory_store()
        self._load_from_disk()

    # =========================================================================
    # POSTGREST DIRECT EXECUTION HELPERS
    # =========================================================================
    def execute_supabase_select(self, table_name, filters=None, order_col=None, order_desc=False, limit=None):
        """Directly queries the live Supabase PostgreSQL table via PostgREST."""
        if self.is_configured and self.admin_client:
            try:
                query = self.admin_client.table(table_name).select('*')
                if filters:
                    for k, v in filters.items():
                        if v is not None:
                            query = query.eq(k, v)
                if order_col:
                    query = query.order(order_col, desc=order_desc)
                if limit:
                    query = query.limit(limit)
                res = query.execute()
                if res and hasattr(res, 'data'):
                    return res.data
            except Exception as e:
                print(f"[Supabase Select Error] {table_name}: {e}")
        return None

    def execute_supabase_insert(self, table_name, data):
        """Directly inserts a record into the live Supabase PostgreSQL table."""
        if self.is_configured and self.admin_client:
            try:
                # Remove transient non-schema keys if present
                clean_data = self._clean_record_for_schema(table_name, data)
                res = self.admin_client.table(table_name).insert(clean_data).execute()
                if res and hasattr(res, 'data') and res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[Supabase Insert Error] {table_name}: {e}")
        return None

    def execute_supabase_update(self, table_name, match_col, match_val, updates):
        """Directly updates a record in the live Supabase PostgreSQL table."""
        if self.is_configured and self.admin_client:
            try:
                clean_updates = self._clean_record_for_schema(table_name, updates)
                res = self.admin_client.table(table_name).update(clean_updates).eq(match_col, match_val).execute()
                if res and hasattr(res, 'data') and res.data:
                    return res.data[0]
            except Exception as e:
                print(f"[Supabase Update Error] {table_name}: {e}")
        return None

    def execute_supabase_delete(self, table_name, match_col, match_val):
        """Directly deletes a record from the live Supabase PostgreSQL table."""
        if self.is_configured and self.admin_client:
            try:
                res = self.admin_client.table(table_name).delete().eq(match_col, match_val).execute()
                if res and hasattr(res, 'data'):
                    return res.data
            except Exception as e:
                print(f"[Supabase Delete Error] {table_name}: {e}")
        return None

    def _clean_record_for_schema(self, table_name, record):
        """Cleans dictionary to match exact Supabase schema definitions."""
        valid_columns = {
            "profiles": {"id", "auth_user_id", "full_name", "email", "phone", "date_of_birth", "gender", "role", "profile_image", "created_at", "updated_at"},
            "departments": {"id", "name", "description", "location", "floor", "code_prefix", "active", "created_at"},
            "doctors": {"id", "profile_id", "department_id", "specialization", "room_number", "average_consultation_minutes", "status", "created_at", "updated_at"},
            "queues": {"id", "department_id", "service_type", "queue_date", "current_token_number", "status", "created_at", "updated_at"},
            "queue_entries": {"id", "queue_id", "patient_id", "doctor_id", "token_number", "token_code", "status", "priority_requested", "priority_approved", "joined_at", "called_at", "serving_at", "completed_at", "estimated_wait_minutes", "counter_number", "created_at"},
            "appointments": {"id", "patient_id", "doctor_id", "department_id", "appointment_date", "appointment_time", "reason", "status", "created_at", "updated_at"},
            "lab_orders": {"id", "patient_id", "doctor_id", "test_name", "status", "ordered_at", "sample_collected_at", "processing_at", "report_ready_at", "report_reference", "notes", "created_at"},
            "bills": {"id", "patient_id", "bill_number", "consultation_fee", "lab_fee", "pharmacy_fee", "registration_fee", "other_charges", "total_amount", "payment_status", "created_at"},
            "payments": {"id", "bill_id", "patient_id", "amount", "payment_method", "transaction_id", "status", "created_at"},
            "notifications": {"id", "user_id", "title", "message", "type", "is_read", "created_at"},
            "hospital_locations": {"id", "name", "location_type", "floor", "description", "x_position", "y_position", "created_at"},
            "priority_requests": {"id", "patient_id", "queue_entry_id", "reason", "status", "reviewed_by", "created_at", "reviewed_at"},
            "feedback": {"id", "patient_id", "department_id", "queue_entry_id", "overall_rating", "waiting_rating", "staff_rating", "doctor_rating", "facility_rating", "comment", "created_at"}
        }
        allowed = valid_columns.get(table_name)
        if not allowed:
            return record
        return {k: v for k, v in record.items() if k in allowed}

    # =========================================================================
    # PERSISTENCE & CACHE ENGINE
    # =========================================================================
    def _save_to_disk(self):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            state = {
                "profiles": self.profiles,
                "departments": self.departments,
                "doctors": self.doctors,
                "queues": self.queues,
                "queue_entries": self.queue_entries,
                "appointments": self.appointments,
                "lab_orders": self.lab_orders,
                "bills": self.bills,
                "payments": self.payments,
                "notifications": self.notifications,
                "hospital_locations": self.hospital_locations,
                "feedback": self.feedback,
                "priority_requests": self.priority_requests
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            pass

    def _load_from_disk(self):
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.profiles = state.get("profiles", self.profiles)
                    self.departments = state.get("departments", self.departments)
                    self.doctors = state.get("doctors", self.doctors)
                    self.queues = state.get("queues", self.queues)
                    self.queue_entries = state.get("queue_entries", self.queue_entries)
                    self.appointments = state.get("appointments", self.appointments)
                    self.lab_orders = state.get("lab_orders", self.lab_orders)
                    self.bills = state.get("bills", self.bills)
                    self.payments = state.get("payments", self.payments)
                    self.notifications = state.get("notifications", self.notifications)
                    self.hospital_locations = state.get("hospital_locations", self.hospital_locations)
                    self.feedback = state.get("feedback", self.feedback)
                    self.priority_requests = state.get("priority_requests", self.priority_requests)
            except Exception:
                pass

    # =========================================================================
    # 1. PROFILES
    # =========================================================================
    def get_profile_by_email(self, email):
        clean_email = email.strip().lower()
        cloud_data = self.execute_supabase_select("profiles", {"email": clean_email})
        if cloud_data:
            return cloud_data[0]
        for p in self.profiles:
            if p["email"].lower() == clean_email:
                return p
        return None

    def get_profile_by_id(self, profile_id):
        cloud_data = self.execute_supabase_select("profiles", {"id": str(profile_id)})
        if cloud_data:
            return cloud_data[0]
        for p in self.profiles:
            if p["id"] == str(profile_id):
                return p
        return None

    def get_profile_by_auth_uid(self, auth_uid):
        cloud_data = self.execute_supabase_select("profiles", {"auth_user_id": str(auth_uid)})
        if cloud_data:
            return cloud_data[0]
        for p in self.profiles:
            if p.get("auth_user_id") == str(auth_uid):
                return p
        return None

    def create_profile(self, profile_data):
        with self._lock:
            profile_id = profile_data.get("id") or str(uuid.uuid4())
            new_p = {
                "id": profile_id,
                "auth_user_id": profile_data.get("auth_user_id", str(uuid.uuid4())),
                "full_name": profile_data.get("full_name"),
                "email": profile_data.get("email").strip().lower(),
                "phone": profile_data.get("phone", ""),
                "gender": profile_data.get("gender", "prefer_not_to_say"),
                "role": profile_data.get("role", "patient"),
                "date_of_birth": profile_data.get("date_of_birth"),
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
            }
            self.execute_supabase_insert("profiles", new_p)
            self.profiles.append(new_p)
            self._save_to_disk()
            return new_p

    def update_profile(self, profile_id, updates):
        with self._lock:
            updates["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            self.execute_supabase_update("profiles", "id", str(profile_id), updates)
            for p in self.profiles:
                if p["id"] == str(profile_id):
                    p.update(updates)
                    self._save_to_disk()
                    return p
            return None

    # =========================================================================
    # 2. DEPARTMENTS
    # =========================================================================
    def get_departments(self, active_only=True):
        cloud_data = self.execute_supabase_select("departments", {"active": True} if active_only else None)
        if cloud_data:
            return cloud_data
        if active_only:
            return [d for d in self.departments if d.get("active", True)]
        return self.departments

    def get_department_by_id(self, dept_id):
        cloud_data = self.execute_supabase_select("departments", {"id": str(dept_id)})
        if cloud_data:
            return cloud_data[0]
        for d in self.departments:
            if d["id"] == str(dept_id):
                return d
        return None

    # =========================================================================
    # 3. DOCTORS
    # =========================================================================
    def get_doctors(self, department_id=None):
        filters = {"department_id": str(department_id)} if department_id else None
        cloud_data = self.execute_supabase_select("doctors", filters)
        if cloud_data:
            return cloud_data
        if department_id:
            return [d for d in self.doctors if d.get("department_id") == str(department_id)]
        return self.doctors

    def get_doctor_by_id(self, doc_id):
        cloud_data = self.execute_supabase_select("doctors", {"id": str(doc_id)})
        if cloud_data:
            return cloud_data[0]
        for d in self.doctors:
            if d["id"] == str(doc_id):
                return d
        return None

    def update_doctor_status(self, doc_id, status):
        with self._lock:
            updates = {"status": status, "updated_at": datetime.datetime.utcnow().isoformat() + "Z"}
            self.execute_supabase_update("doctors", "id", str(doc_id), updates)
            for d in self.doctors:
                if d["id"] == str(doc_id):
                    d["status"] = status
                    self._save_to_disk()
                    return d
            return None

    # =========================================================================
    # 4. QUEUES
    # =========================================================================
    def get_all_queues(self):
        cloud_data = self.execute_supabase_select("queues")
        if cloud_data:
            return cloud_data
        return self.queues

    def get_today_queue(self, department_id, service_type="Consultation"):
        today = datetime.date.today().isoformat()
        cloud_data = self.execute_supabase_select("queues", {
            "department_id": str(department_id),
            "service_type": service_type,
            "queue_date": today
        })
        if cloud_data:
            return cloud_data[0]

        for q in self.queues:
            if q["department_id"] == str(department_id) and q["service_type"].lower() == service_type.lower() and q["queue_date"] == today:
                return q

        # Create new queue
        dept = self.get_department_by_id(department_id)
        new_q = {
            "id": str(uuid.uuid4()),
            "department_id": str(department_id),
            "department_name": dept["name"] if dept else "General",
            "service_type": service_type,
            "queue_date": today,
            "current_token_number": 0,
            "status": "active",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        self.execute_supabase_insert("queues", new_q)
        self.queues.append(new_q)
        self._save_to_disk()
        return new_q

    def update_queue(self, queue_id, updates):
        with self._lock:
            updates["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            self.execute_supabase_update("queues", "id", str(queue_id), updates)
            for q in self.queues:
                if q["id"] == str(queue_id):
                    q.update(updates)
                    self._save_to_disk()
                    return q
            return None

    # =========================================================================
    # 5. QUEUE ENTRIES
    # =========================================================================
    def get_queue_entries(self, queue_id=None, patient_id=None, status=None):
        filters = {}
        if queue_id:
            filters["queue_id"] = str(queue_id)
        if patient_id:
            filters["patient_id"] = str(patient_id)
        if status:
            filters["status"] = status

        cloud_data = self.execute_supabase_select("queue_entries", filters if filters else None, order_col="token_number")
        if cloud_data:
            return cloud_data

        res = self.queue_entries
        if queue_id:
            res = [e for e in res if e["queue_id"] == str(queue_id)]
        if patient_id:
            res = [e for e in res if e["patient_id"] == str(patient_id)]
        if status:
            res = [e for e in res if e["status"] == status]
        return res

    def get_queue_entry_by_id(self, entry_id):
        cloud_data = self.execute_supabase_select("queue_entries", {"id": str(entry_id)})
        if cloud_data:
            return cloud_data[0]
        for e in self.queue_entries:
            if e["id"] == str(entry_id):
                return e
        return None

    def create_queue_entry(self, entry_data):
        with self._lock:
            self.execute_supabase_insert("queue_entries", entry_data)
            self.queue_entries.append(entry_data)
            self._save_to_disk()
            return entry_data

    def update_queue_entry(self, entry_id, updates):
        with self._lock:
            self.execute_supabase_update("queue_entries", "id", str(entry_id), updates)
            for e in self.queue_entries:
                if e["id"] == str(entry_id):
                    e.update(updates)
                    self._save_to_disk()
                    return e
            return None

    # =========================================================================
    # 6. APPOINTMENTS
    # =========================================================================
    def get_appointments(self, patient_id=None, doctor_id=None):
        filters = {}
        if patient_id:
            filters["patient_id"] = str(patient_id)
        if doctor_id:
            filters["doctor_id"] = str(doctor_id)

        cloud_data = self.execute_supabase_select("appointments", filters if filters else None, order_col="appointment_date")
        if cloud_data:
            return cloud_data

        res = self.appointments
        if patient_id:
            res = [a for a in res if a.get("patient_id") == str(patient_id)]
        if doctor_id:
            res = [a for a in res if a.get("doctor_id") == str(doctor_id)]
        return res

    def get_appointment_by_id(self, app_id):
        cloud_data = self.execute_supabase_select("appointments", {"id": str(app_id)})
        if cloud_data:
            return cloud_data[0]
        for a in self.appointments:
            if a["id"] == str(app_id):
                return a
        return None

    def create_appointment(self, app_data):
        with self._lock:
            self.execute_supabase_insert("appointments", app_data)
            self.appointments.append(app_data)
            self._save_to_disk()
            return app_data

    def update_appointment(self, app_id, updates):
        with self._lock:
            updates["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            self.execute_supabase_update("appointments", "id", str(app_id), updates)
            for a in self.appointments:
                if a["id"] == str(app_id):
                    a.update(updates)
                    self._save_to_disk()
                    return a
            return None

    # =========================================================================
    # 7. LAB ORDERS
    # =========================================================================
    def get_lab_orders(self, patient_id=None):
        filters = {"patient_id": str(patient_id)} if patient_id else None
        cloud_data = self.execute_supabase_select("lab_orders", filters, order_col="ordered_at", order_desc=True)
        if cloud_data:
            return cloud_data

        if patient_id:
            return [o for o in self.lab_orders if o.get("patient_id") == str(patient_id)]
        return self.lab_orders

    def get_lab_order_by_id(self, order_id):
        cloud_data = self.execute_supabase_select("lab_orders", {"id": str(order_id)})
        if cloud_data:
            return cloud_data[0]
        for o in self.lab_orders:
            if o["id"] == str(order_id):
                return o
        return None

    def create_lab_order(self, order_data):
        with self._lock:
            self.execute_supabase_insert("lab_orders", order_data)
            self.lab_orders.append(order_data)
            self._save_to_disk()
            return order_data

    def update_lab_order(self, order_id, updates):
        with self._lock:
            self.execute_supabase_update("lab_orders", "id", str(order_id), updates)
            for o in self.lab_orders:
                if o["id"] == str(order_id):
                    o.update(updates)
                    self._save_to_disk()
                    return o
            return None

    # =========================================================================
    # 8. BILLS
    # =========================================================================
    def get_bills(self, patient_id=None):
        filters = {"patient_id": str(patient_id)} if patient_id else None
        cloud_data = self.execute_supabase_select("bills", filters, order_col="created_at", order_desc=True)
        if cloud_data:
            return cloud_data

        if patient_id:
            return [b for b in self.bills if b.get("patient_id") == str(patient_id)]
        return self.bills

    def get_bill_by_id(self, bill_id):
        cloud_data = self.execute_supabase_select("bills", {"id": str(bill_id)})
        if cloud_data:
            return cloud_data[0]
        for b in self.bills:
            if b["id"] == str(bill_id):
                return b
        return None

    def create_bill(self, bill_data):
        with self._lock:
            self.execute_supabase_insert("bills", bill_data)
            self.bills.append(bill_data)
            self._save_to_disk()
            return bill_data

    def update_bill(self, bill_id, updates):
        with self._lock:
            self.execute_supabase_update("bills", "id", str(bill_id), updates)
            for b in self.bills:
                if b["id"] == str(bill_id):
                    b.update(updates)
                    self._save_to_disk()
                    return b
            return None

    # =========================================================================
    # 9. PAYMENTS
    # =========================================================================
    def get_payments(self, patient_id=None, bill_id=None):
        filters = {}
        if patient_id:
            filters["patient_id"] = str(patient_id)
        if bill_id:
            filters["bill_id"] = str(bill_id)

        cloud_data = self.execute_supabase_select("payments", filters if filters else None, order_col="created_at", order_desc=True)
        if cloud_data:
            return cloud_data

        res = self.payments
        if patient_id:
            res = [p for p in res if p.get("patient_id") == str(patient_id)]
        if bill_id:
            res = [p for p in res if p.get("bill_id") == str(bill_id)]
        return res

    def create_payment(self, payment_data):
        with self._lock:
            self.execute_supabase_insert("payments", payment_data)
            self.payments.append(payment_data)
            self._save_to_disk()
            return payment_data

    # =========================================================================
    # 10. NOTIFICATIONS
    # =========================================================================
    def get_notifications(self, user_id=None):
        filters = {"user_id": str(user_id)} if user_id else None
        cloud_data = self.execute_supabase_select("notifications", filters, order_col="created_at", order_desc=True)
        if cloud_data:
            return cloud_data

        if user_id:
            user_notes = [n for n in self.notifications if n.get("user_id") == str(user_id)]
            user_notes.sort(key=lambda x: x["created_at"], reverse=True)
            return user_notes
        return self.notifications

    def create_notification(self, note_data):
        with self._lock:
            self.execute_supabase_insert("notifications", note_data)
            self.notifications.append(note_data)
            self._save_to_disk()
            return note_data

    def mark_notification_read(self, note_id, user_id=None):
        with self._lock:
            updates = {"is_read": True}
            self.execute_supabase_update("notifications", "id", str(note_id), updates)
            for n in self.notifications:
                if n["id"] == str(note_id) and (not user_id or n["user_id"] == str(user_id)):
                    n["is_read"] = True
                    self._save_to_disk()
                    return True
            return False

    def mark_all_notifications_read(self, user_id):
        with self._lock:
            count = 0
            if self.is_configured and self.admin_client:
                try:
                    self.admin_client.table("notifications").update({"is_read": True}).eq("user_id", str(user_id)).execute()
                except Exception:
                    pass
            for n in self.notifications:
                if n["user_id"] == str(user_id) and not n["is_read"]:
                    n["is_read"] = True
                    count += 1
            self._save_to_disk()
            return count

    # =========================================================================
    # 11. FEEDBACK
    # =========================================================================
    def get_feedback(self, patient_id=None):
        filters = {"patient_id": str(patient_id)} if patient_id else None
        cloud_data = self.execute_supabase_select("feedback", filters, order_col="created_at", order_desc=True)
        if cloud_data:
            return cloud_data

        if patient_id:
            return [f for f in self.feedback if f.get("patient_id") == str(patient_id)]
        return self.feedback

    def create_feedback(self, feedback_data):
        with self._lock:
            self.execute_supabase_insert("feedback", feedback_data)
            self.feedback.append(feedback_data)
            self._save_to_disk()
            return feedback_data

    # =========================================================================
    # 12. PRIORITY REQUESTS
    # =========================================================================
    def create_priority_request(self, req_data):
        with self._lock:
            self.execute_supabase_insert("priority_requests", req_data)
            self.priority_requests.append(req_data)
            self._save_to_disk()
            return req_data

    def update_priority_request(self, req_id, updates):
        with self._lock:
            self.execute_supabase_update("priority_requests", "id", str(req_id), updates)
            for r in self.priority_requests:
                if r["id"] == str(req_id):
                    r.update(updates)
                    self._save_to_disk()
                    return r
            return None

    # =========================================================================
    # 13. HOSPITAL LOCATIONS
    # =========================================================================
    def get_hospital_locations(self):
        cloud_data = self.execute_supabase_select("hospital_locations")
        if cloud_data:
            return cloud_data
        return self.hospital_locations

    # =========================================================================
    # SEED DATA INITIALIZATION
    # =========================================================================
    def _init_memory_store(self):
        self.profiles = [
            {
                "id": "a0000000-0000-0000-0000-000000000001",
                "auth_user_id": "00000000-0000-0000-0000-000000000001",
                "full_name": "Hospital Administrator",
                "email": "admin@smartcare.org",
                "phone": "+91 98765 43210",
                "role": "admin",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "s0000000-0000-0000-0000-000000000001",
                "auth_user_id": "00000000-0000-0000-0000-000000000002",
                "full_name": "Staff Nurse Ananya",
                "email": "staff@smartcare.org",
                "phone": "+91 98765 43211",
                "role": "staff",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "b0000000-0000-0000-0000-000000000001",
                "auth_user_id": "00000000-0000-0000-0000-000000000003",
                "full_name": "Dr. Arun Kumar",
                "email": "arun.cardio@smartcare.org",
                "phone": "+91 98765 43212",
                "role": "doctor",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "b0000000-0000-0000-0000-000000000002",
                "auth_user_id": "00000000-0000-0000-0000-000000000004",
                "full_name": "Dr. Priya Devi",
                "email": "priya.genmed@smartcare.org",
                "phone": "+91 98765 43213",
                "role": "doctor",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "b0000000-0000-0000-0000-000000000003",
                "auth_user_id": "00000000-0000-0000-0000-000000000005",
                "full_name": "Dr. Rahul Kumar",
                "email": "rahul.ortho@smartcare.org",
                "phone": "+91 98765 43214",
                "role": "doctor",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "b0000000-0000-0000-0000-000000000004",
                "auth_user_id": "00000000-0000-0000-0000-000000000006",
                "full_name": "Dr. Divya S",
                "email": "divya.pedia@smartcare.org",
                "phone": "+91 98765 43215",
                "role": "doctor",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "c0000000-0000-0000-0000-000000000001",
                "auth_user_id": "00000000-0000-0000-0000-000000000007",
                "full_name": "Priya Sharma",
                "email": "patient@smartcare.org",
                "phone": "+91 98765 43220",
                "role": "patient",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "c0000000-0000-0000-0000-000000000002",
                "auth_user_id": "00000000-0000-0000-0000-000000000008",
                "full_name": "Rahul Raj",
                "email": "rahul.raj@example.com",
                "phone": "+91 98765 43221",
                "role": "patient",
                "created_at": "2026-09-01T08:00:00Z"
            },
            {
                "id": "c0000000-0000-0000-0000-000000000003",
                "auth_user_id": "00000000-0000-0000-0000-000000000009",
                "full_name": "Karthik M",
                "email": "karthik.m@example.com",
                "phone": "+91 98765 43222",
                "role": "patient",
                "created_at": "2026-09-01T08:00:00Z"
            }
        ]

        self.departments = [
            {"id": "d1000000-0000-0000-0000-000000000001", "name": "General Medicine", "description": "Primary outpatient adult care, acute fevers, physical health assessments", "location": "Wing A - Room 101", "floor": "Ground Floor", "code_prefix": "GM", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000002", "name": "Cardiology", "description": "Heart health, ECG, echocardiograms, cardiovascular screenings", "location": "Wing B - Room 204", "floor": "First Floor", "code_prefix": "C", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000003", "name": "Orthopedics", "description": "Bones, joints, spine care, fractures, arthritis clinic", "location": "Wing B - Room 210", "floor": "First Floor", "code_prefix": "ORT", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000004", "name": "Pediatrics", "description": "Comprehensive childcare, vaccinations, developmental assessments", "location": "Wing C - Room 105", "floor": "Ground Floor", "code_prefix": "PED", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000005", "name": "Dermatology", "description": "Skin, hair, nail diagnostics and dermatological therapies", "location": "Wing A - Room 302", "floor": "Second Floor", "code_prefix": "DER", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000006", "name": "Neurology", "description": "Neurological consultations, headache disorders, nerve care", "location": "Wing B - Room 315", "floor": "Second Floor", "code_prefix": "NEU", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000007", "name": "ENT", "description": "Ear, Nose and Throat diagnostics and audiology screenings", "location": "Wing A - Room 205", "floor": "First Floor", "code_prefix": "ENT", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000008", "name": "Laboratory", "description": "Automated hematology, biochemistry, and rapid culture diagnostics", "location": "Central Block - Lab 1", "floor": "Ground Floor", "code_prefix": "LAB", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000009", "name": "Pharmacy", "description": "Outpatient drug dispensing, dosage counseling and generic medicine", "location": "Main Atrium - Counter 4", "floor": "Ground Floor", "code_prefix": "PH", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000010", "name": "Billing", "description": "Cashless insurance claims, computerized billing, receipt counters", "location": "Main Atrium - Counters 1-3", "floor": "Ground Floor", "code_prefix": "BIL", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000011", "name": "Registration", "description": "New patient registrations, digital token kiosks, inquiries", "location": "Main Entrance - Reception", "floor": "Ground Floor", "code_prefix": "REG", "active": True},
            {"id": "d1000000-0000-0000-0000-000000000012", "name": "Emergency", "description": "24/7 Trauma, acute resuscitation and critical medical triage", "location": "Emergency Bay - Gate 2", "floor": "Ground Floor", "code_prefix": "EMG", "active": True}
        ]

        self.doctors = [
            {"id": "doc00000-0000-0000-0000-000000000001", "profile_id": "b0000000-0000-0000-0000-000000000001", "full_name": "Dr. Arun Kumar", "department_id": "d1000000-0000-0000-0000-000000000002", "department_name": "Cardiology", "specialization": "Senior Cardiologist (MD, DM)", "room_number": "Room 204", "average_consultation_minutes": 15, "status": "available"},
            {"id": "doc00000-0000-0000-0000-000000000002", "profile_id": "b0000000-0000-0000-0000-000000000002", "full_name": "Dr. Priya Devi", "department_id": "d1000000-0000-0000-0000-000000000001", "department_name": "General Medicine", "specialization": "Chief Consultant Physician (MD)", "room_number": "Room 101", "average_consultation_minutes": 12, "status": "available"},
            {"id": "doc00000-0000-0000-0000-000000000003", "profile_id": "b0000000-0000-0000-0000-000000000003", "full_name": "Dr. Rahul Kumar", "department_id": "d1000000-0000-0000-0000-000000000003", "department_name": "Orthopedics", "specialization": "Orthopedic Surgeon (MS Ortho)", "room_number": "Room 210", "average_consultation_minutes": 18, "status": "available"},
            {"id": "doc00000-0000-0000-0000-000000000004", "profile_id": "b0000000-0000-0000-0000-000000000004", "full_name": "Dr. Divya S", "department_id": "d1000000-0000-0000-0000-000000000004", "department_name": "Pediatrics", "specialization": "Pediatric Specialist (MD)", "room_number": "Room 105", "average_consultation_minutes": 14, "status": "available"}
        ]

        today_str = datetime.date.today().isoformat()
        self.queues = [
            {"id": "q0000000-0000-0000-0000-000000000001", "department_id": "d1000000-0000-0000-0000-000000000002", "department_name": "Cardiology", "service_type": "Consultation", "queue_date": today_str, "current_token_number": 27, "status": "active"},
            {"id": "q0000000-0000-0000-0000-000000000002", "department_id": "d1000000-0000-0000-0000-000000000001", "department_name": "General Medicine", "service_type": "Consultation", "queue_date": today_str, "current_token_number": 40, "status": "active"},
            {"id": "q0000000-0000-0000-0000-000000000003", "department_id": "d1000000-0000-0000-0000-000000000008", "department_name": "Laboratory", "service_type": "Laboratory", "queue_date": today_str, "current_token_number": 18, "status": "active"},
            {"id": "q0000000-0000-0000-0000-000000000004", "department_id": "d1000000-0000-0000-0000-000000000010", "department_name": "Billing", "service_type": "Billing", "queue_date": today_str, "current_token_number": 32, "status": "active"}
        ]

        self.queue_entries = [
            {
                "id": "e0000000-0000-0000-0000-000000000001",
                "queue_id": "q0000000-0000-0000-0000-000000000001",
                "patient_id": "c0000000-0000-0000-0000-000000000002",
                "patient_name": "Rahul Raj",
                "token_number": 21,
                "token_code": "C-21",
                "status": "serving",
                "estimated_wait_minutes": 0,
                "counter_number": "Room 204",
                "joined_at": "2026-09-04T09:00:00Z",
                "called_at": "2026-09-04T09:30:00Z",
                "serving_at": "2026-09-04T09:32:00Z"
            },
            {
                "id": "e0000000-0000-0000-0000-000000000002",
                "queue_id": "q0000000-0000-0000-0000-000000000001",
                "patient_id": "c0000000-0000-0000-0000-000000000003",
                "patient_name": "Karthik M",
                "token_number": 22,
                "token_code": "C-22",
                "status": "called",
                "estimated_wait_minutes": 5,
                "counter_number": "Room 204",
                "joined_at": "2026-09-04T09:10:00Z",
                "called_at": "2026-09-04T09:40:00Z",
                "serving_at": None
            },
            {
                "id": "e0000000-0000-0000-0000-000000000003",
                "queue_id": "q0000000-0000-0000-0000-000000000001",
                "patient_id": "c0000000-0000-0000-0000-000000000001",
                "patient_name": "Priya Sharma",
                "token_number": 27,
                "token_code": "C-27",
                "status": "waiting",
                "estimated_wait_minutes": 35,
                "counter_number": "Room 204",
                "joined_at": "2026-09-04T09:25:00Z",
                "called_at": None,
                "serving_at": None
            }
        ]

        self.appointments = [
            {
                "id": "app00000-0000-0000-0000-000000000001",
                "patient_id": "c0000000-0000-0000-0000-000000000001",
                "patient_name": "Priya Sharma",
                "doctor_id": "doc00000-0000-0000-0000-000000000001",
                "doctor_name": "Dr. Arun Kumar",
                "department_id": "d1000000-0000-0000-0000-000000000002",
                "department_name": "Cardiology",
                "appointment_date": today_str,
                "appointment_time": "11:30 AM",
                "reason": "Routine hypertension check and ECG evaluation",
                "status": "confirmed",
                "created_at": "2026-09-02T10:00:00Z"
            }
        ]

        self.lab_orders = [
            {
                "id": "lab00000-0000-0000-0000-000000000001",
                "patient_id": "c0000000-0000-0000-0000-000000000001",
                "doctor_id": "doc00000-0000-0000-0000-000000000001",
                "doctor_name": "Dr. Arun Kumar",
                "test_name": "Complete Blood Count (CBC) & Lipid Profile",
                "status": "processing",
                "ordered_at": "2026-09-04T07:30:00Z",
                "sample_collected_at": "2026-09-04T08:00:00Z",
                "processing_at": "2026-09-04T08:30:00Z",
                "report_ready_at": None,
                "report_reference": "LAB-REP-CBC-8812",
                "notes": "Fasting sample collected. Results expected in 2 hours."
            }
        ]

        self.bills = [
            {
                "id": "bil00000-0000-0000-0000-000000000001",
                "patient_id": "c0000000-0000-0000-0000-000000000001",
                "bill_number": "INV-2026-0891",
                "consultation_fee": 500.0,
                "lab_fee": 300.0,
                "pharmacy_fee": 0.0,
                "registration_fee": 100.0,
                "other_charges": 0.0,
                "total_amount": 900.0,
                "payment_status": "unpaid",
                "created_at": "2026-09-04T09:30:00Z"
            }
        ]

        self.payments = []
        self.notifications = []
        self.priority_requests = []

        self.hospital_locations = [
            {"id": "loc00000-0000-0000-0000-000000000001", "name": "Main Entrance", "location_type": "entrance", "floor": "Ground Floor", "description": "Main hospital reception, digital kiosks, information", "x_position": 80, "y_position": 480},
            {"id": "loc00000-0000-0000-0000-000000000002", "name": "Registration Counter", "location_type": "service", "floor": "Ground Floor", "description": "Patient registration, card issue, inquiries", "x_position": 180, "y_position": 420},
            {"id": "loc00000-0000-0000-0000-000000000003", "name": "Central Waiting Lounge", "location_type": "waiting", "floor": "Ground Floor", "description": "Comfortable air-conditioned seating with live token displays", "x_position": 360, "y_position": 360},
            {"id": "loc00000-0000-0000-0000-000000000004", "name": "Billing & Cashless Helpdesk", "location_type": "billing", "floor": "Ground Floor", "description": "OPD billing counters 1 to 3", "x_position": 540, "y_position": 420},
            {"id": "loc00000-0000-0000-0000-000000000005", "name": "Outpatient Pharmacy", "location_type": "pharmacy", "floor": "Ground Floor", "description": "Pharmacy medicine dispensary counter 4", "x_position": 680, "y_position": 420},
            {"id": "loc00000-0000-0000-0000-000000000006", "name": "Central Laboratory & Blood Collection", "location_type": "lab", "floor": "Ground Floor", "description": "Blood draw, sample collection & automated diagnostics", "x_position": 680, "y_position": 220},
            {"id": "loc00000-0000-0000-0000-000000000007", "name": "General Medicine OPD", "location_type": "clinic", "floor": "Ground Floor", "description": "Rooms 101 to 104, Adult health checkups", "x_position": 180, "y_position": 200},
            {"id": "loc00000-0000-0000-0000-000000000008", "name": "Emergency Trauma Bay", "location_type": "emergency", "floor": "Ground Floor", "description": "24x7 Emergency resuscitation and ambulance bay", "x_position": 80, "y_position": 160},
            {"id": "loc00000-0000-0000-0000-000000000009", "name": "Cardiology Center", "location_type": "clinic", "floor": "First Floor", "description": "Cardiology consultation rooms 201-204, ECG, Echo", "x_position": 260, "y_position": 220},
            {"id": "loc00000-0000-0000-0000-000000000010", "name": "Orthopedic Clinic & Cast Room", "location_type": "clinic", "floor": "First Floor", "description": "Rooms 210-214, Joint and spine rehabilitation", "x_position": 500, "y_position": 220},
            {"id": "loc00000-0000-0000-0000-000000000011", "name": "Pediatric Care & Play Area", "location_type": "clinic", "floor": "Ground Floor", "description": "Rooms 105-108, Child friendly clinical rooms", "x_position": 360, "y_position": 160}
        ]

        self.feedback = [
            {
                "id": "fb000000-0000-0000-0000-000000000001",
                "patient_id": "c0000000-0000-0000-0000-000000000001",
                "patient_name": "Priya Sharma",
                "department_id": "d1000000-0000-0000-0000-000000000001",
                "department_name": "General Medicine",
                "queue_entry_id": "e0000000-0000-0000-0000-000000000010",
                "overall_rating": 5,
                "waiting_rating": 4,
                "staff_rating": 5,
                "doctor_rating": 5,
                "facility_rating": 5,
                "comment": "Quick digital token process. Dr. Priya was very attentive and compassionate!",
                "created_at": "2026-08-28T11:00:00Z"
            }
        ]

# Global singleton database service
db = SupabaseService()
