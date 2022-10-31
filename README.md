# Overview

sqlite6nf is an extension to the standard sqlite3 module adding built-in support for tables in 6th normal form
(6nf from now on). A table in 6nf has each non-primary key column split into a separate table. These new tables
can then be made temporal by adding meta columns containing timestamps. Furthermore, temporality requires
records to be only added, but never changed or deleted. Temporal tables allow data to be seen as it was during
different moments in time, instead of only showing the latest state of the database. sqlite6nf adds temporal
support for both table structure (tables and columns) and table content (records).

# Issues

sqlite6nf is currently in a development phase. Many of its features are currently still untested, incomplete or
missing. During the development phase no attempt is made to remain compatible with previous versions. Using
sqlite6nf in its current state could create issues later on for a database. Once sqlite6nf reaches the
production phase in version 1.0 all future versions will be made compatible with it.

Below are all features which are currently untested, incomplete or missing. Once all these issues are closed,
production version 1.0 is reached.

* Documentation
	- [ ] [Expand the description of README and the module docstring. #1](https://github.com/VMaikel/sqlite6nf/issues/1)
	- [ ] [Add docstrings and comments to the SQLite query constants. #2](https://github.com/VMaikel/sqlite6nf/issues/2)
	- [x] [Add docstrings and comments to the regex pattern constants. #3](https://github.com/VMaikel/sqlite6nf/issues/3)
	- [ ] [Add docstrings and comments to the Python functions and classes. #4](https://github.com/VMaikel/sqlite6nf/issues/4)
	- [ ] [Add proper repository structure. #32](https://github.com/VMaikel/sqlite6nf/issues/32)
	- [x] [Add the .gitignore file. #33](https://github.com/VMaikel/sqlite6nf/issues/33)
	- [ ] [Add licensing information. #34](https://github.com/VMaikel/sqlite6nf/issues/34)
	- [ ] [Add unit tests. #35](https://github.com/VMaikel/sqlite6nf/issues/35)
	- [ ] [Add code samples. #36](https://github.com/VMaikel/sqlite6nf/issues/36)
* Bugs
	- [ ] [Cursor.normalise() does not validate the tables argument. #5](https://github.com/VMaikel/sqlite6nf/issues/5)
	- [ ] [Shadow tables are not populated with initial values. #6](https://github.com/VMaikel/sqlite6nf/issues/6)
	- [ ] [Transaction time is not consistently calculated. #7](https://github.com/VMaikel/sqlite6nf/issues/7)
* Questions
	- [ ] [Verify SQL injection safety. #8](https://github.com/VMaikel/sqlite6nf/issues/8)
	- [ ] [Verify proper case (insensitivity) handling of SQLite queries. #9](https://github.com/VMaikel/sqlite6nf/issues/9)
	- [ ] [Verify proper Unicode handling of SQLite queries. #10](https://github.com/VMaikel/sqlite6nf/issues/10)
	- [ ] [Verify proper transaction and savepoint handling. #11](https://github.com/VMaikel/sqlite6nf/issues/11)
	- [ ] [Verify whether sqlite3 aliases should use single or double quotes. #12](https://github.com/VMaikel/sqlite6nf/issues/12)
	- [ ] [Verify proper handling of tables without rowid. #13](https://github.com/VMaikel/sqlite6nf/issues/13)
	- [ ] [Verify proper handling of tables with a multi-column primary key. #14](https://github.com/VMaikel/sqlite6nf/issues/14)
	- [ ] [Verify if the ‘VACUUM’ statement causes issues with the used rowid values. #15](https://github.com/VMaikel/sqlite6nf/issues/15)
* Enhancements
	- [ ] [Add support for selecting records. #16](https://github.com/VMaikel/sqlite6nf/issues/16)
	- [ ] [Add support for altering tables. #17](https://github.com/VMaikel/sqlite6nf/issues/17)
	- [ ] [Add support for dropping tables. #18](https://github.com/VMaikel/sqlite6nf/issues/18)
	- [ ] [Add support for temporary tables. #19](https://github.com/VMaikel/sqlite6nf/issues/19)
	- [ ] [Add support for virtual tables #20](https://github.com/VMaikel/sqlite6nf/issues/20)
	- [ ] [Add support for creating views. #21](https://github.com/VMaikel/sqlite6nf/issues/21)
	- [ ] [Add support for dropping views. #22](https://github.com/VMaikel/sqlite6nf/issues/22)
	- [ ] [Add support for temporary views. #23](https://github.com/VMaikel/sqlite6nf/issues/23)
	- [ ] [Add support for attaching and detaching databases. #24](https://github.com/VMaikel/sqlite6nf/issues/24)
	- [ ] [Add support for join statements which use a comma (,) instead of the keyword 'JOIN'. #25](https://github.com/VMaikel/sqlite6nf/issues/25)
	- [ ] [Add support for record changes from within triggers when recursive triggers are disabled. #26](https://github.com/VMaikel/sqlite6nf/issues/26)
	- [ ] [Add support for temporal criteria from within queries. #27](https://github.com/VMaikel/sqlite6nf/issues/27)
	- [ ] [Add support for user defined Connection and Cursor objects. #28](https://github.com/VMaikel/sqlite6nf/issues/28)
	- [ ] [Add support for user defined meta-columns. #29](https://github.com/VMaikel/sqlite6nf/issues/29)
	- [ ] [Add support for table normalisation on a per-column basis. #30](https://github.com/VMaikel/sqlite6nf/issues/30)
	- [ ] [Add support for deleting old historized data. #30](https://github.com/VMaikel/sqlite6nf/issues/31)
