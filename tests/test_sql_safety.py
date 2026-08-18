"""TDD for the read-only SQL guard behind the 'Ask the data' tab.

The generated SQL runs against a read-only DuckDB connection, but we defend in
depth: only a single SELECT/WITH…SELECT statement is ever executed. Anything that
could write, attach, copy out, or run multiple statements is rejected loudly.
"""

from __future__ import annotations

import pytest

from sql_safety import assert_read_only, is_read_only_select

OK = [
    "select 1",
    "SELECT * FROM main.mart_permits_monthly",
    "  select count(*) from mart_metrics  ",
    "with x as (select 1 as v) select v from x",
    "select * from mart_air_monthly order by obs_month;",  # trailing semicolon ok
    "-- a comment\nselect 1",
]

BAD = [
    "",
    "   ",
    "insert into t values (1)",
    "update t set x=1",
    "delete from t",
    "drop table t",
    "create table t as select 1",
    "alter table t add column x int",
    "attach 'evil.db' as e",
    "copy (select 1) to 'out.csv'",
    "pragma database_list",
    "install httpfs",
    "load httpfs",
    "select 1; drop table t",  # multiple statements
    "select 1; select 2",  # multiple statements
]


@pytest.mark.parametrize("sql", OK)
def test_read_only_accepts(sql):
    assert is_read_only_select(sql) is True


@pytest.mark.parametrize("sql", BAD)
def test_read_only_rejects(sql):
    assert is_read_only_select(sql) is False


def test_assert_read_only_raises_loudly():
    with pytest.raises(ValueError, match="read-only"):
        assert_read_only("drop table t")


def test_assert_read_only_returns_clean_sql():
    # Strips a trailing semicolon so the caller can run it directly.
    assert assert_read_only("select 1;") == "select 1"
