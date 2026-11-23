-- optional, run as root. roles in mysql (app itself uses stray_app)
USE stray_db;

DROP ROLE IF EXISTS 'r_admin', 'r_vet', 'r_volunteer';
CREATE ROLE 'r_admin', 'r_vet', 'r_volunteer';

-- admin
GRANT ALL PRIVILEGES ON stray_db.* TO 'r_admin';

-- vet
GRANT SELECT ON stray_db.* TO 'r_vet';
GRANT INSERT, UPDATE ON stray_db.animal               TO 'r_vet';
GRANT INSERT, UPDATE ON stray_db.treatment            TO 'r_vet';
GRANT INSERT, DELETE ON stray_db.prescription_item    TO 'r_vet';
GRANT UPDATE         ON stray_db.injury_report        TO 'r_vet';
GRANT UPDATE         ON stray_db.vaccination_schedule TO 'r_vet';
GRANT EXECUTE ON PROCEDURE stray_db.sp_report_not_arrived   TO 'r_vet';
GRANT EXECUTE ON PROCEDURE stray_db.sp_finish_treatment     TO 'r_vet';
GRANT EXECUTE ON PROCEDURE stray_db.sp_complete_vaccination TO 'r_vet';
GRANT EXECUTE ON PROCEDURE stray_db.sp_undo_vaccination     TO 'r_vet';

-- volunteer
GRANT SELECT ON stray_db.v_active_feeding_posts TO 'r_volunteer';
GRANT SELECT ON stray_db.v_shelter_summary      TO 'r_volunteer';
GRANT SELECT ON stray_db.v_animal_card          TO 'r_volunteer';
GRANT SELECT, INSERT, UPDATE ON stray_db.feeding_post          TO 'r_volunteer';
GRANT SELECT, INSERT, UPDATE, DELETE ON stray_db.post_reaction TO 'r_volunteer';
GRANT SELECT, INSERT, UPDATE ON stray_db.adoption_application  TO 'r_volunteer';
GRANT SELECT, UPDATE, DELETE ON stray_db.notification          TO 'r_volunteer';
GRANT EXECUTE ON PROCEDURE stray_db.sp_create_injury_report    TO 'r_volunteer';
GRANT EXECUTE ON PROCEDURE stray_db.sp_delete_account          TO 'r_volunteer';

SHOW GRANTS FOR 'r_vet';
