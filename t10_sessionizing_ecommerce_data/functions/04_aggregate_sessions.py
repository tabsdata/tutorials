import tabsdata as td


def duration_to_str_expr(col_name: str, out_name: str | None = None):
    MICROS_PER_SECOND = 1_000_000
    MICROS_PER_MINUTE = 60 * MICROS_PER_SECOND

    us = td.col(col_name).cast(td.Int64)

    minutes = us.truediv(MICROS_PER_MINUTE).floor()
    seconds = (us % MICROS_PER_MINUTE).truediv(MICROS_PER_SECOND).floor()

    if out_name is None:
        out_name = f"{col_name}"

    return (minutes.cast(td.Utf8) + "m " + seconds.cast(td.Utf8) + "s").alias(out_name)


@td.transformer(
    input_tables=["sessionized_logs"],
    output_tables=["aggregated_sessions"],
)
def aggregate_sessions(logs: td.TableFrame):
    action = td.col("user_action")
    base = logs.select(["session", "user_id"]).unique(subset="session", keep="first")
    event_breakdown = logs.group_by("session").agg(
        td.col("user_action")
        .filter(action == "web")
        .count()
        .alias("count of web activities"),
        action.count().alias("count of total activities"),
        action.filter(action.str.starts_with("cart"))
        .count()
        .alias("count of cart activities"),
        action.filter(action.str.starts_with("purchase"))
        .count()
        .alias("count of purchase activities"),
    )
    time_breakdown = logs.group_by("session").agg(
        td.col("timestamp")
        .filter(td.col("user_action") == "purchase")
        .first()
        .sub(td.col("timestamp").first())
        .alias("time to purchase"),
        td.col("timestamp")
        .last()
        .sub(td.col("timestamp").first())
        .alias("total session time"),
    )
    result = base.join(event_breakdown, on="session", how="left")
    result = result.join(time_breakdown, on="session", how="left")

    duration_columns = [
        name for name, type in result.schema.items() if isinstance(type, td.Duration)
    ]

    result = result.with_columns(
        *[duration_to_str_expr(i) for i in duration_columns]
    ).sort("session")

    return result
