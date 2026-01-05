import tabsdata as td


@td.transformer(
    input_tables=["new_cart_logs", "new_purchase_logs", "new_web_logs"],
    output_tables=["new_joined_logs"],
)
def unify_new_log_data(
    cart: td.TableFrame, purchase: td.TableFrame, web: td.TableFrame
):
    if not cart.is_empty():
        cart = cart.select(
            "message",
            "timestamp",
            "event_id",
            "user_id",
            (td.col("event_type") + "_" + td.col("cart_action")).alias("user_action"),
        )

    if not purchase.is_empty():
        purchase = purchase.select(
            "message",
            "timestamp",
            "event_id",
            "user_id",
            td.col("event_type").alias("user_action"),
        )
    if not web.is_empty():
        web = web.select(
            "message",
            "timestamp",
            "event_id",
            "user_id",
            td.col("event_type").alias("user_action"),
        )
    concat_list = [cart, web, purchase]
    empty_check = [i for i in concat_list if not i.is_empty()]

    result = td.concat([cart, web, purchase], how="diagonal")

    if len(empty_check) == 0:
        return td.TableFrame.empty()
    result = result.sort("user_id", "timestamp", descending=False)
    result = result.with_columns(
        td.col("timestamp")
        .cast(td.Datetime)
        .dt.strftime("%Y-%m-%d %H:%M")
        .alias("time_pretty")
    )

    return result


