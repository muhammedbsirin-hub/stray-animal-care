"""
Input validation used by every form.  Each function returns an error
message (str) or None when the value is valid.  The database checks the
most important rules again (UNIQUE, CHECK, triggers).
"""
import re
from datetime import date

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
NAME_RE = re.compile(r"^[A-Za-zÇĞİÖŞÜçğıöşüÂâÎîÛû' -]{2,50}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^05\d{9}$")
LANDLINE_RE = re.compile(r"^0\d{10}$")
SPECIAL_CHARS = "!@#$%^&*()-_=+[]{};:,.?/\\|~<>\"'`"


def required(value, label):
    if value is None or str(value).strip() == "":
        return f"{label} is required."
    return None


def username(value):
    return required(value, "Username") or (
        None if USERNAME_RE.match(value) else "Username: 3-20 characters, only letters, digits and _.")


def person_name(value, label):
    return required(value, label) or (None if NAME_RE.match(value.strip()) else f"{label} may contain only letters.")


def email(value):
    return required(value, "E-mail") or (None if EMAIL_RE.match(value.strip()) else
                                         "E-mail must contain @ and a domain (example: name@mail.com).")


def phone(value):
    return required(value, "Phone") or (None if PHONE_RE.match(value.strip()) else
                                        "Phone must contain only digits, start with 05 and have 11 digits.")


def landline(value):
    return required(value, "Phone") or (None if LANDLINE_RE.match(value.strip()) else
                                        "Phone must contain only digits, start with 0 and have 11 digits.")


def password_problems(pw: str):
    problems = []
    if len(pw) < 8:
        problems.append("at least 8 characters")
    if not re.search(r"[A-Z]", pw):
        problems.append("an upper-case letter")
    if not re.search(r"[a-z]", pw):
        problems.append("a lower-case letter")
    if not re.search(r"\d", pw):
        problems.append("a digit")
    if not any(c in SPECIAL_CHARS for c in pw):
        problems.append("a special character (!@#$...)")
    if " " in pw:
        problems.append("no spaces")
    return problems


def password(pw, repeat=None):
    if not pw:
        return "Password is required."
    problems = password_problems(pw)
    if problems:
        return "Password needs " + ", ".join(problems) + "."
    if repeat is not None and pw != repeat:
        return "Passwords do not match."
    return None


def integer(value, label, low, high, optional=False):
    if value is None or str(value).strip() == "":
        return None if optional else f"{label} is required."
    s = str(value).strip()
    if not s.isdigit():
        return f"{label} must be a whole number."
    if not (low <= int(s) <= high):
        return f"{label} must be between {low} and {high}."
    return None


def birth_year(value):
    this_year = date.today().year
    err = integer(value, "Birth year", 1900, this_year)
    if err:
        return err
    if this_year - int(value) < 18:
        return "You must be at least 18 years old to adopt."
    return None


LICENSE_RE = re.compile(r"^TVHB-\d{5}$")


def license_no(value):
    return required(value, "License no") or (None if LICENSE_RE.match(value.strip()) else
                                             "License no must look like TVHB-12345 (TVHB- and 5 digits).")


def min_length(value, label, n):
    err = required(value, label)
    if err:
        return err
    return None if len(value.strip()) >= n else f"{label} must be at least {n} characters."


def first_error(*errors):
    for e in errors:
        if e:
            return e
    return None
