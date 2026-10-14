from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from matchlens import intelligence
from matchlens.domain import snapshot
from matchlens.intelligence import (
    Analysis,
    Claim,
    Narrative,
    Review,
    generate_analysis,
    validate_evidence,
)


def output(value):
    return SimpleNamespace(final_output=value)


def fixtures():
    return [
        output(
            Analysis(
                headline="Recoveries in advanced areas",
                claims=[
                    Claim(
                        text="Harbor recorded three high recoveries.",
                        evidence_event_ids=["r-3420", "r-3560", "r-3730"],
                        interpretation=False,
                    )
                ],
                uncertainty="Synthetic selected events do not prove a causal tactical change.",
                recommended_view="pitch",
            )
        ),
        output(Review(approved=True, reason="Supported")),
        output(
            Narrative(
                headline="Harbor wins the ball back",
                summary="Three high recoveries in this window.",
                evidence_event_ids=["r-3420", "r-3560", "r-3730"],
            )
        ),
        output(Review(approved=True, reason="Supported")),
    ]


async def test_reviewed_workflow(monkeypatch):
    run = AsyncMock(side_effect=fixtures())
    monkeypatch.setattr("matchlens.intelligence.Runner.run", run)
    result = await generate_analysis(snapshot(), "gpt-6-sol", "fan", "en")
    assert result["source"] == "agents_sdk"
    assert run.await_count == 4
    assert run.call_args_list[0].kwargs["max_turns"] == 4


async def test_rejected_analysis_never_reaches_producer(monkeypatch):
    values = fixtures()
    values[1] = output(Review(approved=False, reason="Unsupported"))
    run = AsyncMock(side_effect=values)
    monkeypatch.setattr("matchlens.intelligence.Runner.run", run)
    with pytest.raises(ValueError, match="rejected"):
        await generate_analysis(snapshot(), "gpt-6-sol", "fan", "en")
    assert run.await_count == 2


async def test_invalid_evidence_is_blocked_before_review(monkeypatch):
    values = fixtures()
    values[0].final_output.claims[0].evidence_event_ids = ["invented"]
    run = AsyncMock(side_effect=values)
    monkeypatch.setattr("matchlens.intelligence.Runner.run", run)
    with pytest.raises(ValueError, match="Evidence"):
        await generate_analysis(snapshot(), "gpt-6-sol", "fan", "en")
    assert run.await_count == 1


async def test_final_translation_review_can_reject(monkeypatch):
    values = fixtures()
    values[-1] = output(Review(approved=False, reason="Translation invented fact"))
    monkeypatch.setattr("matchlens.intelligence.Runner.run", AsyncMock(side_effect=values))
    with pytest.raises(ValueError, match="final narrative"):
        await generate_analysis(snapshot(), "gpt-6-sol", "fan", "es")


@pytest.mark.parametrize("ids", [[], ["r-3420", "r-3420"], ["s-1680"]])
def test_missing_duplicate_or_out_of_window_evidence(ids):
    with pytest.raises(ValueError):
        validate_evidence(ids, snapshot())


async def test_generation_retries_once_with_feedback_and_publishes_atomically(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("MATCHLENS_PROVIDER", "openai")
    monkeypatch.setattr(intelligence, "DATA_DIR", tmp_path)
    client = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(intelligence, "AsyncOpenAI", lambda **kwargs: client)
    monkeypatch.setattr(intelligence, "OpenAIResponsesModel", lambda **kwargs: "model")
    run = AsyncMock(side_effect=[ValueError("Sequence unsupported")] + [{} for _ in range(8)])
    monkeypatch.setattr(intelligence, "generate_analysis", run)
    await intelligence.generate_artifacts()
    assert run.await_count == 9
    assert run.call_args_list[1].args[-1] == "Sequence unsupported"
    assert (tmp_path / "insights.json").exists()
    assert not (tmp_path / "insights.tmp").exists()
    client.close.assert_awaited_once()


async def test_failed_correction_preserves_previous_artifacts(monkeypatch, tmp_path):
    monkeypatch.setenv("MATCHLENS_PROVIDER", "openai")
    monkeypatch.setattr(intelligence, "DATA_DIR", tmp_path)
    (tmp_path / "insights.json").write_text("previous")
    client = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(intelligence, "AsyncOpenAI", lambda **kwargs: client)
    monkeypatch.setattr(intelligence, "OpenAIResponsesModel", lambda **kwargs: "model")
    run = AsyncMock(side_effect=ValueError("Rejected"))
    monkeypatch.setattr(intelligence, "generate_analysis", run)
    with pytest.raises(ValueError, match="Rejected"):
        await intelligence.generate_artifacts()
    assert run.await_count == 2
    assert (tmp_path / "insights.json").read_text() == "previous"
    client.close.assert_awaited_once()
