-- example queries for the report
USE stray_db;

-- 1) overdue vaccinations per shelter (join + group by)
SELECT shelter_name, COUNT(*) AS overdue_doses
  FROM v_vaccination_due
 WHERE due_state = 'OVERDUE'
 GROUP BY shelter_name
 ORDER BY overdue_doses DESC;

-- 2) shelter animals that have no completed vaccination yet (not exists)
SELECT a.animal_id, a.display_name, a.species_name, a.shelter_name
  FROM v_animal_card a
 WHERE a.status = 'IN_SHELTER'
   AND NOT EXISTS (SELECT 1 FROM vaccination_schedule s WHERE s.animal_id = a.animal_id AND s.status = 'DONE');

-- 3) top 5 volunteers by feeding posts in the last 30 days (aggregate + limit)
SELECT u.username, COUNT(*) AS posts
  FROM feeding_post p JOIN user_account u ON u.user_id = p.user_id
 WHERE p.posted_at >= NOW() - INTERVAL 30 DAY AND p.is_deleted = FALSE
 GROUP BY u.username
 ORDER BY posts DESC
 LIMIT 5;

-- 4) volunteers who received the most emojis, with the favourite emoji (subquery)
SELECT u.username, COUNT(*) AS emojis_received,
       (SELECT r2.emoji FROM post_reaction r2 JOIN feeding_post p2 ON p2.post_id = r2.post_id
         WHERE p2.user_id = u.user_id GROUP BY r2.emoji ORDER BY COUNT(*) DESC LIMIT 1) AS favourite
  FROM post_reaction r
  JOIN feeding_post p ON p.post_id = r.post_id
  JOIN user_account u ON u.user_id = p.user_id
 GROUP BY u.user_id, u.username
 ORDER BY emojis_received DESC;

-- 5) animals that received more than one adoption application (having)
SELECT ac.display_name, ac.shelter_name, COUNT(*) AS applications
  FROM adoption_application ap JOIN v_animal_card ac ON ac.animal_id = ap.animal_id
 GROUP BY ap.animal_id, ac.display_name, ac.shelter_name
HAVING COUNT(*) > 1;

-- 6) average days between application and decision (aggregate on dates)
SELECT status, ROUND(AVG(DATEDIFF(reviewed_at, applied_at)), 1) AS avg_days, COUNT(*) AS n
  FROM adoption_application
 WHERE reviewed_at IS NOT NULL
 GROUP BY status;

-- 7) clinics with their morning / evening vet counts (conditional aggregation)
SELECT c.clinic_name,
       SUM(v.shift = 'MORNING') AS morning_vets,
       SUM(v.shift = 'EVENING') AS evening_vets,
       COUNT(*) AS total
  FROM clinic c JOIN veterinarian v ON v.clinic_id = c.clinic_id
 GROUP BY c.clinic_id, c.clinic_name
 ORDER BY total DESC;

-- 8) injury cases per clinic and result (group by two columns)
SELECT c.clinic_name, r.status, COUNT(*) AS cases
  FROM injury_report r JOIN clinic c ON c.clinic_id = r.clinic_id
 GROUP BY c.clinic_name, r.status
 ORDER BY c.clinic_name;

-- 9) shelters that accept cats but have no cat right now (in + not in)
SELECT s.shelter_name
  FROM shelter s
 WHERE s.shelter_id IN (SELECT shelter_id FROM shelter_species WHERE species_id = 1)
   AND s.shelter_id NOT IN (SELECT shelter_id FROM animal WHERE species_id = 1 AND status = 'IN_SHELTER'
                                                            AND shelter_id IS NOT NULL);

-- 10) medicines used most in prescriptions
SELECT m.medicine_name, COUNT(*) AS times_prescribed, ROUND(AVG(p.duration_days), 1) AS avg_days
  FROM prescription_item p JOIN medicine m ON m.medicine_id = p.medicine_id
 GROUP BY m.medicine_name
 ORDER BY times_prescribed DESC;

-- 11) age labels of shelter animals (stored function)
SELECT display_name, species_name, age_weeks, fn_age_label(age_weeks) AS age
  FROM v_animal_card WHERE status = 'IN_SHELTER' ORDER BY age_weeks LIMIT 15;

-- 12) full history of one injury case from the transaction log
SELECT l.changed_at, l.old_status, l.new_status, COALESCE(u.username, 'system') AS by_user
  FROM report_status_log l LEFT JOIN user_account u ON u.user_id = l.changed_by
 WHERE l.report_id = 4 ORDER BY l.changed_at;
