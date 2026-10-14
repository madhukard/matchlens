"""Read-only live-run tools shared by MCP and the standalone experience."""

from typing import Literal

from matchlens.live_domain import MatchState, scenario
from matchlens.live_store import read_run


def get_live_match(
    frame: int = -1,
    audience: Literal["fan", "analyst"] = "fan",
    language: Literal["en", "es"] = "en",
) -> dict:
    """Watch the current synthetic run or inspect a recorded frame; never starts generation."""
    if audience not in ("fan", "analyst") or language not in ("en", "es"):
        raise ValueError("Unsupported audience or language")
    run = read_run()
    frames = run["frames"]
    if frame < -1 or (frame >= len(frames) and frame != -1):
        raise ValueError("Frame out of range")
    if frames:
        index = len(frames) - 1 if frame == -1 else frame
        current = frames[index]
        data = dict(current["snapshot"])
    else:
        index = 0
        current = {}
        data = MatchState().snapshot(3300)
    package = current.get("package")
    if package and current.get("status") == "approved":
        story = package["stories"][f"{audience}_{language}"]
        ids = list(
            dict.fromkeys(
                event_id
                for fact in story["fact_ids"]
                for event_id in data["facts"][fact]["evidence_ids"]
            )
        )
        data["insight"] = {
            "source": "agents_sdk",
            "audience": audience,
            "language": language,
            "analysis": package["selection"],
            "narrative": {**story, "evidence_event_ids": ids},
        }
    else:
        data["insight"] = {
            "source": "statistics_only",
            "audience": audience,
            "language": language,
            "narrative": {
                "headline": "Checking the latest events"
                if language == "en"
                else "Verificando los últimos eventos",
                "summary": "The score and event counts are current. A new explanation appears "
                "only after evidence review."
                if language == "en"
                else "El marcador y los recuentos están actualizados. La explicación aparecerá "
                "solo después de revisar la evidencia.",
                "evidence_event_ids": [],
            },
        }
    trace = current.get("trace", [])
    data["live"] = {
        "run_id": run["run_id"],
        "status": run["status"],
        "delivery": run.get("delivery", "published_run"),
        "updated_at": run.get("updated_at"),
        "frame": index,
        "frame_count": len(frames),
        "frame_status": current.get("status", "waiting"),
        "latency_seconds": current.get("latency_seconds"),
        "input_tokens": sum(t.get("input_tokens", 0) for t in trace),
        "output_tokens": sum(t.get("output_tokens", 0) for t in trace),
        "workflow": [
            {k: t[k] for k in ("agent", "status", "latency_seconds", "reason") if k in t}
            for t in trace
        ],
        "error_type": current.get("error_type"),
        "model": run.get("model"),
        "budget": run.get("budget"),
    }
    return data


def get_live_evidence(
    evidence_ids: list[str], frame: int = -1, run_id: str | None = None
) -> dict:
    """Resolve revision-specific evidence IDs, including a voided goal correction."""
    if not 1 <= len(evidence_ids) <= 50:
        raise ValueError("Supply 1–50 evidence IDs")
    data = get_live_match(frame)
    if run_id is not None and run_id != data["live"]["run_id"]:
        raise ValueError("Run changed; refresh the match before resolving evidence")
    lookup = {e["event_id"]: e for e in data["events"]}
    if not set(evidence_ids) <= lookup.keys():
        raise ValueError("Unknown or superseded evidence in this frame")
    return {
        "run_id": data["live"]["run_id"],
        "revision": data["revision"],
        "evidence_hash": data["evidence_hash"],
        "events": [lookup[i] for i in evidence_ids],
    }


def list_live_scenarios() -> dict:
    return {
        "match_id": "harbor-live",
        "synthetic": True,
        "stages": [
            "Opening control",
            "First chance",
            "Late event arrives",
            "Pressure and recovery",
            "Goal reported",
            "Goal corrected",
        ],
        "arrival_batches": len(scenario()),
        "note": "Watching is read-only. Only the authenticated operator starts a run.",
    }
