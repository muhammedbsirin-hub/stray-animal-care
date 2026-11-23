-- run once as root, creates the user of the app (same password as .env)
CREATE USER IF NOT EXISTS 'stray_app'@'localhost' IDENTIFIED BY 'cWbTFvJSEpHE9mVVLK_Sa1';
GRANT ALL PRIVILEGES ON stray_db.* TO 'stray_app'@'localhost';
-- so stray_app can make functions and triggers
SET PERSIST log_bin_trust_function_creators = 1;
-- turn on events (for ev_close_day)
SET PERSIST event_scheduler = ON;
FLUSH PRIVILEGES;
