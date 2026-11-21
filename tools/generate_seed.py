"""
Generates database/05_seed_data.sql and the sample photos in media/seed/.

Run from the project root:   python tools/generate_seed.py
All demo accounts use the password  Demo1234!
Dates are written relative to NOW()/CURDATE(), so the demo data always
looks fresh on the day the script is executed.
"""
import math
import random
from pathlib import Path

import bcrypt
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_SQL = ROOT / "database" / "05_seed_data.sql"
MEDIA = ROOT / "media" / "seed"
DEMO_PASSWORD = "Demo1234!"

random.seed(2026)


def q(value):
    """SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def raw(expr):
    """Marks an SQL expression that must not be quoted."""
    return _Raw(expr)


class _Raw(str):
    pass


def lit(v):
    return v if isinstance(v, _Raw) else q(v)


def insert(table, cols, rows):
    out = [f"INSERT INTO {table} ({', '.join(cols)}) VALUES"]
    body = [f"  ({', '.join(lit(v) for v in r)})" for r in rows]
    return "\n".join(out) + "\n" + ",\n".join(body) + ";\n"


# ----------------------------------------------------------------------------
# Reference data
# ----------------------------------------------------------------------------
DISTRICTS = [  # name, side, lat, lon
    ("Adalar", "ASIA", 40.8740, 29.0880), ("Ataşehir", "ASIA", 40.9840, 29.1060),
    ("Avcılar", "EUROPE", 40.9790, 28.7210), ("Bağcılar", "EUROPE", 41.0390, 28.8560),
    ("Bahçelievler", "EUROPE", 41.0000, 28.8610), ("Bakırköy", "EUROPE", 40.9800, 28.8730),
    ("Başakşehir", "EUROPE", 41.0930, 28.8020), ("Bayrampaşa", "EUROPE", 41.0460, 28.9030),
    ("Beşiktaş", "EUROPE", 41.0430, 29.0070), ("Beykoz", "ASIA", 41.1340, 29.0930),
    ("Beylikdüzü", "EUROPE", 41.0020, 28.6430), ("Beyoğlu", "EUROPE", 41.0370, 28.9770),
    ("Büyükçekmece", "EUROPE", 41.0200, 28.5850), ("Çekmeköy", "ASIA", 41.0350, 29.1800),
    ("Esenyurt", "EUROPE", 41.0340, 28.6800), ("Eyüpsultan", "EUROPE", 41.0470, 28.9330),
    ("Fatih", "EUROPE", 41.0190, 28.9400), ("Gaziosmanpaşa", "EUROPE", 41.0630, 28.9120),
    ("Kadıköy", "ASIA", 40.9900, 29.0290), ("Kağıthane", "EUROPE", 41.0810, 28.9730),
    ("Kartal", "ASIA", 40.8890, 29.1900), ("Küçükçekmece", "EUROPE", 41.0000, 28.7800),
    ("Maltepe", "ASIA", 40.9350, 29.1300), ("Pendik", "ASIA", 40.8770, 29.2350),
    ("Sancaktepe", "ASIA", 41.0000, 29.2300), ("Sarıyer", "EUROPE", 41.1670, 29.0500),
    ("Şişli", "EUROPE", 41.0600, 28.9870), ("Tuzla", "ASIA", 40.8160, 29.3000),
    ("Ümraniye", "ASIA", 41.0160, 29.1240), ("Üsküdar", "ASIA", 41.0230, 29.0150),
    ("Zeytinburnu", "EUROPE", 40.9940, 28.9040),
]
D_ID = {d[0]: i + 1 for i, d in enumerate(DISTRICTS)}
D_POS = {d[0]: (d[2], d[3]) for d in DISTRICTS}

CLINICS = [  # name, district
    ("Moda Paws Veterinary Clinic", "Kadıköy"),
    ("Bosphorus Animal Hospital", "Beşiktaş"),
    ("Mecidiyeköy Vet Clinic", "Şişli"),
    ("Üsküdar Friends Veterinary Clinic", "Üsküdar"),
    ("Old City Veterinary Center", "Fatih"),
    ("Bakırköy Seaside Animal Clinic", "Bakırköy"),
    ("Ataşehir Care Animal Hospital", "Ataşehir"),
    ("West Istanbul Vet Clinic", "Beylikdüzü"),
    ("Sarıyer Forest Animal Clinic", "Sarıyer"),
    ("Kartal Coast Veterinary Clinic", "Kartal"),
]
VETS_PER_CLINIC = [5, 4, 6, 5, 3, 7, 5, 6, 4, 5]  # min 2, average 5, total 50

SHELTER_DISTRICTS = [
    "Kadıköy", "Üsküdar", "Beşiktaş", "Şişli", "Fatih", "Bakırköy", "Ataşehir", "Maltepe",
    "Kartal", "Pendik", "Tuzla", "Ümraniye", "Beykoz", "Sarıyer", "Eyüpsultan", "Başakşehir",
    "Küçükçekmece", "Beylikdüzü", "Esenyurt", "Zeytinburnu",
]
CAT_ONLY = {"Beyoğlu", "Kadıköy", "Fatih"}
DOG_ONLY = {"Beykoz", "Tuzla"}

FIRST = ["Ayşe", "Mehmet", "Zeynep", "Ahmet", "Elif", "Mustafa", "Fatma", "Emre", "Selin", "Burak",
         "Deniz", "Can", "Merve", "Kerem", "Ece", "Ozan", "Derya", "Hakan", "Gizem", "Murat",
         "Seda", "Onur", "Buse", "Tolga", "İrem", "Serkan", "Pınar", "Barış", "Ceren", "Umut"]
LAST = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Aydın", "Öztürk", "Arslan", "Doğan",
        "Kılıç", "Aslan", "Çetin", "Koç", "Kurt", "Özdemir", "Polat", "Erdem", "Güneş", "Aksoy"]

VOLUNTEERS = [  # username, first, last, district
    ("elif_yildiz", "Elif", "Yıldız", "Kadıköy"), ("mert_kaya", "Mert", "Kaya", "Beşiktaş"),
    ("zeynep_ak", "Zeynep", "Ak", "Üsküdar"), ("can_demir", "Can", "Demir", "Şişli"),
    ("selin_arslan", "Selin", "Arslan", "Fatih"), ("burak_celik", "Burak", "Çelik", "Bakırköy"),
    ("deniz_sahin", "Deniz", "Şahin", "Ataşehir"), ("ece_koc", "Ece", "Koç", "Maltepe"),
    ("ozan_kurt", "Ozan", "Kurt", "Kartal"), ("irem_polat", "İrem", "Polat", "Sarıyer"),
    ("umut_aksoy", "Umut", "Aksoy", "Beylikdüzü"), ("gizem_erdem", "Gizem", "Erdem", "Pendik"),
    ("kerem_gunes", "Kerem", "Güneş", "Ümraniye"), ("seda_dogan", "Seda", "Doğan", "Eyüpsultan"),
]

CAT_NAMES = ["Pamuk", "Boncuk", "Zeytin", "Duman", "Tarçın", "Minnoş", "Şeker", "Sütlaç", "Fıstık",
             "Limon", "Mırmır", "Kahve", "Mocha", "Gece", "Pati", "Lokum", "Biber", "Simit", "Mia", "Leo"]
DOG_NAMES = ["Karabaş", "Paşa", "Kömür", "Bal", "Fındık", "Karamel", "Max", "Rocky", "Zeus", "Luna",
             "Badem", "Odin", "Çakıl", "Toprak", "Marley", "Kuki", "Atlas", "Lucky", "Boby", "Maya"]
COLORS = {"Cat": ["Tabby", "Black", "White", "Ginger", "Calico", "Grey", "Black & white", "Cream"],
          "Dog": ["Brown", "Black", "Cream", "White", "Black & tan", "Grey", "Golden", "Spotted"]}
BREEDS = {"Cat": ["Mixed", "Tabby", "Van Cat", "Turkish Angora", "British Shorthair", "Scottish Fold"],
          "Dog": ["Mixed", "Kangal", "Golden Retriever", "Labrador Retriever", "German Shepherd", "Terrier"]}

MEDICINES = [("Amoxicillin", "TABLET"), ("Amoxicillin-Clavulanate", "TABLET"), ("Meloxicam", "SYRUP"),
             ("Enrofloxacin", "TABLET"), ("Metronidazole", "TABLET"), ("Tramadol", "TABLET"),
             ("Prednisolone", "TABLET"), ("Ivermectin", "INJECTION"), ("Ceftriaxone", "INJECTION"),
             ("Ringer Lactate", "INJECTION"), ("Vitamin B Complex", "INJECTION"), ("Famotidine", "TABLET"),
             ("Silver Sulfadiazine Cream", "OINTMENT"), ("Gentamicin Eye Drops", "DROPS"),
             ("Praziquantel", "TABLET")]


def jitter(pos, amount=0.012):
    return (round(pos[0] + random.uniform(-amount, amount), 6),
            round(pos[1] + random.uniform(-amount, amount), 6))


def phone():
    return "05" + random.choice("3459") + "".join(random.choice("0123456789") for _ in range(8))


# ----------------------------------------------------------------------------
# Sample photos for feeding posts (simple drawn pictures)
# ----------------------------------------------------------------------------
def make_post_image(path, idx, district):
    w, h = 640, 480
    palettes = [((250, 236, 214), (214, 170, 120)), ((222, 236, 222), (120, 170, 130)),
                ((226, 232, 244), (120, 140, 190)), ((246, 226, 226), (190, 120, 120))]
    bg, accent = palettes[idx % len(palettes)]
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    # pavement lines
    for y in range(300, h, 36):
        d.line([(0, y), (w, y + 20)], fill=tuple(max(c - 18, 0) for c in bg), width=3)
    # bowl
    d.ellipse([200, 250, 440, 330], fill=accent)
    d.rectangle([215, 290, 425, 360], fill=accent)
    d.ellipse([215, 335, 425, 385], fill=tuple(max(c - 30, 0) for c in accent))
    d.ellipse([215, 245, 425, 300], fill=(120, 80, 50))
    for _ in range(40):  # kibbles
        x, y = random.randint(230, 410), random.randint(252, 292)
        d.ellipse([x, y, x + 9, y + 7], fill=(160, 110, 60))
    # paw prints
    for (px, py) in [(90, 120), (150, 70), (520, 140), (560, 80)]:
        d.ellipse([px, py, px + 34, py + 30], fill=accent)
        for dx, dy in [(-12, -22), (4, -30), (20, -28), (34, -18)]:
            d.ellipse([px + dx, py + dy, px + dx + 13, py + dy + 13], fill=accent)
    try:
        font = ImageFont.truetype("segoeui.ttf", 30)
        small = ImageFont.truetype("segoeui.ttf", 22)
    except OSError:
        font = small = ImageFont.load_default()
    d.text((24, 400), f"Feeding spot - {district}", fill=(60, 50, 40), font=font)
    d.text((24, 440), f"Sample photo #{idx}", fill=(90, 80, 70), font=small)
    img.save(path, "JPEG", quality=82)


# ----------------------------------------------------------------------------
def main():
    MEDIA.mkdir(parents=True, exist_ok=True)
    pw_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt(rounds=10)).decode()
    sql = ["-- =====================================================================",
           "-- 05_seed_data.sql : sample data (generated by tools/generate_seed.py)",
           "-- All demo accounts: password  Demo1234!",
           "-- =====================================================================",
           "USE stray_db;", "SET NAMES utf8mb4 COLLATE utf8mb4_tr_0900_ai_ci;", ""]

    sql.append(insert("role", ["role_name", "description"], [
        ("ADMIN", "Reviews adoption applications, manages shelters, clinics and users"),
        ("VET", "Veterinarian: treats injured animals and follows vaccinations"),
        ("VOLUNTEER", "Every registered user: feeding posts, injured animal reports, adoption requests"),
        ("ADOPTER", "Volunteer whose adoption application was approved"),
    ]))
    sql.append(insert("district", ["district_name", "side"], [(d[0], d[1]) for d in DISTRICTS]))
    sql.append(insert("species", ["species_name"], [("Cat",), ("Dog",)]))
    breed_rows, breed_ids, bid = [], {"Cat": [], "Dog": []}, 0
    for sp_i, sp in enumerate(["Cat", "Dog"], start=1):
        for b in BREEDS[sp]:
            bid += 1
            breed_rows.append((sp_i, b))
            breed_ids[sp].append(bid)
    sql.append(insert("breed", ["species_id", "breed_name"], breed_rows))

    # clinics
    clinic_rows, clinic_pos = [], []
    for i, (name, dist) in enumerate(CLINICS, start=1):
        lat, lon = jitter(D_POS[dist], 0.006)
        clinic_pos.append((lat, lon))
        area = "0216" if dict((d[0], d[1]) for d in DISTRICTS)[dist] == "ASIA" else "0212"
        clinic_rows.append((name, D_ID[dist], f"Veteriner Sk. No:{random.randint(2, 80)}, {dist} / Istanbul",
                            area + f"{random.randint(1000000, 9999999)}", lat, lon))
    sql.append(insert("clinic", ["clinic_name", "district_id", "address", "phone", "latitude", "longitude"],
                      clinic_rows))

    # users: admins, vets, volunteers
    users, roles = [], []
    users.append(("admin", "System", "Admin", "admin@straycare.org", "05300000001", D_ID["Kadıköy"]))
    users.append(("admin2", "Shelter", "Coordinator", "coordinator@straycare.org", "05300000002", D_ID["Fatih"]))
    roles += [(1, 1), (2, 1)]
    vet_rows, vet_meta, used_names = [], [], set()
    vet_no = 0
    for c_idx, count in enumerate(VETS_PER_CLINIC, start=1):
        for k in range(count):
            vet_no += 1
            while True:
                fn, ln = random.choice(FIRST), random.choice(LAST)
                if (fn, ln) not in used_names:
                    used_names.add((fn, ln))
                    break
            uname = f"vet{vet_no:02d}"
            users.append((uname, fn, ln, f"{uname}@straycare.org", phone(), D_ID[CLINICS[c_idx - 1][1]]))
            user_id = len(users)
            roles.append((user_id, 2))
            shift = "MORNING" if k < math.ceil(count / 2) else "EVENING"
            vet_rows.append((user_id, c_idx, shift, f"TVHB-{30000 + vet_no * 17}"))
            vet_meta.append({"vet_id": vet_no, "user_id": user_id, "clinic": c_idx, "shift": shift,
                             "name": f"Dr. {fn} {ln}"})
    vol_ids = []
    for (uname, fn, ln, dist) in VOLUNTEERS:
        users.append((uname, fn, ln, f"{uname}@example.com", phone(), D_ID[dist]))
        vol_ids.append(len(users))
        roles.append((len(users), 3))
    sql.append(insert("user_account",
                      ["username", "password_hash", "first_name", "last_name", "email", "phone", "district_id",
                       "created_at"],
                      [(u[0], pw_hash, u[1], u[2], u[3], u[4], u[5],
                        raw(f"NOW() - INTERVAL {random.randint(20, 300)} DAY")) for u in users]))
    sql.append(insert("user_role", ["user_id", "role_id"], roles))
    sql.append(insert("veterinarian", ["user_id", "clinic_id", "shift", "license_no"], vet_rows))

    # shelters
    shelter_rows, shelter_species, shelter_meta = [], [], []
    for s_idx, dist in enumerate(SHELTER_DISTRICTS, start=1):
        lat, lon = jitter(D_POS[dist], 0.02)
        nearest = min(range(len(clinic_pos)),
                      key=lambda i: (clinic_pos[i][0] - lat) ** 2 + (clinic_pos[i][1] - lon) ** 2) + 1
        area = "0216" if dict((d[0], d[1]) for d in DISTRICTS)[dist] == "ASIA" else "0212"
        shelter_rows.append((f"{dist} Municipality Animal Shelter", D_ID[dist],
                             f"Hayvan Bakımevi Cd. No:{random.randint(1, 60)}, {dist} / Istanbul",
                             area + f"{random.randint(1000000, 9999999)}", random.choice([60, 80, 100, 120, 150, 200, 250]),
                             lat, lon, nearest))
        accepts = ["Cat"] if dist in CAT_ONLY else ["Dog"] if dist in DOG_ONLY else ["Cat", "Dog"]
        for sp in accepts:
            shelter_species.append((s_idx, 1 if sp == "Cat" else 2))
        shelter_meta.append({"id": s_idx, "district": dist, "accepts": accepts, "clinic": nearest})
    sql.append(insert("shelter", ["shelter_name", "district_id", "address", "phone", "capacity", "latitude",
                                  "longitude", "partner_clinic_id"], shelter_rows))
    sql.append(insert("shelter_species", ["shelter_id", "species_id"], shelter_species))

    sql.append(insert("medicine", ["medicine_name", "form"], MEDICINES))
    sql.append(insert("vaccine", ["vaccine_code", "vaccine_name", "description"], [
        ("DHPP", "Combo vaccine (DHPP / CPV-CDV-CAV-2)", "Dogs: distemper, hepatitis, parvovirus, parainfluenza"),
        ("FVRCP", "Combo vaccine (FVRCP)", "Cats: rhinotracheitis, calicivirus, panleukopenia"),
        ("RABIES", "Rabies vaccine", "Cats and dogs; repeated every year (legal requirement in Turkey)"),
    ]))
    sql.append("-- species 1 = Cat, 2 = Dog ; vaccine 1 = DHPP, 2 = FVRCP, 3 = RABIES\n")
    sql.append(insert("vaccine_rule", ["species_id", "vaccine_id", "first_dose_week", "series_interval_weeks",
                                       "series_last_week", "booster_week", "repeat_interval_weeks"], [
        (2, 1, 8, 3, 14, None, 52),     # dog combo: 8, 11, 14 weeks, then yearly
        (2, 3, 12, None, 12, None, 52),  # dog rabies: 12 weeks, then yearly
        (1, 2, 8, 4, 16, 26, 52),       # cat combo: 8, 12, 16 weeks, booster at 26 weeks, then yearly
        (1, 3, 12, None, 12, None, 52),  # cat rabies: 12 weeks, then yearly
    ]))

    # ---------------------------------------------------------------- animals in shelters
    animal_rows, animal_meta = [], []
    cat_names, dog_names = CAT_NAMES[:], DOG_NAMES[:]
    random.shuffle(cat_names)
    random.shuffle(dog_names)

    def new_name(sp):
        pool = cat_names if sp == "Cat" else dog_names
        if not pool:
            return None
        return pool.pop() if random.random() < 0.85 else None

    def age_weeks():
        r = random.random()
        if r < 0.25:
            return random.randint(4, 11)
        if r < 0.55:
            return random.randint(12, 52)
        return random.randint(53, 520)

    for sh in shelter_meta:
        for _ in range(random.randint(3, 5)):
            sp = random.choice(sh["accepts"])
            sp_id = 1 if sp == "Cat" else 2
            weeks = age_weeks()
            breed = random.choice(breed_ids[sp] + [None])
            sex = random.choice(["MALE", "FEMALE", "FEMALE", "MALE", "UNKNOWN"])
            animal_rows.append((new_name(sp), sp_id, breed, sex, random.choice(COLORS[sp]), weeks,
                                raw(f"CURDATE() - INTERVAL {random.randint(0, 40)} DAY"),
                                weeks > 40 and random.random() < 0.6, "IN_SHELTER", sh["id"],
                                random.choice(["Friendly and calm.", "A bit shy at first, loves treats.",
                                               "Very playful, good with other animals.",
                                               "Found near a park, healthy now.", "Gentle, likes to be held.",
                                               "Energetic, needs a home with space."])))
            animal_meta.append({"id": len(animal_rows), "species": sp, "shelter": sh["id"]})
    sql.append(insert("animal", ["name", "species_id", "breed_id", "sex", "color", "age_weeks_at_intake",
                                 "intake_date", "is_neutered", "status", "shelter_id", "description"],
                      animal_rows))
    sql.append("-- demo: animals of the shelters served by clinic 1 are followed by vet01\n"
               "UPDATE animal SET responsible_vet_id = 1\n"
               " WHERE shelter_id IN (SELECT shelter_id FROM shelter WHERE partner_clinic_id = 1);\n")
    sql.append("-- vaccination calendars are produced by the stored procedure\n")
    for a in animal_meta:
        sql.append(f"CALL sp_generate_vaccination_schedule({a['id']});")
    sql.append("")
    sql.append("-- some calendars: first dose already done, some doses overdue (for the demo)\n"
               "UPDATE vaccination_schedule SET status = 'DONE', done_date = CURDATE() - INTERVAL 2 DAY, done_by = vet_id\n"
               " WHERE dose_label IN ('Catch-up dose','Dose 1') AND planned_date = CURDATE() AND MOD(animal_id, 3) = 1;\n"
               "UPDATE vaccination_schedule SET planned_date = CURDATE() - INTERVAL (2 + MOD(animal_id, 6)) DAY\n"
               " WHERE dose_label IN ('Catch-up dose','Dose 1') AND status = 'PLANNED' AND planned_date = CURDATE()\n"
               "   AND MOD(animal_id, 3) = 0;\n"
               "DELETE FROM notification WHERE notif_type = 'VACCINE_ASSIGNED';\n")

    next_animal = len(animal_rows)

    # ---------------------------------------------------------------- injured animal reports
    sql.append("-- ===================== injured animal reports =====================")

    def vet_of(clinic, shift, n=0):
        vs = [v for v in vet_meta if v["clinic"] == clinic and v["shift"] == shift]
        return vs[n % len(vs)]

    report_no = 0

    def add_report(reporter, sp, clinic, shift, vet, minutes_ago, condition, district, age=None):
        nonlocal report_no
        report_no += 1
        lat, lon = jitter(D_POS[district], 0.01)
        sql.append(insert("injury_report", ["reporter_id", "species_id", "approx_age_weeks", "color",
                                            "condition_desc", "location_note", "district_id", "latitude",
                                            "longitude", "clinic_id", "shift", "assigned_vet_id",
                                            "reported_at"],
                          [(reporter, 1 if sp == "Cat" else 2, age, random.choice(COLORS[sp]), condition,
                            f"Near the main street in {district}", D_ID[district], lat, lon, clinic, shift,
                            vet["vet_id"], raw(f"NOW() - INTERVAL {minutes_ago} MINUTE"))]).rstrip())
        return report_no

    # 1) pending cases today (shown in the vet panel of vet01 and the first evening vet of clinic 1)
    v_m, v_e = vet_of(1, "MORNING"), vet_of(1, "EVENING")
    for (rep, sp, vet, mins, cond, dist) in [
        (vol_ids[0], "Cat", v_m, 35, "Limping on the front left leg, cannot step on it.", "Kadıköy"),
        (vol_ids[2], "Dog", v_m, 80, "Deep cut on the back, bleeding a little.", "Üsküdar"),
        (vol_ids[6], "Cat", v_e, 50, "Eye infection, both eyes closed and wet.", "Kadıköy"),
    ]:
        r = add_report(rep, sp, 1, vet["shift"], vet, mins, cond, dist)
        vet_msg = f"Case #{r}: injured {sp.lower()} - {cond}"
        rep_msg = (f"Case #{r}: please take the animal to {CLINICS[0][0]}. "
                   f"Your vet is {vet['name']} ({vet['shift'].lower()} shift).")
        sql.append(f"CALL sp_notify({vet['user_id']}, 'NEW_CASE', 'New injured animal is on the way', "
                   f"{q(vet_msg)}, 'NEW_CASE:{r}');")
        sql.append(f"CALL sp_notify({rep}, 'REPORT_ASSIGNED', 'Veterinarian assigned', {q(rep_msg)}, "
                   f"'REPORT_ASSIGNED:{r}');")

    # 2) arrived cases -> animal + treatment (+ some discharged today)
    treat_no = 0
    arrived_cases = [
        (vol_ids[1], "Dog", 2, "MORNING", 300, "Hit by a car, back leg injured.", "Beşiktaş", "Fractured femur",
         "SEVERE", [(9, "1 g IV, once a day", 7), (6, "50 mg, twice a day", 5)], None),
        (vol_ids[3], "Cat", 3, "MORNING", 260, "Not eating, very weak.", "Şişli", "Dehydration and gastritis",
         "MODERATE", [(10, "100 ml SC, once a day", 3), (12, "5 mg, once a day", 5)], None),
        (vol_ids[4], "Cat", 5, "MORNING", 400, "Wound on the ear, infected.", "Fatih", "Infected ear wound",
         "MILD", [(2, "50 mg, twice a day", 7), (13, "Apply twice a day", 10)], "DISCHARGED_TO_SHELTER"),
        (vol_ids[5], "Dog", 6, "MORNING", 380, "Skin problem, losing hair.", "Bakırköy", "Mange (sarcoptic)",
         "MODERATE", [(8, "0.2 mg/kg SC, weekly", 21)], "DISCHARGED_TO_SHELTER"),
        (vol_ids[7], "Cat", 7, "MORNING", 330, "Kitten with a runny nose and eyes.", "Ataşehir", "Upper respiratory infection",
         "MILD", [(4, "5 mg/kg, once a day", 7), (14, "1 drop, three times a day", 7)], "RELEASED"),
        (vol_ids[8], "Dog", 10, "MORNING", 200, "Paw cut by glass.", "Kartal", "Paw laceration",
         "MILD", [(1, "250 mg, twice a day", 5)], None),
    ]
    for (rep, sp, clinic, shift, mins, cond, dist, diag, level, presc, finish) in arrived_cases:
        vet = vet_of(clinic, shift, 1)
        r = add_report(rep, sp, clinic, shift, vet, mins, cond, dist)
        next_animal += 1
        weeks = random.choice([10, 20, 40, 80, 150])
        sql.append(insert("animal", ["name", "species_id", "breed_id", "sex", "color", "age_weeks_at_intake",
                                     "intake_date", "status", "description"],
                          [(new_name(sp), 1 if sp == "Cat" else 2, breed_ids[sp][0], random.choice(["MALE", "FEMALE"]),
                            random.choice(COLORS[sp]), weeks, raw("CURDATE()"), "UNDER_TREATMENT",
                            f"Brought by a volunteer from {dist}.")]).rstrip())
        sql.append(f"UPDATE injury_report SET status = 'ARRIVED', resolved_at = NOW() - INTERVAL {mins - 40} MINUTE, "
                   f"resolved_by = {vet['user_id']}, animal_id = {next_animal} WHERE report_id = {r};")
        treat_no += 1
        sql.append(insert("treatment", ["animal_id", "vet_id", "report_id", "started_at", "diagnosis",
                                        "condition_level", "notes"],
                          [(next_animal, vet["vet_id"], r, raw(f"NOW() - INTERVAL {mins - 40} MINUTE"), diag, level,
                            "Examined after arrival.")]).rstrip())
        sql.append(insert("prescription_item", ["treatment_id", "medicine_id", "dosage", "duration_days"],
                          [(treat_no, m, d, days) for (m, d, days) in presc]).rstrip())
        arr_msg = f"Case #{r}: the animal arrived and is being treated by {vet['name']}."
        sql.append(f"CALL sp_notify({rep}, 'REPORT_ARRIVED', 'The animal arrived at the clinic', "
                   f"{q(arr_msg)}, 'REPORT_ARRIVED:{r}');")
        if finish:
            target = next(s for s in shelter_meta if sp in s["accepts"] and s["clinic"] == clinic) \
                if any(sp in s["accepts"] and s["clinic"] == clinic for s in shelter_meta) \
                else next(s for s in shelter_meta if sp in s["accepts"])
            shelter_arg = target["id"] if finish == "DISCHARGED_TO_SHELTER" else "NULL"
            sql.append(f"CALL sp_finish_treatment({treat_no}, {vet['user_id']}, '{finish}', {shelter_arg});")

    # 3) yesterday: animals that never arrived (closed by the end-of-day job)
    for (rep, sp, clinic, dist) in [(vol_ids[9], "Dog", 9, "Sarıyer"), (vol_ids[10], "Cat", 8, "Beylikdüzü")]:
        vet = vet_of(clinic, "EVENING")
        r = add_report(rep, sp, clinic, "EVENING", vet, 60 * 26, "Seen limping, ran away when approached.", dist)
        sql.append(f"UPDATE injury_report SET status = 'NOT_ARRIVED', resolved_at = TIMESTAMP(CURDATE() - INTERVAL 1 DAY, '23:59:00'), "
                   f"resolved_by = NULL WHERE report_id = {r};")
        sql.append(f"CALL sp_notify({rep}, 'REPORT_NOT_ARRIVED', 'Animal did not arrive', "
                   f"'Case #{r} was closed at the end of the day because the animal did not arrive.', 'REPORT_CLOSED:{r}');")

    sql.append("\n-- the log rows were written by the triggers; give them the real event times\n"
               "UPDATE report_status_log l JOIN injury_report r ON r.report_id = l.report_id\n"
               "   SET l.changed_at = IF(l.old_status IS NULL, r.reported_at, r.resolved_at);\n")

    # ---------------------------------------------------------------- feeding posts
    sql.append("-- ===================== feeding posts and emoji reactions =====================")
    post_rows, post_owner = [], []
    for i in range(1, 31):
        owner_idx = random.randrange(len(VOLUNTEERS))
        owner = vol_ids[owner_idx]
        dist = VOLUNTEERS[owner_idx][3] if random.random() < 0.7 else random.choice(SHELTER_DISTRICTS)
        lat, lon = jitter(D_POS[dist], 0.015)
        photo = f"media/seed/post_{i:02d}.jpg"
        make_post_image(ROOT / photo, i, dist)
        when = raw(f"NOW() - INTERVAL {random.randint(10, 1380)} MINUTE") if i <= 18 \
            else raw(f"NOW() - INTERVAL {random.randint(2, 12)} DAY")
        note = random.choice(["Left dry food and fresh water.", "Three cats were waiting here today.",
                              "Refilled the bowl, the area is clean.", "Wet food for the kittens.",
                              "Dogs of the park are fed.", "Water bowl was empty, filled it.", None])
        post_rows.append((owner, lat, lon, photo, note, when))
        post_owner.append(owner)
    sql.append(insert("feeding_post", ["user_id", "latitude", "longitude", "photo_path", "note", "posted_at"],
                      post_rows))
    reactions = []
    for pid, owner in enumerate(post_owner, start=1):
        others = [v for v in vol_ids if v != owner]
        for reactor in random.sample(others, random.randint(0, 5)):
            reactions.append((pid, reactor, random.choice(["HEART", "CLAP", "PAW", "STRONG", "THANKS"])))
    sql.append(insert("post_reaction", ["post_id", "user_id", "emoji"], reactions))

    # ---------------------------------------------------------------- adoption applications
    sql.append("-- ===================== adoption applications =====================")
    shelter_animals = [a for a in animal_meta]
    random.shuffle(shelter_animals)
    picks = shelter_animals[:6]
    app_cols = ["user_id", "animal_id", "applied_at", "full_address", "district_id", "birth_year", "housing_type",
                "ownership", "landlord_permission", "household_size", "has_children", "has_other_pets",
                "other_pets_note", "pet_experience", "hours_alone_per_day", "reason", "agrees_home_visit",
                "agrees_neutering", "agrees_vaccination"]

    def app_row(user_idx, animal, days_ago, ownership="OWNER", housing="APARTMENT", hours=6, exp="SOME"):
        u = VOLUNTEERS[user_idx]
        return (vol_ids[user_idx], animal["id"], raw(f"NOW() - INTERVAL {days_ago} DAY"),
                f"Example Sk. No:{random.randint(1, 90)} D:{random.randint(1, 20)}, {u[3]} / Istanbul", D_ID[u[3]],
                random.randint(1980, 2002), housing, ownership, True if ownership == "TENANT" else None,
                random.randint(1, 5), random.random() < 0.4, random.random() < 0.3, None, exp, hours,
                "I have been volunteering for a long time and I want to give this animal a warm home.",
                True, True, True)

    apps = [
        app_row(0, picks[0], 5, housing="HOUSE_WITH_GARDEN", hours=4, exp="EXPERIENCED"),   # 1 -> approved
        app_row(3, picks[0], 4),                                                          # 2 -> auto rejected
        app_row(1, picks[1], 6, ownership="TENANT"),                                      # 3 -> approved
        app_row(4, picks[2], 3, hours=10, exp="NONE"),                                    # 4 -> rejected
        app_row(2, picks[3], 1, housing="DETACHED_HOUSE", exp="EXPERIENCED"),            # 5 pending
        app_row(6, picks[4], 0, ownership="TENANT", hours=8),                             # 6 pending
        app_row(7, picks[4], 0, exp="SOME", hours=5),                                     # 7 pending (same animal)
        app_row(8, picks[5], 2, housing="HOUSE_WITH_GARDEN", exp="EXPERIENCED", hours=3), # 8 pending
    ]
    sql.append(insert("adoption_application", app_cols, apps))
    sql.append("CALL sp_approve_application(1, 1, 'Great home with a garden. Welcome!');")
    sql.append("CALL sp_approve_application(3, 2, 'Landlord permission checked by phone.');")
    sql.append("CALL sp_reject_application(4, 1, 'The animal would stay alone more than 8 hours a day.');")
    sql.append("UPDATE adoption SET adopted_at = NOW() - INTERVAL 2 DAY;")
    sql.append("UPDATE adoption_application SET reviewed_at = applied_at + INTERVAL 1 DAY WHERE status <> 'PENDING';")
    sql.append("")
    sql.append("-- notifications: make older ones look read\n"
               "UPDATE notification SET is_read = TRUE WHERE notif_type IN ('REACTION') AND MOD(notification_id, 2) = 0;\n")

    OUT_SQL.write_text("\n".join(sql) + "\n", encoding="utf-8")
    print(f"written {OUT_SQL}  ({len(users)} users, {len(animal_rows)} shelter animals, {len(post_rows)} posts)")


if __name__ == "__main__":
    main()
