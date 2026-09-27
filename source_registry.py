"""Validated geographic coverage and provenance for configured data sources.

Registration describes the configured pipeline, not a successful live retrieval.
Observation dates and freshness belong to build metadata, not static declarations.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, fields
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
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'{field.name} must be a nonempty string')
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
