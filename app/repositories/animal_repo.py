"""Animals, shelters and vaccination calendars."""
from app import db
from app.models import Animal, Shelter, VaccinationItem


class AnimalRepository:

    @staticmethod
    def card(animal_id) -> Animal:
        row = db.query_one("SELECT * FROM v_animal_card WHERE animal_id = %s", (animal_id,))
        return Animal.from_row(row) if row else None

    @staticmethod
    def available_in_shelter(shelter_id):
        rows = db.query("""SELECT * FROM v_animal_card WHERE shelter_id = %s AND status = 'IN_SHELTER'
                            ORDER BY species_name, display_name""", (shelter_id,))
        return [Animal.from_row(r) for r in rows]

    @staticmethod
    def search(status=None, text=""):
        sql = "SELECT * FROM v_animal_card WHERE (display_name LIKE %s OR COALESCE(shelter_name,'') LIKE %s)"
        params = [f"%{text}%", f"%{text}%"]
        if status:
            sql += " AND status = %s"
            params.append(status)
        return [Animal.from_row(r) for r in db.query(sql + " ORDER BY animal_id DESC", params)]

    @staticmethod
    def add_to_shelter(data):
        """Admin registers an animal directly into a shelter; the vaccination calendar is created too."""
        with db.transaction() as cur:
            cur.execute("""SELECT COUNT(*) AS n FROM shelter_species WHERE shelter_id = %s AND species_id = %s""",
                        (data["shelter_id"], data["species_id"]))
            if cur.fetchone()["n"] == 0:
                raise db.DbError("This shelter does not accept this species.")
            cur.execute("""INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date,
                                               is_neutered, status, shelter_id, description)
                           VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s, 'IN_SHELTER', %s, %s)""",
                        (data.get("name") or None, data["species_id"], data.get("breed_id"), data["sex"],
                         data.get("color") or None, data["age_weeks"], data.get("is_neutered", False),
                         data["shelter_id"], data.get("description") or None))
            animal_id = cur.lastrowid
            cur.execute("CALL sp_generate_vaccination_schedule(%s)", (animal_id,))
        return animal_id

    @staticmethod
    def update_basic(animal_id, name, color, is_neutered, description):
        db.execute("UPDATE animal SET name = %s, color = %s, is_neutered = %s, description = %s WHERE animal_id = %s",
                   (name or None, color or None, is_neutered, description or None, animal_id))

    # ------------------------------------------------------------ vaccinations
    @staticmethod
    def schedule(animal_id):
        rows = db.query("""SELECT vs.schedule_id, vs.animal_id, v.vaccine_code, v.vaccine_name, vs.dose_label,
                                  vs.planned_date, vs.status, vs.done_date
                             FROM vaccination_schedule vs JOIN vaccine v ON v.vaccine_id = vs.vaccine_id
                            WHERE vs.animal_id = %s AND vs.status <> 'CANCELLED'
                            ORDER BY vs.planned_date, v.vaccine_code""", (animal_id,))
        return [VaccinationItem.from_row(r) for r in rows]

    @staticmethod
    def due_for_vet(vet_id, state=None):
        sql = "SELECT * FROM v_vaccination_due WHERE vet_id = %s"
        params = [vet_id]
        if state == "OVERDUE":
            sql += " AND due_state = 'OVERDUE'"
        elif state == "THIS_WEEK":
            sql += " AND due_state IN ('OVERDUE','THIS_WEEK')"
        return db.query(sql + " ORDER BY planned_date, display_name", params)

    @staticmethod
    def complete_vaccination(schedule_id, vet_user_id):
        db.call("sp_complete_vaccination", (schedule_id, vet_user_id))

    @staticmethod
    def animals_of_vet(vet_id):
        return db.query("""SELECT ac.animal_id, ac.display_name, ac.species_name, ac.breed_name, ac.age_label,
                                  ac.shelter_name, ac.sex,
                                  (SELECT COUNT(*) FROM v_vaccination_due d
                                    WHERE d.animal_id = ac.animal_id AND d.due_state = 'OVERDUE') AS overdue,
                                  (SELECT MIN(planned_date) FROM vaccination_schedule s
                                    WHERE s.animal_id = ac.animal_id AND s.status = 'PLANNED') AS next_date
                             FROM v_animal_card ac
                            WHERE ac.responsible_vet_id = %s AND ac.status = 'IN_SHELTER'
                            ORDER BY overdue DESC, next_date""", (vet_id,))


class ShelterRepository:

    @staticmethod
    def summaries():
        return [Shelter.from_row(r) for r in db.query("SELECT * FROM v_shelter_summary ORDER BY shelter_name")]

    @staticmethod
    def accepting(species_id):
        """Shelters that accept the species and still have room."""
        return db.query("""SELECT s.shelter_id, s.shelter_name, s.district_name, s.capacity, s.animal_count
                             FROM v_shelter_summary s
                             JOIN shelter_species ss ON ss.shelter_id = s.shelter_id AND ss.species_id = %s
                            WHERE s.animal_count < s.capacity ORDER BY s.shelter_name""", (species_id,))

    @staticmethod
    def get(shelter_id):
        row = db.query_one("SELECT * FROM shelter WHERE shelter_id = %s", (shelter_id,))
        if row:
            row["species_ids"] = [r["species_id"] for r in db.query(
                "SELECT species_id FROM shelter_species WHERE shelter_id = %s", (shelter_id,))]
        return row

    @staticmethod
    def save(data, shelter_id=None):
        """Insert or update a shelter together with its accepted species (transaction)."""
        if not data["species_ids"]:
            raise db.DbError("Choose at least one accepted species.")
        with db.transaction() as cur:
            values = (data["shelter_name"], data["district_id"], data["address"], data["phone"], data["capacity"],
                      data["latitude"], data["longitude"], data["partner_clinic_id"])
            if shelter_id is None:
                cur.execute("""INSERT INTO shelter (shelter_name, district_id, address, phone, capacity, latitude,
                                                    longitude, partner_clinic_id)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", values)
                shelter_id = cur.lastrowid
            else:
                cur.execute("""SELECT COUNT(*) AS n FROM animal WHERE shelter_id = %s AND status = 'IN_SHELTER'""",
                            (shelter_id,))
                if cur.fetchone()["n"] > data["capacity"]:
                    raise db.DbError("Capacity cannot be lower than the number of animals in the shelter.")
                cur.execute("""UPDATE shelter SET shelter_name = %s, district_id = %s, address = %s, phone = %s,
                                      capacity = %s, latitude = %s, longitude = %s, partner_clinic_id = %s
                                WHERE shelter_id = %s""", values + (shelter_id,))
                cur.execute("""SELECT DISTINCT species_id FROM animal WHERE shelter_id = %s AND status = 'IN_SHELTER'""",
                            (shelter_id,))
                in_use = {r["species_id"] for r in cur.fetchall()}
                if not in_use.issubset(set(data["species_ids"])):
                    raise db.DbError("A species cannot be removed while such animals live in the shelter.")
                cur.execute("DELETE FROM shelter_species WHERE shelter_id = %s", (shelter_id,))
            for sp in data["species_ids"]:
                cur.execute("INSERT INTO shelter_species (shelter_id, species_id) VALUES (%s, %s)", (shelter_id, sp))
        return shelter_id

    @staticmethod
    def delete(shelter_id):
        if db.scalar("SELECT COUNT(*) FROM animal WHERE shelter_id = %s", (shelter_id,)):
            raise db.DbError("This shelter has animal records, so it cannot be deleted.")
        db.execute("DELETE FROM shelter WHERE shelter_id = %s", (shelter_id,))


class ClinicRepository:

    @staticmethod
    def get(clinic_id):
        return db.query_one("SELECT * FROM clinic WHERE clinic_id = %s", (clinic_id,))

    @staticmethod
    def save(data, clinic_id=None):
        values = (data["clinic_name"], data["district_id"], data["address"], data["phone"], data["latitude"],
                  data["longitude"])
        if clinic_id is None:
            return db.execute("""INSERT INTO clinic (clinic_name, district_id, address, phone, latitude, longitude)
                                 VALUES (%s, %s, %s, %s, %s, %s)""", values)
        db.execute("""UPDATE clinic SET clinic_name = %s, district_id = %s, address = %s, phone = %s, latitude = %s,
                             longitude = %s WHERE clinic_id = %s""", values + (clinic_id,))
        return clinic_id

    @staticmethod
    def delete(clinic_id):
        if db.scalar("SELECT COUNT(*) FROM veterinarian WHERE clinic_id = %s", (clinic_id,)):
            raise db.DbError("This clinic still has veterinarians. Move them to another clinic first.")
        if db.scalar("SELECT COUNT(*) FROM shelter WHERE partner_clinic_id = %s", (clinic_id,)):
            raise db.DbError("This clinic is the partner of a shelter, so it cannot be deleted.")
        db.execute("DELETE FROM clinic WHERE clinic_id = %s", (clinic_id,))
