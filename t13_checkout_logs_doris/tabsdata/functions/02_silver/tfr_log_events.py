#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, TableFramesSpec, TablesTrigger, transformer
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col, concat, lit
from tabsdatak.tableframe.grok import ColumnDefinition

# common event model every source is normalized into, same columns as the
# log_events table in doris
EVENT_SCHEMA = {
    "event_time": td_types.Datetime("ms"),
    "source": td_types.String,
    "service": td_types.String,
    "host": td_types.String,
    "level": td_types.String,
    "event": td_types.String,
    "request_id": td_types.String,
    "user_id": td_types.Int64,
    "http_status": td_types.Int32,
    "duration_ms": td_types.Float64,
    "message": td_types.String,
    "event_id": td_types.String,
}

# grok pattern for the nginx access log lines with the request id and user id
# the gateway appends
GATEWAY_LINE = (
    r'%{IPORHOST:client_ip} - %{NOTSPACE:remote_user} \[%{HTTPDATE:time}\] '
    r'"%{WORD:method} %{NOTSPACE:path} HTTP/%{NUMBER:http_version}" %{INT:status} %{INT:bytes} '
    r'"%{DATA:referrer}" "%{DATA:user_agent}" rt=%{NUMBER:rt} req_id=%{NOTSPACE:req_id} uid=%{NOTSPACE:uid}'
)
GATEWAY_FIELDS = {
    "time": ColumnDefinition("time"),
    "method": ColumnDefinition("method"),
    "path": ColumnDefinition("path"),
    "status": ColumnDefinition("status", td_types.Int32),
    "rt": ColumnDefinition("rt", td_types.Float64),
    "req_id": ColumnDefinition("req_id"),
    "uid": ColumnDefinition("uid"),
}

# grok pattern for the rds postgres log prefix of time, client, user@db and pid
POSTGRES_LINE = r"%{DATA:pg_time} UTC:%{DATA:client}:%{DATA:db_user}@%{DATA:db_name}:\[%{INT:pid}\]:%{WORD:severity}:  %{GREEDYDATA:text}"
POSTGRES_FIELDS = {"severity": ColumnDefinition("severity"), "text": ColumnDefinition("text")}

# postgres severities mapped to the event model levels
POSTGRES_LEVELS = {"LOG": "INFO", "DETAIL": "INFO", "STATEMENT": "INFO", "WARNING": "WARN", "FATAL": "ERROR"}

# phrases in a postgres log message mapped to an event name, lines without one
# fall back to the severity
POSTGRES_EVENTS = {
    "still waiting for": "lock_wait",
    "canceling statement": "statement_canceled",
    "checkpoint": "checkpoint",
    "automatic vacuum": "autovacuum",
    "duration:": "slow_statement",
    "statement:": "statement_logged",
}


# helper function that casts a raw column to string and trims whitespace, blank
# values become null
def text(name: str) -> Expr:
    return col(name).cast(td_types.String).str.extract(r"^\s*(\S.*?)\s*$", 1)


# helper function that converts epoch milliseconds to a datetime
def from_epoch_ms(name: str) -> Expr:
    return col(name).cast(td_types.Int64).cast(td_types.Datetime("ms"))


# helper function that parses an ISO timestamp to a naive utc datetime, swaps the
# T separator and drops the Z first since the json reader can also infer the
# column as a datetime and the text cast then uses a space
def from_iso(name: str) -> Expr:
    return text(name).str.replace("T", " ").str.replace("Z", "").str.to_datetime(
        "%Y-%m-%d %H:%M:%S%.f", time_unit="ms", strict=False,
    )


# helper function that converts a timezone aware datetime to naive utc since
# the doris DATETIME type has no timezone
def naive_utc(expr: Expr) -> Expr:
    return expr.dt.convert_time_zone("UTC").dt.replace_time_zone(None)


# helper function that extracts the digits of an id that carries a prefix as an
# integer, ids without digits become null
def digits(expr: Expr) -> Expr:
    return expr.str.extract(r"(\d+)", 1).cast(td_types.Int64, strict=False)


# helper function that picks one of two strings from a boolean expression, the
# TableFrame api has no when/then so it maps the boolean's string form
def pick(condition: Expr, if_true: str, if_false: str) -> Expr:
    return condition.cast(td_types.String).str.replace_many({"true": if_true, "false": if_false})


# helper function that joins string expressions with a separator, a null part
# becomes an empty string so it doesn't null the whole result
def concat_text(*parts: Expr, separator: str = " ") -> Expr:
    result = parts[0].cast(td_types.String).fill_null("")
    for part in parts[1:]:
        result = result + lit(separator) + part.cast(td_types.String).fill_null("")
    return result


# helper function that builds an event id from a source prefix and a hash of the
# columns that identify a record, for sources without their own id, the hash is
# stable within a polars version
def hashed(prefix: str, *names: str) -> Expr:
    return lit(f"{prefix}:") + concat_text(*[col(name) for name in names], separator="|").hash().cast(td_types.String)


# helper function that selects the event model columns in order, casts each to
# its type so the sources concat vertically and drops rows without a parseable
# time
def conform(frame: TableFrame) -> TableFrame:
    return frame.select(
        *[col(name).cast(dtype).alias(name) for name, dtype in EVENT_SCHEMA.items()]
    ).filter(col("event_time").is_not_null())


# helper function that normalizes the browser events, camelCase fields, epoch
# millisecond times and an error code only on failed checkouts
def frontend_events(raw: TableFrame) -> TableFrame:
    return conform(raw.select(
        from_epoch_ms("ts").alias("event_time"),
        lit("frontend").alias("source"),
        lit("web").alias("service"),
        lit(None).alias("host"),
        pick(text("errorCode").is_null(), "INFO", "ERROR").alias("level"),
        text("eventType").alias("event"),
        text("requestId").alias("request_id"),
        col("userId").alias("user_id"),
        lit(None).alias("http_status"),
        lit(None).alias("duration_ms"),
        concat_text(text("eventType"), text("page"), text("errorCode"), text("errorMessage")).str.strip_chars().alias("message"),
        (lit("web:") + text("messageId")).alias("event_id"),
    ))


# helper function that groks the gateway access log lines into columns, the HTTP
# status sets the level and the nginx time format is parsed with its offset
def gateway_events(raw: TableFrame) -> TableFrame:
    parsed = raw.grok("message", GATEWAY_LINE, GATEWAY_FIELDS)
    status = col("status").cast(td_types.String)
    return conform(parsed.select(
        naive_utc(col("time").str.to_datetime("%d/%b/%Y:%H:%M:%S %z", strict=False)).alias("event_time"),
        lit("gateway").alias("source"),
        lit("api-gateway").alias("service"),
        lit(None).alias("host"),
        status.str.replace(r"^5\d\d$", "ERROR").str.replace(r"^4\d\d$", "WARN").str.replace(r"^\d\d\d$", "INFO")
        .alias("level"),
        lit("http_request").alias("event"),
        col("req_id").alias("request_id"),
        digits(col("uid")).alias("user_id"),
        col("status").alias("http_status"),
        (col("rt") * 1000).alias("duration_ms"),
        concat_text(col("method"), col("path"), status, col("rt").cast(td_types.String) + lit("s")).alias("message"),
        hashed("gw", "message").alias("event_id"),
    ))


# helper function that normalizes the service logs, the lowercase levels are
# uppercased and the ISO times parsed
def service_events(raw: TableFrame) -> TableFrame:
    return conform(raw.select(
        from_iso("timestamp").alias("event_time"),
        lit("services").alias("source"),
        text("service").alias("service"),
        text("host").alias("host"),
        text("level").str.to_uppercase().str.replace("WARNING", "WARN").alias("level"),
        text("event").alias("event"),
        text("request_id").alias("request_id"),
        text("user_id").cast(td_types.Int64, strict=False).alias("user_id"),
        lit(None).alias("http_status"),
        col("duration_ms").alias("duration_ms"),
        text("msg").alias("message"),
        hashed("app", "timestamp", "host", "request_id", "event", "msg").alias("event_id"),
    ))


# helper function that casts the payment webhook events to their proper types,
# pulls the request id out of the idempotency key and the user id out of the
# customer reference and parses the MM/DD/YY times
def payment_rows(raw: TableFrame) -> TableFrame:
    return raw.select(
        text("event_id").alias("payment_event_id"),
        text("created").str.to_datetime("%m/%d/%y %H:%M:%S", time_unit="ms", strict=False).alias("event_time"),
        text("event_type").alias("event_type"),
        text("transaction_request").str.strip_prefix("checkout-").alias("request_id"),
        digits(text("customer_ref")).alias("user_id"),
        (col("amount_cents").cast(td_types.Float64) / 100).alias("amount_usd"),
        text("currency").str.to_uppercase().alias("currency"),
        text("card_brand").alias("card_brand"),
        text("failure_code").alias("failure_code"),
        text("failure_message").alias("failure_message"),
    )


# helper function that turns the typed payment events into log events, declines
# are warnings since they are expected
def payment_events(payments: TableFrame) -> TableFrame:
    return conform(payments.select(
        col("event_time"),
        lit("payments").alias("source"),
        lit("payments").alias("service"),
        lit(None).alias("host"),
        pick(col("event_type") == "charge.failed", "WARN", "INFO").alias("level"),
        col("event_type").alias("event"),
        col("request_id"),
        col("user_id"),
        lit(None).alias("http_status"),
        lit(None).alias("duration_ms"),
        concat_text(col("event_type"), col("amount_usd"), col("currency"), col("card_brand"), col("failure_code"),
             col("failure_message")).str.strip_chars().alias("message"),
        (lit("pay:") + col("payment_event_id")).alias("event_id"),
    ))


# helper function that groks the postgres log lines out of the cloudwatch
# records, maps the severities to levels and names each event from the phrase in
# its message
def infra_events(raw: TableFrame) -> TableFrame:
    parsed = raw.grok("message", POSTGRES_LINE, POSTGRES_FIELDS)
    phrase = "(" + "|".join(POSTGRES_EVENTS) + ")"
    return conform(parsed.select(
        from_epoch_ms("timestamp").alias("event_time"),
        lit("infra").alias("source"),
        lit("orders-db").alias("service"),
        text("logStreamName").alias("host"),
        col("severity").str.replace_many(POSTGRES_LEVELS).alias("level"),
        col("text").str.extract(phrase, 1).str.replace_many(POSTGRES_EVENTS)
        .fill_null(col("severity").str.to_lowercase()).alias("event"),
        lit(None).alias("request_id"),
        lit(None).alias("user_id"),
        lit(None).alias("http_status"),
        col("text").str.extract(r"duration: ([\d.]+) ms", 1).cast(td_types.Float64, strict=False).alias("duration_ms"),
        concat_text(col("severity") + lit(":"), col("text")).alias("message"),
        (lit("cw:") + text("eventId")).alias("event_id"),
    ))


# helper function that concats the raw table versions published since the last
# run into one batch and normalizes it, None when no new files landed
def normalized(versions: TableFramesSpec, normalize) -> TableFrame | None:
    frames = [frame for frame in (versions or []) if frame is not None]
    return normalize(concat(frames, how="diagonal_relaxed")) if frames else None


# helper function that drops rows already in the current table by key, re-read
# files that grew only add their new lines
def unseen(new: TableFrame, head: TableFrame | None, key: str) -> TableFrame:
    new = new.unique(subset=[key])
    return new if head is None else new.join(head.select(key), on=key, how="anti")


# helper function that appends the unseen rows to the current table, None keeps
# the current version when there is no new batch
def append(head: TableFrame | None, new: TableFrame | None) -> TableFrame | None:
    if new is None:
        return None
    return new if head is None else concat([head, new], how="diagonal_relaxed")


# transformer that normalizes each source's new batch into the common event
# model, dedupes it against the events already loaded and appends it to
# log_events, new_log_events holds only this run's events so the doris
# subscriber can append them, payments keeps the typed payment events for the
# checkout summary in gold
@transformer(
    input_tables=[
        "logs_landing/raw_frontend@NEW",
        "logs_landing/raw_gateway@NEW",
        "logs_landing/raw_services@NEW",
        "logs_landing/raw_payments@NEW",
        "logs_landing/raw_infra@NEW",
        "log_events@HEAD",
        "payments@HEAD",
    ],
    output_tables=["log_events", "new_log_events", "payments"],
    trigger_by=TablesTrigger(
        tables=[
            "logs_landing/raw_frontend",
            "logs_landing/raw_gateway",
            "logs_landing/raw_services",
            "logs_landing/raw_payments",
            "logs_landing/raw_infra",
        ],
    ),
)
def tfr_log_events(
    raw_frontend: TableFramesSpec,
    raw_gateway: TableFramesSpec,
    raw_services: TableFramesSpec,
    raw_payments: TableFramesSpec,
    raw_infra: TableFramesSpec,
    log_events_head: TableFrameSpec,
    payments_head: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec, TableFrameSpec]:
    new_payments = normalized(raw_payments, payment_rows)
    if new_payments is not None:
        new_payments = unseen(new_payments, payments_head, "payment_event_id")

    batches = [
        normalized(raw_frontend, frontend_events),
        normalized(raw_gateway, gateway_events),
        normalized(raw_services, service_events),
        payment_events(new_payments) if new_payments is not None else None,
        normalized(raw_infra, infra_events),
    ]
    batches = [frame for frame in batches if frame is not None]
    if not batches:
        return None, None, None
    new_events = unseen(concat(batches), log_events_head, "event_id")

    return append(log_events_head, new_events), new_events, append(payments_head, new_payments)
