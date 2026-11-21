# Stray Animal Care

Desktop application (Python + CustomTkinter) with a MySQL 8 database for
SEN22321E Database System Design.

Volunteers share feeding spots on a map, support each other with emojis,
report injured animals (a random vet of the current shift is assigned) and
apply to adopt shelter animals. Veterinarians receive the cases, treat the
animals, discharge them to shelters and follow the vaccination calendar.
The admin reviews adoption applications and watches daily statistics.

## 1. Install (once)

1. MySQL Server 8.0 and MySQL Workbench must be installed.
2. Python 3.11 or newer.
3. In **MySQL Workbench**, connect as `root`, open `database/00_setup_user.sql`
   and execute it. It creates the user `stray_app` (password is in `.env`).
   If you do not have a `.env` file, copy `.env.example` to `.env` and write
   the same password as in `00_setup_user.sql`.
4. Open the project folder in **PyCharm** → *Settings → Python Interpreter →
   Add → Virtualenv* → then in the terminal:

   ```
   pip install -r requirements.txt
   ```

## 2. Create the database

Either run in the PyCharm terminal:

```
python tools/setup_database.py
```

or execute these files in MySQL Workbench in this order:
`01_schema.sql`, `02_functions_views.sql`, `03_procedures_triggers.sql`, `05_seed_data.sql`.

Running it again resets everything to the sample data.
`04_roles_grants.sql` (optional, as root) shows the role privileges inside MySQL.
`06_report_queries.sql` contains example report queries.

## 3. Run

Right click `main.py` → **Run** (or `python main.py`).
The map needs an internet connection (OpenStreetMap tiles).

## Demo accounts (password for all: `Demo1234!`)

| Role | Username | Notes |
|---|---|---|
| Admin | `admin`, `admin2` | applications, map, daily vet report, management |
| Veterinarian | `vet01` | Moda Paws Veterinary Clinic, morning shift, has 2 incoming cases |
| Veterinarian | `vet04` | same clinic, evening shift, has 1 incoming case |
| Veterinarian | `vet02` … `vet50` | 10 clinics, 2–7 vets each, every clinic has morning and evening vets |
| Volunteer | `elif_yildiz` | approved adopter (has "My adoptions") |
| Volunteer | `mert_kaya`, `zeynep_ak`, `can_demir`, `selin_arslan`, `deniz_sahin`, `ece_koc` … | 14 volunteers |

## Project structure

```
database/            SQL files (schema, functions/views, procedures/triggers/event, seed, queries)
app/config.py        settings from .env
app/db.py            connection, transaction(), friendly error messages
app/models.py        entity classes (User, Animal, Shelter, FeedingPost, ...)
app/repositories/    all SQL used by the screens
app/services.py      login / registration rules
app/validators.py    form checks (phone 05XXXXXXXXX, e-mail with @, strong password ...)
app/ui/              windows and pages (volunteer, vet, admin, common)
media/seed/          sample photos;  media/posts, media/reports: uploaded photos
tools/               seed generator and database setup script
```
