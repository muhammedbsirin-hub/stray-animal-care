"""Password check.  Passwords are stored as plain text (decision of the project group)."""


def check_password(password: str, stored_password: str) -> bool:
    return password == stored_password
