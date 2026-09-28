#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.api import TableFrameSpec, TableFramesSpec, publisher
from tabsdatak.conn.localfile import LocalFileSrc
from tabsdatak.tableframe.functions import concat

# table name prefixes used to build the glob paths for ingesting the csv files
TABLES = [
    "cases",
    "patients",
    "owners",
    "personnel",
    "case_personnel",
    "procedures",
    "med_admin",
    "labs",
    "case_remarks",
    "vitals",
]


# helper function that takes a list of TableFrames as input and concats them
# using the "diagonal_relaxed" scheme to avoid type mismatching or schema
# ordering differences
def all_pets(pets: TableFramesSpec) -> TableFrameSpec:
    frames = [frame for frame in (pets or []) if frame is not None]
    if not frames:
        return None
    return concat(frames, how="diagonal_relaxed")


# publisher that grabs each table's csv files through glob wildcard matching and
# publishes them as raw tables in the landing collection
@publisher(
    source=LocalFileSrc(
        paths=[f"{table}_*.csv" for table in TABLES],
        src_cfg={"tabsdata.src_metadata.drop": True},
    ),
    output_tables=[f"raw_{table}" for table in TABLES],
)
def pub_pet_records(
    cases: TableFramesSpec,
    patients: TableFramesSpec,
    owners: TableFramesSpec,
    personnel: TableFramesSpec,
    case_personnel: TableFramesSpec,
    procedures: TableFramesSpec,
    med_admin: TableFramesSpec,
    labs: TableFramesSpec,
    case_remarks: TableFramesSpec,
    vitals: TableFramesSpec,
) -> tuple[
    TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec,
    TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec, TableFrameSpec,
]:
    return (
        all_pets(cases),
        all_pets(patients),
        all_pets(owners),
        all_pets(personnel),
        all_pets(case_personnel),
        all_pets(procedures),
        all_pets(med_admin),
        all_pets(labs),
        all_pets(case_remarks),
        all_pets(vitals),
    )
