"""
Unit tests for extract/vct_filters.py.

These are pure-function tests: no network, no database, no filesystem.
They exist to lock in the flagship-vs-not-flagship classification rules
described in vct_filters.py's module docstring, so a future refactor
can't silently change what counts as a "real" VCT match without a test
failing.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "extract"))

from vct_filters import is_flagship_vct_serie  # noqa: E402


def test_franchised_league_kickoff_is_flagship():
    assert is_flagship_vct_serie("VCT 2025: Americas Kickoff") is True


def test_franchised_league_stage_is_flagship():
    assert is_flagship_vct_serie("VCT 2025: EMEA Stage 1") is True
    assert is_flagship_vct_serie("VCT 2025: Pacific Stage 2") is True


def test_franchised_league_clash_is_flagship():
    assert is_flagship_vct_serie("VCT 2025: China Clash") is True


def test_champions_event_is_flagship():
    assert is_flagship_vct_serie("Champions Seoul 2025") is True


def test_championship_word_does_not_false_positive_on_champions():
    # "championship" must not match \bchampions\b
    assert is_flagship_vct_serie("VCT Game Changers Championship") is False


def test_real_masters_event_is_flagship():
    assert is_flagship_vct_serie("Masters Bangkok 2025") is True
    assert is_flagship_vct_serie("Masters Toronto 2025") is True


def test_ace_masters_is_excluded():
    # Latin America's "ACE Masters" reuses VCT terminology but is not
    # the real international Masters event.
    assert is_flagship_vct_serie("ACE Masters Latin America") is False


def test_stage_3_is_excluded_as_data_anomaly():
    # The official format only has Stage 1 / Stage 2 per year.
    assert is_flagship_vct_serie("VCT 2025: EMEA Stage 3") is False


def test_game_changers_is_excluded():
    assert is_flagship_vct_serie("VCT 2025: Game Changers Americas") is False


def test_challengers_is_excluded():
    assert is_flagship_vct_serie("VCT Challengers Brazil") is False


def test_qualifiers_are_excluded():
    assert is_flagship_vct_serie("VCT 2025: Pacific Last Chance Qualifier") is False
    assert is_flagship_vct_serie("VCT 2025: Americas Closed Qualifier") is False


def test_unrelated_series_is_excluded():
    assert is_flagship_vct_serie("Some Random Community Cup") is False


def test_is_case_and_whitespace_insensitive():
    assert is_flagship_vct_serie("  vct 2025:   AMERICAS   kickoff  ") is True
