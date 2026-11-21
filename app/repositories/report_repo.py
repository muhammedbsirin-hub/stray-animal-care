"""Read-only statistics for the admin screens."""
from app import db


class ReportRepository:

    @staticmethod
    def overview():
        return db.query_one("""
            SELECT (SELECT COUNT(*) FROM animal WHERE status = 'IN_SHELTER')            AS in_shelters,
                   (SELECT COUNT(*) FROM animal WHERE status = 'UNDER_TREATMENT')       AS under_treatment,
                   (SELECT COUNT(*) FROM adoption_application WHERE status = 'PENDING') AS pending_applications,
                   (SELECT COUNT(*) FROM injury_report WHERE status = 'PENDING')        AS open_cases,
                   (SELECT COUNT(*) FROM v_active_feeding_posts)                        AS posts_24h,
                   (SELECT COUNT(*) FROM adoption)                                      AS adoptions,
                   (SELECT COUNT(*) FROM v_vaccination_due WHERE due_state = 'OVERDUE') AS overdue_vaccines,
                   (SELECT COUNT(*) FROM user_account u JOIN user_role ur ON ur.user_id = u.user_id
                     JOIN role r ON r.role_id = ur.role_id
                     WHERE r.role_name = 'VOLUNTEER' AND u.is_active)                   AS volunteers""")

    @staticmethod
    def vet_daily_stats(days_back):
        """days_back = 0 -> today, 1 -> yesterday only, 7 -> last 7 days (summed)."""
        if days_back == 1:
            cond, params = "day = CURDATE() - INTERVAL 1 DAY", ()
        else:
            cond, params = "day >= CURDATE() - INTERVAL %s DAY", (days_back,)
        return db.query(f"""SELECT vet_id, vet_name, clinic_name, shift, SUM(arrived) AS arrived,
                                   SUM(not_arrived) AS not_arrived, SUM(discharged) AS discharged
                              FROM v_vet_daily_stats WHERE {cond}
                             GROUP BY vet_id, vet_name, clinic_name, shift
                             ORDER BY discharged DESC, arrived DESC""", params)

    @staticmethod
    def active_treatments():
        return db.query("SELECT * FROM v_active_treatments ORDER BY started_at")

    @staticmethod
    def case_log(days_back):
        if days_back == 1:
            cond, params = "DATE(l.changed_at) = CURDATE() - INTERVAL 1 DAY", ()
        else:
            cond, params = "DATE(l.changed_at) >= CURDATE() - INTERVAL %s DAY", (days_back,)
        return db.query(f"""SELECT l.changed_at, l.report_id, l.old_status, l.new_status,
                                   COALESCE(u.username, 'system') AS changed_by, c.clinic_name
                              FROM report_status_log l
                              JOIN injury_report r ON r.report_id = l.report_id
                              JOIN clinic c ON c.clinic_id = r.clinic_id
                              LEFT JOIN user_account u ON u.user_id = l.changed_by
                             WHERE {cond} ORDER BY l.changed_at DESC""", params)
