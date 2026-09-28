#
# Copyright 2026 Tabsdata Inc.
#

from tabsdatak.spi import DestContext, DestDef, DestPlugin, TableFileSpec
from tabsdata_motherduck import MotherDuckDest, MotherDuckDestConn, resolve
from tabsdata_motherduck.error import MotherDuckErrorCode


# helper function that connects to motherduck and creates the target database if
# it doesn't exist
def connect(conn: MotherDuckDestConn):
    import duckdb

    database = resolve(conn.database)
    con = duckdb.connect("md:", config={"motherduck_token": resolve(conn.token)})
    con.execute(f'CREATE DATABASE IF NOT EXISTS "{database}"')
    con.execute(f'USE "{database}"')
    return con


class MotherDuckDestPlugin(DestPlugin[MotherDuckDestConn, MotherDuckDest]):
    def write_out(
        self,
        ctx: DestContext,
        conn: MotherDuckDestConn,
        dest: MotherDuckDest,
        tables: list[TableFileSpec],
    ) -> None:
        if len(tables) != len(dest.tables):
            raise MotherDuckErrorCode.MOTHERDUCK_3.exception(slots=len(tables), tables=len(dest.tables))

        # duckdb reads the parquet files passed in by tabsdata and bulk loads them
        # into motherduck instead of sending insert statements like the postgres
        # connector
        con = connect(conn)
        try:
            con.begin()
            for table, parquet in zip(dest.tables, tables):
                if parquet is None:
                    # skip tables the subscriber returned None for
                    continue
                try:
                    source = "read_parquet('{}')".format(str(parquet).replace("'", "''"))
                    if dest.if_table_exists == "replace":
                        con.execute(f'CREATE OR REPLACE TABLE "{table}" AS SELECT * FROM {source}')
                    else:
                        con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" AS SELECT * FROM {source} LIMIT 0')
                        con.execute(f'INSERT INTO "{table}" BY NAME SELECT * FROM {source}')
                except Exception as e:
                    raise MotherDuckErrorCode.MOTHERDUCK_4.exception(cause=e, table=table)
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


MOTHERDUCK_DEST = DestDef(
    conn=MotherDuckDestConn,
    type_="motherduck-out",
    system="MotherDuck",
    dest_version="v1",
    dest=MotherDuckDest,
    cardinality=lambda dest: len(dest.tables),
    plugin=MotherDuckDestPlugin,
    explorer=None,
    icon=None,
)
