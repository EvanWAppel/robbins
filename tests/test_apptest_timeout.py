"""Every Streamlit AppTest gets an explicit, generous timeout via one conftest helper.

AppTest's 3 s default timeout flakes under machine load, so all page tests must
build their AppTest through the ``app_test`` fixture instead of calling
``AppTest.from_file`` directly.
"""

from pathlib import Path

from conftest import APPTEST_TIMEOUT_S

TESTS = Path(__file__).resolve().parent


def test_app_test_fixture_sets_an_explicit_timeout(app_test):
    at = app_test("views/ask.py")
    assert at.default_timeout == APPTEST_TIMEOUT_S
    assert APPTEST_TIMEOUT_S >= 30


def test_no_test_builds_an_apptest_directly():
    offenders = [
        p.name
        for p in TESTS.glob("test_*.py")
        if p.name != Path(__file__).name and "AppTest.from_" in p.read_text()
    ]
    assert offenders == [], f"Use the app_test fixture from conftest.py instead: {offenders}"
