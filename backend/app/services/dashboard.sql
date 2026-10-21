-- Dashboard queries. Each query starts with a "-- name:" line; dashboard.py runs them by name.
--
-- Every query accepts the same four filters. An empty filter ('') means "don't filter":
--   :doc_type   document type key, e.g. 'brd'
--   :project    project name
--   :date_from  'YYYY-MM-DD'  (on the date a review finished, or a document was uploaded)
--   :date_to    'YYYY-MM-DD'
--
-- Tables used:
--   documents          one row per document (title, type, project, who uploaded it)
--   document_versions  one row per uploaded file (version 1, 2, 3 ...)
--   reviews            one row per review of a version (status, score, passed)
--   rule_results       one row per rule per review (met / partially_met / not_met)
--   document_types     BRD, FRD, ... and custom types


-- name: review_summary
-- How many reviews finished, how many passed, and the average score.
SELECT
    COUNT(*)                                   AS reviews_completed,
    SUM(CASE WHEN r.passed THEN 1 ELSE 0 END)  AS reviews_passed,
    ROUND(AVG(r.score), 1)                     AS average_score
FROM reviews r
JOIN document_versions v ON v.id = r.document_version_id
JOIN documents d         ON d.id = v.document_id
JOIN document_types dt   ON dt.id = d.document_type_id
WHERE r.status = 'complete'
  AND (:doc_type = ''  OR dt.key = :doc_type)
  AND (:project = ''   OR d.project_name = :project)
  AND (:date_from = '' OR DATE(r.completed_at) >= :date_from)
  AND (:date_to = ''   OR DATE(r.completed_at) <= :date_to);


-- name: document_statuses
-- How many documents are Passed, Failed, Corrected, In review or Error right now.
-- Same rules as the Documents page:
--   look at each version's most recent review, then
--   Failed     = the latest version failed
--   Corrected  = the latest version passed and an earlier version failed
--   Passed     = the latest version passed and no earlier version failed
WITH latest_review_per_version AS (
    SELECT v.document_id, v.version_number, r.status, r.passed
    FROM document_versions v
    JOIN reviews r ON r.document_version_id = v.id
    WHERE r.id = (SELECT MAX(r2.id) FROM reviews r2 WHERE r2.document_version_id = v.id)
),
latest_version AS (
    SELECT document_id, MAX(version_number) AS version_number
    FROM latest_review_per_version
    GROUP BY document_id
),
document_status AS (
    SELECT
        d.id,
        CASE
            WHEN now.status IN ('queued', 'processing') THEN 'In review'
            WHEN now.status = 'error' THEN 'Error'
            WHEN NOT now.passed THEN 'Failed'
            WHEN EXISTS (
                SELECT 1 FROM latest_review_per_version earlier
                WHERE earlier.document_id = d.id
                  AND earlier.version_number < now.version_number
                  AND earlier.status = 'complete'
                  AND NOT earlier.passed
            ) THEN 'Corrected'
            ELSE 'Passed'
        END AS status
    FROM documents d
    JOIN document_types dt            ON dt.id = d.document_type_id
    JOIN latest_version lv            ON lv.document_id = d.id
    JOIN latest_review_per_version now ON now.document_id = d.id AND now.version_number = lv.version_number
    WHERE (:doc_type = ''  OR dt.key = :doc_type)
      AND (:project = ''   OR d.project_name = :project)
      AND (:date_from = '' OR DATE(d.created_at) >= :date_from)
      AND (:date_to = ''   OR DATE(d.created_at) <= :date_to)
)
SELECT status, COUNT(*) AS documents
FROM document_status
GROUP BY status;


-- name: pass_fail_by_type
-- Passed and failed reviews for each document type (grouped bar chart).
SELECT
    dt.display_name                                AS document_type,
    SUM(CASE WHEN r.passed THEN 1 ELSE 0 END)      AS passed,
    SUM(CASE WHEN NOT r.passed THEN 1 ELSE 0 END)  AS failed
FROM reviews r
JOIN document_versions v ON v.id = r.document_version_id
JOIN documents d         ON d.id = v.document_id
JOIN document_types dt   ON dt.id = d.document_type_id
WHERE r.status = 'complete'
  AND (:doc_type = ''  OR dt.key = :doc_type)
  AND (:project = ''   OR d.project_name = :project)
  AND (:date_from = '' OR DATE(r.completed_at) >= :date_from)
  AND (:date_to = ''   OR DATE(r.completed_at) <= :date_to)
GROUP BY dt.display_name
ORDER BY dt.display_name;


-- name: reviews_per_day
-- Reviews and passes per day. dashboard.py adds the days up into weeks for the trend chart
-- (done in Python because "start of the week" is written differently in SQLite and PostgreSQL).
SELECT
    DATE(r.completed_at)                       AS day,
    COUNT(*)                                   AS reviews,
    SUM(CASE WHEN r.passed THEN 1 ELSE 0 END)  AS passed
FROM reviews r
JOIN document_versions v ON v.id = r.document_version_id
JOIN documents d         ON d.id = v.document_id
JOIN document_types dt   ON dt.id = d.document_type_id
WHERE r.status = 'complete'
  AND (:doc_type = ''  OR dt.key = :doc_type)
  AND (:project = ''   OR d.project_name = :project)
  AND (:date_from = '' OR DATE(r.completed_at) >= :date_from)
  AND (:date_to = ''   OR DATE(r.completed_at) <= :date_to)
GROUP BY DATE(r.completed_at)
ORDER BY day;


-- name: score_distribution
-- How many reviews scored 0-9, 10-19, ... 90-100 (a score of 100 goes in the 90-100 bucket).
SELECT
    CASE WHEN r.score = 100 THEN 9 ELSE r.score / 10 END  AS bucket,
    COUNT(*)                                              AS reviews
FROM reviews r
JOIN document_versions v ON v.id = r.document_version_id
JOIN documents d         ON d.id = v.document_id
JOIN document_types dt   ON dt.id = d.document_type_id
WHERE r.status = 'complete'
  AND (:doc_type = ''  OR dt.key = :doc_type)
  AND (:project = ''   OR d.project_name = :project)
  AND (:date_from = '' OR DATE(r.completed_at) >= :date_from)
  AND (:date_to = ''   OR DATE(r.completed_at) <= :date_to)
GROUP BY CASE WHEN r.score = 100 THEN 9 ELSE r.score / 10 END
ORDER BY bucket;


-- name: top_failed_rules
-- The 10 rules most often "Not Met" (Partially Met isn't counted).
SELECT
    rr.rule_id,
    rr.rule_title,
    dt.display_name  AS document_type,
    COUNT(*)         AS times_not_met
FROM rule_results rr
JOIN reviews r           ON r.id = rr.review_id
JOIN document_versions v ON v.id = r.document_version_id
JOIN documents d         ON d.id = v.document_id
JOIN document_types dt   ON dt.id = d.document_type_id
WHERE rr.status = 'not_met'
  AND r.status = 'complete'
  AND (:doc_type = ''  OR dt.key = :doc_type)
  AND (:project = ''   OR d.project_name = :project)
  AND (:date_from = '' OR DATE(r.completed_at) >= :date_from)
  AND (:date_to = ''   OR DATE(r.completed_at) <= :date_to)
GROUP BY rr.rule_id, rr.rule_title, dt.display_name
ORDER BY times_not_met DESC, rr.rule_id
LIMIT 10;


-- name: documents_failing_rule
-- The documents behind one bar of the chart above: reviews where :rule_id was Not Met.
SELECT
    d.id             AS document_id,
    d.title,
    d.project_name,
    v.version_number,
    r.id             AS review_id,
    r.score,
    r.completed_at
FROM rule_results rr
JOIN reviews r           ON r.id = rr.review_id
JOIN document_versions v ON v.id = r.document_version_id
JOIN documents d         ON d.id = v.document_id
JOIN document_types dt   ON dt.id = d.document_type_id
WHERE rr.rule_id = :rule_id
  AND rr.status = 'not_met'
  AND r.status = 'complete'
  AND (:doc_type = ''  OR dt.key = :doc_type)
  AND (:project = ''   OR d.project_name = :project)
  AND (:date_from = '' OR DATE(r.completed_at) >= :date_from)
  AND (:date_to = ''   OR DATE(r.completed_at) <= :date_to)
ORDER BY r.completed_at DESC;


-- name: recent_reviews
-- The 10 most recent reviews, whatever their status.
SELECT
    r.id             AS review_id,
    d.id             AS document_id,
    d.title,
    dt.display_name  AS document_type,
    v.version_number,
    r.status,
    r.score,
    r.passed,
    r.created_at
FROM reviews r
JOIN document_versions v ON v.id = r.document_version_id
JOIN documents d         ON d.id = v.document_id
JOIN document_types dt   ON dt.id = d.document_type_id
WHERE (:doc_type = ''  OR dt.key = :doc_type)
  AND (:project = ''   OR d.project_name = :project)
  AND (:date_from = '' OR DATE(r.created_at) >= :date_from)
  AND (:date_to = ''   OR DATE(r.created_at) <= :date_to)
ORDER BY r.created_at DESC, r.id DESC
LIMIT 10;
