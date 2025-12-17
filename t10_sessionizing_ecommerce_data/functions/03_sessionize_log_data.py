import polars as pl
import tabsdata as td


@td.transformer(
    input_tables=["joined_logs"],
    output_tables=["sessionized_logs"],
)
def sessionize_log_data(logs: td.TableFrame):
    threshold = 30
    logs = logs.with_columns(
        td.col("timestamp")
        .cast(td.Datetime)
        .alias("timediff")
        .diff()
        .cast(td.Int64)
        .truediv(60000000)
    )
    logs = logs.with_columns(td.col("user_id").alias("user_id_hash").hash())
    logs = logs.with_columns(
        td.col("user_id_hash")
        .reinterpret(signed=True)
        .diff()
        .alias("user_id_hash_diff")
    )
    logs = logs.with_columns(
        td.col("user_id_hash_diff")
        .ne(0)  # diff != 0 (null → null)
        .fill_null(False)  # treat null as false
        .alias("New_User")
    )

    logs = logs.with_columns(
        (td.col("timediff") > threshold)
        .and_(td.col("timediff").is_not_null())
        .fill_null(False)
        .alias("max_time_inactive_hit"),
        td.col("timestamp").cast(td.Datetime),
    )

    logs = logs.with_columns(
        td.col("New_User")
        .or_(td.col("max_time_inactive_hit").and_(td.col("user_action").ne("purchase")))
        .alias("New_Session_Hit")
    )
    logs = logs.with_columns(
        pl.col("New_Session_Hit").cum_sum().add(1).alias("session")
    ).drop(
        [
            "timediff",
            "New_Session_Hit",
            "max_time_inactive_hit",
            "user_id_hash",
            "user_id_hash_diff",
        ],
    )

    return logs
