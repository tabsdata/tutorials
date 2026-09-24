#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak._medallion.gold.dim import build_type1_dim
from tabsdatak.api import TableFrameSpec, transformer
from tabsdatak.tableframe import TableFrame
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col, lit

REGION_GROUPS = {
    "Manhattan": "Core",
    "Brooklyn": "Outer Borough",
    "Queens": "Outer Borough",
    "Bronx": "Bronx",
    "Staten Island": "Staten Island",
    "EWR": "Airport",
}

def zone_type_match(column: str, pattern: str, label: str) -> Expr:
    # label where the zone name matches pattern, null otherwise
    return col(column).str.extract(pattern).str.replace_all(r".+", label)


# Zone dimension: the current zones with region group, zone type and Manhattan flag.
@transformer(
    input_tables=["nyc_silver/zone_lookup_current_silver@HEAD"],
    output_tables=["dim_zone"],
)
def tfr_dim_zone_type1(current: TableFrameSpec) -> TableFrameSpec:
    dim = build_type1_dim(current)
    if dim is None:
        return None

    regions = TableFrame.from_dict({
        "borough": list(REGION_GROUPS),
        "region_group": list(REGION_GROUPS.values()),
    })
    return (
        dim.rename({"LocationID": "zone_key", "Borough": "borough", "Zone": "zone_name"})
        .join(regions, on="borough", how="left")
        .with_columns([
            # region, zone type and Manhattan flag for BI filtering
            col("region_group").fill_null(lit("Unknown")),
            # zone type from the zone name, first match wins
            zone_type_match("zone_name", r"(Airport|JFK|LGA|EWR)", "Airport")
            .fill_null(zone_type_match("zone_name", r"(Center|Midtown|Downtown)", "CBD"))
            .fill_null(zone_type_match("zone_name", r"(Residential)", "Residential"))
            .fill_null(lit("Mixed"))
            .alias("zone_type"),
            (col("borough") == lit("Manhattan")).alias("is_manhattan"),
        ])
    )
