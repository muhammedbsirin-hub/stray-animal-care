-- sample data (made by tools/generate_seed.py), all passwords: Demo1234!
USE stray_db;
SET NAMES utf8mb4 COLLATE utf8mb4_tr_0900_ai_ci;

INSERT INTO role (role_name) VALUES
  ('ADMIN'),
  ('VET'),
  ('VOLUNTEER'),
  ('ADOPTER');

INSERT INTO district (district_name) VALUES
  ('Adalar'),
  ('Ataşehir'),
  ('Avcılar'),
  ('Bağcılar'),
  ('Bahçelievler'),
  ('Bakırköy'),
  ('Başakşehir'),
  ('Bayrampaşa'),
  ('Beşiktaş'),
  ('Beykoz'),
  ('Beylikdüzü'),
  ('Beyoğlu'),
  ('Büyükçekmece'),
  ('Çekmeköy'),
  ('Esenyurt'),
  ('Eyüpsultan'),
  ('Fatih'),
  ('Gaziosmanpaşa'),
  ('Kadıköy'),
  ('Kağıthane'),
  ('Kartal'),
  ('Küçükçekmece'),
  ('Maltepe'),
  ('Pendik'),
  ('Sancaktepe'),
  ('Sarıyer'),
  ('Şişli'),
  ('Tuzla'),
  ('Ümraniye'),
  ('Üsküdar'),
  ('Zeytinburnu');

INSERT INTO species (species_name) VALUES
  ('Cat'),
  ('Dog');

INSERT INTO breed (species_id, breed_name) VALUES
  (1, 'Mixed'),
  (1, 'Tabby'),
  (1, 'Van Cat'),
  (1, 'Turkish Angora'),
  (1, 'British Shorthair'),
  (1, 'Scottish Fold'),
  (2, 'Mixed'),
  (2, 'Kangal'),
  (2, 'Golden Retriever'),
  (2, 'Labrador Retriever'),
  (2, 'German Shepherd'),
  (2, 'Terrier');

INSERT INTO clinic (clinic_name, district_id, address, phone, latitude, longitude) VALUES
  ('Moda Paws Veterinary Clinic', 19, 'Veteriner Sk. No:67, Kadıköy / Istanbul', '02162721960', 40.985429, 29.02903),
  ('Bosphorus Animal Hospital', 9, 'Veteriner Sk. No:73, Beşiktaş / Istanbul', '02128056747', 41.047609, 29.011738),
  ('Mecidiyeköy Vet Clinic', 27, 'Veteriner Sk. No:64, Şişli / Istanbul', '02128400346', 41.0634, 28.987574),
  ('Üsküdar Friends Veterinary Clinic', 30, 'Veteriner Sk. No:16, Üsküdar / Istanbul', '02165819091', 41.019879, 29.01637),
  ('Bakırköy Seaside Animal Clinic', 6, 'Veteriner Sk. No:64, Bakırköy / Istanbul', '02126271957', 40.983801, 28.872396);

INSERT INTO user_account (username, password, first_name, last_name, email, phone) VALUES
  ('admin', 'Demo1234!', 'System', 'Admin', 'admin@straycare.org', '05300000001'),
  ('vet01', 'Demo1234!', 'Fatma', 'Çetin', 'vet01@straycare.org', '05555681518'),
  ('vet02', 'Demo1234!', 'Hakan', 'Doğan', 'vet02@straycare.org', '05572940557'),
  ('vet03', 'Demo1234!', 'Kerem', 'Demir', 'vet03@straycare.org', '05998716897'),
  ('vet04', 'Demo1234!', 'Merve', 'Polat', 'vet04@straycare.org', '05569788093'),
  ('vet05', 'Demo1234!', 'İrem', 'Çelik', 'vet05@straycare.org', '05381967273'),
  ('vet06', 'Demo1234!', 'Barış', 'Şahin', 'vet06@straycare.org', '05978486488'),
  ('vet07', 'Demo1234!', 'Buse', 'Özdemir', 'vet07@straycare.org', '05963440029'),
  ('vet08', 'Demo1234!', 'Ece', 'Polat', 'vet08@straycare.org', '05953477876'),
  ('vet09', 'Demo1234!', 'Hakan', 'Kaya', 'vet09@straycare.org', '05557178472'),
  ('vet10', 'Demo1234!', 'Kerem', 'Özdemir', 'vet10@straycare.org', '05347513627'),
  ('vet11', 'Demo1234!', 'Umut', 'Yılmaz', 'vet11@straycare.org', '05307981933'),
  ('vet12', 'Demo1234!', 'Ahmet', 'Aksoy', 'vet12@straycare.org', '05384520599'),
  ('elif_yildiz', 'Demo1234!', 'Elif', 'Yıldız', 'elif_yildiz@example.com', '05928379298'),
  ('mert_kaya', 'Demo1234!', 'Mert', 'Kaya', 'mert_kaya@example.com', '05516229486'),
  ('zeynep_ak', 'Demo1234!', 'Zeynep', 'Ak', 'zeynep_ak@example.com', '05928360161'),
  ('can_demir', 'Demo1234!', 'Can', 'Demir', 'can_demir@example.com', '05355008754'),
  ('selin_arslan', 'Demo1234!', 'Selin', 'Arslan', 'selin_arslan@example.com', '05951779922'),
  ('burak_celik', 'Demo1234!', 'Burak', 'Çelik', 'burak_celik@example.com', '05469579318'),
  ('deniz_sahin', 'Demo1234!', 'Deniz', 'Şahin', 'deniz_sahin@example.com', '05903208073'),
  ('ece_koc', 'Demo1234!', 'Ece', 'Koç', 'ece_koc@example.com', '05902838222');

INSERT INTO user_role (user_id, role_id) VALUES
  (1, 1),
  (2, 2),
  (3, 2),
  (4, 2),
  (5, 2),
  (6, 2),
  (7, 2),
  (8, 2),
  (9, 2),
  (10, 2),
  (11, 2),
  (12, 2),
  (13, 2),
  (14, 3),
  (15, 3),
  (16, 3),
  (17, 3),
  (18, 3),
  (19, 3),
  (20, 3),
  (21, 3);

INSERT INTO veterinarian (user_id, clinic_id, shift, license_no) VALUES
  (2, 1, 'MORNING', 'TVHB-30017'),
  (3, 1, 'MORNING', 'TVHB-30034'),
  (4, 1, 'EVENING', 'TVHB-30051'),
  (5, 2, 'MORNING', 'TVHB-30068'),
  (6, 2, 'EVENING', 'TVHB-30085'),
  (7, 3, 'MORNING', 'TVHB-30102'),
  (8, 3, 'MORNING', 'TVHB-30119'),
  (9, 3, 'EVENING', 'TVHB-30136'),
  (10, 4, 'MORNING', 'TVHB-30153'),
  (11, 4, 'EVENING', 'TVHB-30170'),
  (12, 5, 'MORNING', 'TVHB-30187'),
  (13, 5, 'EVENING', 'TVHB-30204');

INSERT INTO shelter (shelter_name, district_id, address, phone, capacity, latitude, longitude, partner_clinic_id) VALUES
  ('Kadıköy Municipality Animal Shelter', 19, 'Hayvan Bakımevi Cd. No:27, Kadıköy / Istanbul', '02162319675', 120, 40.985599, 29.026014, 1),
  ('Üsküdar Municipality Animal Shelter', 30, 'Hayvan Bakımevi Cd. No:17, Üsküdar / Istanbul', '02168783206', 120, 41.015196, 29.008763, 4),
  ('Beşiktaş Municipality Animal Shelter', 9, 'Hayvan Bakımevi Cd. No:19, Beşiktaş / Istanbul', '02128846710', 80, 41.06297, 29.0196, 2),
  ('Şişli Municipality Animal Shelter', 27, 'Hayvan Bakımevi Cd. No:8, Şişli / Istanbul', '02129845818', 250, 41.053032, 28.986282, 3),
  ('Fatih Municipality Animal Shelter', 17, 'Hayvan Bakımevi Cd. No:7, Fatih / Istanbul', '02124595877', 80, 41.019988, 28.930953, 5),
  ('Bakırköy Municipality Animal Shelter', 6, 'Hayvan Bakımevi Cd. No:30, Bakırköy / Istanbul', '02126543899', 120, 40.960196, 28.856725, 5),
  ('Ataşehir Municipality Animal Shelter', 2, 'Hayvan Bakımevi Cd. No:55, Ataşehir / Istanbul', '02164061027', 60, 40.985802, 29.119342, 1),
  ('Beykoz Municipality Animal Shelter', 10, 'Hayvan Bakımevi Cd. No:36, Beykoz / Istanbul', '02164632979', 60, 41.128078, 29.07927, 2);

INSERT INTO shelter_species (shelter_id, species_id) VALUES
  (1, 1),
  (2, 1),
  (2, 2),
  (3, 1),
  (3, 2),
  (4, 1),
  (4, 2),
  (5, 1),
  (6, 1),
  (6, 2),
  (7, 1),
  (7, 2),
  (8, 2);

INSERT INTO medicine (medicine_name, form) VALUES
  ('Amoxicillin', 'TABLET'),
  ('Amoxicillin-Clavulanate', 'TABLET'),
  ('Meloxicam', 'SYRUP'),
  ('Enrofloxacin', 'TABLET'),
  ('Metronidazole', 'TABLET'),
  ('Tramadol', 'TABLET'),
  ('Prednisolone', 'TABLET'),
  ('Ivermectin', 'INJECTION'),
  ('Ceftriaxone', 'INJECTION'),
  ('Ringer Lactate', 'INJECTION'),
  ('Vitamin B Complex', 'INJECTION'),
  ('Famotidine', 'TABLET'),
  ('Silver Sulfadiazine Cream', 'OINTMENT'),
  ('Gentamicin Eye Drops', 'DROPS'),
  ('Praziquantel', 'TABLET');

INSERT INTO vaccine (vaccine_code, vaccine_name) VALUES
  ('DHPP', 'Dog combo vaccine (DHPP)'),
  ('FVRCP', 'Cat combo vaccine (FVRCP)'),
  ('RABIES', 'Rabies vaccine');

-- species 1 = cat, 2 = dog / vaccine 1 = dhpp, 2 = fvrcp, 3 = rabies

INSERT INTO vaccine_rule (species_id, vaccine_id, first_dose_week, series_interval_weeks, series_last_week, booster_week, repeat_interval_weeks) VALUES
  (2, 1, 8, 3, 14, NULL, 52),
  (2, 3, 12, NULL, 12, NULL, 52),
  (1, 2, 8, 4, 16, 26, 52),
  (1, 3, 12, NULL, 12, NULL, 52);

INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date, is_neutered, status, shelter_id, description) VALUES
  ('Leo', 1, 6, 'UNKNOWN', 'Grey', 18, CURDATE() - INTERVAL 20 DAY, FALSE, 'IN_SHELTER', 1, 'Found near a park, healthy now.'),
  ('Fıstık', 1, 5, 'FEMALE', 'Black & white', 214, CURDATE() - INTERVAL 7 DAY, FALSE, 'IN_SHELTER', 1, 'Gentle, likes to be held.'),
  (NULL, 2, 7, 'MALE', 'Black & tan', 34, CURDATE() - INTERVAL 21 DAY, FALSE, 'IN_SHELTER', 2, 'Very playful, good with other animals.'),
  (NULL, 1, 3, 'UNKNOWN', 'Grey', 38, CURDATE() - INTERVAL 12 DAY, FALSE, 'IN_SHELTER', 2, 'Gentle, likes to be held.'),
  ('Simit', 1, 2, 'UNKNOWN', 'Tabby', 110, CURDATE() - INTERVAL 8 DAY, TRUE, 'IN_SHELTER', 2, 'Gentle, likes to be held.'),
  ('Şeker', 1, 3, 'MALE', 'Ginger', 20, CURDATE() - INTERVAL 26 DAY, FALSE, 'IN_SHELTER', 3, 'Energetic, needs a home with space.'),
  ('Limon', 1, 5, 'MALE', 'Black & white', 146, CURDATE() - INTERVAL 16 DAY, FALSE, 'IN_SHELTER', 3, 'A bit shy at first, loves treats.'),
  (NULL, 1, 4, 'FEMALE', 'White', 11, CURDATE() - INTERVAL 40 DAY, FALSE, 'IN_SHELTER', 3, 'Gentle, likes to be held.'),
  ('Lokum', 1, NULL, 'UNKNOWN', 'Grey', 385, CURDATE() - INTERVAL 40 DAY, TRUE, 'IN_SHELTER', 4, 'Energetic, needs a home with space.'),
  ('Bal', 2, 12, 'FEMALE', 'White', 4, CURDATE() - INTERVAL 32 DAY, FALSE, 'IN_SHELTER', 4, 'A bit shy at first, loves treats.'),
  ('Tarçın', 1, 5, 'FEMALE', 'Ginger', 172, CURDATE() - INTERVAL 23 DAY, TRUE, 'IN_SHELTER', 5, 'Energetic, needs a home with space.'),
  ('Mırmır', 1, NULL, 'UNKNOWN', 'White', 42, CURDATE() - INTERVAL 40 DAY, TRUE, 'IN_SHELTER', 5, 'Found near a park, healthy now.'),
  ('Mia', 1, NULL, 'UNKNOWN', 'Tabby', 469, CURDATE() - INTERVAL 40 DAY, TRUE, 'IN_SHELTER', 5, 'Very playful, good with other animals.'),
  ('Atlas', 2, 7, 'UNKNOWN', 'Black & tan', 5, CURDATE() - INTERVAL 36 DAY, FALSE, 'IN_SHELTER', 6, 'Friendly and calm.'),
  (NULL, 2, NULL, 'FEMALE', 'Black', 45, CURDATE() - INTERVAL 5 DAY, TRUE, 'IN_SHELTER', 6, 'Found near a park, healthy now.'),
  ('Badem', 2, 7, 'UNKNOWN', 'White', 31, CURDATE() - INTERVAL 10 DAY, FALSE, 'IN_SHELTER', 6, 'Very playful, good with other animals.'),
  ('Zeus', 2, 8, 'MALE', 'Spotted', 36, CURDATE() - INTERVAL 27 DAY, FALSE, 'IN_SHELTER', 7, 'Very playful, good with other animals.'),
  ('Zeytin', 1, 2, 'FEMALE', 'White', 68, CURDATE() - INTERVAL 1 DAY, FALSE, 'IN_SHELTER', 7, 'Gentle, likes to be held.'),
  ('Boncuk', 1, 3, 'FEMALE', 'White', 85, CURDATE() - INTERVAL 38 DAY, FALSE, 'IN_SHELTER', 7, 'A bit shy at first, loves treats.'),
  ('Kömür', 2, 10, 'FEMALE', 'Black', 16, CURDATE() - INTERVAL 22 DAY, FALSE, 'IN_SHELTER', 8, 'Found near a park, healthy now.'),
  ('Fındık', 2, NULL, 'FEMALE', 'Spotted', 7, CURDATE() - INTERVAL 37 DAY, FALSE, 'IN_SHELTER', 8, 'Very playful, good with other animals.');

-- vet01 follows the animals of clinic 1 shelters
UPDATE animal SET responsible_vet_id = 1
 WHERE shelter_id IN (SELECT shelter_id FROM shelter WHERE partner_clinic_id = 1);

-- make vaccine calendars

CALL sp_generate_vaccination_schedule(1);
CALL sp_generate_vaccination_schedule(2);
CALL sp_generate_vaccination_schedule(3);
CALL sp_generate_vaccination_schedule(4);
CALL sp_generate_vaccination_schedule(5);
CALL sp_generate_vaccination_schedule(6);
CALL sp_generate_vaccination_schedule(7);
CALL sp_generate_vaccination_schedule(8);
CALL sp_generate_vaccination_schedule(9);
CALL sp_generate_vaccination_schedule(10);
CALL sp_generate_vaccination_schedule(11);
CALL sp_generate_vaccination_schedule(12);
CALL sp_generate_vaccination_schedule(13);
CALL sp_generate_vaccination_schedule(14);
CALL sp_generate_vaccination_schedule(15);
CALL sp_generate_vaccination_schedule(16);
CALL sp_generate_vaccination_schedule(17);
CALL sp_generate_vaccination_schedule(18);
CALL sp_generate_vaccination_schedule(19);
CALL sp_generate_vaccination_schedule(20);
CALL sp_generate_vaccination_schedule(21);

-- some doses done, some late (for demo)
UPDATE vaccination_schedule SET status = 'DONE', done_date = CURDATE() - INTERVAL 2 DAY
 WHERE dose_label IN ('Catch-up dose','Dose 1') AND planned_date = CURDATE() AND MOD(animal_id, 3) = 1;
UPDATE vaccination_schedule SET planned_date = CURDATE() - INTERVAL (2 + MOD(animal_id, 6)) DAY
 WHERE dose_label IN ('Catch-up dose','Dose 1') AND status = 'PLANNED' AND planned_date = CURDATE()
   AND MOD(animal_id, 3) = 0;
DELETE FROM notification WHERE notif_type = 'VACCINE_ASSIGNED';

-- injured animal reports
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (14, 1, NULL, 'Black', 'Limping on the front left leg, cannot step on it.', 19, 40.981651, 29.034581, 1, 'MORNING', 1, NOW() - INTERVAL 35 MINUTE);
CALL sp_notify(2, 'NEW_CASE', 'New injured animal is on the way', 'Case #1: injured cat - Limping on the front left leg, cannot step on it.', 'NEW_CASE:1');
CALL sp_notify(14, 'REPORT_ASSIGNED', 'Veterinarian assigned', 'Please take the injured cat to Moda Paws Veterinary Clinic. Your vet is Dr. Fatma Çetin (morning shift).', 'REPORT_ASSIGNED:1');
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (16, 2, NULL, 'Black & tan', 'Deep cut on the back, bleeding a little.', 30, 41.029168, 29.020559, 1, 'MORNING', 1, NOW() - INTERVAL 80 MINUTE);
CALL sp_notify(2, 'NEW_CASE', 'New injured animal is on the way', 'Case #2: injured dog - Deep cut on the back, bleeding a little.', 'NEW_CASE:2');
CALL sp_notify(16, 'REPORT_ASSIGNED', 'Veterinarian assigned', 'Please take the injured dog to Moda Paws Veterinary Clinic. Your vet is Dr. Fatma Çetin (morning shift).', 'REPORT_ASSIGNED:2');
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (20, 1, NULL, 'Grey', 'Eye infection, both eyes closed and wet.', 19, 40.995066, 29.023521, 1, 'EVENING', 3, NOW() - INTERVAL 50 MINUTE);
CALL sp_notify(4, 'NEW_CASE', 'New injured animal is on the way', 'Case #3: injured cat - Eye infection, both eyes closed and wet.', 'NEW_CASE:3');
CALL sp_notify(20, 'REPORT_ASSIGNED', 'Veterinarian assigned', 'Please take the injured cat to Moda Paws Veterinary Clinic. Your vet is Dr. Kerem Demir (evening shift).', 'REPORT_ASSIGNED:3');
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (15, 2, NULL, 'Grey', 'Hit by a car, back leg injured.', 9, 41.041652, 29.008232, 2, 'MORNING', 4, NOW() - INTERVAL 300 MINUTE);
INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date, status, description) VALUES
  ('Karamel', 2, 7, 'MALE', 'White', 80, CURDATE(), 'UNDER_TREATMENT', 'Brought by a volunteer from Beşiktaş.');
UPDATE injury_report SET status = 'ARRIVED', resolved_at = NOW() - INTERVAL 260 MINUTE, resolved_by = 5, animal_id = 22 WHERE report_id = 4;
INSERT INTO treatment (animal_id, vet_id, report_id, started_at, diagnosis, condition_level, notes) VALUES
  (22, 4, 4, NOW() - INTERVAL 260 MINUTE, 'Fractured femur', 'SEVERE', 'Examined after arrival.');
INSERT INTO prescription_item (treatment_id, medicine_id, dosage, duration_days) VALUES
  (1, 9, '1 g IV, once a day', 7),
  (1, 6, '50 mg, twice a day', 5);
CALL sp_notify(15, 'REPORT_ARRIVED', 'The animal arrived at the clinic', 'The injured dog you reported arrived and is being treated by Dr. Merve Polat.', 'REPORT_ARRIVED:4');
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (17, 1, NULL, 'Grey', 'Not eating, very weak.', 27, 41.066128, 28.981403, 3, 'MORNING', 7, NOW() - INTERVAL 260 MINUTE);
INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date, status, description) VALUES
  ('Gece', 1, 1, 'FEMALE', 'Ginger', 40, CURDATE(), 'UNDER_TREATMENT', 'Brought by a volunteer from Şişli.');
UPDATE injury_report SET status = 'ARRIVED', resolved_at = NOW() - INTERVAL 220 MINUTE, resolved_by = 8, animal_id = 23 WHERE report_id = 5;
INSERT INTO treatment (animal_id, vet_id, report_id, started_at, diagnosis, condition_level, notes) VALUES
  (23, 7, 5, NOW() - INTERVAL 220 MINUTE, 'Dehydration and gastritis', 'MODERATE', 'Examined after arrival.');
INSERT INTO prescription_item (treatment_id, medicine_id, dosage, duration_days) VALUES
  (2, 10, '100 ml SC, once a day', 3),
  (2, 12, '5 mg, once a day', 5);
CALL sp_notify(17, 'REPORT_ARRIVED', 'The animal arrived at the clinic', 'The injured cat you reported arrived and is being treated by Dr. Buse Özdemir.', 'REPORT_ARRIVED:5');
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (18, 1, NULL, 'White', 'Wound on the ear, infected.', 30, 41.016088, 29.019861, 4, 'MORNING', 9, NOW() - INTERVAL 400 MINUTE);
INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date, status, description) VALUES
  ('Pati', 1, 1, 'MALE', 'Grey', 80, CURDATE(), 'UNDER_TREATMENT', 'Brought by a volunteer from Üsküdar.');
UPDATE injury_report SET status = 'ARRIVED', resolved_at = NOW() - INTERVAL 360 MINUTE, resolved_by = 10, animal_id = 24 WHERE report_id = 6;
INSERT INTO treatment (animal_id, vet_id, report_id, started_at, diagnosis, condition_level, notes) VALUES
  (24, 9, 6, NOW() - INTERVAL 360 MINUTE, 'Infected ear wound', 'MILD', 'Examined after arrival.');
INSERT INTO prescription_item (treatment_id, medicine_id, dosage, duration_days) VALUES
  (3, 2, '50 mg, twice a day', 7),
  (3, 13, 'Apply twice a day', 10);
CALL sp_notify(18, 'REPORT_ARRIVED', 'The animal arrived at the clinic', 'The injured cat you reported arrived and is being treated by Dr. Hakan Kaya.', 'REPORT_ARRIVED:6');
CALL sp_finish_treatment(3, 10, 'DISCHARGED_TO_SHELTER', 2);
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (19, 2, NULL, 'Black & tan', 'Skin problem, losing hair.', 6, 40.975329, 28.880336, 5, 'MORNING', 11, NOW() - INTERVAL 380 MINUTE);
INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date, status, description) VALUES
  ('Kuki', 2, 7, 'FEMALE', 'White', 20, CURDATE(), 'UNDER_TREATMENT', 'Brought by a volunteer from Bakırköy.');
UPDATE injury_report SET status = 'ARRIVED', resolved_at = NOW() - INTERVAL 340 MINUTE, resolved_by = 12, animal_id = 25 WHERE report_id = 7;
INSERT INTO treatment (animal_id, vet_id, report_id, started_at, diagnosis, condition_level, notes) VALUES
  (25, 11, 7, NOW() - INTERVAL 340 MINUTE, 'Mange (sarcoptic)', 'MODERATE', 'Examined after arrival.');
INSERT INTO prescription_item (treatment_id, medicine_id, dosage, duration_days) VALUES
  (4, 8, '0.2 mg/kg SC, weekly', 21);
CALL sp_notify(19, 'REPORT_ARRIVED', 'The animal arrived at the clinic', 'The injured dog you reported arrived and is being treated by Dr. Umut Yılmaz.', 'REPORT_ARRIVED:7');
CALL sp_finish_treatment(4, 12, 'DISCHARGED_TO_SHELTER', 6);
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (21, 1, NULL, 'Black', 'Kitten with a runny nose and eyes.', 19, 40.986635, 29.021869, 1, 'MORNING', 2, NOW() - INTERVAL 330 MINUTE);
INSERT INTO animal (name, species_id, breed_id, sex, color, age_weeks_at_intake, intake_date, status, description) VALUES
  ('Duman', 1, 1, 'FEMALE', 'Black & white', 40, CURDATE(), 'UNDER_TREATMENT', 'Brought by a volunteer from Kadıköy.');
UPDATE injury_report SET status = 'ARRIVED', resolved_at = NOW() - INTERVAL 290 MINUTE, resolved_by = 3, animal_id = 26 WHERE report_id = 8;
INSERT INTO treatment (animal_id, vet_id, report_id, started_at, diagnosis, condition_level, notes) VALUES
  (26, 2, 8, NOW() - INTERVAL 290 MINUTE, 'Upper respiratory infection', 'MILD', 'Examined after arrival.');
INSERT INTO prescription_item (treatment_id, medicine_id, dosage, duration_days) VALUES
  (5, 4, '5 mg/kg, once a day', 7),
  (5, 14, '1 drop, three times a day', 7);
CALL sp_notify(21, 'REPORT_ARRIVED', 'The animal arrived at the clinic', 'The injured cat you reported arrived and is being treated by Dr. Hakan Doğan.', 'REPORT_ARRIVED:8');
CALL sp_finish_treatment(5, 3, 'RELEASED', NULL);
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (16, 2, NULL, 'Grey', 'Seen limping, ran away when approached.', 9, 41.040989, 29.007995, 2, 'EVENING', 5, NOW() - INTERVAL 1560 MINUTE);
UPDATE injury_report SET status = 'NOT_ARRIVED', resolved_at = TIMESTAMP(CURDATE() - INTERVAL 1 DAY, '23:59:00'), resolved_by = NULL WHERE report_id = 9;
CALL sp_notify(16, 'REPORT_NOT_ARRIVED', 'Animal did not arrive', 'The injured dog you reported yesterday did not arrive at the clinic, so the report was closed at the end of the day.', 'REPORT_CLOSED:9');
INSERT INTO injury_report (reporter_id, species_id, approx_age_weeks, color, condition_desc, district_id, latitude, longitude, clinic_id, shift, assigned_vet_id, reported_at) VALUES
  (20, 1, NULL, 'Cream', 'Seen limping, ran away when approached.', 6, 40.983482, 28.869737, 5, 'EVENING', 12, NOW() - INTERVAL 1560 MINUTE);
UPDATE injury_report SET status = 'NOT_ARRIVED', resolved_at = TIMESTAMP(CURDATE() - INTERVAL 1 DAY, '23:59:00'), resolved_by = NULL WHERE report_id = 10;
CALL sp_notify(20, 'REPORT_NOT_ARRIVED', 'Animal did not arrive', 'The injured cat you reported yesterday did not arrive at the clinic, so the report was closed at the end of the day.', 'REPORT_CLOSED:10');

-- fix the log times
UPDATE report_status_log l JOIN injury_report r ON r.report_id = l.report_id
   SET l.changed_at = IF(l.old_status IS NULL, r.reported_at, r.resolved_at);

-- feeding posts and emojis
INSERT INTO feeding_post (user_id, latitude, longitude, photo_path, note, posted_at) VALUES
  (17, 41.064447, 28.973801, 'media/seed/post_01.jpg', NULL, NOW() - INTERVAL 529 MINUTE),
  (21, 40.928209, 29.140267, 'media/seed/post_02.jpg', 'Water bowl was empty, filled it.', NOW() - INTERVAL 390 MINUTE),
  (16, 41.026684, 29.027371, 'media/seed/post_03.jpg', NULL, NOW() - INTERVAL 569 MINUTE),
  (19, 40.969138, 28.8818, 'media/seed/post_04.jpg', 'Wet food for the kittens.', NOW() - INTERVAL 791 MINUTE),
  (14, 40.981557, 29.035907, 'media/seed/post_05.jpg', 'Dogs of the park are fed.', NOW() - INTERVAL 1205 MINUTE),
  (17, 41.046597, 28.98256, 'media/seed/post_06.jpg', 'Left dry food and fresh water.', NOW() - INTERVAL 1218 MINUTE),
  (17, 41.067515, 28.976774, 'media/seed/post_07.jpg', 'Refilled the bowl, the area is clean.', NOW() - INTERVAL 410 MINUTE),
  (16, 41.041345, 29.003255, 'media/seed/post_08.jpg', NULL, NOW() - INTERVAL 400 MINUTE),
  (21, 40.925434, 29.117598, 'media/seed/post_09.jpg', 'Left dry food and fresh water.', NOW() - INTERVAL 553 MINUTE),
  (17, 41.050943, 28.989848, 'media/seed/post_10.jpg', 'Water bowl was empty, filled it.', NOW() - INTERVAL 912 MINUTE),
  (14, 41.016269, 28.93613, 'media/seed/post_11.jpg', 'Three cats were waiting here today.', NOW() - INTERVAL 753 MINUTE),
  (16, 41.120938, 29.097191, 'media/seed/post_12.jpg', 'Water bowl was empty, filled it.', NOW() - INTERVAL 897 MINUTE);

INSERT INTO post_reaction (post_id, user_id, emoji) VALUES
  (3, 15, 'STRONG'),
  (3, 20, 'HEART'),
  (3, 18, 'PAW'),
  (5, 15, 'STRONG'),
  (5, 16, 'CLAP'),
  (6, 16, 'CLAP'),
  (7, 20, 'HEART'),
  (7, 14, 'THANKS'),
  (7, 21, 'STRONG'),
  (8, 15, 'CLAP'),
  (8, 18, 'CLAP'),
  (9, 15, 'STRONG'),
  (9, 16, 'PAW'),
  (10, 21, 'STRONG'),
  (10, 18, 'CLAP'),
  (10, 19, 'HEART'),
  (11, 18, 'THANKS'),
  (11, 17, 'THANKS'),
  (11, 16, 'THANKS'),
  (12, 17, 'PAW'),
  (12, 21, 'THANKS'),
  (12, 15, 'HEART');

UPDATE feeding_post SET posted_at = posted_at - INTERVAL 6 DAY WHERE post_id = 9;
UPDATE feeding_post SET posted_at = posted_at - INTERVAL 10 DAY WHERE post_id = 10;
UPDATE feeding_post SET posted_at = posted_at - INTERVAL 5 DAY WHERE post_id = 11;
UPDATE feeding_post SET posted_at = posted_at - INTERVAL 9 DAY WHERE post_id = 12;
UPDATE post_reaction r JOIN feeding_post p ON p.post_id = r.post_id
   SET r.reacted_at = p.posted_at + INTERVAL 2 HOUR WHERE p.posted_at < NOW() - INTERVAL 24 HOUR;
UPDATE notification n JOIN post_reaction r ON n.event_key = CONCAT('REACTION:', r.post_id, ':', r.user_id)
   SET n.message = fn_reaction_message(r.post_id, r.user_id, r.emoji), n.created_at = r.reacted_at;

-- adoption applications
INSERT INTO adoption_application (user_id, animal_id, applied_at, full_address, district_id, birth_year, housing_type, ownership, landlord_permission, household_size, has_children, has_other_pets, other_pets_note, pet_experience, hours_alone_per_day, reason, agrees_home_visit, agrees_neutering, agrees_vaccination) VALUES
  (14, 11, NOW() - INTERVAL 5 DAY, 'Example Sk. No:89 D:3, Kadıköy / Istanbul', 19, 2000, 'HOUSE_WITH_GARDEN', 'OWNER', NULL, 1, TRUE, FALSE, NULL, 'EXPERIENCED', 4, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE),
  (17, 11, NOW() - INTERVAL 4 DAY, 'Example Sk. No:60 D:11, Şişli / Istanbul', 27, 2002, 'APARTMENT', 'OWNER', NULL, 1, FALSE, FALSE, NULL, 'SOME', 6, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE),
  (15, 2, NOW() - INTERVAL 6 DAY, 'Example Sk. No:66 D:14, Beşiktaş / Istanbul', 9, 1990, 'APARTMENT', 'TENANT', TRUE, 4, TRUE, FALSE, NULL, 'SOME', 6, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE),
  (18, 16, NOW() - INTERVAL 3 DAY, 'Example Sk. No:36 D:4, Fatih / Istanbul', 17, 2002, 'APARTMENT', 'OWNER', NULL, 1, FALSE, TRUE, NULL, 'NONE', 10, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE),
  (16, 18, NOW() - INTERVAL 1 DAY, 'Example Sk. No:42 D:19, Üsküdar / Istanbul', 30, 1990, 'DETACHED_HOUSE', 'OWNER', NULL, 2, TRUE, FALSE, NULL, 'EXPERIENCED', 6, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE),
  (20, 1, NOW() - INTERVAL 0 DAY, 'Example Sk. No:2 D:10, Ataşehir / Istanbul', 2, 1985, 'APARTMENT', 'TENANT', TRUE, 5, FALSE, FALSE, NULL, 'SOME', 8, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE),
  (21, 1, NOW() - INTERVAL 0 DAY, 'Example Sk. No:36 D:15, Maltepe / Istanbul', 23, 1996, 'APARTMENT', 'OWNER', NULL, 1, FALSE, TRUE, NULL, 'SOME', 5, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE),
  (19, 14, NOW() - INTERVAL 2 DAY, 'Example Sk. No:35 D:13, Bakırköy / Istanbul', 6, 1980, 'HOUSE_WITH_GARDEN', 'OWNER', NULL, 2, TRUE, TRUE, NULL, 'EXPERIENCED', 3, 'I have been volunteering for a long time and I want to give this animal a warm home.', TRUE, TRUE, TRUE);

CALL sp_approve_application(1, 1, 'Great home with a garden. Welcome!');
CALL sp_approve_application(3, 1, 'Landlord permission checked by phone.');
CALL sp_reject_application(4, 1, 'The animal would stay alone more than 8 hours a day.');
UPDATE adoption SET adopted_at = NOW() - INTERVAL 2 DAY;
UPDATE adoption_application SET reviewed_at = applied_at + INTERVAL 1 DAY WHERE status <> 'PENDING';

-- mark some notifications as read
UPDATE notification SET is_read = TRUE WHERE notif_type IN ('REACTION') AND MOD(notification_id, 2) = 0;

