import tabsdata as td


@td.transformer(
    input_tables=["new_joined_logs", "all_joined_logs"],
    output_tables=["all_joined_logs"],
)
def append_new_logs_to_master(
    joined_logs: td.TableFrame, all_joined_logs: td.TableFrame
):
    if all_joined_logs is None:
        return joined_logs
    return td.concat([all_joined_logs, joined_logs])


if __name__ == "__main__":
    import td_sync

    td_sync.sync_with_server("session_analysis", True)
