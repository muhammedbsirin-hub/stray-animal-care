"""Injured animal reports (volunteer -> vet) and treatments."""
from app import db
from app.models import InjuryReport

_REPORT_SELECT = """
SELECT r.report_id, r.reported_at, s.species_name, r.species_id, r.condition_desc, r.approx_age_weeks, r.color,
       d.district_name, c.clinic_name, CONCAT('Dr. ', vu.first_name, ' ', vu.last_name) AS vet_name, r.shift,
       r.status, CONCAT(ru.first_name, ' ', ru.last_name) AS reporter_name, ru.phone AS reporter_phone,
       t.outcome AS result
  FROM injury_report r
  JOIN species s        ON s.species_id = r.species_id
  LEFT JOIN district d  ON d.district_id = r.district_id
  JOIN clinic c         ON c.clinic_id = r.clinic_id
  JOIN veterinarian v   ON v.vet_id = r.assigned_vet_id
  JOIN user_account vu  ON vu.user_id = v.user_id
  JOIN user_account ru  ON ru.user_id = r.reporter_id
  LEFT JOIN treatment t ON t.report_id = r.report_id
"""


class CaseRepository:

    # ============================================================ volunteer side
    @staticmethod
    def create_report(reporter_id, species_id, age_weeks, color, condition, district_id,
                      lat, lon, clinic_id):
        """Calls sp_create_injury_report -> (report_id, vet_name, shift)."""
        args = db.call("sp_create_injury_report",
                       (reporter_id, species_id, age_weeks, color or None, condition,
                        district_id, lat, lon, clinic_id, 0, "", ""))
        return args[9], args[10], args[11]

    @staticmethod
    def my_reports(user_id):
        rows = db.query(_REPORT_SELECT + " WHERE r.reporter_id = %s ORDER BY r.reported_at DESC", (user_id,))
        return [InjuryReport.from_row(r) for r in rows]

    # ============================================================ vet side
    @staticmethod
    def close_old_cases():
        """Cases of previous days that are still pending become NOT_ARRIVED."""
        db.call("sp_close_day", (False,))

    @staticmethod
    def pending_for_vet(vet_id):
        rows = db.query(_REPORT_SELECT + " WHERE r.assigned_vet_id = %s AND r.status = 'PENDING' ORDER BY r.reported_at",
                        (vet_id,))
        return [InjuryReport.from_row(r) for r in rows]

    @staticmethod
    def closed_today_for_vet(vet_id):
        rows = db.query(_REPORT_SELECT + """ WHERE r.assigned_vet_id = %s AND r.status <> 'PENDING'
                                              AND DATE(r.resolved_at) = CURDATE() ORDER BY r.resolved_at DESC""",
                        (vet_id,))
        return [InjuryReport.from_row(r) for r in rows]

    @staticmethod
    def mark_not_arrived(report_id, vet_user_id):
        db.call("sp_report_not_arrived", (report_id, vet_user_id))

    @staticmethod
    def mark_arrived(report_id, vet, animal, treatment, prescriptions):
        """
        One transaction: check the case, create the animal, the treatment and the
        prescription, close the case as ARRIVED and notify the volunteer.
        """
        with db.transaction() as cur:
            cur.execute("""SELECT status, reporter_id, assigned_vet_id, species_id FROM injury_report
                            WHERE report_id = %s""", (report_id,))
            case = cur.fetchone()
            if case is None:
                raise db.DbError("Case not found.")
            if case["assigned_vet_id"] != vet.vet_id:
                raise db.DbError("This case is assigned to another veterinarian.")
            if case["status"] != "PENDING":
                raise db.DbError("This case is already closed.")

            cur.execute("""INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date,
                                               is_neutered, status, description)
                           VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 'UNDER_TREATMENT', %s)""",
                        (animal.get("name") or None, case["species_id"], animal.get("breed_id"), animal["sex"],
                         animal.get("color") or None, animal["age_weeks"], animal.get("is_neutered", False),
                         animal.get("description") or None))
            animal_id = cur.lastrowid
            cur.execute("""INSERT INTO treatment (animal_id, vet_id, report_id, diagnosis, condition_level, notes)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (animal_id, vet.vet_id, report_id, treatment["diagnosis"], treatment["condition_level"],
                         treatment.get("notes") or None))
            treatment_id = cur.lastrowid
            for p in prescriptions:
                cur.execute("""INSERT INTO prescription_item (treatment_id, medicine_id, dosage, duration_days)
                               VALUES (%s, %s, %s, %s)""",
                            (treatment_id, p["medicine_id"], p["dosage"], p["duration_days"]))
            cur.execute("""UPDATE injury_report SET status = 'ARRIVED', resolved_at = NOW(), resolved_by = %s,
                                                    animal_id = %s
                            WHERE report_id = %s""", (vet.user_id, animal_id, report_id))
            cur.execute("UPDATE notification SET is_read = TRUE WHERE user_id = %s AND event_key = %s",
                        (vet.user_id, f"NEW_CASE:{report_id}"))
            cur.execute("CALL sp_notify(%s, 'REPORT_ARRIVED', 'The animal arrived at the clinic', %s, %s)",
                        (case["reporter_id"],
                         "The injured animal you reported arrived at the clinic and is being treated. "
                         "Thank you for your help!",
                         f"REPORT_ARRIVED:{report_id}"))
        return animal_id, treatment_id

    # ============================================================ treatments
    @staticmethod
    def active_treatments(vet_id):
        return db.query("""SELECT t.treatment_id, t.animal_id, ac.display_name, ac.species_id, ac.species_name,
                                  ac.age_label, t.diagnosis, t.condition_level, t.notes, t.started_at, t.report_id
                             FROM treatment t JOIN v_animal_card ac ON ac.animal_id = t.animal_id
                            WHERE t.vet_id = %s AND t.outcome = 'UNDER_TREATMENT'
                            ORDER BY t.started_at""", (vet_id,))

    @staticmethod
    def prescriptions(treatment_id):
        return db.query("""SELECT m.medicine_name, m.form, p.dosage, p.duration_days
                             FROM prescription_item p JOIN medicine m ON m.medicine_id = p.medicine_id
                            WHERE p.treatment_id = %s ORDER BY m.medicine_name""", (treatment_id,))

    @staticmethod
    def finish_treatment(treatment_id, vet_user_id, outcome, shelter_id):
        db.call("sp_finish_treatment", (treatment_id, vet_user_id, outcome, shelter_id))

    @staticmethod
    def treatments_of_animal(animal_id):
        return db.query("""SELECT t.started_at, t.ended_at, t.diagnosis, t.condition_level, t.outcome,
                                  CONCAT('Dr. ', u.first_name, ' ', u.last_name) AS vet_name, c.clinic_name
                             FROM treatment t JOIN veterinarian v ON v.vet_id = t.vet_id
                             JOIN user_account u ON u.user_id = v.user_id JOIN clinic c ON c.clinic_id = v.clinic_id
                            WHERE t.animal_id = %s ORDER BY t.started_at DESC""", (animal_id,))
