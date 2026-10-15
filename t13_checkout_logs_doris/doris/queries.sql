-- Copyright 2026 Tabsdata Inc.
--
-- investigation of the support ticket "I tried to check out at 2:14 PM, got
-- charged, but the order never completed", in the order an engineer would run
-- them. times are UTC

-- 1. everything customer 48291 did around 14:14, across every source
SELECT event_time, source, service, level, event, message
FROM log_events
WHERE user_id = 48291
  AND event_time BETWEEN '2026-09-30 14:10:00' AND '2026-09-30 14:20:00'
ORDER BY event_time;

-- 2. whether it's more than one customer, errors per service
SELECT service, count(*) AS errors
FROM log_events
WHERE level = 'ERROR'
GROUP BY service
ORDER BY errors DESC;

-- 3. full text search for the error across every source, the database log
--    shows up next to the service logs even though it has no request id
SELECT event_time, source, service, message
FROM log_events
WHERE message MATCH_ANY 'timeout'
ORDER BY event_time
LIMIT 20;

-- 4. search and aggregation together, statement timeouts per minute
SELECT date_trunc(event_time, 'minute') AS minute, service, count(*) AS timeouts
FROM log_events
WHERE message MATCH_PHRASE 'statement timeout'
GROUP BY 1, 2
ORDER BY 1, 2;

-- 5. what started right before the first timeout
SELECT event_time, source, service, host, event, message
FROM log_events
WHERE event_time BETWEEN '2026-09-30 14:08:00' AND '2026-09-30 14:08:35'
  AND (source = 'infra' OR event LIKE 'migration%')
ORDER BY event_time;

-- 6. the migration from start to finish
SELECT event_time, source, service, message
FROM log_events
WHERE message MATCH_ANY 'migration'
   OR message MATCH_PHRASE 'create index'
ORDER BY event_time;

-- 7. blast radius, every checkout charged without an order
SELECT count(*) AS checkouts,
       count(DISTINCT user_id) AS customers,
       round(sum(amount_usd), 2) AS charged_usd,
       min(started_at) AS first_seen,
       max(started_at) AS last_seen
FROM checkout_requests
WHERE outcome = 'charged_without_order';

-- 8. the refund list, the charge id comes from the checkout service log of
--    each request
SELECT r.started_at, r.user_id, r.request_id, r.amount_usd,
       regexp_extract(e.message, 'charge (ch_[A-Za-z0-9]+)', 1) AS charge_id
FROM checkout_requests r
JOIN log_events e ON e.request_id = r.request_id AND e.event = 'payment_captured'
WHERE r.outcome = 'charged_without_order'
ORDER BY r.started_at;

-- 9. checkout outcomes per hour, the incident next to normal declines
SELECT date_trunc(started_at, 'hour') AS hour, outcome, count(*) AS checkouts
FROM checkout_requests
GROUP BY 1, 2
ORDER BY 1, 2;
