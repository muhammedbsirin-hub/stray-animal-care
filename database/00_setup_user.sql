-- =====================================================================
-- 00_setup_user.sql  --  RUN ONCE AS root IN MYSQL WORKBENCH
-- Creates the application user for the Stray Animal Care project.
-- This is a LOCAL DEVELOPMENT account; the same password is in .env
-- =====================================================================
CREATE USER IF NOT EXISTS 'stray_app'@'localhost' IDENTIFIED BY 'cWbTFvJSEpHE9mVVLK_Sa1';
GRANT ALL PRIVILEGES ON stray_db.* TO 'stray_app'@'localhost';
-- needed so a non-root user can create stored functions / triggers
SET PERSIST log_bin_trust_function_creators = 1;
-- needed for the daily end-of-day EVENT
SET PERSIST event_scheduler = ON;
FLUSH PRIVILEGES;
