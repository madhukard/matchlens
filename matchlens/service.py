"""Read-only shared service: no model credentials or paid calls on the public path."""

import json
from pathlib import Path
from typing import Literal

from matchlens.domain import EVENTS, MATCH, MATCH_ID, snapshot, validate_match

Audience = Literal["fan", "analyst"]
Language = Literal["en", "es"]
INSIGHTS = Path(__file__).parent / "data" / "insights.json"


def get_match_snapshot(
    match_id: str = MATCH_ID, start_second: int = 3300, end_second: int = 3900
) -> dict:
    """Read exact statistics and synthetic events for a half-open match window."""
    return snapshot(match_id, start_second, end_second)


def list_matches() -> dict:
    """List available fictional matches and their data coverage."""
    return {"matches": [MATCH]}


def get_evidence(event_ids: list[str], match_id: str = MATCH_ID) -> dict:
    """Resolve cited event IDs to original synthetic evidence; rejects unknown IDs."""
    validate_match(match_id)
    if not event_ids or len(event_ids) > 40:
        raise ValueError("Supply between 1 and 40 event IDs")
    lookup = {e.event_id: e for e in EVENTS}
    if any(event_id not in lookup for event_id in event_ids):
        raise ValueError("Unknown evidence event ID")
    return {
        "match_id": match_id,
        "synthetic": True,
        "events": [lookup[event_id].model_dump(mode="json") for event_id in event_ids],
    }


def explain_moment(
    match_id: str = MATCH_ID,
    start_second: int = 3300,
    end_second: int = 3900,
    audience: Audience = "fan",
    language: Language = "en",
) -> dict:
    data = snapshot(match_id, start_second, end_second)
    if audience not in ("fan", "analyst") or language not in ("en", "es"):
        raise ValueError("Unsupported audience or language")
    saved = json.loads(INSIGHTS.read_text()) if INSIGHTS.exists() else []
    insight = next(
        (
            item
            for item in saved
            if item["audience"] == audience
            and item["language"] == language
            and item["window"] == data["window"]
        ),
        None,
    )
    if insight:
        data["insight"] = insight
    else:
        data["insight"] = {
            "source": "statistics_only",
            "audience": audience,
            "language": language,
            "narrative": {
                "headline": "Explore the evidence" if language == "en" else "Explora la evidencia",
                "summary": (
                    "No reviewed AI narrative is saved for this window. Explore the exact "
                    "statistics and synthetic events below."
                    if language == "en"
                    else "No hay una narración de IA revisada para este intervalo. Explora las "
                    "estadísticas y los eventos sintéticos."
                ),
                "evidence_event_ids": [],
            },
        }
    return data


def compare_match_windows(
    match_id: str = MATCH_ID, split_second: int = 3300, window_seconds: int = 600
) -> dict:
    """Compare equal windows before and after a split using exact event counts."""
    if window_seconds < 1 or window_seconds > 2700:
        raise ValueError("window_seconds must be between 1 and 2700")
    before = snapshot(match_id, split_second - window_seconds, split_second)
    after = snapshot(match_id, split_second, split_second + window_seconds)
    return {
        "before": before,
        "after": after,
        "note": "Compare recorded events only; these are not possession estimates.",
    }


def create_recap(
    match_id: str = MATCH_ID, audience: Audience = "fan", language: Language = "en"
) -> dict:
    """Retrieve the prepared full-match recap; no mutation or paid generation."""
    return explain_moment(match_id, 0, 5400, audience, language)
