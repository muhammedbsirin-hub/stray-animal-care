"""Small reference lists used by combo boxes."""
from app import db


class LookupRepository:

    @staticmethod
    def districts():
        return db.query("SELECT district_id, district_name FROM district ORDER BY district_name")

    @staticmethod
    def species():
        return db.query("SELECT species_id, species_name FROM species ORDER BY species_name")

    @staticmethod
    def breeds(species_id):
        return db.query("SELECT breed_id, breed_name FROM breed WHERE species_id = %s ORDER BY breed_name",
                        (species_id,))

    @staticmethod
    def clinics():
        return db.query("""SELECT c.clinic_id, c.clinic_name, d.district_name, c.address, c.phone,
                                  c.latitude, c.longitude,
                                  (SELECT COUNT(*) FROM veterinarian v WHERE v.clinic_id = c.clinic_id) AS vets
                             FROM clinic c JOIN district d ON d.district_id = c.district_id
                            ORDER BY c.clinic_name""")

    @staticmethod
    def medicines():
        return db.query("SELECT medicine_id, medicine_name, form FROM medicine ORDER BY medicine_name")
