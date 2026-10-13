"""Validated geographic coverage and provenance for configured data sources.

Registration describes the configured pipeline, not a successful live retrieval.
Observation dates and freshness belong to build metadata, not static declarations.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields
from urllib.parse import urlparse


@dataclass(frozen=True)
class Source:
    source_id: str
    topic: str
    publisher: str
    url: str
    geography_kind: str
    coverage: str
    record_grain: str
    limitations: str

    def __post_init__(self) -> None:
        for f in fields(self):
            value = getattr(self, f.name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{f.name} must be a nonempty string')
        if self.geography_kind not in {'municipality', 'county', 'agency', 'station'}:
            raise ValueError('Unsupported geography_kind')
        parsed = urlparse(self.url)
        if parsed.scheme not in {'https', 'http'} or not parsed.netloc:
            raise ValueError('url must be an absolute HTTP(S) URL')


def validate_sources(sources: Iterable[Source]) -> None:
    """Reject ambiguous registry IDs before exposing or loading the inventory."""
    seen: set[str] = set()
    for source in sources:
        if source.source_id in seen:
            raise ValueError(f'Duplicate source_id: {source.source_id}')
        seen.add(source.source_id)


def source_record_key(source_id: str, record_id: str) -> str:
    """Lossless qualified key; delimiters inside either component cannot collide."""
    if not source_id.strip() or not record_id.strip():
        raise ValueError('source_id and record_id must be nonempty')
    return json.dumps([source_id, record_id], ensure_ascii=False, separators=(',', ':'))


# Normalized permit fields a PermitSource maps from its publisher's columns.
PERMIT_FIELDS = (
    'permit_number', 'permit_class', 'status', 'applied_date', 'issue_date',
    'valuation', 'housing_units', 'address', 'latitude', 'longitude',
)
_REQUIRED_PERMIT_FIELDS = ('permit_number', 'permit_class', 'issue_date')


@dataclass(frozen=True)
class PermitSource:
    """One publisher's building-permit feed and how it maps to structure permits.

    ``fields`` maps a normalized name (``PERMIT_FIELDS``) to the publisher's column;
    a column starting with ``_`` is synthesized at fetch time (``_lat``/``_lon``
    from feature geometry). ``include``/``exclude`` map a publisher column to the
    trimmed values kept/dropped, so trade-only and administrative records never
    count as structure permits. ``valuation_basis`` names the publisher's own
    valuation definition; None means it publishes none.
    """

    source_id: str
    publisher: str
    platform: str
    endpoint: str
    county_fips: str
    coverage: str
    jurisdiction: str
    fields: Mapping[str, str]
    server_where: str = '1=1'
    include: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    exclude: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    jurisdiction_field: str | None = None
    jurisdiction_labels: Mapping[str, str] = field(default_factory=dict)
    point_field: str | None = None
    valuation_basis: str | None = None
    scope: str = 'Structure permits'

    def __post_init__(self) -> None:
        if self.platform not in {'socrata', 'arcgis'}:
            raise ValueError(f'Unsupported platform: {self.platform}')
        if self.coverage not in {'City', 'Unincorporated county', 'Multi-jurisdiction'}:
            raise ValueError(f'Unsupported coverage: {self.coverage}')
        missing = [f for f in _REQUIRED_PERMIT_FIELDS if f not in self.fields]
        if missing:
            raise ValueError(f'{self.source_id} must map {", ".join(missing)}')
        unknown = set(self.fields) - set(PERMIT_FIELDS)
        if unknown:
            raise ValueError(f'{self.source_id} maps unknown fields: {sorted(unknown)}')

    @property
    def out_fields(self) -> tuple[str, ...]:
        """Publisher columns to request — only what is used, so personal names never load."""
        cols = [c for c in self.fields.values() if not c.startswith('_')]
        cols += [*self.include, *self.exclude]
        cols += [c for c in (self.jurisdiction_field, self.point_field) if c]
        return tuple(dict.fromkeys(cols))
