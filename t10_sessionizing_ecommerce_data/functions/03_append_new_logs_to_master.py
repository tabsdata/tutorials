import tabsdata as td


@td.transformer(
    input_tables=["new_joined_logs", "all_joined_logs"],
    output_tables=["all_joined_logs"],
)
def append_new_logs_to_master(
    new_joined_logs: td.TableFrame, all_joined_logs: td.TableFrame
):
    new_joined_logs = new_joined_logs.with_columns(
        td.col("timestamp").cast(td.Datetime)
    )
    if all_joined_logs is None:
        return new_joined_logs
    return td.concat([all_joined_logs, new_joined_logs])


