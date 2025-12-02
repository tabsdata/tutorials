import tabsdata as td


@td.transformer(
    input_tables=["sf_snapshot", "sf_snapshot@HEAD^"],
    output_tables=["status_agg"],
)
def agg_statuses(leads: td.TableFrame, old_leads: td.TableFrame):

    status_agg = leads.group_by(td.col("STATUS")).agg(
        td.col("STATUS").alias("STATUS_COUNT").count()
    )
    if old_leads is None:
        old_leads = status_agg.rename({"STATUS_COUNT": "OLD_STATUS_COUNT"})
    else:
        old_leads = old_leads.group_by(td.col("STATUS")).agg(
            td.col("STATUS").alias("OLD_STATUS_COUNT").count()
        )

    status_agg = status_agg.join(
        old_leads,
        how="left",
        on="STATUS",
    )
    status_agg = (
        status_agg.with_columns(
            td.col("STATUS_COUNT")
            .sub(td.col("OLD_STATUS_COUNT").cast(td.Int32))
            .alias("DELTA")
        )
        .drop("OLD_STATUS_COUNT")
        .sort(td.col("STATUS"), descending=True)
    )
    return status_agg
