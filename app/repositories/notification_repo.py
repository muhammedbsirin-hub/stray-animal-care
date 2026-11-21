"""Personal notifications (every user only sees his/her own)."""
from app import db
from app.models import Notification


class NotificationRepository:

    @staticmethod
    def list(user_id):
        rows = db.query("""SELECT notification_id, notif_type, title, message, is_read, created_at
                             FROM notification WHERE user_id = %s
                            ORDER BY created_at DESC, notification_id DESC""", (user_id,))
        return [Notification.from_row(r) for r in rows]

    @staticmethod
    def unread_count(user_id):
        return db.scalar("SELECT COUNT(*) FROM notification WHERE user_id = %s AND is_read = FALSE", (user_id,))

    @staticmethod
    def mark_read(notification_id, user_id):
        db.execute("UPDATE notification SET is_read = TRUE WHERE notification_id = %s AND user_id = %s",
                   (notification_id, user_id))

    @staticmethod
    def mark_all_read(user_id):
        db.execute("UPDATE notification SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE", (user_id,))

    @staticmethod
    def delete(notification_id, user_id):
        return db.execute("DELETE FROM notification WHERE notification_id = %s AND user_id = %s",
                          (notification_id, user_id))

    @staticmethod
    def delete_read(user_id):
        return db.execute("DELETE FROM notification WHERE user_id = %s AND is_read = TRUE", (user_id,))
