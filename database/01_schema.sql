-- =====================================================================
-- Stray Animal Care System  --  SEN22321E Database System Design
-- 01_schema.sql : database, 24 tables, PK / UNIQUE / CHECK constraints,
--                 then all FOREIGN KEYs at the end (ALTER TABLE).
-- Run order: 01 -> 02 -> 03 -> 05 (04 is optional, run as root)
-- =====================================================================

DROP DATABASE IF EXISTS stray_db;
CREATE DATABASE stray_db CHARACTER SET utf8mb4 COLLATE utf8mb4_tr_0900_ai_ci;
USE stray_db;
SET NAMES utf8mb4 COLLATE utf8mb4_tr_0900_ai_ci;

-- =====================================================================
-- 1) TABLES
-- =====================================================================

-- ---------- Users and roles ------------------------------------------

CREATE TABLE role (
    role_id      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    role_name    VARCHAR(20)  NOT NULL,          -- ADMIN, VET, VOLUNTEER, ADOPTER
    description  VARCHAR(150) NULL,
    CONSTRAINT pk_role PRIMARY KEY (role_id),
    CONSTRAINT uq_role_name UNIQUE (role_name)
);

CREATE TABLE district (
    district_id    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    district_name  VARCHAR(50) NOT NULL,
    side           ENUM('EUROPE','ASIA') NOT NULL,   -- side of the Bosphorus
    CONSTRAINT pk_district PRIMARY KEY (district_id),
    CONSTRAINT uq_district_name UNIQUE (district_name)
);

CREATE TABLE user_account (
    user_id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username        VARCHAR(20)  NOT NULL,
    password        VARCHAR(64)  NOT NULL,           -- stored as plain text (group decision)
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    email           VARCHAR(100) NOT NULL,
    phone           CHAR(11)     NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,  -- FALSE = account closed (soft delete)
    CONSTRAINT pk_user_account PRIMARY KEY (user_id),
    CONSTRAINT uq_user_username UNIQUE (username),
    CONSTRAINT uq_user_email UNIQUE (email),
    CONSTRAINT chk_user_username CHECK (REGEXP_LIKE(username, '^[A-Za-z0-9_]{3,20}$', 'c')),
    CONSTRAINT chk_user_phone    CHECK (REGEXP_LIKE(phone, '^05[0-9]{9}$')),
    CONSTRAINT chk_user_email    CHECK (REGEXP_LIKE(email, '^[^@ ]+@[^@ ]+[.][^@ ]+$'))
);

CREATE TABLE user_role (                         -- M:N  user_account <-> role
    user_id     INT UNSIGNED     NOT NULL,
    role_id     TINYINT UNSIGNED NOT NULL,
    granted_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_user_role PRIMARY KEY (user_id, role_id)
);

-- ---------- Animals: species and breeds --------------------------------

CREATE TABLE species (
    species_id    TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    species_name  VARCHAR(30) NOT NULL,          -- Cat, Dog
    CONSTRAINT pk_species PRIMARY KEY (species_id),
    CONSTRAINT uq_species_name UNIQUE (species_name)
);

CREATE TABLE breed (
    breed_id    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    species_id  TINYINT UNSIGNED  NOT NULL,
    breed_name  VARCHAR(50) NOT NULL,
    CONSTRAINT pk_breed PRIMARY KEY (breed_id),
    CONSTRAINT uq_breed_name UNIQUE (species_id, breed_name),
    CONSTRAINT uq_breed_species UNIQUE (breed_id, species_id)   -- target of composite FK from animal
);

-- ---------- Clinics, veterinarians, shelters ---------------------------

CREATE TABLE clinic (
    clinic_id    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    clinic_name  VARCHAR(100) NOT NULL,
    district_id  SMALLINT UNSIGNED NOT NULL,
    address      VARCHAR(200) NOT NULL,
    phone        CHAR(11) NOT NULL,
    latitude     DECIMAL(9,6) NOT NULL,
    longitude    DECIMAL(9,6) NOT NULL,
    CONSTRAINT pk_clinic PRIMARY KEY (clinic_id),
    CONSTRAINT uq_clinic_name UNIQUE (clinic_name),
    CONSTRAINT chk_clinic_phone CHECK (REGEXP_LIKE(phone, '^0[0-9]{10}$'))
);

CREATE TABLE veterinarian (                      -- specialisation of user_account (1:1)
    vet_id      SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED      NOT NULL,
    clinic_id   SMALLINT UNSIGNED NOT NULL,
    shift       ENUM('MORNING','EVENING') NOT NULL,  -- MORNING 07:00-16:59, EVENING 17:00-06:59
    license_no  VARCHAR(20) NOT NULL,
    CONSTRAINT pk_veterinarian PRIMARY KEY (vet_id),
    CONSTRAINT uq_vet_user UNIQUE (user_id),
    CONSTRAINT uq_vet_license UNIQUE (license_no),
    CONSTRAINT chk_vet_license CHECK (REGEXP_LIKE(license_no, '^TVHB-[0-9]{5}$', 'c'))
);

CREATE TABLE shelter (
    shelter_id         SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    shelter_name       VARCHAR(100) NOT NULL,
    district_id        SMALLINT UNSIGNED NOT NULL,
    address            VARCHAR(200) NOT NULL,
    phone              CHAR(11) NOT NULL,
    capacity           SMALLINT UNSIGNED NOT NULL,
    latitude           DECIMAL(9,6) NOT NULL,
    longitude          DECIMAL(9,6) NOT NULL,
    partner_clinic_id  SMALLINT UNSIGNED NOT NULL,   -- clinic whose vets follow the vaccinations
    CONSTRAINT pk_shelter PRIMARY KEY (shelter_id),
    CONSTRAINT uq_shelter_name UNIQUE (shelter_name),
    CONSTRAINT chk_shelter_capacity CHECK (capacity BETWEEN 1 AND 2000),
    CONSTRAINT chk_shelter_phone CHECK (REGEXP_LIKE(phone, '^0[0-9]{10}$'))
);

CREATE TABLE shelter_species (                   -- M:N  which species a shelter accepts
    shelter_id  SMALLINT UNSIGNED NOT NULL,
    species_id  TINYINT UNSIGNED  NOT NULL,
    CONSTRAINT pk_shelter_species PRIMARY KEY (shelter_id, species_id)
);

-- ---------- Animals -----------------------------------------------------

CREATE TABLE animal (
    animal_id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name                 VARCHAR(40)  NULL,          -- strays often have no name
    species_id           TINYINT UNSIGNED  NOT NULL,
    breed_id             SMALLINT UNSIGNED NULL,     -- NULL = unknown
    sex                  ENUM('MALE','FEMALE','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',
    color                VARCHAR(40)  NULL,
    age_weeks_at_intake  SMALLINT UNSIGNED NOT NULL, -- age is stored in WEEKS
    intake_date          DATE NOT NULL,              -- current age = derived from these two
    is_neutered          BOOLEAN NOT NULL DEFAULT FALSE,
    status               ENUM('UNDER_TREATMENT','IN_SHELTER','ADOPTED','RELEASED','DECEASED') NOT NULL,
    shelter_id           SMALLINT UNSIGNED NULL,
    responsible_vet_id   SMALLINT UNSIGNED NULL,     -- vet that follows the vaccination calendar
    description          VARCHAR(255) NULL,
    photo_path           VARCHAR(255) NULL,
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_animal PRIMARY KEY (animal_id),
    CONSTRAINT chk_animal_age CHECK (age_weeks_at_intake <= 1500),
    CONSTRAINT chk_animal_shelter CHECK (status <> 'IN_SHELTER' OR shelter_id IS NOT NULL)
);

-- ---------- Injured animal reports and treatment -------------------------

CREATE TABLE injury_report (
    report_id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    reporter_id       INT UNSIGNED NOT NULL,          -- volunteer
    species_id        TINYINT UNSIGNED NOT NULL,
    approx_age_weeks  SMALLINT UNSIGNED NULL,
    color             VARCHAR(40)  NULL,
    condition_desc    VARCHAR(500) NOT NULL,
    district_id       SMALLINT UNSIGNED NULL,
    latitude          DECIMAL(9,6) NULL,
    longitude         DECIMAL(9,6) NULL,
    photo_path        VARCHAR(255) NULL,
    clinic_id         SMALLINT UNSIGNED NOT NULL,
    shift             ENUM('MORNING','EVENING') NOT NULL,  -- decided from the report time
    assigned_vet_id   SMALLINT UNSIGNED NOT NULL,          -- random vet of that clinic + shift
    status            ENUM('PENDING','ARRIVED','NOT_ARRIVED') NOT NULL DEFAULT 'PENDING',
    reported_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at       DATETIME NULL,
    resolved_by       INT UNSIGNED NULL,               -- NULL = closed by the system (end of day)
    animal_id         INT UNSIGNED NULL,               -- filled when the animal arrives
    CONSTRAINT pk_injury_report PRIMARY KEY (report_id),
    CONSTRAINT uq_report_animal UNIQUE (animal_id),
    CONSTRAINT chk_report_resolved CHECK (status = 'PENDING' OR resolved_at IS NOT NULL)
);

CREATE TABLE report_status_log (                  -- transaction log: ARRIVED / NOT_ARRIVED history
    log_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    report_id   INT UNSIGNED NOT NULL,
    old_status  ENUM('PENDING','ARRIVED','NOT_ARRIVED') NULL,
    new_status  ENUM('PENDING','ARRIVED','NOT_ARRIVED') NOT NULL,
    changed_by  INT UNSIGNED NULL,                 -- NULL = system
    changed_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_report_status_log PRIMARY KEY (log_id)
);

CREATE TABLE treatment (
    treatment_id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    animal_id             INT UNSIGNED NOT NULL,
    vet_id                SMALLINT UNSIGNED NOT NULL,
    report_id             INT UNSIGNED NULL,
    started_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    diagnosis             VARCHAR(255) NOT NULL,
    condition_level       ENUM('MILD','MODERATE','SEVERE','CRITICAL') NOT NULL,
    notes                 VARCHAR(500) NULL,
    outcome               ENUM('UNDER_TREATMENT','DISCHARGED_TO_SHELTER','RELEASED','DECEASED')
                          NOT NULL DEFAULT 'UNDER_TREATMENT',
    ended_at              DATETIME NULL,
    discharge_shelter_id  SMALLINT UNSIGNED NULL,
    CONSTRAINT pk_treatment PRIMARY KEY (treatment_id),
    CONSTRAINT uq_treatment_report UNIQUE (report_id),
    CONSTRAINT chk_treatment_discharge CHECK (outcome <> 'DISCHARGED_TO_SHELTER' OR discharge_shelter_id IS NOT NULL),
    CONSTRAINT chk_treatment_ended CHECK (outcome = 'UNDER_TREATMENT' OR ended_at IS NOT NULL)
);

CREATE TABLE medicine (
    medicine_id    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    medicine_name  VARCHAR(80) NOT NULL,
    form           ENUM('TABLET','SYRUP','INJECTION','OINTMENT','DROPS') NOT NULL,
    CONSTRAINT pk_medicine PRIMARY KEY (medicine_id),
    CONSTRAINT uq_medicine_name UNIQUE (medicine_name)
);

CREATE TABLE prescription_item (                  -- M:N  treatment <-> medicine
    treatment_id   INT UNSIGNED      NOT NULL,
    medicine_id    SMALLINT UNSIGNED NOT NULL,
    dosage         VARCHAR(60) NOT NULL,
    duration_days  TINYINT UNSIGNED NOT NULL,
    CONSTRAINT pk_prescription_item PRIMARY KEY (treatment_id, medicine_id),
    CONSTRAINT chk_prescription_days CHECK (duration_days BETWEEN 1 AND 90)
);

-- ---------- Vaccination -------------------------------------------------

CREATE TABLE vaccine (
    vaccine_id    TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
    vaccine_code  VARCHAR(10)  NOT NULL,              -- DHPP, FVRCP, RABIES
    vaccine_name  VARCHAR(80)  NOT NULL,
    description   VARCHAR(255) NULL,
    CONSTRAINT pk_vaccine PRIMARY KEY (vaccine_id),
    CONSTRAINT uq_vaccine_code UNIQUE (vaccine_code)
);

CREATE TABLE vaccine_rule (                         -- protocol used to build the calendar
    rule_id                SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    species_id             TINYINT UNSIGNED NOT NULL,
    vaccine_id             TINYINT UNSIGNED NOT NULL,
    first_dose_week        TINYINT UNSIGNED NOT NULL,   -- age (weeks) of the first dose
    series_interval_weeks  TINYINT UNSIGNED NULL,       -- NULL = single dose
    series_last_week       TINYINT UNSIGNED NOT NULL,   -- series continues until this age
    booster_week           TINYINT UNSIGNED NULL,       -- extra booster (cats: 26 weeks)
    repeat_interval_weeks  TINYINT UNSIGNED NOT NULL,   -- adult repeat (52 = yearly)
    CONSTRAINT pk_vaccine_rule PRIMARY KEY (rule_id),
    CONSTRAINT uq_vaccine_rule UNIQUE (species_id, vaccine_id),
    CONSTRAINT chk_rule_weeks CHECK (first_dose_week <= series_last_week),
    CONSTRAINT chk_rule_interval CHECK (series_interval_weeks IS NULL OR series_interval_weeks > 0),
    CONSTRAINT chk_rule_repeat CHECK (repeat_interval_weeks > 0)
);

CREATE TABLE vaccination_schedule (
    schedule_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    animal_id     INT UNSIGNED NOT NULL,
    vaccine_id    TINYINT UNSIGNED NOT NULL,
    dose_label    VARCHAR(30) NOT NULL,               -- 'Dose 1', 'Booster', 'Annual'...
    planned_date  DATE NOT NULL,
    vet_id        SMALLINT UNSIGNED NOT NULL,         -- assigned vet
    status        ENUM('PLANNED','DONE','CANCELLED') NOT NULL DEFAULT 'PLANNED',
    done_date     DATE NULL,
    done_by       SMALLINT UNSIGNED NULL,
    generated_from INT UNSIGNED NULL,                 -- dose planned automatically when this one was done
    notes         VARCHAR(255) NULL,
    CONSTRAINT pk_vaccination_schedule PRIMARY KEY (schedule_id),
    CONSTRAINT chk_schedule_done CHECK (status <> 'DONE' OR done_date IS NOT NULL)
);

-- ---------- Volunteers: feeding posts and emoji reactions ---------------

CREATE TABLE feeding_post (
    post_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED NOT NULL,
    latitude    DECIMAL(9,6) NOT NULL,
    longitude   DECIMAL(9,6) NOT NULL,
    photo_path  VARCHAR(255) NOT NULL,
    note        VARCHAR(255) NULL,
    posted_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_feeding_post PRIMARY KEY (post_id),
    CONSTRAINT chk_post_lat CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_post_lon CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE post_reaction (                       -- one emoji per user per post
    post_id     INT UNSIGNED NOT NULL,
    user_id     INT UNSIGNED NOT NULL,
    emoji       ENUM('HEART','CLAP','PAW','STRONG','THANKS') NOT NULL,
    reacted_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_post_reaction PRIMARY KEY (post_id, user_id)
);

-- ---------- Adoption ----------------------------------------------------

CREATE TABLE adoption_application (
    application_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id              INT UNSIGNED NOT NULL,
    animal_id            INT UNSIGNED NOT NULL,
    applied_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status               ENUM('PENDING','APPROVED','REJECTED','WITHDRAWN') NOT NULL DEFAULT 'PENDING',
    full_address         VARCHAR(255) NOT NULL,
    district_id          SMALLINT UNSIGNED NOT NULL,
    birth_year           SMALLINT UNSIGNED NOT NULL,
    housing_type         ENUM('APARTMENT','HOUSE_WITH_GARDEN','DETACHED_HOUSE') NOT NULL,
    ownership            ENUM('OWNER','TENANT') NOT NULL,
    landlord_permission  BOOLEAN NULL,
    household_size       TINYINT UNSIGNED NOT NULL,
    has_children         BOOLEAN NOT NULL,
    has_other_pets       BOOLEAN NOT NULL,
    other_pets_note      VARCHAR(150) NULL,
    pet_experience       ENUM('NONE','SOME','EXPERIENCED') NOT NULL,
    hours_alone_per_day  TINYINT UNSIGNED NOT NULL,
    reason               VARCHAR(500) NOT NULL,
    agrees_home_visit    BOOLEAN NOT NULL,
    agrees_neutering     BOOLEAN NOT NULL,
    agrees_vaccination   BOOLEAN NOT NULL,
    reviewed_by          INT UNSIGNED NULL,
    reviewed_at          DATETIME NULL,
    admin_note           VARCHAR(255) NULL,
    CONSTRAINT pk_adoption_application PRIMARY KEY (application_id),
    CONSTRAINT uq_application_user_animal UNIQUE (user_id, animal_id),
    CONSTRAINT chk_app_household CHECK (household_size BETWEEN 1 AND 20),
    CONSTRAINT chk_app_hours CHECK (hours_alone_per_day <= 24),
    CONSTRAINT chk_app_tenant CHECK (ownership = 'OWNER' OR landlord_permission IS NOT NULL),
    CONSTRAINT chk_app_agreements CHECK (agrees_home_visit AND agrees_neutering AND agrees_vaccination)
);

CREATE TABLE adoption (
    adoption_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    application_id  INT UNSIGNED NOT NULL,
    adopted_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    contract_no     VARCHAR(20) NOT NULL,
    CONSTRAINT pk_adoption PRIMARY KEY (adoption_id),
    CONSTRAINT uq_adoption_application UNIQUE (application_id),   -- 1:1 with an approved application
    CONSTRAINT uq_adoption_contract UNIQUE (contract_no)
);

-- ---------- Notifications -----------------------------------------------

CREATE TABLE notification (
    notification_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id          INT UNSIGNED NOT NULL,
    notif_type       ENUM('REACTION','REPORT_ASSIGNED','NEW_CASE','REPORT_ARRIVED','REPORT_NOT_ARRIVED',
                          'ANIMAL_DISCHARGED','NEW_APPLICATION','APPLICATION_APPROVED',
                          'APPLICATION_REJECTED','VACCINE_ASSIGNED','ACCOUNT') NOT NULL,
    title            VARCHAR(100) NOT NULL,
    message          VARCHAR(500) NOT NULL,
    is_read          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_key        VARCHAR(80) NULL,               -- prevents duplicate notifications
    CONSTRAINT pk_notification PRIMARY KEY (notification_id),
    CONSTRAINT uq_notification_event UNIQUE (user_id, event_key)
);

-- =====================================================================
-- 2) FOREIGN KEYS
-- =====================================================================

ALTER TABLE user_role
    ADD CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES role (role_id);

ALTER TABLE breed
    ADD CONSTRAINT fk_breed_species FOREIGN KEY (species_id) REFERENCES species (species_id);

ALTER TABLE clinic
    ADD CONSTRAINT fk_clinic_district FOREIGN KEY (district_id) REFERENCES district (district_id);

ALTER TABLE veterinarian
    ADD CONSTRAINT fk_vet_user   FOREIGN KEY (user_id)   REFERENCES user_account (user_id),
    ADD CONSTRAINT fk_vet_clinic FOREIGN KEY (clinic_id) REFERENCES clinic (clinic_id);

ALTER TABLE shelter
    ADD CONSTRAINT fk_shelter_district FOREIGN KEY (district_id)       REFERENCES district (district_id),
    ADD CONSTRAINT fk_shelter_clinic   FOREIGN KEY (partner_clinic_id) REFERENCES clinic (clinic_id);

ALTER TABLE shelter_species
    ADD CONSTRAINT fk_shsp_shelter FOREIGN KEY (shelter_id) REFERENCES shelter (shelter_id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_shsp_species FOREIGN KEY (species_id) REFERENCES species (species_id);

ALTER TABLE animal
    ADD CONSTRAINT fk_animal_species FOREIGN KEY (species_id) REFERENCES species (species_id),
    ADD CONSTRAINT fk_animal_breed   FOREIGN KEY (breed_id, species_id) REFERENCES breed (breed_id, species_id),
    ADD CONSTRAINT fk_animal_shelter FOREIGN KEY (shelter_id) REFERENCES shelter (shelter_id),
    ADD CONSTRAINT fk_animal_vet     FOREIGN KEY (responsible_vet_id) REFERENCES veterinarian (vet_id)
        ON DELETE SET NULL;

ALTER TABLE injury_report
    ADD CONSTRAINT fk_report_reporter FOREIGN KEY (reporter_id)     REFERENCES user_account (user_id),
    ADD CONSTRAINT fk_report_species  FOREIGN KEY (species_id)      REFERENCES species (species_id),
    ADD CONSTRAINT fk_report_district FOREIGN KEY (district_id)     REFERENCES district (district_id),
    ADD CONSTRAINT fk_report_clinic   FOREIGN KEY (clinic_id)       REFERENCES clinic (clinic_id),
    ADD CONSTRAINT fk_report_vet      FOREIGN KEY (assigned_vet_id) REFERENCES veterinarian (vet_id),
    ADD CONSTRAINT fk_report_resolver FOREIGN KEY (resolved_by)     REFERENCES user_account (user_id),
    ADD CONSTRAINT fk_report_animal   FOREIGN KEY (animal_id)       REFERENCES animal (animal_id);

ALTER TABLE report_status_log
    ADD CONSTRAINT fk_log_report FOREIGN KEY (report_id)  REFERENCES injury_report (report_id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_log_user   FOREIGN KEY (changed_by) REFERENCES user_account (user_id);

ALTER TABLE treatment
    ADD CONSTRAINT fk_treatment_animal  FOREIGN KEY (animal_id) REFERENCES animal (animal_id),
    ADD CONSTRAINT fk_treatment_vet     FOREIGN KEY (vet_id)    REFERENCES veterinarian (vet_id),
    ADD CONSTRAINT fk_treatment_report  FOREIGN KEY (report_id) REFERENCES injury_report (report_id),
    ADD CONSTRAINT fk_treatment_shelter FOREIGN KEY (discharge_shelter_id) REFERENCES shelter (shelter_id);

ALTER TABLE prescription_item
    ADD CONSTRAINT fk_presc_treatment FOREIGN KEY (treatment_id) REFERENCES treatment (treatment_id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_presc_medicine  FOREIGN KEY (medicine_id)  REFERENCES medicine (medicine_id);

ALTER TABLE vaccine_rule
    ADD CONSTRAINT fk_rule_species FOREIGN KEY (species_id) REFERENCES species (species_id),
    ADD CONSTRAINT fk_rule_vaccine FOREIGN KEY (vaccine_id) REFERENCES vaccine (vaccine_id);

ALTER TABLE vaccination_schedule
    ADD CONSTRAINT fk_sched_animal  FOREIGN KEY (animal_id)  REFERENCES animal (animal_id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_sched_vaccine FOREIGN KEY (vaccine_id) REFERENCES vaccine (vaccine_id),
    ADD CONSTRAINT fk_sched_vet     FOREIGN KEY (vet_id)     REFERENCES veterinarian (vet_id),
    ADD CONSTRAINT fk_sched_doneby  FOREIGN KEY (done_by)    REFERENCES veterinarian (vet_id),
    ADD CONSTRAINT fk_sched_generated FOREIGN KEY (generated_from) REFERENCES vaccination_schedule (schedule_id)
        ON DELETE CASCADE;                         -- recursive (unary) relationship

ALTER TABLE feeding_post
    ADD CONSTRAINT fk_post_user FOREIGN KEY (user_id) REFERENCES user_account (user_id);

ALTER TABLE post_reaction
    ADD CONSTRAINT fk_reaction_post FOREIGN KEY (post_id) REFERENCES feeding_post (post_id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_reaction_user FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE;

ALTER TABLE adoption_application
    ADD CONSTRAINT fk_app_user     FOREIGN KEY (user_id)     REFERENCES user_account (user_id),
    ADD CONSTRAINT fk_app_animal   FOREIGN KEY (animal_id)   REFERENCES animal (animal_id),
    ADD CONSTRAINT fk_app_district FOREIGN KEY (district_id) REFERENCES district (district_id),
    ADD CONSTRAINT fk_app_reviewer FOREIGN KEY (reviewed_by) REFERENCES user_account (user_id);

ALTER TABLE adoption
    ADD CONSTRAINT fk_adoption_application FOREIGN KEY (application_id) REFERENCES adoption_application (application_id);

ALTER TABLE notification
    ADD CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE;

-- =====================================================================
-- 3) INDEXES used by the application screens
-- =====================================================================
CREATE INDEX ix_post_time        ON feeding_post (posted_at);
CREATE INDEX ix_report_vet       ON injury_report (assigned_vet_id, status);
CREATE INDEX ix_sched_vet_date   ON vaccination_schedule (vet_id, status, planned_date);
CREATE INDEX ix_notification_usr ON notification (user_id, is_read, created_at);
CREATE INDEX ix_animal_shelter   ON animal (shelter_id, status);
