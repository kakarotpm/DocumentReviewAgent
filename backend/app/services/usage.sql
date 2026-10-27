-- Usage Analytics queries. Each query starts with a "-- name:" line; usage.py runs them by name.
--
-- Every query accepts the same two filters. An empty filter ('') means "don't filter":
--   :date_from  'YYYY-MM-DD'  (the day the AI call was made)
--   :date_to    'YYYY-MM-DD'
--
-- Tables used:
--   ai_usage      one row per AI call: model, purpose, tokens, and its cost when it was made
--   model_prices  US dollars per 1 million tokens, per model (edited on the Usage Analytics page)
--
-- How cost works:
--   Each call's cost is saved when the call is made, using that day's price (ai_usage.cost_usd),
--   so changing a price later doesn't rewrite past spending.
--   If no price was set for the model at the time (cost_usd is empty), today's price is used instead.
--   If there's still no price, the call's cost is unknown (NULL) and is counted in unpriced_calls.
--
--   cost = (input tokens - cached input tokens) x input price
--        + cached input tokens                  x cached input price
--        + output tokens                        x output price
--          (all divided by 1,000,000, because prices are per million tokens)
--
-- Each query starts with the same "priced_usage" step: the filtered calls, each with its cost.


-- name: usage_summary
-- Totals for the summary cards.
WITH priced_usage AS (
    SELECT
        u.*,
        COALESCE(
            u.cost_usd,
            ((u.input_tokens - u.cached_input_tokens) * p.input_per_million
             + u.cached_input_tokens * p.cached_input_per_million
             + u.output_tokens * p.output_per_million) / 1000000.0
        ) AS cost
    FROM ai_usage u
    LEFT JOIN model_prices p ON p.model = u.model
    WHERE (:date_from = '' OR DATE(u.created_at) >= :date_from)
      AND (:date_to = ''   OR DATE(u.created_at) <= :date_to)
)
SELECT
    COUNT(*)                                                  AS calls,
    COALESCE(SUM(input_tokens), 0)                            AS input_tokens,
    COALESCE(SUM(cached_input_tokens), 0)                     AS cached_input_tokens,
    COALESCE(SUM(output_tokens), 0)                           AS output_tokens,
    SUM(cost)                                                 AS cost,
    SUM(CASE WHEN cost IS NULL THEN 1 ELSE 0 END)             AS unpriced_calls,
    COUNT(DISTINCT review_id)                                 AS reviews,
    SUM(CASE WHEN review_id IS NOT NULL THEN cost END)        AS review_cost
FROM priced_usage;


-- name: usage_per_day
-- Tokens and cost per day. usage.py adds the days up into weeks or months for the trend chart.
WITH priced_usage AS (
    SELECT
        u.*,
        COALESCE(
            u.cost_usd,
            ((u.input_tokens - u.cached_input_tokens) * p.input_per_million
             + u.cached_input_tokens * p.cached_input_per_million
             + u.output_tokens * p.output_per_million) / 1000000.0
        ) AS cost
    FROM ai_usage u
    LEFT JOIN model_prices p ON p.model = u.model
    WHERE (:date_from = '' OR DATE(u.created_at) >= :date_from)
      AND (:date_to = ''   OR DATE(u.created_at) <= :date_to)
)
SELECT
    DATE(created_at)                        AS day,
    COUNT(*)                                AS calls,
    SUM(input_tokens + output_tokens)       AS tokens,
    COALESCE(SUM(cost), 0)                  AS cost
FROM priced_usage
GROUP BY DATE(created_at)
ORDER BY day;


-- name: usage_by_model
-- One row per model: calls, tokens and cost. has_price = 0 means no price is set for it yet.
WITH priced_usage AS (
    SELECT
        u.*,
        COALESCE(
            u.cost_usd,
            ((u.input_tokens - u.cached_input_tokens) * p.input_per_million
             + u.cached_input_tokens * p.cached_input_per_million
             + u.output_tokens * p.output_per_million) / 1000000.0
        ) AS cost,
        CASE WHEN p.id IS NULL THEN 0 ELSE 1 END AS has_price
    FROM ai_usage u
    LEFT JOIN model_prices p ON p.model = u.model
    WHERE (:date_from = '' OR DATE(u.created_at) >= :date_from)
      AND (:date_to = ''   OR DATE(u.created_at) <= :date_to)
)
SELECT
    provider,
    model,
    COUNT(*)                     AS calls,
    SUM(input_tokens)            AS input_tokens,
    SUM(cached_input_tokens)     AS cached_input_tokens,
    SUM(output_tokens)           AS output_tokens,
    SUM(cost)                    AS cost,
    MAX(has_price)               AS has_price
FROM priced_usage
GROUP BY provider, model
ORDER BY cost DESC, calls DESC;


-- name: usage_by_purpose
-- One row per purpose: document reviews, workbook reviews, drafting a new type, drafting one rule.
WITH priced_usage AS (
    SELECT
        u.*,
        COALESCE(
            u.cost_usd,
            ((u.input_tokens - u.cached_input_tokens) * p.input_per_million
             + u.cached_input_tokens * p.cached_input_per_million
             + u.output_tokens * p.output_per_million) / 1000000.0
        ) AS cost
    FROM ai_usage u
    LEFT JOIN model_prices p ON p.model = u.model
    WHERE (:date_from = '' OR DATE(u.created_at) >= :date_from)
      AND (:date_to = ''   OR DATE(u.created_at) <= :date_to)
)
SELECT
    purpose,
    COUNT(*)                            AS calls,
    SUM(input_tokens + output_tokens)   AS tokens,
    SUM(cost)                           AS cost
FROM priced_usage
GROUP BY purpose
ORDER BY cost DESC, calls DESC;
