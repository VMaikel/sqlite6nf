# Overview

Sqlite6nf is an extension to the standard sqlite3 module adding built-in support for tables in 6th normal form
(6nf from now on). A table in 6nf has each non-primary key column split into a separate table. These new tables
can then be made temporal by adding meta columns containing timestamps. Furthermore, temporality requires
records to be only added, but never changed or deleted. Temporal tables allow data to be seen as it was during
different moments in time, instead of only showing the latest state of the database. Sqlite6nf adds temporal
support for both table structure (tables and columns) and table content (records).

# Issues

Please be aware that sqlite6nf is currently in a development phase. Many of its features are currently still
untested, incomplete or missing. During the development phase no attempt is made to remain compatible with
previous versions. Using sqlite6nf in its current state could create issues later on for a database. Once
sqlite6nf reaches the production phase in version 1.0 all future versions will be made compatible with it.

Below are all features which are currently untested, incomplete or missing. Once all these issues are closed,
production version 1.0 will have been reached.

* Documentation
	- [ ] [#1 Expand the description of README and the module docstring.](https://github.com/VMaikel/sqlite6nf/issues/1)
	- [ ] [#2 Add docstrings and comments to the sqlite query constants.](https://github.com/VMaikel/sqlite6nf/issues/2)
	- [ ] [#3 Add docstrings and comments to the regex pattern constants.](https://github.com/VMaikel/sqlite6nf/issues/3)
	- [ ] [#4 Add docstrings and comments to the Python functions and classes.](https://github.com/VMaikel/sqlite6nf/issues/4)
* Bugs
	- [ ] [#5 Cursor.normalise() does not validate the tables argument.](https://github.com/VMaikel/sqlite6nf/issues/5)
	- [ ] [#6 Shadow tables are not populated with initial values.](https://github.com/VMaikel/sqlite6nf/issues/6)
	- [ ] [#7 Transaction time is not consistently calculated.](https://github.com/VMaikel/sqlite6nf/issues/7)
* Questions
	- [ ] [#8 Verify SQL injection safety.](https://github.com/VMaikel/sqlite6nf/issues/8)
	- [ ] [#9 Verify proper case (insensitivity) handling of SQLite queries.](https://github.com/VMaikel/sqlite6nf/issues/9)
	- [ ] [#10 Verify proper Unicode handling of SQLite queries.](https://github.com/VMaikel/sqlite6nf/issues/10)
	- [ ] [#11 Verify proper transaction and savepoint handling.](https://github.com/VMaikel/sqlite6nf/issues/11)
	- [ ] [#12 Verify whether sqlite3 aliases should use single or double quotes.](https://github.com/VMaikel/sqlite6nf/issues/12)
	- [ ] [#13 Verify proper handling of tables without rowid.](https://github.com/VMaikel/sqlite6nf/issues/13)
	- [ ] [#14 Verify proper handling of tables with a multi-column primary key.](https://github.com/VMaikel/sqlite6nf/issues/14)
	- [ ] [#15 Verify if the ‘VACUUM’ statement causes issues with the used rowid values.](https://github.com/VMaikel/sqlite6nf/issues/15)
* Enhancements
	- [ ] [#16 Add support for selecting records.](https://github.com/VMaikel/sqlite6nf/issues/16)
	- [ ] [#17 Add support for altering tables.](https://github.com/VMaikel/sqlite6nf/issues/17)
	- [ ] [#18 Add support for dropping tables.](https://github.com/VMaikel/sqlite6nf/issues/18)
	- [ ] [#19 Add support for temporary tables.](https://github.com/VMaikel/sqlite6nf/issues/19)
	- [ ] [#20 Add support for virtual tables](https://github.com/VMaikel/sqlite6nf/issues/20)
	- [ ] [#21 Add support for creating views.](https://github.com/VMaikel/sqlite6nf/issues/21)
	- [ ] [#22 Add support for dropping views.](https://github.com/VMaikel/sqlite6nf/issues/22)
	- [ ] [#23 Add support for temporary views.](https://github.com/VMaikel/sqlite6nf/issues/23)
	- [ ] [#24 Add support for attaching and detaching databases.](https://github.com/VMaikel/sqlite6nf/issues/24)
	- [ ] [#25 Add support for join statements which use a comma (,) instead of the keyword 'JOIN'.](https://github.com/VMaikel/sqlite6nf/issues/25)
	- [ ] [#26 Add support for record changes from within triggers when recursive triggers are disabled.](https://github.com/VMaikel/sqlite6nf/issues/26)
	- [ ] [#27 Add support for temporal criteria from within queries.](https://github.com/VMaikel/sqlite6nf/issues/27)
	- [ ] [#28 Add support for user defined Connection and Cursor objects.](https://github.com/VMaikel/sqlite6nf/issues/28)
	- [ ] [#29 Add support for user defined meta-columns.](https://github.com/VMaikel/sqlite6nf/issues/29)
	- [ ] [#30 Add support for table normalisation on a per-column basis.](https://github.com/VMaikel/sqlite6nf/issues/30)
	- [ ] [#31 Add support for deleting old historized data.](https://github.com/VMaikel/sqlite6nf/issues/31)
