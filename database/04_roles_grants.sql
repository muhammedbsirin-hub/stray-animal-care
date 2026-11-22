-- =====================================================================
-- 04_roles_grants.sql  (OPTIONAL - run as root)
-- Shows that the privileges of the application roles can also be
-- defined inside MySQL.  The desktop app itself connects with one
-- account (stray_app) and checks the role of the signed-in user.
-- =====================================================================
USE stray_db;

DROP ROLE IF EXISTS 'r_admin', 'r_vet', 'r_volunteer';
CREATE ROLE 'r_admin', 'r_vet', 'r_volunteer';

-- administrator: everything in the database
GRANT ALL PRIVILEGES ON stray_db.* TO 'r_admin';

-- veterinarian: reads everything, writes cases, treatments and vaccinations
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

-- volunteer: own posts, emojis, reports and applications
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
