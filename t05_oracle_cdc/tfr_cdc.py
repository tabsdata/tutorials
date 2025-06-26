import polars as pl
import polars.selectors as cs
import tabsdata as td
import datetime as dt
import functools

@td.transformer(
    input_tables=["customers@HEAD^", "customers@HEAD", "customers_cdc"],
    output_tables=["customers_cdc"],
)
def tfr_cdc(current: td.TableFrame, new: td.TableFrame, cdc: td.TableFrame) -> td.TableFrame:
    # Handle first commit
    if current is None:
        current = new.clear()

    timestamp = dt.datetime.now()

    # INSERTS
    added = (
        new.join(current, on="SEQ", how="left", suffix="_old")
        .filter(td.col("FIRST_old").is_null())
        .drop(cs.matches(".*_old"))
        .with_columns([
            td.lit("INSERT").alias("OPERATION"),
            td.lit(timestamp).alias("DATA_CHANGE_DATETIME"),
        ])
    )

    # DELETES
    deleted = (
        current.join(new, on="SEQ", how="left", suffix="_new")
        .filter(td.col("FIRST_new").is_null())
        .drop(cs.matches(".*_new"))
        .with_columns([
            td.lit("DELETE").alias("OPERATION"),
            td.lit(timestamp).alias("DATA_CHANGE_DATETIME"),
        ])
    )

    # UPDATES
    columns_to_compare = [col for col in new.columns() if col not in ["SEQ", "$td.id", "$td.src"]]
    update_filter = functools.reduce(lambda a, b: a | b, [
        td.col(col) != td.col(f"{col}_old") for col in columns_to_compare
    ])

    updated = (
        new.join(current, on="SEQ", how="inner", suffix="_old")
        .filter(update_filter)
        .drop(cs.matches(".*_old"))
        .with_columns([
            td.lit("UPDATE").alias("OPERATION"),
            td.lit(timestamp).alias("DATA_CHANGE_DATETIME"),
        ])
    )

    if cdc is None:
        cdc = deleted.clear()

    # Combine changes and sort
    return (
        td.concat([cdc, deleted, added, updated])
        .sort(by="DATA_CHANGE_DATETIME", descending=True)
    )


