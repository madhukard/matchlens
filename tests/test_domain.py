import pytest
from pydantic import ValidationError

from matchlens.domain import EVENTS, MATCH_ID, Window, snapshot
from matchlens.service import compare_match_windows, explain_moment, get_evidence


def test_evidence_exact_counts_and_score():
    data = snapshot()
    assert data["stats"]["harbor"]["high_recoveries"] == 3
    assert data["stats"]["harbor"]["shots"] == 3
    assert data["score"] == {"harbor": 1, "summit": 1}
    assert snapshot(end_second=5400)["score"] == {"harbor": 2, "summit": 1}
    assert len({e.event_id for e in EVENTS}) == len(EVENTS)


def test_half_open_windows_do_not_double_count():
    left = snapshot(start_second=3300, end_second=3420)
    right = snapshot(start_second=3420, end_second=3500)
    assert "r-3420" not in {e["event_id"] for e in left["events"]}
    assert "r-3420" in {e["event_id"] for e in right["events"]}


@pytest.mark.parametrize("start,end", [(10, 10), (20, 10), (-1, 20), (0, 5401)])
def test_invalid_window(start, end):
    with pytest.raises(ValidationError):
        Window(start_second=start, end_second=end)


def test_unknown_match_and_evidence_rejected():
    with pytest.raises(ValueError):
        snapshot("other-tenant-match")
    with pytest.raises(ValueError):
        get_evidence(["fake-event"])
    with pytest.raises(ValueError):
        get_evidence([])
    assert get_evidence(["r-3420"])["events"][0]["second"] == 3420


def test_empty_window_does_not_claim_accuracy():
    data = snapshot(start_second=1, end_second=2)
    assert data["stats"]["harbor"]["pass_accuracy"] is None
    assert data["events"] == []
    assert explain_moment(start_second=1, end_second=2)["insight"]["source"] == "statistics_only"


def test_comparison_boundaries():
    data = compare_match_windows()
    assert data["before"]["window"]["end_second"] == data["after"]["window"]["start_second"]
    with pytest.raises(ValueError):
        compare_match_windows(MATCH_ID, 100, 600)
