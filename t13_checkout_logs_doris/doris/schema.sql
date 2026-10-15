-- Copyright 2026 Tabsdata Inc.
--
-- tables the doris subscribers load into, python tabsdata/run.py doris creates
-- the database from creds.json and runs this file in it. to run it by hand:
--   mysql -h 127.0.0.1 -P 9030 -u root -e "CREATE DATABASE IF NOT EXISTS checkout_logs"
--   mysql -h 127.0.0.1 -P 9030 -u root checkout_logs < doris/schema.sql
--
-- replication_num is 1 for a single backend, use 3 on a real cluster

-- every log line from every source in the common event model, duplicate key
-- since logs are append only, partitioned by day with the time series
-- compaction policy doris recommends for logs, the inverted index on message
-- is what MATCH_ANY, MATCH_ALL and MATCH_PHRASE search
CREATE TABLE IF NOT EXISTS log_events (
    event_time   DATETIME(3)  NOT NULL COMMENT 'when the event happened, UTC',
    source       VARCHAR(16)  NOT NULL COMMENT 'frontend, gateway, services, payments or infra',
    service      VARCHAR(64)  NULL,
    host         VARCHAR(128) NULL,
    level        VARCHAR(8)   NULL COMMENT 'INFO, WARN or ERROR',
    event        VARCHAR(64)  NULL,
    request_id   VARCHAR(64)  NULL,
    user_id      BIGINT       NULL,
    http_status  INT          NULL,
    duration_ms  DOUBLE       NULL,
    message      STRING       NULL,
    event_id     VARCHAR(96)  NULL,
    INDEX idx_message (message) USING INVERTED PROPERTIES ("parser" = "english", "support_phrase" = "true"),
    INDEX idx_request_id (request_id) USING INVERTED,
    INDEX idx_service (service) USING INVERTED,
    INDEX idx_event (event) USING INVERTED,
    INDEX idx_level (level) USING INVERTED
)
DUPLICATE KEY (event_time, source)
AUTO PARTITION BY RANGE (date_trunc(event_time, 'day')) ()
DISTRIBUTED BY RANDOM BUCKETS AUTO
PROPERTIES (
    "replication_num" = "1",
    "compaction_policy" = "time_series"
);

-- one row per checkout correlated across the sources, unique key so each
-- request appears once, replaced on every load
CREATE TABLE IF NOT EXISTS checkout_requests (
    request_id     VARCHAR(64)  NOT NULL,
    user_id        BIGINT       NULL,
    started_at     DATETIME(3)  NULL,
    ended_at       DATETIME(3)  NULL,
    outcome        VARCHAR(32)  NULL COMMENT 'completed, charged_without_order, payment_declined or failed_before_payment',
    http_status    INT          NULL,
    amount_usd     DOUBLE       NULL,
    events         INT          NULL,
    services       INT          NULL,
    error_message  STRING       NULL,
    INDEX idx_error_message (error_message) USING INVERTED PROPERTIES ("parser" = "english", "support_phrase" = "true")
)
UNIQUE KEY (request_id)
DISTRIBUTED BY HASH (request_id) BUCKETS 1
PROPERTIES (
    "replication_num" = "1"
);
