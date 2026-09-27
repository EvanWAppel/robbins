"""Source provenance must not imply broader geographic coverage."""

import pytest

from source_registry import Source, source_record_key, validate_sources


def test_source_retains_explicit_coverage(source_registration):
    source = Source(**source_registration)
    assert source.geography_kind == "municipality"
    assert source.coverage == "Example City only"


def test_source_ids_must_be_unique(source_registration):
    source = Source(**source_registration)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_sources((source, source))


@pytest.mark.parametrize("field", ["source_id", "coverage", "record_grain", "limitations"])
def test_missing_metadata_is_rejected(source_registration, field):
    source_registration[field] = " "
    with pytest.raises(ValueError, match=field):
        Source(**source_registration)


def test_unknown_geography_kind_is_rejected(source_registration):
    source_registration["geography_kind"] = "everywhere"
    with pytest.raises(ValueError, match="geography_kind"):
        Source(**source_registration)


def test_source_qualified_keys_cannot_collide():
    assert source_record_key("city.a", "123") != source_record_key("county.b", "123")
    assert source_record_key("a:b", "c") != source_record_key("a", "b:c")
    with pytest.raises(ValueError):
        source_record_key("city.a", "")


def test_configured_inventory_is_valid():
    import city_config as cfg

    validate_sources(cfg.DATA_SOURCES)
    topics = {source.topic for source in cfg.DATA_SOURCES}
    assert len(topics) == 15
    assert next(s for s in cfg.DATA_SOURCES if s.source_id == "seattle.permits").coverage == "City of Seattle"
    assert next(s for s in cfg.DATA_SOURCES if s.source_id == "federal.ntd").geography_kind == "agency"
    assert next(s for s in cfg.DATA_SOURCES if s.source_id == "noaa.weather").geography_kind == "station"
