-- functions and views
USE stray_db;
SET NAMES utf8mb4 COLLATE utf8mb4_tr_0900_ai_ci;

DROP FUNCTION IF EXISTS fn_current_age_weeks;
DROP FUNCTION IF EXISTS fn_age_label;
DROP FUNCTION IF EXISTS fn_shift_for_time;
DROP FUNCTION IF EXISTS fn_reaction_message;

DELIMITER //

-- current age in weeks
CREATE FUNCTION fn_current_age_weeks(p_age_weeks INT, p_intake_date DATE)
RETURNS INT
NOT DETERMINISTIC NO SQL
BEGIN
    RETURN p_age_weeks + FLOOR(GREATEST(DATEDIFF(CURDATE(), p_intake_date), 0) / 7);
END //

-- age as text (weeks, months or years)
CREATE FUNCTION fn_age_label(p_weeks INT)
RETURNS VARCHAR(30)
DETERMINISTIC NO SQL
BEGIN
    DECLARE v_years INT;
    DECLARE v_months INT;
    IF p_weeks < 12 THEN
        RETURN CONCAT(p_weeks, IF(p_weeks = 1, ' week', ' weeks'));
    ELSEIF p_weeks <= 52 THEN
        SET v_months = FLOOR(p_weeks / 4.345);
        RETURN CONCAT(v_months, IF(v_months = 1, ' month', ' months'));
    END IF;
    SET v_years = FLOOR(p_weeks / 52);
    SET v_months = FLOOR((p_weeks - v_years * 52) / 4.345);
    RETURN CONCAT(v_years, IF(v_years = 1, ' year', ' years'),
                  IF(v_months = 0, '', CONCAT(' ', v_months, IF(v_months = 1, ' month', ' months'))));
END //

-- which shift for a time
CREATE FUNCTION fn_shift_for_time(p_time TIME)
RETURNS VARCHAR(10)
DETERMINISTIC NO SQL
BEGIN
    IF p_time >= '07:00:00' AND p_time < '17:00:00' THEN
        RETURN 'MORNING';
    END IF;
    RETURN 'EVENING';
END //

-- emoji notification text
CREATE FUNCTION fn_reaction_message(p_post_id INT UNSIGNED, p_user_id INT UNSIGNED, p_emoji VARCHAR(10))
RETURNS VARCHAR(255)
NOT DETERMINISTIC READS SQL DATA
BEGIN
    RETURN CONCAT((SELECT username FROM user_account WHERE user_id = p_user_id),
                  ' supported your feeding post from ',
                  (SELECT DATE_FORMAT(posted_at, '%d.%m %H:%i') FROM feeding_post WHERE post_id = p_post_id),
                  ' with "',
                  CASE p_emoji WHEN 'HEART' THEN 'Love' WHEN 'CLAP' THEN 'Applause' WHEN 'PAW' THEN 'Paw'
                               WHEN 'STRONG' THEN 'Strong' ELSE 'Thank you' END, '".');
END //

DELIMITER ;

-- all info of an animal
CREATE OR REPLACE VIEW v_animal_card AS
SELECT a.animal_id,
       COALESCE(a.name, CONCAT('#', a.animal_id)) AS display_name,
       a.name, a.species_id, s.species_name,
       a.breed_id, COALESCE(b.breed_name, 'Unknown') AS breed_name,
       a.sex, a.color, a.is_neutered, a.status, a.description,
       a.age_weeks_at_intake, a.intake_date,
       fn_current_age_weeks(a.age_weeks_at_intake, a.intake_date) AS age_weeks,
       fn_age_label(fn_current_age_weeks(a.age_weeks_at_intake, a.intake_date)) AS age_label,
       a.shelter_id, sh.shelter_name,
       a.responsible_vet_id,
       CONCAT('Dr. ', u.first_name, ' ', u.last_name) AS responsible_vet_name
FROM animal a
JOIN species s        ON s.species_id = a.species_id
LEFT JOIN breed b     ON b.breed_id = a.breed_id
LEFT JOIN shelter sh  ON sh.shelter_id = a.shelter_id
LEFT JOIN veterinarian v ON v.vet_id = a.responsible_vet_id
LEFT JOIN user_account u ON u.user_id = v.user_id;

-- posts of last 24 hours (map)
CREATE OR REPLACE VIEW v_active_feeding_posts AS
SELECT p.post_id, p.user_id, u.username, CONCAT(u.first_name, ' ', u.last_name) AS full_name,
       p.latitude, p.longitude, p.photo_path, p.note, p.posted_at,
       (SELECT COUNT(*) FROM post_reaction r WHERE r.post_id = p.post_id) AS reaction_count
FROM feeding_post p
JOIN user_account u ON u.user_id = p.user_id
WHERE p.is_deleted = FALSE
  AND u.is_active = TRUE
  AND p.posted_at >= NOW() - INTERVAL 24 HOUR;

-- shelters with animal counts
CREATE OR REPLACE VIEW v_shelter_summary AS
SELECT sh.shelter_id, sh.shelter_name, d.district_name, sh.address, sh.phone, sh.capacity,
       sh.latitude, sh.longitude, c.clinic_name AS partner_clinic,
       (SELECT GROUP_CONCAT(sp.species_name ORDER BY sp.species_name SEPARATOR ', ')
          FROM shelter_species ss JOIN species sp ON sp.species_id = ss.species_id
         WHERE ss.shelter_id = sh.shelter_id) AS accepted_species,
       COUNT(a.animal_id) AS animal_count,
       COALESCE(SUM(a.species_id = (SELECT species_id FROM species WHERE species_name = 'Cat')), 0) AS cat_count,
       COALESCE(SUM(a.species_id = (SELECT species_id FROM species WHERE species_name = 'Dog')), 0) AS dog_count,
       ROUND(100 * COUNT(a.animal_id) / sh.capacity) AS occupancy_pct
FROM shelter sh
JOIN district d ON d.district_id = sh.district_id
JOIN clinic c   ON c.clinic_id = sh.partner_clinic_id
LEFT JOIN animal a ON a.shelter_id = sh.shelter_id AND a.status = 'IN_SHELTER'
GROUP BY sh.shelter_id, sh.shelter_name, d.district_name, sh.address, sh.phone, sh.capacity,
         sh.latitude, sh.longitude, c.clinic_name;

-- planned vaccines of shelter animals
CREATE OR REPLACE VIEW v_vaccination_due AS
SELECT vs.schedule_id, vs.animal_id, ac.display_name, ac.species_name, ac.age_label, ac.shelter_name,
       vs.vaccine_id, vc.vaccine_code, vc.vaccine_name, vs.dose_label, vs.planned_date, vs.vet_id,
       DATEDIFF(vs.planned_date, CURDATE()) AS days_left,
       CAST(CASE WHEN vs.planned_date < CURDATE() THEN 'OVERDUE'
                 WHEN vs.planned_date <= CURDATE() + INTERVAL 7 DAY THEN 'THIS_WEEK'
                 ELSE 'UPCOMING' END AS CHAR(10)) COLLATE utf8mb4_tr_0900_ai_ci AS due_state
FROM vaccination_schedule vs
JOIN v_animal_card ac ON ac.animal_id = vs.animal_id
JOIN vaccine vc       ON vc.vaccine_id = vs.vaccine_id
WHERE vs.status = 'PLANNED'
  AND ac.status = 'IN_SHELTER';

-- daily stats of vets
CREATE OR REPLACE VIEW v_vet_daily_stats AS
SELECT x.vet_id,
       CONCAT('Dr. ', u.first_name, ' ', u.last_name) AS vet_name,
       c.clinic_name, v.shift, x.day,
       SUM(x.arrived)     AS arrived,
       SUM(x.not_arrived) AS not_arrived,
       SUM(x.discharged)  AS discharged
FROM (
    SELECT assigned_vet_id AS vet_id, DATE(resolved_at) AS day,
           (status = 'ARRIVED') AS arrived, (status = 'NOT_ARRIVED') AS not_arrived, 0 AS discharged
      FROM injury_report WHERE status <> 'PENDING'
    UNION ALL
    SELECT vet_id, DATE(ended_at), 0, 0, 1
      FROM treatment WHERE outcome IN ('DISCHARGED_TO_SHELTER','RELEASED')
) x
JOIN veterinarian v ON v.vet_id = x.vet_id
JOIN user_account u ON u.user_id = v.user_id
JOIN clinic c       ON c.clinic_id = v.clinic_id
GROUP BY x.vet_id, vet_name, c.clinic_name, v.shift, x.day;

-- animals under treatment
CREATE OR REPLACE VIEW v_active_treatments AS
SELECT t.treatment_id, t.animal_id, ac.display_name, ac.species_name, t.diagnosis, t.condition_level,
       t.started_at, t.vet_id, CONCAT('Dr. ', u.first_name, ' ', u.last_name) AS vet_name, c.clinic_name
FROM treatment t
JOIN v_animal_card ac ON ac.animal_id = t.animal_id
JOIN veterinarian v   ON v.vet_id = t.vet_id
JOIN user_account u   ON u.user_id = v.user_id
JOIN clinic c         ON c.clinic_id = v.clinic_id
WHERE t.outcome = 'UNDER_TREATMENT';

-- application details for admin
CREATE OR REPLACE VIEW v_application_dossier AS
SELECT ap.application_id, ap.status, ap.applied_at,
       ap.user_id, u.username, CONCAT(u.first_name, ' ', u.last_name) AS applicant_name,
       u.email, u.phone,
       YEAR(CURDATE()) - ap.birth_year AS applicant_age,
       ap.full_address, d.district_name, ap.housing_type, ap.ownership, ap.landlord_permission,
       ap.household_size, ap.has_children, ap.has_other_pets, ap.other_pets_note,
       ap.pet_experience, ap.hours_alone_per_day, ap.reason,
       ap.agrees_home_visit, ap.agrees_neutering, ap.agrees_vaccination,
       ap.animal_id, ac.display_name AS animal_name, ac.species_name, ac.age_label, ac.shelter_name,
       ap.reviewed_at, ap.admin_note
FROM adoption_application ap
JOIN user_account u   ON u.user_id = ap.user_id
JOIN district d       ON d.district_id = ap.district_id
JOIN v_animal_card ac ON ac.animal_id = ap.animal_id;
