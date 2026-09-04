import uuid
import datetime
from backend.services.supabase_service import db

class NotificationService:
    @staticmethod
    def get_user_notifications(user_id):
        return db.get_notifications(user_id=user_id)

    @staticmethod
    def send_notification(user_id, title, message, note_type="system"):
        note = {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "title": title,
            "message": message,
            "type": note_type,
            "is_read": False,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        db.create_notification(note)
        return note

    @staticmethod
    def mark_read(notification_id, user_id):
        return db.mark_notification_read(notification_id, user_id)

    @staticmethod
    def mark_all_read(user_id):
        return db.mark_all_notifications_read(user_id)
