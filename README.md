# Overview
sqlite6nf is an extension to the sqlite3 module adding support for temporal tables as defined by the [SQL:2011 (ISO/IEC 9075:2011) standard](https://cs.ulb.ac.be/public/_media/teaching/infoh415/tempfeaturessql2011.pdf). Temporal tables add a time dimension to regular tables. This can for example be used for logging all row changes or viewing data from different moments in time.

# Usage
All temporal tables use a period in order to store the time component. A period consists of 2 conventional columns which represent the start time (included) and end time (excluded). All temporal periods have the constraint `PeriodStart < PeriodEnd`. There exist 2 types of periods: application-time (a.k.a. valid time) and system-time (a.k.a. transaction time). A table can have both period types at the same time.

## Application-time period tables
The values of application-time periods are defined by the user and can be changed at any time. It's possible for a table to have multiple application-time periods at once.

### CREATE
The application-time period needs to be explicitly defined during the `CREATE` statement.
```sql
CREATE TABLE TableName (
[...],
PeriodStart [...],
PeriodEnd [...],
PERIOD FOR PeriodName (PeriodStart, PeriodEnd)
);
```

The application-time period can be used as part of a primary key. Doing so assures that the timeframe of primary keys does not overlap.
```sql
PRIMARY KEY ([...], PeriodName WITHOUT OVERLAPS)
```

The application-time period can also be used as part of a foreign key. Doing so assures that the foreign key exists for the entire duration in the parent table.
```sql
FOREIGN KEY ([...], PERIOD PeriodName) REFERENCES ParentTableName ([...], PERIOD ParentPeriodName)
```

### UPDATE AND DELETE
Rows can be updated based on their application-time period. If the period is not fully contained within the criteria then the row is split up. The original row is updated with the new values and its period columns are made to fit within the criteria. For the timeframe outside the criteria new rows are inserted with corresponding period values. The remaining column values of these rows remain the same as the original values from before the update.
```sql
UPDATE TableName
FOR PORTION OF PeriodName
FROM TimestampStart
TO TimestampEnd
[...];
```

For deletion the same rules apply as for updating, except that the original row is deleted instead.
```sql
DELETE FROM TableName
FOR PORTION OF PeriodName
FROM TimestampStart
TO TimestampEnd
[...];
```

### SELECT
The application-time periods can be used for selecting rows. A period value can be either `PeriodName`, `PERIOD (PeriodStart, PeriodEnd)` or any conventional column/value. The following table contains the possible comparisons which can be done on period values and includes their equivalent conditions:
| Comparison | Period1 COMPARISON Period2 | Period COMPARISON Timestamp | Timestamp COMPARISON Period |
| :---: | :---: | :---: | :---: |
EQUALS | `Period1Start=Period2Start AND Period1End=Period2End` | `PeriodStart=Timestamp AND PeriodEnd=Timestamp` which is always false | `Timestamp=PeriodStart AND Timestamp=PeriodEnd` which is always false
CONTAINS | `Period1Start<=Period2Start AND Period1End>=Period2End` | `PeriodStart<=Timestamp AND PeriodEnd>Timestamp` | `Timestamp<=PeriodStart AND Timestamp>PeriodEnd` which is always false
OVERLAPS | `Period1Start<Period2End AND Period1End>Period1Start` | `PeriodStart<=Timestamp AND PeriodEnd>Timestamp` | `Timestamp>=PeriodStart AND Timestamp<PeriodEnd`
PRECEDES | `Period1End<=Period2Start` | `PeriodEnd<=Timestamp` | `Timestamp<PeriodStart`
IMMEDIATELY PRECEDES | `Period1End=Period2Start` | `PeriodEnd=Timestamp` | Always false
SUCCEEDS | `Period1Start>=Period2End` | `PeriodStart>Timestamp` | `Timestamp>=PeriodEnd`
IMMEDIATELY SUCCEEDS | `Period1Start=Period2End` | Always false | `Timestamp=PeriodEnd`

## System-versioned tables
The values of system-time periods are automatically defined and should never be changed by the user. The current system time remains the same for an entire transaction. System-versioned tables differentiates between current system rows and historical rows. The period of current system rows contains the current system time and ends at `9999-12-31 23:59:59`. Historical rows can be considered either changed or deleted.

### CREATE
The system-time period needs to be explicitly defined during the `CREATE` statement and requires the name `SYSTEM_TIME`.
```sql
CREATE TABLE TableName (
[...],
PeriodStart [...] GENERATED ALWAYS AS ROW START,
PeriodEnd [...] GENERATED ALWAYS AS ROW END,
PERIOD FOR SYSTEM_TIME (PeriodStart, PeriodEnd)
) WITH SYSTEM VERSIONING;
```

Constraints (including primary keys and foreign keys) only affect current system rows. Both the system-period and its columns don't need to be manually specified during the creation of these constraints.

### UPDATE and DELETE
Only current system rows are directly affected by `UPDATE` and `DELETE` statements. When a row is updated a copy of the original row is automatically inserted. The `PeriodStart` of the original row and `PeriodEnd` of the newly inserted row are both set to the current system time of the transaction. When a row is deleted the `PeriodEnd` column is set to the current system time of the transaction. The `FOR PORTION OF PeriodName` clause is not possible for system-time periods.

### SELECT
The system-time periods can be used for selecting rows. The following criteria can be used on period values between the `FROM` and `WHERE` clause:
- `FOR SYSTEM_TIME AS OF Timestamp`, which is equivalent to `PeriodStart<=Timestamp AND PeriodEnd>Timestamp`.
- `FOR SYSTEM_TIME FROM TimestampStart TO TimestampEnd`, which is equivalent to `PeriodStart<=TimestampStart AND PeriodEnd<TimestampEnd`.
- `FOR SYSTEM_TIME BETWEEN TimestampStart AND TimestampEnd`, which is equivalent to `PeriodStart<=TimestampStart AND PeriodEnd<=TimestampEnd`.

When no system-time period is specified only the current system rows are returned, which is equivalent to `FOR SYSTEM_TIME AS OF Now`.

# Development
sqlite6nf is currently in a development phase. Many of its features are currently still untested, incomplete or missing. During the development phase no attempt is made to remain compatible with previous versions. Using sqlite6nf in its current state could create issues later on for a database. Once sqlite6nf reaches the production phase in version 1.0 all future versions will be made compatible with it.

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
