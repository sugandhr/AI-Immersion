import unittest
import uuid
import datetime
from backend.app import create_app
from backend.services.supabase_service import db
from backend.services.queue_service import QueueService

class SupabaseStorageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_profile_storage(self):
        unique_email = f"test_patient_{uuid.uuid4().hex[:6]}@example.com"
        profile = db.create_profile({
            "full_name": "Test Supabase Patient",
            "email": unique_email,
            "role": "patient",
            "phone": "+91 99999 88888"
        })
        self.assertIsNotNone(profile["id"])
        self.assertEqual(profile["email"], unique_email)

        # Verify retrieval
        fetched = db.get_profile_by_email(unique_email)
        self.assertEqual(fetched["id"], profile["id"])

        # Update profile
        updated = db.update_profile(profile["id"], {"phone": "+91 00000 11111"})
        self.assertEqual(updated["phone"], "+91 00000 11111")

    def test_queue_entry_lifecycle_storage(self):
        unique_patient_id = str(uuid.uuid4())
        dept = db.get_departments()[0]

        # Join Queue
        ok, msg, data = QueueService.join_queue(
            patient_id=unique_patient_id,
            department_id=dept["id"],
            service_type="Consultation"
        )
        self.assertTrue(ok)
        entry = data["entry"]
        self.assertIn(dept["code_prefix"], entry["token_code"])
        self.assertEqual(entry["status"], "waiting")

        # Verify entry exists in storage
        stored = db.get_queue_entry_by_id(entry["id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["id"], entry["id"])

        # Call next
        call_ok, call_msg, called_entry = QueueService.call_next(entry["queue_id"], "Room 101")
        self.assertTrue(call_ok)

        # Complete entry
        comp_ok, comp_msg, comp_entry = QueueService.complete_entry(entry["id"])
        self.assertTrue(comp_ok)
        self.assertEqual(comp_entry["status"], "completed")

    def test_billing_and_payment_storage(self):
        patient_id = str(uuid.uuid4())
        new_bill = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "bill_number": f"INV-TEST-{uuid.uuid4().hex[:4]}",
            "consultation_fee": 500.0,
            "lab_fee": 250.0,
            "pharmacy_fee": 0.0,
            "registration_fee": 50.0,
            "other_charges": 0.0,
            "total_amount": 800.0,
            "payment_status": "unpaid",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db.create_bill(new_bill)

        # Retrieve bill
        stored_bill = db.get_bill_by_id(new_bill["id"])
        self.assertEqual(stored_bill["total_amount"], 800.0)

        # Update payment
        db.update_bill(new_bill["id"], {"payment_status": "paid"})
        payment = {
            "id": str(uuid.uuid4()),
            "bill_id": new_bill["id"],
            "patient_id": patient_id,
            "amount": 800.0,
            "payment_method": "UPI",
            "transaction_id": f"TXN_TEST_{uuid.uuid4().hex[:6]}",
            "status": "completed",
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db.create_payment(payment)

        # Verify payments query
        user_payments = db.get_payments(patient_id=patient_id)
        self.assertEqual(len(user_payments), 1)
        self.assertEqual(user_payments[0]["amount"], 800.0)

    def test_lab_order_and_notification_storage(self):
        patient_id = str(uuid.uuid4())
        new_order = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "test_name": "Thyroid Profile (T3, T4, TSH)",
            "status": "ordered",
            "ordered_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db.create_lab_order(new_order)
        orders = db.get_lab_orders(patient_id=patient_id)
        self.assertEqual(len(orders), 1)

        # Create notification
        note = {
            "id": str(uuid.uuid4()),
            "user_id": patient_id,
            "title": "Test Notification",
            "message": "Sample message",
            "type": "system",
            "is_read": False,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db.create_notification(note)
        user_notes = db.get_notifications(user_id=patient_id)
        self.assertEqual(len(user_notes), 1)
        self.assertFalse(user_notes[0]["is_read"])

        # Mark read
        db.mark_notification_read(note["id"], user_id=patient_id)
        updated_notes = db.get_notifications(user_id=patient_id)
        self.assertTrue(updated_notes[0]["is_read"])

if __name__ == "__main__":
    unittest.main()
