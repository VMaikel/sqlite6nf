#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Extension to the sqlite3 module adding support for temporal tables.

sqlite6nf is an extension to the sqlite3 module adding support for temporal tables as defined by the SQL:2011
(ISO/IEC 9075:2011) standard. Temporal tables add a time dimension to regular tables. This can for example be
used for logging all row changes or viewing data from different moments in time.


The sqlite6nf module is split into 3 parts:
    * The SQLite code for creating, updating and selecting from shadow tables.
    * The regex code for interpreting and altering queries.
    * The Python code for changing the default behaviour of the sqlite3 module.

The specif behaviour of sqlite6nf is explained further in each of these parts. For the default behaviour please
see the sqlite3 documentation.


sqlite6nf is currently in a development phase. Many of its features are currently still untested, incomplete or
missing. During the development phase no attempt is made to remain compatible with previous versions. Using
sqlite6nf in its current state could create issues later on for a database. Once sqlite6nf reaches the
production phase in version 1.0 all future versions will be made compatible with it.
"""


__author__ = 'Maikel Verbeek'
__copyright__ = 'Copyright (C) 2022 Maikel Verbeek'
__version__ = '0.2.2'
__date__ = '2022/11/15'
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


"""
The following constants contain all regex patterns used in sqlite6nf. Their main purpose is to identify the
type and components of SQLite queries.

Apart from where necessary for identification, no syntactic verification is done on queries. It is expected
that sqlite3 will catch any invalid syntax and exit execution accordingly.

Comments (single and multiline) and quotes (single, double, square bracket and grave accent) are each treated
as a single segment. Single quotes, double quotes and grave accents can only be closed by an odd number of
characters of the same type in a row.

The pattern constants loosely follow the structure below:
├── Ignore: Any part which is not used by sqlite6nf.
│   └── Space: Any part which is ignored by the SQLite interpreter.
│       └── Comment: Single and multiline comments.
├── Object: A complete reference to a table object.
│   └── Identifier: Any part which is recognised by the sqlite interpreter as a standalone name.
└── Query: SQLite queries which are analysed by sqlite6nf.


Below are all parts which are currently incomplete or missing in the pattern constants. These issues will be
fixed before production version 1.0 is reached.
    * The 'alter_table' pattern is missing the 'RENAME TO', 'RENAME COLUMN TO', 'ADD COLUMN' and 'DROP COLUMN'
        query segments.
    * The 'attach_database' pattern is missing the 'schema' query segment.
    * The 'select_from' pattern is missing the 'JOIN object' query segment which use a comma (,) instead of the
        keyword 'JOIN'.
"""
# Comments end either by being closed or reaching the end of the string.
# Ending a string with '/*' results in a sqlite3 syntax error.
_PATTERN_COMMENT_SINGLE_LINE = re.compile(r'''(?x:
    --  # Open
    (?s:.*?)  # Comment
    (?:\n|$)  # Close
    )''')
_PATTERN_COMMENT_MULTI_LINE = re.compile(r'''(?x:
    /\*  # Open
    (?s:.*?)  # Comment
    (?:\*/|$)  # Close
    )''')
_PATTERN_COMMENT = re.compile(rf'''(?x:
    {_PATTERN_COMMENT_SINGLE_LINE.pattern}|{_PATTERN_COMMENT_MULTI_LINE.pattern}
    )''')
_PATTERN_SPACE = re.compile(rf'''(?x:
    \s|{_PATTERN_COMMENT.pattern}
    )''')
# Identifiers with single quotes, double quotes or grave accents can only be closed by an odd number of
# characters of the same type in a row.
# If a quoted identifier is not closed, SQLite will throw an operational error. In order to avoid the regex
# pattern matching from mixing up the quoted and unquoted parts in these cases, the '$' sign has been added as
# a substitute for a closing quote.
_PATTERN_IDENTIFIER_SINGLE_QUOTE = re.compile(r'''(?x:
    '  # Open
    (?P<identifier_single_quote>(?s:.*?)[^'](?:'{2})*)  # Identifier
    (?:'(?!')|$)  # Close
    )''')
_PATTERN_IDENTIFIER_DOUBLE_QUOTE = re.compile(r'''(?x:
    "  # Open
    (?P<identifier_double_quote>(?s:.*?)[^"](?:"{2})*)  # Identifier
    (?:"(?!")|$)  # Close
    )''')
_PATTERN_IDENTIFIER_SQUARE_BRACKET = re.compile(r'''(?x:
    \[  # Open
    (?P<identifier_square_bracket>(?s:.*?))  # Identifier
    (?:]|$)  # Close
    )''')
_PATTERN_IDENTIFIER_GRAVE_ACCENT = re.compile(r'''(?x:
    `  # Open
    (?P<identifier_grave_accent>(?s:.*?)[^`](?:`{2})*)  # Identifier
    (?:`(?!`)|$)  # Close
    )''')
# An identifier without quotes can only contain alphanumeric characters (including underscores) and may not
# begin with a number.
_PATTERN_IDENTIFIER_NO_QUOTE = re.compile(r'''(?x:
    (?<![0-9A-Z_a-z])  # Open
    (?P<identifier_no_quote>[A-Z_a-z][0-9A-Z_a-z]*?)  # Identifier
    (?![0-9A-Z_a-z])  # Close
    )''')
_PATTERN_IDENTIFIER = re.compile(rf'''(?x:
    (?P<identifier>{_PATTERN_IDENTIFIER_SINGLE_QUOTE.pattern}|{_PATTERN_IDENTIFIER_DOUBLE_QUOTE.pattern}
        |{_PATTERN_IDENTIFIER_SQUARE_BRACKET.pattern}|{_PATTERN_IDENTIFIER_GRAVE_ACCENT.pattern}
        |{_PATTERN_IDENTIFIER_NO_QUOTE.pattern})
    )''')
# Rename all named capturing groups starting with 'identifier' to 'schema'.
_PATTERN_OBJECT_SCHEMA = re.compile(re.sub(r'(?<=\(\?P<)identifier', 'schema', _PATTERN_IDENTIFIER.pattern))
# Rename all named capturing groups starting with 'identifier' to 'table'.
_PATTERN_OBJECT_TABLE = re.compile(re.sub(r'(?<=\(\?P<)identifier', 'table', _PATTERN_IDENTIFIER.pattern))
# The schema is an optional part of an object.
# Whitespace is allowed both before and after the schema dot, regardless of which identifier quotes are used.
_PATTERN_OBJECT = re.compile(rf'''(?x:
    (?:{_PATTERN_OBJECT_SCHEMA.pattern}{_PATTERN_SPACE.pattern}*?\.{_PATTERN_SPACE.pattern}*?)?  # Schema
    {_PATTERN_OBJECT_TABLE.pattern}  # Table
    )''')
_PATTERN_IGNORE = re.compile(rf'''(?x:
    {_PATTERN_SPACE.pattern}|{_PATTERN_IDENTIFIER_SINGLE_QUOTE.pattern}|{_PATTERN_IDENTIFIER_DOUBLE_QUOTE.pattern}
        |{_PATTERN_IDENTIFIER_SQUARE_BRACKET.pattern}|{_PATTERN_IDENTIFIER_GRAVE_ACCENT.pattern}|(?s:.)
    )''')
# Change all named capturing groups to non-capturing groups.
_PATTERN_IGNORE = re.compile(re.sub(r'\(\?P<(?s:.*?)>', '(?:', _PATTERN_IGNORE.pattern))
# Change all unnamed capturing groups to non-capturing groups.
_PATTERN_IGNORE = re.compile(re.sub(r'\((?!\?)', '(?:', _PATTERN_IGNORE.pattern))
# '^' and ';' have a different length (0 and 1 respectively) and therefore need a separate lookbehind.
_PATTERN_QUERY = re.compile(rf'''(?x:
    (?:(?<=^)|(?<=;))  # Open
    {_PATTERN_IGNORE.pattern}*?  # Query
    (?:;|$)  # Close
    )''')
_PATTERN_QUERY_CREATE_TABLE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_SPACE.pattern}*?(?i:CREATE)  # Create
    (?:{_PATTERN_SPACE.pattern}+?(?P<temporary>(?i:TEMP|TEMPORARY)))?  # Temporary
    {_PATTERN_SPACE.pattern}+?(?i:TABLE)  # Table
    # If not exists
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:NOT){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}  # Object
    ))''')
# At the moment the 'alter_table' pattern is missing the 'RENAME TO', 'RENAME COLUMN TO', 'ADD COLUMN' and
# 'DROP COLUMN' query segments.
_PATTERN_QUERY_ALTER_TABLE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_SPACE.pattern}*?(?i:ALTER){_PATTERN_SPACE.pattern}+?(?i:TABLE)  # Alter table
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}  # Object
    # TBA
    ))''')
# The 'DROP TABLE' query can also be used on virtual tables.
_PATTERN_QUERY_DROP_TABLE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_SPACE.pattern}*?(?i:DROP){_PATTERN_SPACE.pattern}+?(?i:TABLE)  # Drop table
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?  # If exists
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}  # Object
    ))''')
_PATTERN_QUERY_CREATE_VIEW = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_SPACE.pattern}*?(?i:CREATE)  # Create
    (?:{_PATTERN_SPACE.pattern}+?(?P<temporary>(?i:TEMP|TEMPORARY)))?  # Temporary
    {_PATTERN_SPACE.pattern}+?(?i:VIEW)  # View
    # If not exists
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:NOT){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}  # Object
    ))''')
_PATTERN_QUERY_DROP_VIEW = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_SPACE.pattern}*?(?i:DROP){_PATTERN_SPACE.pattern}+?(?i:VIEW)  # Drop view
    (?:{_PATTERN_SPACE.pattern}+?(?i:IF){_PATTERN_SPACE.pattern}+?(?i:EXISTS))?  # If exists
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT.pattern}  # Object
    ))''')
# At the moment the 'attach_database' pattern is missing the 'schema' query segment.
_PATTERN_QUERY_ATTACH_DATABASE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_SPACE.pattern}*?(?i:ATTACH)  # Attach
    {_PATTERN_SPACE.pattern}+?(?i:DATABASE)  # Database
    {_PATTERN_SPACE.pattern}+?  # TBA
    ))''')
_PATTERN_QUERY_DETACH_DATABASE = re.compile(rf'''(?x:(?P<query>
    {_PATTERN_SPACE.pattern}*?(?i:DETACH)  # Detach
    (?:{_PATTERN_SPACE.pattern}+?(?i:DATABASE))?  # Database
    {_PATTERN_SPACE.pattern}*?{_PATTERN_OBJECT_SCHEMA.pattern}  # Schema
    ))''')
# The 'select_from' pattern contains both 'FROM object' and 'JOIN object' query segments.
# An object may be proceeded by an unlimited amount of opening round brackets.
# At the moment the 'select_from' pattern is missing the 'JOIN object' query segment which use a comma instead
# of the keyword 'JOIN'.
_PATTERN_QUERY_SELECT_FROM = re.compile(rf'''(?x:(?P<query>
    (?<![0-9A-Z_a-z])(?i:FROM|JOIN)  # From/join
    (?:{_PATTERN_SPACE.pattern}|\()*?  # Opening brackets
    (?!(?i:WITH|SELECT)(?![0-9A-Z_a-z])) # Not a subquery
    {_PATTERN_OBJECT.pattern}  # Object
    (?!{_PATTERN_SPACE.pattern}*?\() # Not a function
    ))''')


class Cursor(sqlite3.Cursor):
    def execute(
            self: 'Cursor',
            sql: str,
            parameters: Union[Sequence[Any], Mapping[str, Any]] = (),
            /,
            *,
            transaction: Optional[date] = None,
            ) -> Cursor:
        super().execute(sql, parameters)
        return self

    def executemany(
            self: 'Cursor',
            sql: str,
            parameters: Union[Sequence[Any], Mapping[str, Any], Iterator[Any]],
            /,
            *,
            transaction: Optional[date] = None,
            ) -> sqlite3.Cursor:
        super().executemany(sql, parameters)
        return self

    def executescript(
            self: 'Cursor',
            sql_script: str,
            /,
            *,
            transaction: Optional[date] = None,
            ) -> sqlite3.Cursor:
        super().executescript(sql_script)
        return self


class Connection(sqlite3.Connection):
    def cursor(
            self: 'Connection',
            factory: Type['Cursor'] = Cursor,
            ) -> 'Cursor':
        cursor = super().cursor(factory)
        return cursor

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
