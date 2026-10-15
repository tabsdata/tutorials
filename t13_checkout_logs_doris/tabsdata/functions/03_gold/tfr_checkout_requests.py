#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, transformer
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.functions import col, lit

# outcome of a checkout from whether the card was charged, declined and whether
# the order was created
OUTCOMES = {
    "paid": [True, True, False, False],
    "declined": [False, False, True, False],
    "ordered": [True, False, False, False],
    "outcome": ["completed", "charged_without_order", "payment_declined", "failed_before_payment"],
}


# transformer that correlates the events of each checkout request across the
# frontend, gateway, services and payments logs into one row per checkout, the
# outcome comes from joining the paid, declined and ordered flags onto the
# outcome table and the charged amount from the payment events
@transformer(
    input_tables=["logs_silver/log_events", "logs_silver/payments"],
    output_tables=["checkout_requests"],
)
def tfr_checkout_requests(log_events: TableFrameSpec, payments: TableFrameSpec) -> TableFrameSpec:
    if log_events is None:
        return None
    checkouts = log_events.filter(col("event").is_in(["checkout_clicked", "checkout_started"])).select(
        "request_id"
    ).unique()

    # sorts by time first so first() in the aggregation picks the earliest
    # service error, the application's own message is more specific than the
    # gateway status or the error the browser shows
    events = log_events.join(checkouts, on="request_id", how="semi").sort("event_time")
    summary = events.group_by("request_id").agg(
        col("user_id").max().alias("user_id"),
        col("event_time").min().alias("started_at"),
        col("event_time").max().alias("ended_at"),
        (col("event") == "charge.succeeded").max().alias("paid"),
        (col("event") == "charge.failed").max().alias("declined"),
        (col("event") == "order_created").max().alias("ordered"),
        col("http_status").filter(col("source") == "gateway").first().alias("http_status"),
        col("event_id").count().cast(td_types.Int32).alias("events"),
        col("service").n_unique().cast(td_types.Int32).alias("services"),
        col("message").filter(col("source") == "services", col("level") == "ERROR").first().alias("error_message"),
    )

    outcomes = TableFrame.from_dict(OUTCOMES)
    summary = summary.join(outcomes, on=["paid", "declined", "ordered"], how="left")
    if payments is not None:
        amounts = payments.filter(col("event_type").is_in(["charge.succeeded", "charge.failed"])).group_by(
            "request_id"
        ).agg(col("amount_usd").max().alias("amount_usd"))
        summary = summary.join(amounts, on="request_id", how="left")
    else:
        summary = summary.with_columns(lit(None).cast(td_types.Float64).alias("amount_usd"))

    return summary.select(
        "request_id",
        "user_id",
        "started_at",
        "ended_at",
        col("outcome").fill_null("unknown"),
        "http_status",
        "amount_usd",
        "events",
        "services",
        "error_message",
    ).sort("started_at")
