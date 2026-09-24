#
# Copyright 2026 Tabsdata Inc.
#

import calendar
from datetime import date, timedelta

import tabsdatak.tableframe.datatypes as td_types
from tabsdatak.api import TableFrameSpec, transformer
from tabsdatak.tableframe import TableFrame

CALENDAR_START = date(2020, 1, 1)
CALENDAR_END = date(2030, 12, 31)

US_FIXED_HOLIDAYS = {(1, 1), (7, 4), (12, 25)}

# Narrowed so date_sk matches the Int32 date key build_fact puts on the fact.
CALENDAR_TYPES = {
    "date_sk": td_types.Int32,
    "year": td_types.Int32,
    "month": td_types.Int8,
    "month_of_year": td_types.Int8,
    "day_of_month": td_types.Int8,
    "day_of_week": td_types.Int8,
    "week_of_year": td_types.Int8,
    "quarter": td_types.Int8,
}


# Generated 2020-2030 calendar. The zone table is only the trigger: it puts
# dim_date on the dimension load, next to dim_zone.
@transformer(
    input_tables=["nyc_silver/zone_lookup_current_silver@HEAD"],
    output_tables=["dim_date"],
)
def tfr_dim_date(_zones: TableFrameSpec) -> TableFrameSpec:
    days = [CALENDAR_START + timedelta(days=n) for n in range((CALENDAR_END - CALENDAR_START).days + 1)]
    day_of_week = [day.isoweekday() % 7 + 1 for day in days]  # 1=Sunday..7=Saturday, as Spark

    return TableFrame.from_dict({
        "date_sk": [day.year * 10000 + day.month * 100 + day.day for day in days],
        "date_key": days,
        "year": [day.year for day in days],
        "month": [day.month for day in days],
        "month_of_year": [day.month for day in days],
        "month_name": [calendar.month_name[day.month] for day in days],
        "day_of_month": [day.day for day in days],
        "day_of_week": day_of_week,
        "day_name": [calendar.day_name[day.weekday()] for day in days],
        "is_weekend": [dow in (1, 7) for dow in day_of_week],
        "week_of_year": [day.isocalendar()[1] for day in days],
        "quarter": [(day.month - 1) // 3 + 1 for day in days],
        "quarter_year": [f"Q{(day.month - 1) // 3 + 1}-{day.year}" for day in days],
        "is_us_holiday": [(day.month, day.day) in US_FIXED_HOLIDAYS for day in days],
    }).cast(CALENDAR_TYPES)
