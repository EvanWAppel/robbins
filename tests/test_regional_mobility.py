from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(model):
    return (ROOT / 'models/marts' / model).read_text().replace(
        "{{ config(materialized='table') }}", ''
    ).replace("{{ ref('stg_ntd_ridership') }}", 'stg_ntd_ridership')


def test_new_ferries_keep_their_operator_identity(ntd_database):
    rows = dict(ntd_database.execute(render('mart_ferry_by_operator.sql')).fetchall())
    assert rows == {'Washington State Ferries': 10, 'King County Water Taxi': 7,
                    'Kitsap Transit': 20, 'Pierce County Ferry': 5}


def test_unknown_operator_is_not_relabelled_as_king_county(ntd_database):
    ntd_database.execute("insert into stg_ntd_ridership values ('Future Ferry', 'Future Ferry', true, '2024-01-01', 1)")
    rows = dict(ntd_database.execute(render('mart_ferry_by_operator.sql')).fetchall())
    assert rows['Future Ferry'] == 1


def test_coverage_preserves_ferry_split_and_reporting_window(ntd_database):
    rows = ntd_database.execute(render('mart_mobility_coverage.sql')).df()
    assert len(rows) == 6
    king_ferry = rows[(rows.agency == 'King County') & rows.is_ferry].iloc[0]
    assert king_ferry.boardings == 3
    assert king_ferry.months_reported == 1
    assert str(king_ferry.first_month.date()) == '2024-01-01'


def test_wsf_share_does_not_assume_wsf_is_largest():
    import pandas as pd
    import pytest

    from mobility import operator_share

    operators = pd.DataFrame({'operator': ['Kitsap Transit', 'Washington State Ferries'], 'boardings': [20, 10]})
    assert operator_share(operators, 'Washington State Ferries') == pytest.approx(100 / 3)
    assert operator_share(operators, 'Missing operator') is None
    assert operator_share(operators.assign(boardings=0), 'Washington State Ferries') is None
