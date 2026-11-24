"""Business services that use several repositories."""
from app import validators
from app.db import DbError
from app.models import Session
from app.repositories import UserRepository


class AuthService:

    @staticmethod
    def login(username, password) -> Session:
        username = (username or "").strip()
        if not username or not password:
            raise DbError("Please enter your username and password.")
        row = UserRepository.find_login(username)
        if row is None:
            raise DbError("There is no user with this username.")
        if not row["is_active"]:
            raise DbError("This account has been closed.")
        if password != row["password"]:
            raise DbError("Wrong password.")
        user = UserRepository.get(row["user_id"])
        vet = UserRepository.get_vet(user.user_id) if user.has_role("VET") else None
        return Session(user=user, vet=vet)

    @staticmethod
    def reload(session: Session) -> Session:
        user = UserRepository.get(session.user_id)
        return Session(user=user, vet=UserRepository.get_vet(user.user_id) if user.has_role("VET") else None)

    @staticmethod
    def validate_registration(d):
        """Returns the first problem or None (form level + uniqueness)."""
        err = validators.first_error(
            validators.person_name(d["first_name"], "First name"),
            validators.person_name(d["last_name"], "Last name"),
            validators.username(d["username"]),
            validators.email(d["email"]),
            validators.phone(d["phone"]),
            validators.password(d["password"], d["password2"]),
        )
        if err:
            return err
        if UserRepository.username_taken(d["username"]):
            return "This username is already taken. Please choose another one."
        if UserRepository.email_taken(d["email"]):
            return "This e-mail address is already registered."
        return None

    @staticmethod
    def verify_password(user_id, password):
        stored = UserRepository.get_password(user_id)
        return stored is not None and stored == password
