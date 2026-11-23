-- procedures, triggers and the event
USE stray_db;
SET NAMES utf8mb4 COLLATE utf8mb4_tr_0900_ai_ci;

DROP PROCEDURE IF EXISTS sp_notify;
DROP PROCEDURE IF EXISTS sp_create_injury_report;
DROP PROCEDURE IF EXISTS sp_report_not_arrived;
DROP PROCEDURE IF EXISTS sp_close_day;
DROP PROCEDURE IF EXISTS sp_generate_vaccination_schedule;
DROP PROCEDURE IF EXISTS sp_finish_treatment;
DROP PROCEDURE IF EXISTS sp_complete_vaccination;
DROP PROCEDURE IF EXISTS sp_undo_vaccination;
DROP PROCEDURE IF EXISTS sp_approve_application;
DROP PROCEDURE IF EXISTS sp_reject_application;
DROP PROCEDURE IF EXISTS sp_delete_account;

DELIMITER //

-- adds a notification (no duplicates)
CREATE PROCEDURE sp_notify(IN p_user_id INT UNSIGNED, IN p_type VARCHAR(30),
                           IN p_title VARCHAR(100), IN p_message VARCHAR(500),
                           IN p_event_key VARCHAR(80))
BEGIN
    INSERT IGNORE INTO notification (user_id, notif_type, title, message, event_key)
    VALUES (p_user_id, p_type, p_title, p_message, p_event_key);
END //

-- volunteer reports injured animal, random vet of clinic + shift is picked
CREATE PROCEDURE sp_create_injury_report(
    IN  p_reporter_id INT UNSIGNED, IN p_species_id TINYINT UNSIGNED, IN p_age_weeks SMALLINT UNSIGNED,
    IN  p_color VARCHAR(40), IN p_condition VARCHAR(500),
    IN  p_district_id SMALLINT UNSIGNED, IN p_lat DECIMAL(9,6), IN p_lon DECIMAL(9,6),
    IN  p_photo_path VARCHAR(255), IN p_clinic_id SMALLINT UNSIGNED,
    OUT p_report_id INT UNSIGNED, OUT p_vet_name VARCHAR(120), OUT p_shift VARCHAR(10))
BEGIN
    DECLARE v_vet_id SMALLINT UNSIGNED DEFAULT NULL;
    DECLARE v_vet_user INT UNSIGNED;
    DECLARE v_clinic VARCHAR(100);
    DECLARE v_species VARCHAR(30);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    IF p_condition IS NULL OR TRIM(p_condition) = '' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Please describe the condition of the animal.';
    END IF;

    SET p_shift = fn_shift_for_time(CURTIME());

    START TRANSACTION;
    SELECT v.vet_id, v.user_id, CONCAT('Dr. ', u.first_name, ' ', u.last_name)
      INTO v_vet_id, v_vet_user, p_vet_name
      FROM veterinarian v JOIN user_account u ON u.user_id = v.user_id
     WHERE v.clinic_id = p_clinic_id AND v.shift = p_shift AND u.is_active = TRUE
     ORDER BY RAND() LIMIT 1;

    IF v_vet_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No veterinarian is working in this shift at the selected clinic.';
    END IF;

    SELECT clinic_name INTO v_clinic FROM clinic WHERE clinic_id = p_clinic_id;
    SELECT species_name INTO v_species FROM species WHERE species_id = p_species_id;

    INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc,
                               district_id, latitude, longitude, photo_path, clinic_id, shift, assigned_vet_id)
    VALUES (p_reporter_id, p_species_id, p_age_weeks, p_color, TRIM(p_condition),
            p_district_id, p_lat, p_lon, p_photo_path, p_clinic_id, p_shift, v_vet_id);
    SET p_report_id = LAST_INSERT_ID();

    CALL sp_notify(v_vet_user, 'NEW_CASE', 'New injured animal is on the way',
                   CONCAT('Case #', p_report_id, ': injured ', LOWER(v_species), ' - ', LEFT(TRIM(p_condition), 120)),
                   CONCAT('NEW_CASE:', p_report_id));
    CALL sp_notify(p_reporter_id, 'REPORT_ASSIGNED', 'Veterinarian assigned',
                   CONCAT('Please take the injured ', LOWER(v_species), ' to ', v_clinic, '. Your vet is ',
                          p_vet_name, ' (', LOWER(p_shift), ' shift).'),
                   CONCAT('REPORT_ASSIGNED:', p_report_id));
    COMMIT;
END //

-- vet says the animal did not come
CREATE PROCEDURE sp_report_not_arrived(IN p_report_id INT UNSIGNED, IN p_vet_user_id INT UNSIGNED)
BEGIN
    DECLARE v_status VARCHAR(15);
    DECLARE v_reporter INT UNSIGNED;
    DECLARE v_owner INT UNSIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    SELECT r.status, r.reporter_id, v.user_id INTO v_status, v_reporter, v_owner
      FROM injury_report r JOIN veterinarian v ON v.vet_id = r.assigned_vet_id
     WHERE r.report_id = p_report_id
       FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Case not found.';
    END IF;
    IF v_owner <> p_vet_user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This case is assigned to another veterinarian.';
    END IF;
    IF v_status <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This case is already closed.';
    END IF;

    UPDATE injury_report
       SET status = 'NOT_ARRIVED', resolved_at = NOW(), resolved_by = p_vet_user_id
     WHERE report_id = p_report_id;

    DELETE FROM notification WHERE user_id = p_vet_user_id AND event_key = CONCAT('NEW_CASE:', p_report_id);
    CALL sp_notify(v_reporter, 'REPORT_NOT_ARRIVED', 'Animal did not arrive',
                   (SELECT CONCAT('The injured animal you reported on ', DATE_FORMAT(reported_at, '%d.%m %H:%i'),
                                  ' did not arrive at the clinic. The report was closed.')
                      FROM injury_report WHERE report_id = p_report_id),
                   CONCAT('REPORT_CLOSED:', p_report_id));
    COMMIT;
END //

-- end of day: pending cases become not arrived
CREATE PROCEDURE sp_close_day(IN p_include_today BOOLEAN)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
    START TRANSACTION;

    DELETE n FROM notification n
      JOIN injury_report r ON n.event_key = CONCAT('NEW_CASE:', r.report_id)
     WHERE r.status = 'PENDING' AND (p_include_today OR DATE(r.reported_at) < CURDATE());

    INSERT IGNORE INTO notification (user_id, notif_type, title, message, event_key)
    SELECT r.reporter_id, 'REPORT_NOT_ARRIVED', 'Animal did not arrive',
           CONCAT('The injured animal you reported on ', DATE_FORMAT(r.reported_at, '%d.%m %H:%i'),
                  ' did not arrive at the clinic, so the report was closed at the end of the day.'),
           CONCAT('REPORT_CLOSED:', r.report_id)
      FROM injury_report r
     WHERE r.status = 'PENDING' AND (p_include_today OR DATE(r.reported_at) < CURDATE());

    UPDATE injury_report
       SET status = 'NOT_ARRIVED', resolved_at = NOW(), resolved_by = NULL
     WHERE status = 'PENDING' AND (p_include_today OR DATE(reported_at) < CURDATE());
    COMMIT;
END //

-- makes the vaccine calendar from vaccine_rule
CREATE PROCEDURE sp_generate_vaccination_schedule(IN p_animal_id INT UNSIGNED)
BEGIN
    DECLARE v_species TINYINT UNSIGNED DEFAULT NULL;
    DECLARE v_age INT;
    DECLARE v_shelter SMALLINT UNSIGNED;
    DECLARE v_vet SMALLINT UNSIGNED DEFAULT NULL;
    DECLARE v_vet_user INT UNSIGNED;
    DECLARE v_name VARCHAR(60);
    DECLARE v_wk INT;
    DECLARE v_dose INT;
    DECLARE r_vaccine TINYINT UNSIGNED;
    DECLARE r_first, r_interval, r_last, r_booster, r_repeat INT;
    DECLARE v_done BOOLEAN DEFAULT FALSE;
    DECLARE cur_rules CURSOR FOR
        SELECT vaccine_id, first_dose_week, series_interval_weeks, series_last_week, booster_week, repeat_interval_weeks
          FROM vaccine_rule WHERE species_id = v_species ORDER BY vaccine_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;

    SELECT species_id, fn_current_age_weeks(age_weeks_at_intake, intake_date), shelter_id, responsible_vet_id,
           COALESCE(name, CONCAT('#', animal_id))
      INTO v_species, v_age, v_shelter, v_vet, v_name
      FROM animal WHERE animal_id = p_animal_id;

    IF v_species IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Animal not found.';
    END IF;
    IF v_shelter IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A vaccination calendar is only created for animals in a shelter.';
    END IF;

    IF v_vet IS NULL THEN
        SELECT v.vet_id INTO v_vet
          FROM veterinarian v
          JOIN user_account u ON u.user_id = v.user_id
          JOIN shelter s      ON s.partner_clinic_id = v.clinic_id
         WHERE s.shelter_id = v_shelter AND u.is_active = TRUE
         ORDER BY (SELECT COUNT(*) FROM animal a
                    WHERE a.responsible_vet_id = v.vet_id AND a.status = 'IN_SHELTER'), v.vet_id
         LIMIT 1;
        IF v_vet IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The partner clinic of this shelter has no active veterinarian.';
        END IF;
        UPDATE animal SET responsible_vet_id = v_vet WHERE animal_id = p_animal_id;
    END IF;
    SELECT user_id INTO v_vet_user FROM veterinarian WHERE vet_id = v_vet;

    -- cancel old calendar
    UPDATE vaccination_schedule SET status = 'CANCELLED' WHERE animal_id = p_animal_id AND status = 'PLANNED';

    SET v_done = FALSE;
    OPEN cur_rules;
    rule_loop: LOOP
        FETCH cur_rules INTO r_vaccine, r_first, r_interval, r_last, r_booster, r_repeat;
        IF v_done THEN LEAVE rule_loop; END IF;

        IF v_age <= r_last THEN
            -- young animal
            SET v_wk = GREATEST(r_first, v_age);
            SET v_dose = 0;
            dose_loop: LOOP
                SET v_dose = v_dose + 1;
                INSERT INTO vaccination_schedule (animal_id, vaccine_id, dose_label, planned_date, vet_id)
                VALUES (p_animal_id, r_vaccine, CONCAT('Dose ', v_dose), CURDATE() + INTERVAL (v_wk - v_age) WEEK, v_vet);
                IF r_interval IS NULL OR v_wk >= r_last THEN LEAVE dose_loop; END IF;
                SET v_wk = v_wk + r_interval;
            END LOOP;
            IF r_booster IS NOT NULL AND r_booster > v_wk THEN
                INSERT INTO vaccination_schedule (animal_id, vaccine_id, dose_label, planned_date, vet_id)
                VALUES (p_animal_id, r_vaccine, 'Booster', CURDATE() + INTERVAL (r_booster - v_age) WEEK, v_vet);
                SET v_wk = r_booster;
            END IF;
            INSERT INTO vaccination_schedule (animal_id, vaccine_id, dose_label, planned_date, vet_id)
            VALUES (p_animal_id, r_vaccine, 'Annual', CURDATE() + INTERVAL (v_wk + r_repeat - v_age) WEEK, v_vet);
        ELSE
            -- older animal: one dose now, then every year
            INSERT INTO vaccination_schedule (animal_id, vaccine_id, dose_label, planned_date, vet_id)
            VALUES (p_animal_id, r_vaccine, 'Catch-up dose', CURDATE(), v_vet);
            INSERT INTO vaccination_schedule (animal_id, vaccine_id, dose_label, planned_date, vet_id)
            VALUES (p_animal_id, r_vaccine, 'Annual', CURDATE() + INTERVAL r_repeat WEEK, v_vet);
        END IF;
    END LOOP;
    CLOSE cur_rules;

    CALL sp_notify(v_vet_user, 'VACCINE_ASSIGNED', 'New animal assigned to you',
                   CONCAT(v_name, ' was added to your vaccination list.'),
                   CONCAT('VACCINE_ASSIGNED:', p_animal_id, ':', CURDATE()));
END //

-- vet finishes treatment (shelter, released or deceased)
CREATE PROCEDURE sp_finish_treatment(IN p_treatment_id INT UNSIGNED, IN p_vet_user_id INT UNSIGNED,
                                     IN p_outcome VARCHAR(25), IN p_shelter_id SMALLINT UNSIGNED)
BEGIN
    DECLARE v_outcome VARCHAR(25);
    DECLARE v_owner INT UNSIGNED;
    DECLARE v_animal INT UNSIGNED;
    DECLARE v_species TINYINT UNSIGNED;
    DECLARE v_report INT UNSIGNED;
    DECLARE v_reporter INT UNSIGNED;
    DECLARE v_name VARCHAR(60);
    DECLARE v_shelter_name VARCHAR(100);
    DECLARE v_free INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    IF p_outcome NOT IN ('DISCHARGED_TO_SHELTER','RELEASED','DECEASED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Unknown treatment result.';
    END IF;

    START TRANSACTION;
    SELECT t.outcome, v.user_id, t.animal_id, a.species_id, t.report_id, COALESCE(a.name, CONCAT('#', a.animal_id))
      INTO v_outcome, v_owner, v_animal, v_species, v_report, v_name
      FROM treatment t
      JOIN veterinarian v ON v.vet_id = t.vet_id
      JOIN animal a       ON a.animal_id = t.animal_id
     WHERE t.treatment_id = p_treatment_id
       FOR UPDATE;

    IF v_outcome IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Treatment not found.';
    END IF;
    IF v_owner <> p_vet_user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This treatment belongs to another veterinarian.';
    END IF;
    IF v_outcome <> 'UNDER_TREATMENT' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This treatment is already finished.';
    END IF;

    IF p_outcome = 'DISCHARGED_TO_SHELTER' THEN
        IF p_shelter_id IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Please choose a shelter.';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM shelter_species WHERE shelter_id = p_shelter_id AND species_id = v_species) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The selected shelter does not accept this species.';
        END IF;
        SELECT sh.capacity - COUNT(a.animal_id), sh.shelter_name INTO v_free, v_shelter_name
          FROM shelter sh LEFT JOIN animal a ON a.shelter_id = sh.shelter_id AND a.status = 'IN_SHELTER'
         WHERE sh.shelter_id = p_shelter_id
         GROUP BY sh.capacity, sh.shelter_name;
        IF v_free <= 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The selected shelter is full.';
        END IF;
    END IF;

    UPDATE treatment
       SET outcome = p_outcome, ended_at = NOW(),
           discharge_shelter_id = IF(p_outcome = 'DISCHARGED_TO_SHELTER', p_shelter_id, NULL)
     WHERE treatment_id = p_treatment_id;

    IF p_outcome = 'DISCHARGED_TO_SHELTER' THEN
        -- age first, then intake date
        UPDATE animal SET age_weeks_at_intake = fn_current_age_weeks(age_weeks_at_intake, intake_date),
                          intake_date = CURDATE(),
                          status = 'IN_SHELTER', shelter_id = p_shelter_id, responsible_vet_id = NULL
         WHERE animal_id = v_animal;
        CALL sp_generate_vaccination_schedule(v_animal);
    ELSE
        UPDATE animal SET status = p_outcome WHERE animal_id = v_animal;
    END IF;

    IF v_report IS NOT NULL THEN
        SELECT reporter_id INTO v_reporter FROM injury_report WHERE report_id = v_report;
        CALL sp_notify(v_reporter, 'ANIMAL_DISCHARGED', 'Update about the animal you reported',
                       CONCAT('The animal you reported (', v_name, '): ',
                              CASE p_outcome
                                   WHEN 'DISCHARGED_TO_SHELTER' THEN CONCAT('treatment finished, moved to ', v_shelter_name, '.')
                                   WHEN 'RELEASED' THEN 'treatment finished, the animal was released.'
                                   ELSE 'unfortunately the animal could not be saved.' END),
                       CONCAT('FINISHED:', v_report));
    END IF;
    COMMIT;
END //

-- vaccine done, next year is added
CREATE PROCEDURE sp_complete_vaccination(IN p_schedule_id INT UNSIGNED, IN p_vet_user_id INT UNSIGNED)
BEGIN
    DECLARE v_status VARCHAR(10);
    DECLARE v_animal INT UNSIGNED;
    DECLARE v_vaccine TINYINT UNSIGNED;
    DECLARE v_assigned SMALLINT UNSIGNED;
    DECLARE v_me SMALLINT UNSIGNED;
    DECLARE v_repeat INT;
    DECLARE v_left INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    SELECT status, animal_id, vaccine_id, vet_id INTO v_status, v_animal, v_vaccine, v_assigned
      FROM vaccination_schedule WHERE schedule_id = p_schedule_id FOR UPDATE;
    SELECT vet_id INTO v_me FROM veterinarian WHERE user_id = p_vet_user_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vaccination not found.';
    END IF;
    IF v_me IS NULL OR v_me <> v_assigned THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This vaccination is assigned to another veterinarian.';
    END IF;
    IF v_status <> 'PLANNED' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This vaccination is not planned any more.';
    END IF;

    UPDATE vaccination_schedule SET status = 'DONE', done_date = CURDATE(), done_by = v_me
     WHERE schedule_id = p_schedule_id;

    SELECT COUNT(*) INTO v_left FROM vaccination_schedule
     WHERE animal_id = v_animal AND vaccine_id = v_vaccine AND status = 'PLANNED';
    IF v_left = 0 THEN
        SELECT r.repeat_interval_weeks INTO v_repeat
          FROM vaccine_rule r JOIN animal a ON a.species_id = r.species_id
         WHERE a.animal_id = v_animal AND r.vaccine_id = v_vaccine;
        INSERT INTO vaccination_schedule (animal_id, vaccine_id, dose_label, planned_date, vet_id, generated_from)
        VALUES (v_animal, v_vaccine, 'Annual', CURDATE() + INTERVAL v_repeat WEEK, v_assigned, p_schedule_id);
    END IF;
    COMMIT;
END //

-- undo a done vaccine
CREATE PROCEDURE sp_undo_vaccination(IN p_schedule_id INT UNSIGNED, IN p_vet_user_id INT UNSIGNED)
BEGIN
    DECLARE v_status VARCHAR(10);
    DECLARE v_assigned SMALLINT UNSIGNED;
    DECLARE v_me SMALLINT UNSIGNED;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    SELECT status, vet_id INTO v_status, v_assigned
      FROM vaccination_schedule WHERE schedule_id = p_schedule_id FOR UPDATE;
    SELECT vet_id INTO v_me FROM veterinarian WHERE user_id = p_vet_user_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vaccination not found.';
    END IF;
    IF v_me IS NULL OR v_me <> v_assigned THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This vaccination is assigned to another veterinarian.';
    END IF;
    IF v_status <> 'DONE' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only a vaccination marked as done can be taken back.';
    END IF;
    IF EXISTS (SELECT 1 FROM vaccination_schedule WHERE generated_from = p_schedule_id AND status = 'DONE') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'The next dose is already given, so this one cannot be taken back.';
    END IF;

    DELETE FROM vaccination_schedule WHERE generated_from = p_schedule_id AND status = 'PLANNED';
    UPDATE vaccination_schedule SET status = 'PLANNED', done_date = NULL, done_by = NULL
     WHERE schedule_id = p_schedule_id;
    COMMIT;
END //

-- admin approves an application
CREATE PROCEDURE sp_approve_application(IN p_application_id INT UNSIGNED, IN p_admin_id INT UNSIGNED,
                                        IN p_note VARCHAR(255))
BEGIN
    DECLARE v_status VARCHAR(10);
    DECLARE v_animal INT UNSIGNED;
    DECLARE v_user INT UNSIGNED;
    DECLARE v_animal_status VARCHAR(20);
    DECLARE v_name VARCHAR(60);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    IF NOT EXISTS (SELECT 1 FROM user_role ur JOIN role r ON r.role_id = ur.role_id
                    WHERE ur.user_id = p_admin_id AND r.role_name = 'ADMIN') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only an administrator can approve applications.';
    END IF;

    START TRANSACTION;
    SELECT ap.status, ap.animal_id, ap.user_id, a.status, COALESCE(a.name, CONCAT('#', a.animal_id))
      INTO v_status, v_animal, v_user, v_animal_status, v_name
      FROM adoption_application ap JOIN animal a ON a.animal_id = ap.animal_id
     WHERE ap.application_id = p_application_id
       FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Application not found.';
    END IF;
    IF v_status <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only pending applications can be approved.';
    END IF;
    IF v_animal_status <> 'IN_SHELTER' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This animal is no longer available.';
    END IF;

    UPDATE adoption_application
       SET status = 'APPROVED', reviewed_by = p_admin_id, reviewed_at = NOW(), admin_note = p_note
     WHERE application_id = p_application_id;

    -- reject others for same animal
    INSERT IGNORE INTO notification (user_id, notif_type, title, message, event_key)
    SELECT user_id, 'APPLICATION_REJECTED', 'Adoption application result',
           CONCAT('Sorry, ', v_name, ' has been adopted by another family. Your application #',
                  application_id, ' was closed.'),
           CONCAT('APP_RESULT:', application_id)
      FROM adoption_application
     WHERE animal_id = v_animal AND status = 'PENDING';
    UPDATE adoption_application
       SET status = 'REJECTED', reviewed_by = p_admin_id, reviewed_at = NOW(),
           admin_note = 'Animal adopted by another applicant'
     WHERE animal_id = v_animal AND status = 'PENDING';

    UPDATE animal SET status = 'ADOPTED' WHERE animal_id = v_animal;

    INSERT INTO adoption (application_id, contract_no)
    VALUES (p_application_id, CONCAT('ADP-', YEAR(CURDATE()), '-', LPAD(p_application_id, 5, '0')));

    INSERT IGNORE INTO user_role (user_id, role_id)
    SELECT v_user, role_id FROM role WHERE role_name = 'ADOPTER';

    CALL sp_notify(v_user, 'APPLICATION_APPROVED', 'Your adoption application was approved!',
                   CONCAT('Congratulations! You can now adopt ', v_name,
                          '. The shelter will contact you. See "My Adoptions".'),
                   CONCAT('APP_RESULT:', p_application_id));
    COMMIT;
END //

CREATE PROCEDURE sp_reject_application(IN p_application_id INT UNSIGNED, IN p_admin_id INT UNSIGNED,
                                       IN p_note VARCHAR(255))
BEGIN
    DECLARE v_status VARCHAR(10);
    DECLARE v_user INT UNSIGNED;
    DECLARE v_name VARCHAR(60);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    START TRANSACTION;
    SELECT ap.status, ap.user_id, COALESCE(a.name, CONCAT('#', a.animal_id)) INTO v_status, v_user, v_name
      FROM adoption_application ap JOIN animal a ON a.animal_id = ap.animal_id
     WHERE ap.application_id = p_application_id FOR UPDATE;
    IF v_status IS NULL OR v_status <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only pending applications can be rejected.';
    END IF;

    UPDATE adoption_application
       SET status = 'REJECTED', reviewed_by = p_admin_id, reviewed_at = NOW(), admin_note = p_note
     WHERE application_id = p_application_id;
    CALL sp_notify(v_user, 'APPLICATION_REJECTED', 'Adoption application result',
                   CONCAT('Your application #', p_application_id, ' for ', v_name, ' was not approved.',
                          IF(p_note IS NULL OR p_note = '', '', CONCAT(' Note: ', p_note))),
                   CONCAT('APP_RESULT:', p_application_id));
    COMMIT;
END //

-- close an account (soft delete), admin cant be deleted, vet only by admin
CREATE PROCEDURE sp_delete_account(IN p_user_id INT UNSIGNED, IN p_actor_id INT UNSIGNED)
BEGIN
    DECLARE v_active BOOLEAN DEFAULT NULL;
    DECLARE v_vet SMALLINT UNSIGNED DEFAULT NULL;
    DECLARE v_clinic SMALLINT UNSIGNED;
    DECLARE v_shift VARCHAR(10);
    DECLARE v_other SMALLINT UNSIGNED DEFAULT NULL;
    DECLARE v_actor_admin BOOLEAN;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    SELECT is_active INTO v_active FROM user_account WHERE user_id = p_user_id;
    IF v_active IS NULL OR v_active = FALSE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Account not found or already closed.';
    END IF;

    SET v_actor_admin = EXISTS (SELECT 1 FROM user_role ur JOIN role r ON r.role_id = ur.role_id
                                 WHERE ur.user_id = p_actor_id AND r.role_name = 'ADMIN');
    IF p_actor_id <> p_user_id AND NOT v_actor_admin THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'You can only delete your own account.';
    END IF;
    IF EXISTS (SELECT 1 FROM user_role ur JOIN role r ON r.role_id = ur.role_id
                WHERE ur.user_id = p_user_id AND r.role_name = 'ADMIN') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An administrator account cannot be deleted.';
    END IF;

    SELECT vet_id, clinic_id, shift INTO v_vet, v_clinic, v_shift FROM veterinarian WHERE user_id = p_user_id;
    IF v_vet IS NOT NULL AND NOT v_actor_admin THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Veterinarian accounts can only be closed by the administrator.';
    END IF;
    IF v_vet IS NOT NULL THEN
        IF EXISTS (SELECT 1 FROM injury_report WHERE assigned_vet_id = v_vet AND status = 'PENDING')
           OR EXISTS (SELECT 1 FROM treatment WHERE vet_id = v_vet AND outcome = 'UNDER_TREATMENT') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'You still have open cases or treatments. Close them first.';
        END IF;
        SELECT v.vet_id INTO v_other
          FROM veterinarian v JOIN user_account u ON u.user_id = v.user_id
         WHERE v.clinic_id = v_clinic AND v.vet_id <> v_vet AND u.is_active = TRUE AND v.shift = v_shift
         LIMIT 1;
        IF v_other IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Every clinic needs at least one morning and one evening veterinarian.';
        END IF;
    END IF;

    START TRANSACTION;
    -- just deactivate
    UPDATE user_account SET is_active = FALSE WHERE user_id = p_user_id;
    UPDATE feeding_post SET is_deleted = TRUE WHERE user_id = p_user_id;
    DELETE FROM post_reaction WHERE user_id = p_user_id;
    UPDATE adoption_application SET status = 'WITHDRAWN' WHERE user_id = p_user_id AND status = 'PENDING';
    DELETE FROM notification WHERE user_id = p_user_id;
    IF v_vet IS NOT NULL THEN
        -- give animals and vaccines to another vet
        UPDATE animal SET responsible_vet_id = v_other WHERE responsible_vet_id = v_vet;
        UPDATE vaccination_schedule SET vet_id = v_other WHERE vet_id = v_vet AND status = 'PLANNED';
    END IF;
    COMMIT;
END //

-- triggers
DROP TRIGGER IF EXISTS trg_report_ai //
DROP TRIGGER IF EXISTS trg_report_au //
DROP TRIGGER IF EXISTS trg_reaction_bi //
DROP TRIGGER IF EXISTS trg_reaction_ai //
DROP TRIGGER IF EXISTS trg_reaction_bu //
DROP TRIGGER IF EXISTS trg_reaction_au //
DROP TRIGGER IF EXISTS trg_reaction_ad //
DROP TRIGGER IF EXISTS trg_application_bi //
DROP TRIGGER IF EXISTS trg_application_ai //
DROP TRIGGER IF EXISTS trg_vet_bu //
DROP TRIGGER IF EXISTS trg_vet_bd //

-- save status changes to log
CREATE TRIGGER trg_report_ai AFTER INSERT ON injury_report FOR EACH ROW
BEGIN
    INSERT INTO report_status_log (report_id, old_status, new_status, changed_by)
    VALUES (NEW.report_id, NULL, NEW.status, NEW.reporter_id);
END //

CREATE TRIGGER trg_report_au AFTER UPDATE ON injury_report FOR EACH ROW
BEGIN
    IF NEW.status <> OLD.status THEN
        INSERT INTO report_status_log (report_id, old_status, new_status, changed_by)
        VALUES (NEW.report_id, OLD.status, NEW.status, NEW.resolved_by);
    END IF;
END //

-- checks before adding emoji
CREATE TRIGGER trg_reaction_bi BEFORE INSERT ON post_reaction FOR EACH ROW
BEGIN
    DECLARE v_owner INT UNSIGNED;
    DECLARE v_deleted BOOLEAN;
    SELECT user_id, is_deleted INTO v_owner, v_deleted FROM feeding_post WHERE post_id = NEW.post_id;
    IF v_owner = NEW.user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'You cannot react to your own post.';
    END IF;
    IF v_deleted THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This post was deleted.';
    END IF;
    IF (SELECT posted_at FROM feeding_post WHERE post_id = NEW.post_id) < NOW() - INTERVAL 24 HOUR THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This post is older than 24 hours and is no longer on the map.';
    END IF;
END //

-- emoji can change only in 24 hours
CREATE TRIGGER trg_reaction_bu BEFORE UPDATE ON post_reaction FOR EACH ROW
BEGIN
    IF NEW.emoji <> OLD.emoji
       AND (SELECT posted_at FROM feeding_post WHERE post_id = NEW.post_id) < NOW() - INTERVAL 24 HOUR THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This post is older than 24 hours, its emoji cannot be changed.';
    END IF;
END //

-- notify post owner
CREATE TRIGGER trg_reaction_ai AFTER INSERT ON post_reaction FOR EACH ROW
BEGIN
    CALL sp_notify((SELECT user_id FROM feeding_post WHERE post_id = NEW.post_id),
                   'REACTION', 'New support on your feeding post', fn_reaction_message(NEW.post_id, NEW.user_id, NEW.emoji),
                   CONCAT('REACTION:', NEW.post_id, ':', NEW.user_id));
END //

-- emoji changed, update notification
CREATE TRIGGER trg_reaction_au AFTER UPDATE ON post_reaction FOR EACH ROW
BEGIN
    IF NEW.emoji <> OLD.emoji THEN
        UPDATE notification
           SET message = fn_reaction_message(NEW.post_id, NEW.user_id, NEW.emoji),
               is_read = FALSE, created_at = NOW()
         WHERE event_key = CONCAT('REACTION:', NEW.post_id, ':', NEW.user_id);
    END IF;
END //

-- emoji removed, delete notification
CREATE TRIGGER trg_reaction_ad AFTER DELETE ON post_reaction FOR EACH ROW
BEGIN
    DELETE FROM notification WHERE event_key = CONCAT('REACTION:', OLD.post_id, ':', OLD.user_id);
END //

-- adoption rules
CREATE TRIGGER trg_application_bi BEFORE INSERT ON adoption_application FOR EACH ROW
BEGIN
    DECLARE v_animal_status VARCHAR(20);
    SELECT status INTO v_animal_status FROM animal WHERE animal_id = NEW.animal_id;
    IF v_animal_status IS NULL OR v_animal_status <> 'IN_SHELTER' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This animal is not available for adoption.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM user_account WHERE user_id = NEW.user_id AND is_active = TRUE) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Account is not active.';
    END IF;
    IF NEW.birth_year < 1900 OR YEAR(CURDATE()) - NEW.birth_year < 18 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Applicants must be at least 18 years old.';
    END IF;
    IF NEW.ownership = 'TENANT' AND NEW.landlord_permission = FALSE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tenants need the permission of the landlord.';
    END IF;
    IF (SELECT COUNT(*) FROM adoption_application
         WHERE user_id = NEW.user_id AND status = 'PENDING') >= 3 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'You can have at most 3 pending applications.';
    END IF;
END //

-- notify admin
CREATE TRIGGER trg_application_ai AFTER INSERT ON adoption_application FOR EACH ROW
BEGIN
    INSERT IGNORE INTO notification (user_id, notif_type, title, message, event_key)
    SELECT u.user_id, 'NEW_APPLICATION', 'New adoption application',
           CONCAT('Application #', NEW.application_id, ' is waiting for your review.'),
           CONCAT('NEW_APPLICATION:', NEW.application_id)
      FROM user_account u
      JOIN user_role ur ON ur.user_id = u.user_id
      JOIN role r       ON r.role_id = ur.role_id
     WHERE r.role_name = 'ADMIN' AND u.is_active = TRUE;
END //

-- clinic needs a morning and an evening vet
CREATE TRIGGER trg_vet_bu BEFORE UPDATE ON veterinarian FOR EACH ROW
BEGIN
    IF (NEW.clinic_id <> OLD.clinic_id OR NEW.shift <> OLD.shift)
       AND (SELECT COUNT(*) FROM veterinarian v JOIN user_account u ON u.user_id = v.user_id
             WHERE v.clinic_id = OLD.clinic_id AND v.shift = OLD.shift
               AND v.vet_id <> OLD.vet_id AND u.is_active = TRUE) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Every clinic needs at least one morning and one evening veterinarian.';
    END IF;
END //

CREATE TRIGGER trg_vet_bd BEFORE DELETE ON veterinarian FOR EACH ROW
BEGIN
    IF (SELECT COUNT(*) FROM veterinarian v JOIN user_account u ON u.user_id = v.user_id
         WHERE v.clinic_id = OLD.clinic_id AND v.shift = OLD.shift
           AND v.vet_id <> OLD.vet_id AND u.is_active = TRUE) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Every clinic needs at least one morning and one evening veterinarian.';
    END IF;
END //

-- event: every day 23:59 close pending cases
DROP EVENT IF EXISTS ev_close_day //
CREATE EVENT ev_close_day
    ON SCHEDULE EVERY 1 DAY
    STARTS (TIMESTAMP(CURDATE()) + INTERVAL 23 HOUR + INTERVAL 59 MINUTE)
    DO CALL sp_close_day(TRUE) //

DELIMITER ;
