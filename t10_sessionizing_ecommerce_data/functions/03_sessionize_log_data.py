import tabsdata as td


@td.transformer(
    input_tables=["joined_logs"],
    output_tables=["sessionized_logs"],
)
def sessionize_log_data(logs: td.TableFrame):
    threshold = 30

    logs = logs.sort("user_id", "timestamp", "event_id")

    logs = logs.with_columns(
        td.col("timestamp")
        .cast(td.Datetime)
        .diff()
        .cast(td.Int64)
        .truediv(60000000)
        .alias("timediff"),
        td.col("user_id").hash().alias("user_id_hash"),
    )

    logs = logs.with_columns(
        td.col("user_id_hash")
        .reinterpret(signed=True)
        .diff()
        .alias("user_id_hash_diff"),
        (td.col("timediff") > threshold)
        .and_(td.col("timediff").is_not_null())
        .fill_null(False)
        .alias("max_time_inactive_hit"),
        td.col("timestamp").cast(td.Datetime),
    )

    logs = logs.with_columns(
        td.col("user_id_hash_diff").ne(0).fill_null(False).alias("New_User")
    )

    logs = logs.with_columns(
        td.col("New_User")
        .or_(td.col("max_time_inactive_hit").and_(td.col("user_action").ne("purchase")))
        .alias("New_Session_Hit")
    )

    counter = (
        logs.filter(td.col("New_Session_Hit").eq(True))
        .select(
            td.col("user_id"),
            td.col("timestamp").alias("timestamp_right"),
        )
        .with_columns(td.col("user_id").rank(method="ordinal").add(1).alias("rank"))
        .select("user_id", "timestamp_right", "rank")
    )

    logs = logs.drop(
        ["timediff", "max_time_inactive_hit", "user_id_hash", "user_id_hash_diff"]
    )

    event_to_rank = (
        logs.select("user_id", "event_id", "timestamp")
        .join(counter, how="left", on="user_id")
        .sort("user_id", "timestamp", "event_id", "rank")
        .filter(td.col("timestamp").le(td.col("timestamp_right")))
        .unique("event_id", keep="first", maintain_order=True)
        .select("event_id", "rank")
    )

    logs = logs.join(event_to_rank, how="left", on="event_id").sort(
        "user_id", "timestamp", "event_id", "rank"
    )

    logs = logs.with_columns(
        td.col("rank")
        .sub(td.col("New_Session_Hit").fill_null(False).not_().cast(td.Int64))
        .alias("session")
    )

    return logs
