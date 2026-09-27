"""Exercise selection, missing coverage, and navigation using synthetic data."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import app_db

ROOT = Path(__file__).resolve().parents[1]


def test_air_selection_and_missing_coverage(monkeypatch, air_database):
    monkeypatch.setattr(app_db, 'query', lambda sql, params=(): air_database.cursor().execute(sql, params).df())
    app = AppTest.from_file(str(ROOT / 'views/air_quality.py')).run()
    assert not app.exception
    assert app.metric[0].value == '2'
    app.selectbox[0].set_value('53035').run()
    assert not app.exception
    assert app.metric[0].value == '1'
    assert app.session_state['selected_county'] == '53035'
    app.selectbox[0].set_value('53073').run()
    assert not app.exception
    assert not app.metric
    assert any('missing coverage' in info.value for info in app.info)


def test_ozone_only_county_does_not_crash(monkeypatch, air_database):
    air_database.execute("delete from mart_air_observations where pollutant = 'PM2.5'")
    monkeypatch.setattr(app_db, 'query', lambda sql, params=(): air_database.cursor().execute(sql, params).df())
    app = AppTest.from_file(str(ROOT / 'views/air_quality.py')).run()
    assert not app.exception
    assert app.metric[0].value == '0'
    assert app.metric[2].value == 'No PM2.5 data'
    assert any('No mapped PM2.5' in info.value for info in app.info)


def test_unsupported_county_does_not_query_seattle(monkeypatch):
    def reject_query(*args, **kwargs):
        raise AssertionError('An unsupported selection queried the old geography')

    monkeypatch.setattr(app_db, 'query', reject_query)
    app = AppTest.from_file(str(ROOT / 'streamlit_app.py'))
    app.session_state['selected_county'] = '53035'
    app.run()
    assert not app.exception
    assert any('Kitsap County filtering is not available' in info.value for info in app.info)
