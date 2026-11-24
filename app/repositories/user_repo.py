from app import db
from app.models import User, Veterinarian


class UserRepository:

    @staticmethod
    def find_login(username):
        return db.query_one("""SELECT user_id, password, is_active FROM user_account WHERE username = %s
                                ORDER BY is_active DESC, user_id DESC LIMIT 1""", (username,))

    @staticmethod
    def get(user_id) -> User:
        row = db.query_one("SELECT * FROM user_account WHERE user_id = %s", (user_id,))
        if row is None:
            return None
        user = User.from_row(row)
        user.roles = {r["role_name"] for r in db.query(
            "SELECT r.role_name FROM user_role ur JOIN role r ON r.role_id = ur.role_id WHERE ur.user_id = %s",
            (user_id,))}
        return user

    @staticmethod
    def get_password(user_id):
        return db.scalar("SELECT password FROM user_account WHERE user_id = %s", (user_id,))

    @staticmethod
    def get_vet(user_id):
        row = db.query_one("""SELECT v.vet_id, v.user_id, v.clinic_id, c.clinic_name, v.shift, v.license_no
                                FROM veterinarian v JOIN clinic c ON c.clinic_id = v.clinic_id
                               WHERE v.user_id = %s""", (user_id,))
        return Veterinarian.from_row(row) if row else None

    @staticmethod
    def username_taken(username):
        return db.scalar("SELECT COUNT(*) FROM user_account WHERE username = %s AND is_active = TRUE",
                         (username,)) > 0

    @staticmethod
    def email_taken(email, except_user_id=0):
        return db.scalar("SELECT COUNT(*) FROM user_account WHERE email = %s AND user_id <> %s AND is_active = TRUE",
                         (email, except_user_id)) > 0

    @staticmethod
    def register_volunteer(data):
        with db.transaction() as cur:
            cur.execute("""INSERT INTO user_account (username, password, first_name, last_name, email, phone)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (data["username"], data["password"], data["first_name"], data["last_name"],
                         data["email"], data["phone"]))
            user_id = cur.lastrowid
            cur.execute("INSERT INTO user_role (user_id, role_id) SELECT %s, role_id FROM role WHERE role_name = 'VOLUNTEER'",
                        (user_id,))
            cur.execute("CALL sp_notify(%s, 'ACCOUNT', 'Welcome!', %s, 'WELCOME')",
                        (user_id, "Your volunteer account is ready. Share feeding spots, report injured animals "
                                  "and find a friend to adopt."))
        return user_id

    @staticmethod
    def create_vet(data):
        with db.transaction() as cur:
            cur.execute("""INSERT INTO user_account (username, password, first_name, last_name, email, phone)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (data["username"], data["password"], data["first_name"], data["last_name"],
                         data["email"], data["phone"]))
            user_id = cur.lastrowid
            cur.execute("INSERT INTO user_role (user_id, role_id) SELECT %s, role_id FROM role WHERE role_name = 'VET'",
                        (user_id,))
            cur.execute("INSERT INTO veterinarian (user_id, clinic_id, shift, license_no) VALUES (%s, %s, %s, %s)",
                        (user_id, data["clinic_id"], data["shift"], data["license_no"]))
        return user_id

    @staticmethod
    def update_profile(user_id, first_name, last_name, email, phone):
        db.execute("""UPDATE user_account SET first_name = %s, last_name = %s, email = %s, phone = %s
                       WHERE user_id = %s""", (first_name, last_name, email, phone, user_id))
        db.call("sp_notify", (user_id, "ACCOUNT", "Profile updated", "Your profile information was changed.", None))

    @staticmethod
    def change_password(user_id, new_password):
        db.execute("UPDATE user_account SET password = %s WHERE user_id = %s", (new_password, user_id))
        db.call("sp_notify", (user_id, "ACCOUNT", "Password changed", "Your password was changed successfully.", None))

    @staticmethod
    def delete_account(user_id, actor_id):
        db.call("sp_delete_account", (user_id, actor_id))

    @staticmethod
    def list_users(search=""):
        like = f"%{search}%"
        return db.query("""SELECT u.user_id, u.username, CONCAT(u.first_name, ' ', u.last_name) AS full_name,
                                  u.email, u.phone, u.is_active,
                                  GROUP_CONCAT(r.role_name ORDER BY r.role_id SEPARATOR ', ') AS roles
                             FROM user_account u
                             LEFT JOIN user_role ur ON ur.user_id = u.user_id
                             LEFT JOIN role r ON r.role_id = ur.role_id
                            WHERE u.username LIKE %s OR u.first_name LIKE %s OR u.last_name LIKE %s
                            GROUP BY u.user_id ORDER BY u.user_id""", (like, like, like))

    @staticmethod
    def list_vets():
        return db.query("""SELECT v.vet_id, v.user_id, u.username, CONCAT('Dr. ', u.first_name, ' ', u.last_name) AS vet_name,
                                  c.clinic_id, c.clinic_name, v.shift, v.license_no, u.phone, u.is_active,
                                  (SELECT COUNT(*) FROM animal a WHERE a.responsible_vet_id = v.vet_id
                                      AND a.status = 'IN_SHELTER') AS animals
                             FROM veterinarian v JOIN user_account u ON u.user_id = v.user_id
                             JOIN clinic c ON c.clinic_id = v.clinic_id
                            ORDER BY c.clinic_name, v.shift, vet_name""")

    @staticmethod
    def update_vet(vet_id, clinic_id, shift):
        db.execute("UPDATE veterinarian SET clinic_id = %s, shift = %s WHERE vet_id = %s", (clinic_id, shift, vet_id))
