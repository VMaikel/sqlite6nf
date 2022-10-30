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

Below are all features which are currently untested, incomplete or missing. Once all items are checked off,
production version 1.0 will have been reached.
    [] Verify sql injection safety.
    [] Verify proper case (insensitivity) handling.
    [] Verify proper unicode handling.
    [] Verify proper transaction and savepoint handling.
    [] Verify whether sqlite3 aliases should use single or double quotes.
    [] Verify proper handling of tables without rowid.
    [] Verify proper handling of tables with a multi-column primary key.
    [] Verify proper use of rowid values after the 'VACUUM' statement has been executed on a database.
    [] Verify proper handling of the Cursor.normalise() method when provided with incorrect table names.
    [] Populate shadow tables with initial values during their creation.
    [] Add support for selecting records.
    [] Add support for altering tables.
    [] Add support for dropping tables.
    [] Add support for temporary tables.
    [] Add support for creating views.
    [] Add support for dropping views.
    [] Add support for temporary views.
    [] Add support for attaching and detaching databases.
    [] Add support for join statements which use a comma (,) instead of the keyword 'JOIN'.
    [] Add support for record changes from within triggers when recursive triggers are disabled.
    [] Add support for user defined Connection and Cursor objects.
    [] Add support for user defined timestamps (like valid time) alongside the default transaction time.
    [] Add support for table normalisation on a per-column basis.
    [] Investigate possibility to set transaction time equal to commit time.
    [] Investigate and possibly add support for temporal criteria within queries instead of requiring them as
        arguments.
    [] Investigate and possibly add support for non-timestamp meta columns.
    [] Investigate and possibly add support for virtual tables.
    [] Investigate and possibly add support for easily deleting old historized content and structure.