import tabsdata as td


@td.transformer(
    input_tables=["cart_log", "purchase_log", "web_log"],
    output_tables=["joined_logs"],
)
def create_unified_log(
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
