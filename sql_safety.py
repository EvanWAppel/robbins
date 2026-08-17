"""Read-only SQL guard for the 'Ask the data' tab.

The DuckDB connection the app uses is already ``read_only=True``, but we defend in
depth at the query layer too: only a single ``SELECT`` / ``WITH … SELECT`` statement
is ever executed. Anything that could write, attach a database, copy data out, or
smuggle a second statement is rejected — loudly, per the house rule against hiding
errors.
"""

from __future__ import annotations

import re

# Statement-leading keywords that are never allowed: anything that isn't a plain
# read. DuckDB is read-only anyway, but these would mutate or reach outside it.
_FORBIDDEN_LEADING = {
    "insert", "update", "delete", "drop", "create", "alter", "truncate",
    "attach", "detach", "copy", "pragma", "set", "reset", "install", "load",
    "export", "import", "call", "vacuum", "checkpoint", "replace", "merge",
    "grant", "revoke", "begin", "commit", "rollback", "use",
}

# Tokens that are dangerous *anywhere* in the query — writes, config, and DuckDB's
# external-read functions (which could read arbitrary local files or URLs). These
# are not column names in any mart, so a word-boundary match is safe.
_FORBIDDEN_ANYWHERE = {
    "attach", "detach", "copy", "pragma", "install", "load", "export", "import",
    "insert", "update", "delete", "drop", "create", "alter", "vacuum", "checkpoint",
    "read_csv", "read_csv_auto", "read_parquet", "read_json", "read_json_auto",
    "read_text", "read_blob", "parquet_scan", "glob", "sniff_csv",
}


def _strip(sql: str) -> str:
    """Remove line/block comments and surrounding whitespace."""
    no_line = re.sub(r"--[^\n]*", " ", sql)
    no_block = re.sub(r"/\*.*?\*/", " ", no_line, flags=re.DOTALL)
    return no_block.strip()


def is_read_only_select(sql: str) -> bool:
    """True only if ``sql`` is a single read-only SELECT/WITH…SELECT statement."""
    cleaned = _strip(sql)
    if not cleaned:
        return False
    # A single statement only: allow exactly one optional trailing semicolon.
    body = cleaned.removesuffix(";")
    if ";" in body:
        return False
    lowered = body.lstrip().lower()
    if not lowered.startswith(("select", "with")):
        return False
    first_word = re.match(r"[a-z_]+", lowered)
    if first_word and first_word.group() in _FORBIDDEN_LEADING:
        return False
    # Reject dangerous tokens (writes, config, external-read functions) anywhere.
    for token in re.findall(r"\b[a-z_]+\b", lowered):
        if token in _FORBIDDEN_ANYWHERE:
            return False
    return True


def assert_read_only(sql: str) -> str:
    """Return the cleaned single-statement SQL, or raise if it isn't read-only."""
    if not is_read_only_select(sql):
        raise ValueError(f"Refusing to run non read-only SQL: {sql!r}")
    cleaned = _strip(sql)
    return cleaned[:-1].rstrip() if cleaned.endswith(";") else cleaned
