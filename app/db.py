"""
Database access helpers.

* One shared connection (desktop app, one user at a time) with autocommit on.
* transaction() groups several statements: COMMIT if all succeed, ROLLBACK otherwise.
* Every MySQL error is turned into DbError with a message a user can understand.
"""
from contextlib import contextmanager
from decimal import Decimal

import mysql.connector
from mysql.connector import Error as MySQLError

from app.config import DB_CONFIG


class DbError(Exception):
    """Error with a user friendly message."""


CONSTRAINT_MESSAGES = {
    "uq_user_username": "This username is already taken.",
    "uq_user_email": "This e-mail address is already registered.",
    "chk_user_username": "Username: 3-20 characters, only letters, digits and _.",
    "chk_user_phone": "Phone number must start with 05 and have 11 digits.",
    "chk_user_email": "Please enter a valid e-mail address.",
    "uq_clinic_name": "A clinic with this name already exists.",
    "uq_shelter_name": "A shelter with this name already exists.",
    "uq_vet_license": "This license number is already registered.",
    "chk_vet_license": "License no must look like TVHB-12345 (TVHB- and 5 digits).",
    "chk_shelter_capacity": "Capacity must be between 1 and 2000.",
    "chk_shelter_phone": "Phone number must start with 0 and have 11 digits.",
    "chk_clinic_phone": "Phone number must start with 0 and have 11 digits.",
    "uq_application_user_animal": "You have already applied for this animal.",
    "chk_app_agreements": "All agreements must be accepted.",
    "chk_app_tenant": "Tenants must answer the landlord permission question.",
    "chk_app_household": "Household size must be between 1 and 20.",
    "chk_app_hours": "Hours alone must be between 0 and 24.",
    "chk_prescription_days": "Duration must be between 1 and 90 days.",
    "pk_prescription_item": "This medicine is already in the prescription.",
    "chk_animal_age": "Age is not realistic.",
}


def _friendly(err: MySQLError) -> str:
    msg = getattr(err, "msg", str(err)) or str(err)
    code = getattr(err, "errno", None)
    if code == 1644:
        return msg
    for name, text in CONSTRAINT_MESSAGES.items():
        if name in msg:
            return text
    if code == 1062:
        return "This record already exists."
    if code == 1451:
        return "This record is used by other records, so it cannot be deleted."
    if code == 1452:
        return "A related record was not found."
    if code == 3819:
        return "Some values are not valid: " + msg
    if code in (2003, 2005, 2013, 2055):
        return "Cannot connect to the database. Is MySQL running?"
    if code == 1045:
        return "Database login failed. Check the user and password in the .env file."
    return f"Database error: {msg}"


_conn = None


def get_connection():
    global _conn
    try:
        if _conn is None or not _conn.is_connected():
            _conn = mysql.connector.connect(**DB_CONFIG)
    except MySQLError as e:
        raise DbError(_friendly(e)) from e
    return _conn


def _clean(row):
    if row is None:
        return None
    def conv(v):
        if isinstance(v, Decimal):
            return int(v) if v == v.to_integral_value() else float(v)
        return v
    return {k: conv(v) for k, v in row.items()}


def query(sql, params=()):
    try:
        cur = get_connection().cursor(dictionary=True, buffered=True)
        cur.execute(sql, params)
        rows = [_clean(r) for r in cur.fetchall()]
        cur.close()
        return rows
    except MySQLError as e:
        raise DbError(_friendly(e)) from e


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def scalar(sql, params=()):
    row = query_one(sql, params)
    return None if row is None else next(iter(row.values()))


def execute(sql, params=()):
    """INSERT/UPDATE/DELETE outside a transaction; returns lastrowid or rowcount."""
    try:
        cur = get_connection().cursor()
        cur.execute(sql, params)
        result = cur.lastrowid or cur.rowcount
        cur.close()
        return result
    except MySQLError as e:
        raise DbError(_friendly(e)) from e


def call(proc, args=()):
    """Calls a stored procedure; returns the argument list (OUT values filled)."""
    try:
        cur = get_connection().cursor()
        result = cur.callproc(proc, args)
        for _ in cur.stored_results():
            pass
        cur.close()
        return list(result)
    except MySQLError as e:
        raise DbError(_friendly(e)) from e


@contextmanager
def transaction():
    """with transaction() as cur:  ...  -> COMMIT, or ROLLBACK on any error."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True, buffered=True)
    try:
        conn.start_transaction()
        yield cur
        conn.commit()
    except MySQLError as e:
        conn.rollback()
        raise DbError(_friendly(e)) from e
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
