import tabsdata as td


@td.transformer(
    input_tables=["new_cart_logs", "new_purchase_logs", "new_web_logs"],
    output_tables=["new_joined_logs"],
)
def unify_new_log_data(
    cart: td.TableFrame, purchase: td.TableFrame, web: td.TableFrame
):
    cart = cart.select(
        "message",
        "timestamp",
        "event_id",
        "user_id",
        (td.col("event_type") + "_" + td.col("cart_action")).alias("user_action"),
    )
    purchase = purchase.select(
        "message",
        "timestamp",
        "event_id",
        "user_id",
        td.col("event_type").alias("user_action"),
    )
    web = web.select(
        "message",
        "timestamp",
        "event_id",
        "user_id",
        td.col("event_type").alias("user_action"),
    )

    result = td.concat([cart, web, purchase])
    result = result.sort("user_id", "timestamp", descending=False)
    result = result.with_columns(
        td.col("timestamp")
        .cast(td.Datetime)
        .dt.strftime("%Y-%m-%d %H:%M")
        .alias("time_pretty")
    )

    return result


if __name__ == "__main__":
    import td_sync

    td_sync.sync_with_server("session_analysis", True)
