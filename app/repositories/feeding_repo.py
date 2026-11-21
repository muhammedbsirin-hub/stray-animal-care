"""Feeding posts on the map and emoji reactions."""
from app import db
from app.models import FeedingPost

EMOJIS = ["HEART", "CLAP", "PAW", "STRONG", "THANKS"]


class FeedingRepository:

    @staticmethod
    def active_posts():
        """Posts of the last 24 hours (view v_active_feeding_posts)."""
        return [FeedingPost.from_row(r) for r in db.query("SELECT * FROM v_active_feeding_posts ORDER BY posted_at")]

    @staticmethod
    def recent_posts(days):
        rows = db.query("""SELECT p.post_id, p.user_id, u.username, CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                                  p.latitude, p.longitude, p.photo_path, p.note, p.posted_at,
                                  (SELECT COUNT(*) FROM post_reaction r WHERE r.post_id = p.post_id) AS reaction_count
                             FROM feeding_post p JOIN user_account u ON u.user_id = p.user_id
                            WHERE p.is_deleted = FALSE AND p.posted_at >= NOW() - INTERVAL %s DAY
                            ORDER BY p.posted_at""", (days,))
        return [FeedingPost.from_row(r) for r in rows]

    @staticmethod
    def get(post_id):
        row = db.query_one("""SELECT p.post_id, p.user_id, u.username, CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                                     p.latitude, p.longitude, p.photo_path, p.note, p.posted_at, p.is_deleted
                                FROM feeding_post p JOIN user_account u ON u.user_id = p.user_id
                               WHERE p.post_id = %s""", (post_id,))
        return row

    @staticmethod
    def reaction_summary(post_id):
        rows = db.query("SELECT emoji, COUNT(*) AS n FROM post_reaction WHERE post_id = %s GROUP BY emoji", (post_id,))
        return {r["emoji"]: r["n"] for r in rows}

    @staticmethod
    def reactions(post_id):
        return db.query("""SELECT r.emoji, r.reacted_at, u.username
                             FROM post_reaction r JOIN user_account u ON u.user_id = r.user_id
                            WHERE r.post_id = %s ORDER BY r.reacted_at DESC""", (post_id,))

    @staticmethod
    def my_reaction(post_id, user_id):
        return db.scalar("SELECT emoji FROM post_reaction WHERE post_id = %s AND user_id = %s", (post_id, user_id))

    @staticmethod
    def create_post(user_id, lat, lon, photo_path, note):
        return db.execute("""INSERT INTO feeding_post (user_id, latitude, longitude, photo_path, note)
                             VALUES (%s, %s, %s, %s, %s)""", (user_id, lat, lon, photo_path, note or None))

    @staticmethod
    def react(post_id, user_id, emoji):
        """One emoji per user per post: a new choice replaces the old one."""
        if emoji not in EMOJIS:
            raise ValueError("Unknown emoji")
        db.execute("""INSERT INTO post_reaction (post_id, user_id, emoji) VALUES (%s, %s, %s)
                      ON DUPLICATE KEY UPDATE emoji = VALUES(emoji), reacted_at = NOW()""", (post_id, user_id, emoji))

    @staticmethod
    def remove_reaction(post_id, user_id):
        return db.execute("DELETE FROM post_reaction WHERE post_id = %s AND user_id = %s", (post_id, user_id))

    @staticmethod
    def my_posts(user_id):
        return db.query("""SELECT p.post_id, p.posted_at, p.note, p.photo_path, p.latitude, p.longitude,
                                  (p.posted_at >= NOW() - INTERVAL 24 HOUR) AS on_map,
                                  (SELECT COUNT(*) FROM post_reaction r WHERE r.post_id = p.post_id) AS reactions
                             FROM feeding_post p
                            WHERE p.user_id = %s AND p.is_deleted = FALSE
                            ORDER BY p.posted_at DESC""", (user_id,))

    @staticmethod
    def my_given_reactions(user_id):
        return db.query("""SELECT r.post_id, r.emoji, r.reacted_at, u.username AS owner, p.posted_at, p.note
                             FROM post_reaction r
                             JOIN feeding_post p ON p.post_id = r.post_id
                             JOIN user_account u ON u.user_id = p.user_id
                            WHERE r.user_id = %s ORDER BY r.reacted_at DESC""", (user_id,))

    @staticmethod
    def delete_post(post_id, user_id):
        """Only the owner can delete; the row is kept (soft delete) for history."""
        return db.execute("UPDATE feeding_post SET is_deleted = TRUE WHERE post_id = %s AND user_id = %s",
                          (post_id, user_id))
