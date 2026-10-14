"""Evaluation fixtures and release gates: deterministic tests, not model grades."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from test_live import package, state_at

from matchlens.evaluate import challenge_cases, evaluate
from matchlens.live_agents import Budget, Workflow, validate_package
from matchlens.live_domain import MatchState, scenario


def test_challenge_cases_change_semantics():
    cases = dict(challenge_cases())
    assert len(cases) == 4
    assert not cases["empty_feed"]["events"]
    failed = cases["all_passes_unsuccessful"]
    passes = [e for e in failed["events"] if e["kind"] == "pass"]
    assert passes and all(not e["successful"] for e in passes)
    assert failed["facts"]["before.summit.pass"]["value"] == 10
    restored = cases["goal_reinstated"]
    assert restored["score"]["harbor"] == 1
    assert restored["facts"]["corrections.void_goals"]["value"] == 0
    assert "finish-4@3" in restored["facts"]["score.harbor"]["evidence_ids"]
    corrected = cases["two_voided_goals"]
    assert corrected["score"]["harbor"] == 0
    assert corrected["facts"]["corrections.void_goals"]["value"] == 2


@pytest.mark.parametrize("seed", range(20))
def test_reordered_duplicate_delivery_preserves_current_facts(seed):
    batches = scenario(seed)
    canonical, reordered = MatchState(), MatchState()
    for _, events in batches:
        for event in events:
            canonical.ingest(event)
        # Reorder within batches, preserving cross-batch revision dependencies.
        for event in reversed(events):
            reordered.ingest(event)
            reordered.ingest(event)
    expected, actual = canonical.snapshot(3659), reordered.snapshot(3659)
    assert actual["score"] == expected["score"]
    assert actual["facts"] == expected["facts"]
    assert actual["events"] == expected["events"]


@pytest.mark.parametrize("locale", ["fan_en", "analyst_en", "fan_es", "analyst_es"])
def test_correction_missing_in_any_localization_is_blocked(locale):
    data = state_at()[1]
    candidate = package(data)
    candidate.selection.fact_ids.append("score.harbor")
    getattr(candidate.stories, locale).fact_ids = ["score.harbor"]
    with pytest.raises(ValueError, match="Every localized"):
        validate_package(candidate, data)


async def test_persistent_verifier_rejection_stops_after_two_attempts(monkeypatch):
    data = state_at()[1]
    candidate = package(data)
    workflow = Workflow("mock", Budget())
    call = AsyncMock(
        side_effect=[
            candidate.selection,
            SimpleNamespace(approved=True),
            candidate.stories,
            SimpleNamespace(approved=False, reason="Unsupported claim"),
        ]
        * 2
    )
    monkeypatch.setattr(workflow, "call", call)
    with pytest.raises(ValueError, match="Unsupported claim"):
        await workflow.produce(data)
    assert call.await_count == 8
    assert [t["attempt"] for t in workflow.trace if t["status"] == "rejected"] == [1, 2]


async def test_existing_report_rejected_before_model_calls(tmp_path):
    target = tmp_path / "report.json"
    target.write_text("original")
    with pytest.raises(FileExistsError):
        await evaluate("unused", target=target)
    assert target.read_text() == "original"
