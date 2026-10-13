"""Regional building permits — normalize each publisher's feed to structure permits.

Nine publishers (Seattle, Pierce County, Tacoma, Bellevue, Everett, Bellingham,
Puyallup, Kitsap County, Thurston Regional Planning Council) define "building
permit" differently. Each feed is reduced to one schema of *structure* permits
(new / addition / alteration / re-roof / demolition) by per-source rules in
``city_config.PERMIT_SOURCES``; a uniform 2016+ window applies; impossible dates
are nulled rather than trusted; keys are source-qualified so two publishers'
"B1" never collide. Only mapped columns survive, so personal names never load.

Valuation keeps each publisher's own definition (``valuation_basis``) and must
not be summed across publishers.
"""

from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from city_config import REGION_COUNTIES
from source_registry import PermitSource, source_record_key

__all__ = ["NORMALIZED_COLUMNS", "PermitSource", "normalize_permits", "permits_queries"]

log = logging.getLogger(__name__)

NORMALIZED_COLUMNS = (
    "permit_key", "source_id", "permit_number", "jurisdiction", "county_fips",
    "county", "coverage", "scope", "permit_class", "status", "applied_date",
    "issue_date", "valuation", "valuation_basis", "housing_units", "address",
    "latitude", "longitude",
)

# Generous Puget Sound envelope: anything outside is a geocoding error (e.g. 0,0).
_LAT = (46.0, 49.1)
_LON = (-125.0, -120.5)
_LOCAL_TZ = "America/Los_Angeles"


def _clean_text(s: pd.Series) -> pd.Series:
    """Trimmed strings; blanks become null."""
    out = s.astype("string").str.strip()
    return out.mask(out == "")


def _parse_dates(s: pd.Series, today: date, label: str) -> pd.Series:
    """ArcGIS epoch-millis or ISO-ish strings -> date; future/unparseable -> null."""
    numeric = pd.to_numeric(s, errors="coerce")
    from_ms = pd.to_datetime(numeric, unit="ms", errors="coerce")
    text = s.where(numeric.isna()).astype("string").str.strip()
    # Offset-bearing timestamps (Socrata fixed-timestamp columns) are instants:
    # take their Pacific calendar date. Naive strings are already local dates.
    has_tz = text.str.contains(r"(?:Z|[+-]\d\d:?\d\d)$", regex=True).fillna(False)
    naive = pd.to_datetime(text.where(~has_tz), errors="coerce", format="mixed")
    aware = (
        pd.to_datetime(text.where(has_tz), errors="coerce", format="mixed", utc=True)
        .dt.tz_convert(_LOCAL_TZ)
        .dt.tz_localize(None)
    )
    parsed = from_ms.fillna(naive).fillna(aware).dt.normalize()
    future = parsed.notna() & (parsed > pd.Timestamp(today))
    unparseable = s.notna() & parsed.isna()
    if future.any() or unparseable.any():
        log.warning("  %s: nulled %d future and %d unparseable dates",
                    label, int(future.sum()), int(unparseable.sum()))
    return parsed.mask(future)


def _column(df: pd.DataFrame, spec: PermitSource, name: str) -> pd.Series:
    src = spec.fields.get(name)
    if src is None:
        return pd.Series(pd.NA, index=df.index, dtype="object")
    return df[src]


def normalize_permits(
    spec: PermitSource, df: pd.DataFrame, *, start: date, today: date
) -> pd.DataFrame:
    """Reduce one publisher's raw records to normalized structure permits."""
    label = spec.source_id
    n_raw = len(df)
    keep = pd.Series(True, index=df.index)
    for col, values in spec.include.items():
        vals = _clean_text(df[col])
        keep &= vals.isin(values).fillna(False)
    for col, values in spec.exclude.items():
        vals = _clean_text(df[col])
        keep &= ~vals.isin(values).fillna(False)
    rule_cols = [*spec.include, *spec.exclude]
    if rule_cols:
        dropped = df.loc[~keep, rule_cols].astype("string").fillna("<null>")
        top = dropped.value_counts().head(10)
        log.info("  %s: structure rule kept %d of %d; top dropped: %s",
                 label, int(keep.sum()), n_raw, top.to_dict())
    df = df[keep]

    out = pd.DataFrame(index=df.index)
    out["source_id"] = spec.source_id
    out["permit_number"] = _clean_text(_column(df, spec, "permit_number"))
    out["permit_key"] = [
        source_record_key(spec.source_id, p) if pd.notna(p) else pd.NA
        for p in out["permit_number"]
    ]
    if spec.jurisdiction_field:
        jur = _clean_text(df[spec.jurisdiction_field]).replace(dict(spec.jurisdiction_labels))
        out["jurisdiction"] = jur.fillna(spec.jurisdiction)
    else:
        out["jurisdiction"] = spec.jurisdiction
    out["county_fips"] = spec.county_fips
    out["county"] = REGION_COUNTIES[spec.county_fips]
    out["coverage"] = spec.coverage
    out["scope"] = spec.scope
    out["permit_class"] = _clean_text(_column(df, spec, "permit_class"))
    out["status"] = _clean_text(_column(df, spec, "status"))
    out["applied_date"] = _parse_dates(_column(df, spec, "applied_date"), today, f"{label} applied")
    out["issue_date"] = _parse_dates(_column(df, spec, "issue_date"), today, f"{label} issued")
    if spec.valuation_basis:
        out["valuation"] = pd.to_numeric(_column(df, spec, "valuation"), errors="coerce")
    else:
        out["valuation"] = pd.Series(float("nan"), index=df.index)
    out["valuation_basis"] = spec.valuation_basis
    out["housing_units"] = pd.to_numeric(
        _column(df, spec, "housing_units"), errors="coerce"
    ).round().astype("Int64")
    out["address"] = _clean_text(_column(df, spec, "address"))
    lat = pd.to_numeric(_column(df, spec, "latitude"), errors="coerce")
    lon = pd.to_numeric(_column(df, spec, "longitude"), errors="coerce")
    bad = lat.notna() & ~(lat.between(*_LAT) & lon.between(*_LON))
    if bad.any():
        log.warning("  %s: nulled %d out-of-region coordinates", label, int(bad.sum()))
    out["latitude"] = lat.mask(bad)
    out["longitude"] = lon.mask(bad)

    begin = pd.Timestamp(start)
    issued_in = out["issue_date"].notna() & (out["issue_date"] >= begin)
    pending_in = (out["issue_date"].isna() & out["applied_date"].notna()
                  & (out["applied_date"] >= begin))
    out = out[(issued_in | pending_in) & out["permit_key"].notna()]
    dupes = out["permit_key"].duplicated()
    if dupes.any():
        log.info("  %s: dropped %d duplicate permit numbers", label, int(dupes.sum()))
    out = out[~dupes].reset_index(drop=True)
    for col in ("applied_date", "issue_date"):
        out[col] = pd.Series([d.date() if pd.notna(d) else None for d in out[col]], dtype="object")
    if out.empty:
        raise ValueError(f"{label}: no structure permits since {start} after filtering")
    log.info("  %s: %d structure permits since %s", label, len(out), start)
    return out[list(NORMALIZED_COLUMNS)]


def permits_queries(county_fips: str | None = None) -> dict[str, tuple[str, tuple]]:
    """Parameterized page queries; the county filter applies before every aggregate.

    Region view series are counties; a county view's series are its jurisdictions.
    Valuation is one series per publisher (never summed across publishers), and
    publishers without a valuation definition are left out of it. A county with
    no integrated publisher yields empty results — never another county's data.
    """
    where = "where county_fips = ?" if county_fips else ""
    andw = "and county_fips = ?" if county_fips else ""
    one = (county_fips,) if county_fips else ()
    monthly = "main.mart_permits_monthly"
    series = "jurisdiction" if county_fips else "county"
    return {
        "kpis": (
            f"""select sum(permit_count) as permits,
                count(distinct source_id) as publishers,
                count(distinct jurisdiction) as jurisdictions,
                min(issue_month) as first_month, max(issue_month) as last_month
                from {monthly} {where}""",
            one,
        ),
        "monthly": (
            f"""select issue_month, {series} as series, sum(permit_count) as permits
                from {monthly} {where}
                group by 1, 2 order by 1, 2""",
            one,
        ),
        "annual": (
            f"""select extract(year from issue_month)::int as year, jurisdiction,
                any_value(county) as county, sum(permit_count) as permits
                from {monthly} {where}
                group by 1, 2 order by 2, 1""",
            one,
        ),
        "valuation_monthly": (
            f"""select issue_month, source_id, any_value(valuation_basis) as valuation_basis,
                sum(total_valuation) as total_valuation
                from {monthly} where valuation_basis is not null {andw}
                group by 1, 2 order by 2, 1""",
            one,
        ),
        "publishers": (
            f"""select source_id as publisher_source, jurisdiction, any_value(county) as county,
                any_value(coverage) as coverage, any_value(scope) as scope,
                any_value(valuation_basis) as valuation_basis,
                sum(permit_count) as permits,
                min(issue_month) as first_month, max(issue_month) as last_month
                from {monthly} {where}
                group by 1, 2 order by county, permits desc""",
            one,
        ),
        "by_class": (
            f"""select source_id, jurisdiction, county, permit_class, permit_count,
                total_valuation, valuation_basis
                from main.mart_permits_by_class {where}
                order by permit_count desc""",
            one,
        ),
        "map": (
            f"""select latitude, longitude, permit_number, jurisdiction, source_id,
                coalesce(address, 'Address unavailable') as address,
                coalesce(permit_class, 'Type unavailable') as permit_class,
                cast(issue_date as varchar) as issue_date
                from main.mart_permits_map_sample {where}""",
            one,
        ),
    }
