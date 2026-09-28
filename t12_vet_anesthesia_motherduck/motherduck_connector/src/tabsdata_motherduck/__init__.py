#
# Copyright 2026 Tabsdata Inc.
#

"""motherduck destination connector for tabsdata subscribers

the token and database are stored in the connection on the subscriber's
collection and the subscriber specifies the target tables:

    @subscriber(
        input_tables=["gold/dim_patient", "gold/fct_anesthesia_case"],
        destination=MotherDuckDest(tables=["dim_patient", "fct_anesthesia_case"]),
    )
    def to_motherduck(dim_patient, fct_anesthesia_case):
        return dim_patient, fct_anesthesia_case
"""

from typing import Annotated, Literal

from pydantic import StringConstraints

import tabsdatak._api as _api
from tabsdatak.api import Dest, Secret, StrOrSecretSpec
from tabsdatak.spi import Conn
from tabsdata_motherduck.error import MotherDuckErrorCode

# restricts table names to plain identifiers so they can be used in the sql
# without quoting
TableName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")]


# helper function that returns the value of a plain string or a secret
def resolve(spec: StrOrSecretSpec) -> str:
    return spec.value() if isinstance(spec, Secret) else spec


@_api.dataclass(MotherDuckErrorCode.MOTHERDUCK_1, kw_only=True)
class MotherDuckDestConn(Conn):
    """connection for MotherDuckDest that stores the motherduck token and target
    database, the token needs write access and the database is created if it
    doesn't exist
    """

    token: StrOrSecretSpec
    database: StrOrSecretSpec


@_api.dataclass(MotherDuckErrorCode.MOTHERDUCK_2, kw_only=True)
class MotherDuckDest(Dest):
    """destination that writes subscriber tables to motherduck, tables map to the
    subscriber's input tables in order. if_table_exists defaults to replace which
    recreates each table, append inserts the rows and creates the table if needed
    """

    tables: list[TableName]
    if_table_exists: Literal["append", "replace"] = "replace"
