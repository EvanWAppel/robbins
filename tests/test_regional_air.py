from regional_air import air_queries


def result(con, name, county=None):
    sql, params = air_queries(county)[name]
    return con.execute(sql, params).df()


def test_county_selection_changes_every_output(air_database):
    assert result(air_database, 'categories', '53033').day_count.sum() == 2
    assert result(air_database, 'categories', '53035').day_count.sum() == 1
    assert result(air_database, 'worst', '53033').max_aqi.max() == 60
    assert result(air_database, 'monthly', '53033').max_aqi.max() == 60
    assert set(result(air_database, 'sites', '53033').county) == {'King'}
    assert result(air_database, 'coverage', '53033').reading_count.sum() == 2


def test_region_counts_each_day_once(air_database):
    assert result(air_database, 'categories').day_count.sum() == 2
    assert result(air_database, 'worst').max_aqi.max() == 160
    assert len(result(air_database, 'sites')) == 2


def test_missing_county_is_empty_not_zero_aqi(air_database):
    for name in air_queries('53073'):
        assert result(air_database, name, '53073').empty


def test_selection_is_parameterized():
    for sql, params in air_queries("x' OR 1=1 --").values():
        assert "x' OR" not in sql
        assert params == ("x' OR 1=1 --",)


def test_staging_uses_ids_not_site_names():
    from pathlib import Path

    import duckdb

    con = duckdb.connect()
    con.execute('''create table source_air (
        state_code varchar, county_code varchar, site_num varchar,
        county_name varchar, local_site_name varchar, latitude double,
        longitude double, date_local varchar, parameter_name varchar,
        units varchar, arithmetic_mean double, aqi double)''')
    con.execute('''insert into source_air values
        ('53', '033', '1', 'King', 'Old name', 47.6, -122.3, '2024-01-01', 'PM2.5', 'ug', 10, 40),
        ('53', '033', '1', 'King', 'New name', 47.61, -122.3, '2024-01-01', 'PM2.5', 'ug', 20, 60),
        ('53', '035', '1', 'Kitsap', 'Old name', 47.5, -122.6, '2024-01-01', 'PM2.5', 'ug', 30, 100),
        ('53', '035', '2', 'Kitsap', 'No AQI', 47.5, -122.6, '2024-01-01', 'PM2.5', 'ug', 30, NULL)''')
    sql = (Path(__file__).resolve().parents[1] / 'models/staging/stg_air_quality.sql').read_text()
    sql = sql.replace("{{ source('raw', 'air_quality') }}", 'source_air')
    out = con.execute(sql).df()
    assert len(out) == 2
    assert set(out.site_id) == {'530330001', '530350001'}
    assert out.set_index('county').loc['King', 'aqi'] == 50
    con.close()
