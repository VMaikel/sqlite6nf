#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Extension to the sqlite3 module adding support for temporal table structure and content.

Sqlite6nf is an extension to the standard sqlite3 module adding built-in support for tables in 6th normal form
(6nf from now on). A table in 6nf has each non-primary key column split into a separate table. These new tables
can then be made temporal by adding meta columns containing timestamps. Furthermore, temporality requires
records to be only added, but never changed or deleted. Temporal tables allow data to be seen as it was during
different moments in time, instead of only showing the latest state of the database. Sqlite6nf adds temporal
support for both table structure (tables and columns) and table content (records).

The sqlite6nf module is split into 3 parts:
    * The sqlite code for creating, updating and selecting from 6nf tables.
    * The regex code for interpreting and altering queries.
    * The Python code for changing the default behaviour of the sqlite3 module.

The specif behaviour of sqlite6nf is explained further in each of these parts. For the default behaviour please
see the sqlite3 documentation.


Please be aware that sqlite6nf is currently in a development phase. Many of its features are currently still
untested, incomplete or missing. During the development phase no attempt is made to remain compatible with
previous versions. Using sqlite6nf in its current state could create issues later on for a database. Once
sqlite6nf reaches the production phase in version 1.0 all future versions will be made compatible with it.

Below are all features which are currently untested, incomplete or missing. Once all these issues are closed,
production version 1.0 will have been reached.
    * Documentation
        [ ] #1 Expand the description of README and the module docstring.
        [ ] #2 Add docstrings and comments to the sqlite query constants.
        [ ] #3 Add docstrings and comments to the regex pattern constants.
        [ ] #4 Add docstrings and comments to the Python functions and classes.
    * Bugs
        [ ] #5 Cursor.normalise() does not validate the tables argument.
        [ ] #6 Shadow tables are not populated with initial values.
        [ ] #7 Transaction time is not consistently calculated.
    * Questions
        [ ] #8 Verify SQL injection safety.
        [ ] #9 Verify proper case (insensitivity) handling of SQLite queries.
        [ ] #10 Verify proper Unicode handling of SQLite queries.
        [ ] #11 Verify proper transaction and savepoint handling.
        [ ] #12 Verify whether sqlite3 aliases should use single or double quotes.
        [ ] #13 Verify proper handling of tables without rowid.
        [ ] #14 Verify proper handling of tables with a multi-column primary key.
        [ ] #15 Verify if the ‘VACUUM’ statement causes issues with the used rowid values.
    * Enhancements
        [ ] #16 Add support for selecting records.
        [ ] #17 Add support for altering tables.
        [ ] #18 Add support for dropping tables.
        [ ] #19 Add support for temporary tables.
        [ ] #20 Add support for virtual tables
        [ ] #21 Add support for creating views.
        [ ] #22 Add support for dropping views.
        [ ] #23 Add support for temporary views.
        [ ] #24 Add support for attaching and detaching databases.
        [ ] #25 Add support for join statements which use a comma (,) instead of the keyword 'JOIN'.
        [ ] #26 Add support for record changes from within triggers when recursive triggers are disabled.
        [ ] #27 Add support for temporal criteria from within queries.
        [ ] #28 Add support for user defined Connection and Cursor objects.
        [ ] #29 Add support for user defined meta-columns.
        [ ] #30 Add support for table normalisation on a per-column basis.
        [ ] #31 Add support for deleting old historized data.
"""


__author__ = 'Maikel Verbeek'
__copyright__ = 'Copyright (C) 2022 Maikel Verbeek'
__version__ = '0.1.1'
__date__ = '2022/10/30'
__status__ = 'Development'


from typing import Any, Iterable, Iterator, Mapping, Optional, Sequence, Type, Union
import sqlite3
from sqlite3 import *
from datetime import date, datetime
from os import PathLike
import re


# language=sql
_SQL_TRANSACTION_BEGIN = '''
    BEGIN IMMEDIATE TRANSACTION;
    '''
# language=sql
_SQL_TRANSACTION_COMMIT = '''
    COMMIT TRANSACTION;
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_TABLE = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_table" (
        "id" INTEGER PRIMARY KEY
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_TABLE_EXIST = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_table_exist" (
        "id" INTEGER NOT NULL,
        "transaction" TEXT NOT NULL,
        "exist" INTEGER NOT NULL,
        PRIMARY KEY ("id", "transaction"),
        FOREIGN KEY ("id") REFERENCES "sqlite6nf_table"("id")
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_TABLE_NAME = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_table_name" (
        "id" INTEGER NOT NULL,
        "transaction" TEXT NOT NULL,
        "name" INTEGER NOT NULL,
        PRIMARY KEY ("id", "transaction"),
        FOREIGN KEY ("id") REFERENCES "sqlite6nf_table"("id")
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_COLUMN = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_column" (
        "id" INTEGER PRIMARY KEY,
        "table_id" INTEGER NOT NULL,
        FOREIGN KEY ("table_id") REFERENCES "sqlite6nf_table"("id")
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_COLUMN_EXIST = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_column_exist" (
        "id" INTEGER NOT NULL,
        "transaction" TEXT NOT NULL,
        "exist" INTEGER NOT NULL,
        PRIMARY KEY ("id", "transaction"),
        FOREIGN KEY ("id") REFERENCES "sqlite6nf_column"("id")
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_COLUMN_NAME = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_column_name" (
        "id" INTEGER NOT NULL,
        "transaction" TEXT NOT NULL,
        "name" INTEGER NOT NULL,
        PRIMARY KEY ("id", "transaction"),
        FOREIGN KEY ("id") REFERENCES "sqlite6nf_column"("id")
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_INSTANCE = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_{table_id}" (
        "id" INT PRIMARY KEY
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_INSTANCE_EXIST = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_{table_id}_exist" (
        "id" INTEGER NOT NULL,
        "transaction" TEXT NOT NULL,
        "exist" INTEGER NOT NULL,
        PRIMARY KEY ("id", "transaction"),
        FOREIGN KEY ("id") REFERENCES "sqlite6nf_{table_id}"("id")
        );
    '''
# language=sql
_SQL_CREATE_TABLE_SQLITE6NF_INSTANCE_VALUE = '''
    CREATE TABLE IF NOT EXISTS "sqlite6nf_{table_id}_{column_id}" (
        "id" INTEGER NOT NULL,
        "transaction" TEXT NOT NULL,
        "value" {dtype},
        PRIMARY KEY ("id", "transaction"),
        FOREIGN KEY ("id") REFERENCES "sqlite6nf_{table_id}"("id")
        );
    '''
# language=sql
_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_INSERT_INSTANCE = '''
    CREATE TRIGGER IF NOT EXISTS "sqlite6nf_trigger_insert_{table_id}"
    AFTER INSERT ON "{table_name}"
    FOR EACH ROW BEGIN
        INSERT INTO "sqlite6nf_{table_id}"
        ("id")
        VALUES ("NEW"."rowid");

        INSERT INTO "sqlite6nf_{table_id}_exist"
        ("id", "transaction", "exist")
        VALUES ("NEW"."rowid", strftime('%Y-%m-%d %H:%M:%f', 'now'), 1);
    END;
    '''
# language=sql
_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_DELETE_INSTANCE = '''
    CREATE TRIGGER IF NOT EXISTS "sqlite6nf_trigger_delete_{table_id}"
    AFTER DELETE ON "{table_name}"
    FOR EACH ROW BEGIN
        INSERT INTO "sqlite6nf_{table_id}_exist"
        ("id", "transaction", "exist")
        VALUES ("OLD"."rowid", strftime('%Y-%m-%d %H:%M:%f', 'now'), 0);
    END;
    '''
# language=sql
_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_INSERT_INSTANCE_VALUE = '''
    CREATE TRIGGER IF NOT EXISTS "sqlite6nf_trigger_insert_{table_id}_{column_id}"
    AFTER INSERT ON "{table_name}"
    FOR EACH ROW BEGIN
        INSERT INTO "sqlite6nf_{table_id}_{column_id}"
        ("id", "transaction", "value")
        VALUES ("NEW"."rowid", strftime('%Y-%m-%d %H:%M:%f', 'now'), "NEW"."{column_name}");
    END;
    '''
# language=sql
_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_UPDATE_INSTANCE_VALUE = '''
    CREATE TRIGGER IF NOT EXISTS "sqlite6nf_trigger_update_{table_id}_{column_id}"
    AFTER UPDATE OF "{column_name}" ON "{table_name}"
    FOR EACH ROW BEGIN
        INSERT INTO "sqlite6nf_{table_id}_{column_id}"
        ("id", "transaction", "value")
        VALUES ("NEW"."rowid", strftime('%Y-%m-%d %H:%M:%f', 'now'), "NEW"."{column_name}");
    END;
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_TABLE = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_table"
    ("id")
    VALUES (NULL)
    RETURNING *;
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_TABLE_EXIST = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_table_exist"
    ("id", "transaction", "exist")
    VALUES (:id, :transaction, :exist);
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_TABLE_NAME = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_table_name"
    ("id", "transaction", "name")
    VALUES (:id, :transaction, :name);
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_COLUMN = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_column"
    ("id", "table_id")
    VALUES (NULL, :table_id)
    RETURNING *;
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_COLUMN_EXIST = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_column_exist"
    ("id", "transaction", "exist")
    VALUES (:id, :transaction, :exist);
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_COLUMN_NAME = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_column_name"
    ("id", "transaction", "name")
    VALUES (:id, :transaction, :name);
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_INSTANCE = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_{table_id}"
    ("id")
    VALUES (NULL)
    RETURNING *;
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_INSTANCE_EXIST = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_{table_id}_exist"
    ("id", "transaction", "exist")
    VALUES (:id, :transaction, :exist);
    '''
# language=sql
_SQL_INSERT_INTO_SQLITE6NF_INSTANCE_VALUE = '''
    INSERT OR ROLLBACK INTO "sqlite6nf_{table_id}_{column_id}"
    ("id", "transaction", "value")
    VALUES (:id, :transaction, :value);
    '''
# language=sql
_SQL_SELECT_FROM_SQLITE_SCHEMA = '''
    SELECT "sqlite_schema".*
    FROM "sqlite_schema" AS "sqlite_schema"
    LEFT OUTER JOIN (
        SELECT "sqlite6nf_table_name"."id", "sqlite6nf_table_name"."name", max("sqlite6nf_table_name", "transaction")
        FROM "sqlite6nf_table_name"
        GROUP BY "sqlite6nf_table_name"."id"
        ) AS "sqlite6nf_table_name"
    ON "sqlite6nf_table_name"."name" = "sqlite_schema"."name"
    WHERE "sqlite_schema"."type" = 'table'
    AND NOT lower("sqlite_schema"."name") GLOB 'sqlite6nf_*'
    AND "sqlite6nf_table_name"."name" IS NULL;
    '''
# language=sql
_SQL_SELECT_FROM_PRAGMA_TABLE_INFO = '''
    SELECT "pragma_table_info".*
    FROM "sqlite_schema" AS "sqlite_schema"
    LEFT JOIN pragma_table_info("sqlite_schema"."name") AS "pragma_table_info"
    WHERE "sqlite_schema"."type" = 'table'
    AND NOT lower("sqlite_schema"."name") GLOB 'sqlite6nf_*'
    AND "sqlite_schema"."name" = :name;
    '''


_PATTERN_COMMENT_SINGLE_LINE = re.compile(r'''(?x:
    --
    (?s:.*?)
    (?:\n|$)
    )''')
_PATTERN_COMMENT_MULTI_LINE = re.compile(r'''(?x:
    /\*
    (?s:.*?)
    (?:\*/|$)
    )''')
_PATTERN_COMMENT = re.compile(rf'''(?x:
    {_PATTERN_COMMENT_SINGLE_LINE.pattern}|{_PATTERN_COMMENT_MULTI_LINE.pattern}
    )''')
_PATTERN_SPACE = re.compile(rf'''(?x:
    \s|{_PATTERN_COMMENT.pattern}
    )''')
_PATTERN_IDENTIFIER_SINGLE_QUOTE = re.compile(r'''(?x:
    '
    (?P<identifier_single_quote>(?s:.*?)[^'](?:'{2})*)
    (?:'(?!')|$)
    )''')
_PATTERN_IDENTIFIER_DOUBLE_QUOTE = re.compile(r'''(?x:
    "
    (?P<identifier_double_quote>(?s:.*?)[^"](?:"{2})*)
    (?:"(?!")|$)
    )''')
_PATTERN_IDENTIFIER_SQUARE_BRACKET = re.compile(r'''(?x:
    \[
    (?P<identifier_square_bracket>(?s:.*?))
    (?:]|$)
    )''')
_PATTERN_IDENTIFIER_GRAVE_ACCENT = re.compile(r'''(?x:
    `
    (?P<identifier_grave_accent>(?s:.*?)[^`](?:`{2})*)
    (?:`(?!`)|$)
    )''')
_PATTERN_IDENTIFIER_NO_QUOTE = re.compile(r'''(?x:
    (?<![0-9A-Z_a-z])
    (?P<identifier_no_quote>[A-Z_a-z][0-9A-Z_a-z]*?)
    (?![0-9A-Z_a-z])
    )''')
_PATTERN_IDENTIFIER = re.compile(rf'''(?x:
    (?P<identifier>{_PATTERN_IDENTIFIER_SINGLE_QUOTE.pattern}|{_PATTERN_IDENTIFIER_DOUBLE_QUOTE.pattern}
        |{_PATTERN_IDENTIFIER_SQUARE_BRACKET.pattern}|{_PATTERN_IDENTIFIER_GRAVE_ACCENT.pattern}
        |{_PATTERN_IDENTIFIER_NO_QUOTE.pattern})
    )''')
_PATTERN_OBJECT_SCHEMA = re.compile(re.sub(r'(?<=\(\?P<)identifier', 'schema', _PATTERN_IDENTIFIER.pattern))
_PATTERN_OBJECT_TABLE = re.compile(re.sub(r'(?<=\(\?P<)identifier', 'table', _PATTERN_IDENTIFIER.pattern))
_PATTERN_OBJECT = re.compile(rf'''(?x:
    (?:{_PATTERN_OBJECT_SCHEMA.pattern}{_PATTERN_SPACE.pattern}*?\.{_PATTERN_SPACE.pattern}*?)?
    {_PATTERN_OBJECT_TABLE.pattern}
    )''')
_PATTERN_IGNORE = re.compile(rf'''(?x:
    {_PATTERN_SPACE.pattern}|{_PATTERN_IDENTIFIER_SINGLE_QUOTE.pattern}|{_PATTERN_IDENTIFIER_DOUBLE_QUOTE.pattern}
        |{_PATTERN_IDENTIFIER_SQUARE_BRACKET.pattern}|{_PATTERN_IDENTIFIER_GRAVE_ACCENT.pattern}|(?s:.)
    )''')
_PATTERN_IGNORE = re.compile(re.sub(r'\(\?P<(?s:.*?)>', '(?:', _PATTERN_IGNORE.pattern))
_PATTERN_IGNORE = re.compile(re.sub(r'\((?!\?)', '(?:', _PATTERN_IGNORE.pattern))
_PATTERN_QUERY_OPEN = re.compile(rf'''(?x:
    (?<=^)|(?<=;)
    )''')
_PATTERN_QUERY_CREATE_TABLE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_QUERY_OPEN.pattern}
    {_PATTERN_SPACE.pattern}*?(?i:CREATE)
    (?:{_PATTERN_SPACE.pattern}+?(?P<temporary>(?i:TEMP|TEMPORARY)))?
    {_PATTERN_SPACE.pattern}+?(?i:TABLE)
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:NOT){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}
    ))''')
_PATTERN_QUERY_CREATE_TABLE = re.compile(re.sub(r'(?<=\(\?P<)', 'create_table_', _PATTERN_QUERY_CREATE_TABLE.pattern))
_PATTERN_QUERY_ALTER_TABLE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_QUERY_OPEN.pattern}
    {_PATTERN_SPACE.pattern}*?(?i:ALTER){_PATTERN_SPACE.pattern}+?(?i:TABLE)
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}
    ))''')
_PATTERN_QUERY_ALTER_TABLE = re.compile(re.sub(r'(?<=\(\?P<)', 'alter_table_', _PATTERN_QUERY_ALTER_TABLE.pattern))
_PATTERN_QUERY_DROP_TABLE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_QUERY_OPEN.pattern}
    {_PATTERN_SPACE.pattern}*?(?i:DROP){_PATTERN_SPACE.pattern}+?(?i:TABLE)
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}
    ))''')
_PATTERN_QUERY_DROP_TABLE = re.compile(re.sub(r'(?<=\(\?P<)', 'drop_table_', _PATTERN_QUERY_DROP_TABLE.pattern))
_PATTERN_QUERY_CREATE_VIEW = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_QUERY_OPEN.pattern}
    {_PATTERN_SPACE.pattern}*?(?i:CREATE)
    (?:{_PATTERN_SPACE.pattern}+?(?P<temporary>(?i:TEMP|TEMPORARY)))?
    {_PATTERN_SPACE.pattern}+?(?i:VIEW)
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:NOT){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}
    ))''')
_PATTERN_QUERY_CREATE_VIEW = re.compile(re.sub(r'(?<=\(\?P<)', 'create_view_', _PATTERN_QUERY_CREATE_VIEW.pattern))
_PATTERN_QUERY_DROP_VIEW = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_QUERY_OPEN.pattern}
    {_PATTERN_SPACE.pattern}*?(?i:DROP){_PATTERN_SPACE.pattern}+?(?i:VIEW)
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}
    ))''')
_PATTERN_QUERY_DROP_VIEW = re.compile(re.sub(r'(?<=\(\?P<)', 'drop_view_', _PATTERN_QUERY_DROP_VIEW.pattern))
_PATTERN_QUERY_ATTACH_DATABASE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_QUERY_OPEN.pattern}
    {_PATTERN_SPACE.pattern}*?(?i:ATTACH)
    {_PATTERN_SPACE.pattern}+?(?i:DATABASE)
    {_PATTERN_SPACE.pattern}+?
    ))''')
_PATTERN_QUERY_ATTACH_DATABASE = re.compile(re.sub(r'(?<=\(\?P<)', 'attach_database_',
                                                   _PATTERN_QUERY_ATTACH_DATABASE.pattern))
_PATTERN_QUERY_DETACH_DATABASE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_QUERY_OPEN.pattern}
    {_PATTERN_SPACE.pattern}*?(?i:DETACH)
    (:{_PATTERN_SPACE.pattern}+?(?i:DATABASE))?
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT_SCHEMA.pattern}
    ))''')
_PATTERN_QUERY_DETACH_DATABASE = re.compile(re.sub(r'(?<=\(\?P<)', 'detach_database_',
                                                   _PATTERN_QUERY_DETACH_DATABASE.pattern))
_PATTERN_QUERY_SELECT_FROM = re.compile(rf'''(?x:(?P<query>
    (?<![0-9A-Z_a-z])
    (?i:FROM|JOIN)(?:{_PATTERN_SPACE.pattern}|\()*?
    {_PATTERN_OBJECT.pattern}
    ))''')
_PATTERN_QUERY_SELECT_FROM = re.compile(re.sub(r'(?<=\(\?P<)', 'select_from_', _PATTERN_QUERY_SELECT_FROM.pattern))
_PATTERN_SIMULATE = re.compile(rf'''(?x:
    {_PATTERN_IGNORE.pattern}*?
    (?:{_PATTERN_QUERY_CREATE_TABLE.pattern}|{_PATTERN_QUERY_ALTER_TABLE.pattern}|{_PATTERN_QUERY_DROP_TABLE.pattern}
        |{_PATTERN_QUERY_CREATE_VIEW.pattern}|{_PATTERN_QUERY_DROP_VIEW.pattern}
        |{_PATTERN_QUERY_ATTACH_DATABASE.pattern}|{_PATTERN_QUERY_DETACH_DATABASE.pattern}|$)
    )''')
_PATTERN_SUBSTITUTE = re.compile(rf'''(?x:
    {_PATTERN_IGNORE.pattern}*?
    (?:{_PATTERN_QUERY_SELECT_FROM.pattern}|$)
    )''')


class Cursor(sqlite3.Cursor):
    def execute(
            self: 'Cursor',
            sql: str,
            parameters: Union[Sequence[Any], Mapping[str, Any]] = (),
            /,
            *,
            transaction: Optional[date] = None,
            ) -> Cursor:
        self.simulate(sql, transaction)
        sql = self.substitute(sql, transaction)
        cursor = super().execute(sql, parameters)
        return cursor

    def executemany(
            self: 'Cursor',
            sql: str,
            parameters: Union[Sequence[Any], Mapping[str, Any], Iterator[Any]],
            /,
            *,
            transaction: Optional[date] = None,
            ) -> sqlite3.Cursor:
        self.simulate(sql, transaction)
        sql = self.substitute(sql, transaction)
        cursor = super().executemany(sql, parameters)
        return cursor

    def executescript(
            self: 'Cursor',
            sql_script: str,
            /,
            *,
            transaction: Optional[date] = None,
            ) -> sqlite3.Cursor:
        self.simulate(sql_script, transaction)
        sql_script = self.substitute(sql_script, transaction)
        cursor = super().executescript(sql_script)
        return cursor

    def simulate(
            self: 'Cursor',
            sql: str,
            transaction: Optional[date] = None,
            ) -> None:
        matches = re.finditer(_PATTERN_SIMULATE, sql)
        for match in matches:
            if match:
                if match.group('create_table_query'):
                    pass
                elif match.group('alter_table_query'):
                    pass
                elif match.group('drop_table_query'):
                    pass
                elif match.group('create_view_query'):
                    pass
                elif match.group('drop_view_query'):
                    pass
                elif match.group('attach_database_query'):
                    pass
                elif match.group('detach_database_query'):
                    pass
        return

    def substitute(
            self: 'Cursor',
            sql: str,
            transaction: Optional[date] = None,
            ) -> str:
        if transaction:
            matches = re.finditer(_PATTERN_SUBSTITUTE, sql)
            for match in reversed(list(matches)):
                if match:
                    if match.group('select_from_query'):
                        pass
        return sql


class Connection(sqlite3.Connection):
    def cursor(
            self: 'Connection',
            factory: Type['Cursor'] = Cursor,
            ) -> 'Cursor':
        cursor = super().cursor(factory)
        return cursor

    def simulate(
            self: 'Connection',
            sql: str,
            transaction: Optional[date] = None,
            ) -> None:
        cursor = self.cursor()
        cursor.simulate(sql, transaction)
        return

    def substitute(
            self: 'Connection',
            sql: str,
            transaction: Optional[date] = None,
            ) -> str:
        cursor = self.cursor()
        sql = cursor.substitute(sql, transaction)
        return sql

    def normalize(
            self: 'Connection',
            tables: Union[None, str, Iterable[str]] = None,
            ) -> None:
        cursor = super().cursor()
        cursor.row_factory = sqlite3.Row
        in_transaction = self.in_transaction
        if not in_transaction:
            cursor.execute(_SQL_TRANSACTION_BEGIN)
        cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_TABLE)
        cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_TABLE_EXIST)
        cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_TABLE_NAME)
        cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_COLUMN)
        cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_COLUMN_EXIST)
        cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_COLUMN_NAME)
        if tables is None:
            tables = cursor.execute(_SQL_SELECT_FROM_SQLITE_SCHEMA).fetchall()
            tables = [record['name'] for record in tables]
        elif isinstance(tables, str):
            tables = [tables]
        transaction = datetime.now()
        exist = 1
        for table_name in tables:
            table_id = cursor.execute(_SQL_INSERT_INTO_SQLITE6NF_TABLE).fetchone()['id']
            table_parameters = {'id': table_id, 'transaction': transaction, 'exist': exist, 'name': table_name}
            table_format = {'table_id': table_id, 'table_name': table_name.replace('"', '""')}
            cursor.execute(_SQL_INSERT_INTO_SQLITE6NF_TABLE_EXIST, table_parameters)
            cursor.execute(_SQL_INSERT_INTO_SQLITE6NF_TABLE_NAME, table_parameters)
            cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_INSTANCE.format(**table_format))
            cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_INSTANCE_EXIST.format(**table_format))
            cursor.execute(_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_INSERT_INSTANCE.format(**table_format))
            cursor.execute(_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_DELETE_INSTANCE.format(**table_format))
            columns = cursor.execute(_SQL_SELECT_FROM_PRAGMA_TABLE_INFO, table_parameters).fetchall()
            columns = [[record['name'], record['type']] for record in columns]
            for column_name, dtype in columns:
                column_id = cursor.execute(_SQL_INSERT_INTO_SQLITE6NF_COLUMN, table_format).fetchone()['id']
                column_parameters = {**table_parameters, 'id': column_id, 'name': column_name}
                column_format = {**table_format, 'column_id': column_id, 'column_name': column_name.replace('"', '""'),
                                 'dtype': dtype}
                cursor.execute(_SQL_INSERT_INTO_SQLITE6NF_COLUMN_EXIST, column_parameters)
                cursor.execute(_SQL_INSERT_INTO_SQLITE6NF_COLUMN_NAME, column_parameters)
                cursor.execute(_SQL_CREATE_TABLE_SQLITE6NF_INSTANCE_VALUE.format(**column_format))
                cursor.execute(_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_INSERT_INSTANCE_VALUE.format(**column_format))
                cursor.execute(_SQL_CREATE_TRIGGER_SQLITE6NF_TRIGGER_UPDATE_INSTANCE_VALUE.format(**column_format))
        if not in_transaction:
            cursor.execute(_SQL_TRANSACTION_COMMIT)
        cursor.close()
        return


def connect(
        database: Union[str, bytes, PathLike],
        timeout: float = 5.0,
        detect_types: int = 0,
        isolation_level: Union[str, None] = 'DEFERRED',
        check_same_thread: bool = True,
        factory: Type['Connection'] = Connection,
        cached_statements: int = 128,
        uri: bool = False,
        ) -> 'Connection':
    connection = sqlite3.connect(**locals())
    return connection
