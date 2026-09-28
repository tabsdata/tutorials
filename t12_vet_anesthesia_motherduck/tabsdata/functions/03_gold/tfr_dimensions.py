#
# Copyright 2026 Tabsdata Inc.
#

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, transformer
from tabsdatak.tableframe.expr import Expr
from tabsdatak.tableframe.functions import col


# helper function that converts a date to an integer date key in YYYYMMDD format
def date_key(date: Expr) -> Expr:
    return (
        date.dt.year().cast(td_types.Int32) * 10000
        + date.dt.month().cast(td_types.Int32) * 100
        + date.dt.day().cast(td_types.Int32)
    )


# transformer that builds the dimension tables for the star schema from the
# silver tables
@transformer(
    input_tables=[
        "vet_silver/patients",
        "vet_silver/owners",
        "vet_silver/staff",
        "vet_silver/cases",
    ],
    output_tables=["dim_patient", "dim_owner", "dim_staff", "dim_date"],
)
def tfr_dimensions(
    patients: TableFrameSpec,
    owners: TableFrameSpec,
    staff: TableFrameSpec,
    cases: TableFrameSpec,
) -> tuple[TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec]:
    dim_patient = patients.select(
        "patient_id", "owner_id", "animal_name", "species", "breed", "date_of_birth", "weight_kg",
    )
    dim_owner = owners
    dim_staff = staff

    dates = col("date")
    dim_date = cases.select(col("procedure_date").alias("date")).unique().select(
        date_key(dates).alias("date_key"),
        dates,
        dates.dt.year().alias("year"),
        dates.dt.quarter().alias("quarter"),
        dates.dt.month().alias("month"),
        dates.dt.strftime("%B").alias("month_name"),
        dates.dt.day().alias("day"),
        dates.dt.strftime("%A").alias("day_name"),
    )

    return dim_patient, dim_owner, dim_staff, dim_date
