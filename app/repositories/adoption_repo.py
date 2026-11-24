"""Adoption applications, approvals and adoptions."""
from app import db

APPLICATION_COLUMNS = ["full_address", "district_id", "birth_year", "housing_type", "ownership",
                       "landlord_permission", "household_size", "has_children", "has_other_pets", "other_pets_note",
                       "pet_experience", "hours_alone_per_day", "reason", "agrees_home_visit", "agrees_neutering",
                       "agrees_vaccination"]


class AdoptionRepository:

    @staticmethod
    def submit(user_id, animal_id, form):
        """The BEFORE INSERT trigger checks age, availability and the 3-pending limit."""
        cols = ["user_id", "animal_id"] + APPLICATION_COLUMNS
        values = [user_id, animal_id] + [form.get(c) for c in APPLICATION_COLUMNS]
        sql = f"INSERT INTO adoption_application ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})"
        return db.execute(sql, values)

    @staticmethod
    def already_applied(user_id, animal_id):
        return db.scalar("""SELECT COUNT(*) FROM adoption_application
                             WHERE user_id = %s AND animal_id = %s AND status <> 'WITHDRAWN'""",
                         (user_id, animal_id)) > 0

    @staticmethod
    def my_applications(user_id):
        return db.query("""SELECT ap.application_id, ap.applied_at, ap.status, ac.display_name, ac.species_name,
                                  ac.shelter_name, ap.reviewed_at, ap.admin_note
                             FROM adoption_application ap JOIN v_animal_card ac ON ac.animal_id = ap.animal_id
                            WHERE ap.user_id = %s ORDER BY ap.applied_at DESC""", (user_id,))

    @staticmethod
    def withdraw(application_id, user_id):
        n = db.execute("""UPDATE adoption_application SET status = 'WITHDRAWN'
                           WHERE application_id = %s AND user_id = %s AND status = 'PENDING'""",
                       (application_id, user_id))
        if not n:
            raise db.DbError("Only your pending applications can be withdrawn.")

    @staticmethod
    def my_adoptions(user_id):
        return db.query("""SELECT ad.adoption_id, ad.contract_no, ad.adopted_at, ac.animal_id, ac.display_name,
                                  ac.species_name, ac.breed_name, ac.age_label, ac.shelter_name
                             FROM adoption ad
                             JOIN adoption_application ap ON ap.application_id = ad.application_id
                             JOIN v_animal_card ac ON ac.animal_id = ap.animal_id
                            WHERE ap.user_id = %s ORDER BY ad.adopted_at DESC""", (user_id,))

    # ============================================================ admin
    @staticmethod
    def dossiers(status=None):
        if status:
            return db.query("SELECT * FROM v_application_dossier WHERE status = %s ORDER BY applied_at", (status,))
        return db.query("SELECT * FROM v_application_dossier ORDER BY applied_at DESC")

    @staticmethod
    def dossier(application_id):
        return db.query_one("SELECT * FROM v_application_dossier WHERE application_id = %s", (application_id,))

    @staticmethod
    def competing(application_id):
        return db.scalar("""SELECT COUNT(*) FROM adoption_application o JOIN adoption_application a
                                ON a.animal_id = o.animal_id
                             WHERE a.application_id = %s AND o.application_id <> a.application_id
                               AND o.status = 'PENDING'""", (application_id,))

    @staticmethod
    def approve(application_id, admin_id, note):
        db.call("sp_approve_application", (application_id, admin_id, note or None))

    @staticmethod
    def reject(application_id, admin_id, note):
        db.call("sp_reject_application", (application_id, admin_id, note or None))
