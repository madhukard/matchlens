import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import RateLimitError

from matchlens import live_agents, live_service, live_store
from matchlens.live_agents import Budget, Package, Selection, Stories, Story, Workflow
from matchlens.live_domain import MatchState, scenario
from matchlens.worker import run_stream


def state_at(index=5):
    state = MatchState()
    for clock, events in scenario()[: index + 1]:
        for event in events:
            state.ingest(event)
    return state, state.snapshot(clock)


def package(data):
    fact = (
        "corrections.void_goals"
        if data["facts"]["corrections.void_goals"]["value"]
        else "score.harbor"
    )
    story = Story(headline="Current state", summary="Synthetic match update.", fact_ids=[fact])
    return Package(
        selection=Selection(
            angle="Update", fact_ids=[fact], recommended_view="timeline", uncertainty="Synthetic"
        ),
        stories=Stories(fan_en=story, analyst_en=story, fan_es=story, analyst_es=story),
    )


def test_correction_retracts_goal_and_supersedes_evidence():
    _, before = state_at(4)
    _, after = state_at(5)
    assert before["score"]["harbor"] == 1
    assert after["score"]["harbor"] == 0
    assert after["facts"]["corrections.void_goals"]["value"] == 1
    assert "finish-4@1" not in [e["event_id"] for e in after["events"]]
    assert next(e for e in after["events"] if e["event_id"] == "finish-4@2")["void"]


def test_late_duplicate_and_conflicting_delivery():
    state, data = state_at(2)
    assert data["facts"]["before.summit.pass"]["value"] == 10
    first = scenario()[0][1][0]
    revision = len(state.arrivals)
    assert state.ingest(first) is False
    assert len(state.arrivals) == revision
    with pytest.raises(ValueError, match="Conflicting"):
        state.ingest(first.model_copy(update={"player": "different"}))
    with pytest.raises(ValueError, match="gap"):
        state.ingest(first.model_copy(update={"revision": 3}))


def test_snapshot_cannot_see_future_and_seed_varies_coordinates():
    state, _ = state_at()
    early = state.snapshot(3400)
    assert all(e["second"] <= 3400 for e in early["events"])
    assert early["facts"]["after.harbor.pass"]["value"] == 0
    assert scenario(1)[0][1][0].x != scenario(2)[0][1][0].x


def test_budget_fails_before_call():
    budget = Budget(tokens=1)
    with pytest.raises(ValueError, match="budget"):
        budget.reserve("a", "b", Package)
    assert budget.calls_left == 48


def test_authored_pass_chains_are_continuous():
    for seed in (1, 7, 19):
        for _, events in scenario(seed):
            passes = [e for e in events if e.event_id.startswith("p-")]
            # The deliberate duplicate in batch three belongs to an earlier move.
            passes = [e for e in passes if e.possession_id == passes[0].possession_id]
            for first, second in zip(passes, passes[1:]):
                assert (first.end_x, first.end_y) == (second.x, second.y)
            recoveries = [e for e in events if e.kind == "recovery"]
            if recoveries:
                assert (recoveries[0].end_x, recoveries[0].end_y) == (passes[0].x, passes[0].y)


async def test_rejected_handoff_corrects_once(monkeypatch):
    _, data = state_at()
    good = package(data)
    bad = good.selection.model_copy(update={"fact_ids": ["invented"]})
    workflow = Workflow("model", Budget())
    call = AsyncMock(
        side_effect=[
            bad,
            good.selection,
            SimpleNamespace(approved=True),
            good.stories,
            SimpleNamespace(approved=True),
        ]
    )
    monkeypatch.setattr(workflow, "call", call)
    assert await workflow.produce(data) == good
    assert call.await_count == 5
    assert workflow.trace[0]["status"] == "rejected"


async def test_rate_limit_retry_reserves_again_and_reports_progress(monkeypatch):
    response = httpx.Response(429, request=httpx.Request("POST", "https://example.test"))
    error = RateLimitError("Quota", response=response, body=None)
    value = package(state_at()[1]).selection
    result = SimpleNamespace(
        final_output=value,
        context_wrapper=SimpleNamespace(
            usage=SimpleNamespace(input_tokens=20, output_tokens=10, requests=1)
        ),
    )
    runner = AsyncMock(side_effect=[error, result])
    monkeypatch.setattr(live_agents.Runner, "run", runner)
    sleep = AsyncMock()
    monkeypatch.setattr(live_agents.asyncio, "sleep", sleep)
    statuses = []
    budget = Budget()
    workflow = Workflow("test-model", budget, lambda trace: statuses.append(trace[-1]["status"]))
    assert await workflow.call("Test", "Check", {}, Selection) == value
    assert budget.calls_left == 46
    assert statuses == ["running", "failed", "running", "completed"]
    sleep.assert_awaited_once_with(20)


async def test_editor_receives_final_reviewer_feedback_on_retry(monkeypatch):
    _, data = state_at()
    good = package(data)
    workflow = Workflow("model", Budget())
    approved = SimpleNamespace(approved=True)
    rejected = SimpleNamespace(approved=False, reason="Pass attempts are not completions")
    call = AsyncMock(
        side_effect=[
            good.selection,
            approved,
            good.stories,
            rejected,
            good.selection,
            approved,
            good.stories,
            approved,
        ]
    )
    monkeypatch.setattr(workflow, "call", call)
    assert await workflow.produce(data) == good
    editor_calls = [c for c in call.call_args_list if c.args[0] == "Audience editor"]
    assert editor_calls[0].args[2]["review_feedback"] == ""
    assert editor_calls[1].args[2]["review_feedback"] == rejected.reason


async def test_failed_review_never_publishes_old_narrative(monkeypatch):
    async def produce(self, data):
        if data["facts"]["corrections.void_goals"]["value"]:
            raise ValueError("Rejected correction")
        return package(data)

    monkeypatch.setattr(Workflow, "produce", produce)
    published = []

    def capture(run, archive=False):
        published.append(json.loads(json.dumps(run)))

    result = await run_stream("model", interval=0, publish_fn=capture)
    assert result["status"] == "completed"
    assert result["frames"][-1]["status"] == "statistics_only"
    assert "package" not in result["frames"][-1]
    assert result["frames"][-2]["package"]
    assert any(r["frames"][-1]["status"] == "reviewing" for r in published)


def test_live_evidence_rejects_superseded_goal(monkeypatch):
    _, data = state_at()
    run = {
        "run_id": "test",
        "status": "completed",
        "frames": [{"snapshot": data, "status": "approved", "package": package(data).model_dump()}],
    }
    monkeypatch.setattr(live_service, "read_run", lambda: run)
    assert live_service.get_live_match()["score"]["harbor"] == 0
    with pytest.raises(ValueError, match="superseded"):
        live_service.get_live_evidence(["finish-4@1"])
    assert live_service.get_live_evidence(["finish-4@2"])["events"][0]["void"]
    with pytest.raises(ValueError, match="Run changed"):
        live_service.get_live_evidence(["finish-4@2"], run_id="previous")
    assert live_service.get_live_evidence(["finish-4@2"], run_id="test")["run_id"] == "test"
    with pytest.raises(ValueError):
        live_service.get_live_match(frame=99)


def test_store_failure_is_marked_recording(monkeypatch, tmp_path):
    fallback = tmp_path / "recorded.json"
    fallback.write_text(json.dumps({"run_id": "old", "status": "running", "frames": []}))
    monkeypatch.setattr(live_store, "FALLBACK", fallback)
    monkeypatch.setattr(live_store, "_cache", None)
    monkeypatch.setenv("MATCHLENS_LIVE_FILE", str(tmp_path / "missing"))
    result = live_store.read_run()
    assert result["status"] == "recorded"
    assert result["delivery"] == "bundled_recording"
