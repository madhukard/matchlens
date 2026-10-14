"""Verify a completed public synthetic run and all localized tool variants."""

import argparse
import json
from pathlib import Path

import httpx

from matchlens.live_agents import Package, validate_package


def verify(base: str, save: Path | None = None):
    with httpx.Client(base_url=base.rstrip("/"), timeout=30) as client:
        response = client.get("/api/run")
        response.raise_for_status()
        run = response.json()
        assert run["status"] == "completed", "Run is not complete"
        assert len(run["frames"]) == 6
        for index, frame in enumerate(run["frames"]):
            assert frame["status"] == "approved", f"Frame {index} has no approved narrative"
            validate_package(Package.model_validate(frame["package"]), frame["snapshot"])
            for audience in ("fan", "analyst"):
                for language in ("en", "es"):
                    response = client.post(
                        "/api/tools",
                        json={
                            "name": "get_live_match",
                            "arguments": {
                                "frame": index,
                                "audience": audience,
                                "language": language,
                            },
                        },
                    )
                    response.raise_for_status()
                    data = response.json()["structuredContent"]
                    assert data["live"]["run_id"] == run["run_id"]
                    assert data["insight"]["source"] == "agents_sdk"
                    assert data["insight"]["language"] == language
                    assert data["score"]["harbor"] == (1 if index == 4 else 0)
        for evidence_id, expected in (("finish-4@1", 422), ("finish-4@2", 200)):
            response = client.post(
                "/api/tools",
                json={
                    "name": "get_live_evidence",
                    "arguments": {
                        "evidence_ids": [evidence_id],
                        "frame": 5,
                        "run_id": run["run_id"],
                    },
                },
            )
            assert response.status_code == expected
        assert (
            client.post(
                "/api/tools",
                json={
                    "name": "get_live_evidence",
                    "arguments": {"evidence_ids": ["finish-4@2"], "run_id": "different-run"},
                },
            ).status_code
            == 422
        )
        if save:
            save.write_text(json.dumps(run, indent=2, ensure_ascii=False))
        print(
            f"PASS: {run['run_id']}; 6 approved frames, 24 localized variants; "
            "retracted citation rejected"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base")
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    verify(args.base, args.save)
