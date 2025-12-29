from itertools import accumulate

import tabsdata as td
from polar_sub import drill


@td.transformer(
    input_tables=["all_joined_logs"],
    output_tables=["sessionized_logs"],
)
def sessionize_log_data(logs: td.TableFrame):
    threshold = 30

    logs = logs.sort("user_id", "timestamp", "event_id")

    logs = logs.with_columns(
        td.col("timestamp").diff().dt.total_minutes().alias("timediff"),
        td.col("user_id").hash().alias("user_id_hash"),
    )

    logs = logs.with_columns(
        td.col("user_id_hash")
        .reinterpret(signed=True)
        .diff()
        .alias("user_id_hash_diff"),
        (td.col("timediff").is_not_null())
        .and_(td.col("timediff").gt(threshold))
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

    session_dict = logs.select(td.col("New_Session_Hit"), td.col("event_id")).to_dict()

    session_counter = session_dict["New_Session_Hit"]
    session_counter = [i + 1 for i in accumulate(session_counter)]

    session_dict["New_Session_Hit"] = session_counter
    session_column = td.TableFrame.from_dict(session_dict).rename(
        {"New_Session_Hit": "session"}
    )

    logs = logs.join(session_column, on="event_id", how="left").sort(
        "user_id", "timestamp"
    )

    return logs


if __name__ == "__main__":
    import td_sync

    x = td_sync.download_table("session_analysis", "all_joined_logs")

    x = sessionize_log_data(x)
    drill(x)
