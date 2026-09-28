#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.conn.common.error import ConnException, ConnInitException
from tabsdatak.error import ErrorCode, ErrorDef


class MotherDuckRuntimeException(ConnException):
    """raised when a write to motherduck fails"""


class MotherDuckErrorCode(ErrorCode):
    MOTHERDUCK_1 = ErrorDef(ConnInitException, "MotherDuckDestConn validation failed")
    MOTHERDUCK_2 = ErrorDef(ConnInitException, "MotherDuckDest validation failed")
    MOTHERDUCK_3 = ErrorDef(
        MotherDuckRuntimeException,
        "MotherDuck received {slots} table(s) for {tables} target table(s)",
    )
    MOTHERDUCK_4 = ErrorDef(MotherDuckRuntimeException, "MotherDuck write to {table} failed")
