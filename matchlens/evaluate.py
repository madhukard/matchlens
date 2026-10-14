"""Reproducible paired evaluation. Model grading is advisory, never a human audit."""

import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter

from pydantic import Field

from matchlens.live_agents import Budget, StrictModel, Workflow
from matchlens.live_domain import MatchState, scenario
from matchlens.worker import model_client, timestamp


class Grade(StrictModel):
    factually_supported: bool
    audience_adapted: bool
    correction_clear: bool
    unsupported_claims: list[str] = Field(max_length=8)
    reason: str = Field(max_length=500)


def cases():
    for name, phase, sparse in (
        ("opening", 1, False),
        ("pressure", 3, False),
        ("goal_correction", 5, False),
        ("sparse", 3, True),
    ):
        state = MatchState()
        for clock, events in scenario(seed=19)[: phase + 1]:
            for event in events:
                if not sparse or event.kind in ("pass", "pressure"):
                    state.ingest(event)
        yield name, state.snapshot(clock)


def challenge_cases():
    """Additional authored cases change facts, not just pitch coordinates."""
    yield "empty_feed", MatchState().snapshot(3359)
    state = MatchState()
    for clock, events in scenario(seed=31)[:4]:
        for event in events:
            if event.kind == "pass":
                event = event.model_copy(update={"successful": False})
            state.ingest(event)
    yield "all_passes_unsuccessful", state.snapshot(clock)
    state = MatchState()
    for clock, events in scenario(seed=31):
        for event in events:
            state.ingest(event)
    goal = state.events["finish-4"]
    state.ingest(goal.model_copy(update={"revision": 3, "void": False}))
    yield "goal_reinstated", state.snapshot(clock)
    second_goal = goal.model_copy(update={"event_id": "second-goal", "revision": 1})
    state.ingest(second_goal.model_copy(update={"void": False}))
    state.ingest(second_goal.model_copy(update={"revision": 2, "void": True}))
    state.ingest(goal.model_copy(update={"revision": 4, "void": True}))
    yield "two_voided_goals", state.snapshot(clock)


async def evaluate(model, extended=False, target=None):
    target = Path(target or "matchlens/data/evaluation.json")
    if target.exists():
        raise FileExistsError(f"Preserve existing evaluation: {target}")
    budget = Budget(tokens=1_200_000, calls=64)
    results = []
    suite = list(cases()) + (list(challenge_cases()) if extended else [])
    for index, (name, data) in enumerate(suite):
        # Counterbalance order to reduce consistent first/second-call bias.
        for baseline in (True, False) if index % 2 == 0 else (False, True):
            workflow = Workflow(model, budget)
            start = perf_counter()
            row = {
                "case": name,
                "approach": "single" if baseline else "multi",
                "evidence_hash": data["evidence_hash"],
                "snapshot": data,
            }
            try:
                package = await workflow.produce(data, baseline=baseline)
                row.update(published=True, package=package.model_dump())
            except Exception as error:
                row.update(published=False, error_type=type(error).__name__)
                if isinstance(error, ValueError):
                    row["failure_reason"] = str(error)
            row["latency_seconds"] = round(perf_counter() - start, 3)
            row["trace"] = workflow.trace
            row["input_tokens"] = sum(t.get("input_tokens", 0) for t in workflow.trace)
            row["output_tokens"] = sum(t.get("output_tokens", 0) for t in workflow.trace)
            if row["published"]:
                grader = Workflow(model, budget)
                try:
                    grade = await grader.call(
                        "Blinded evaluation grader",
                        "Grade this anonymous candidate against the supplied evidence. "
                        "Check all four localized stories, claims, cited facts, score "
                        "correction and audience differences. When no correction exists, "
                        "correction_clear is true unless one is invented. Report specific "
                        "unsupported claims. Do not favor longer or more technical writing.",
                        {
                            "facts": data["facts"],
                            "comparison": data["comparison"],
                            "candidate": package.model_dump(),
                        },
                        Grade,
                    )
                    row["advisory_grade"] = grade.model_dump()
                except Exception as error:
                    row["grading_error"] = type(error).__name__
                row["grader_trace"] = grader.trace
            results.append(row)
            print(
                f"{name}/{row['approach']}: published={row['published']} "
                f"latency={row['latency_seconds']}s",
                flush=True,
            )
            Path(".local").mkdir(exist_ok=True)
            Path(".local/evaluation-progress.json").write_text(json.dumps(results, indent=2))
    summary = {}
    for approach in ("single", "multi"):
        rows = [r for r in results if r["approach"] == approach]
        summary[approach] = {
            "cases": len(rows),
            "published": sum(r["published"] for r in rows),
            "advisory_supported": sum(
                r.get("advisory_grade", {}).get("factually_supported", False) for r in rows
            ),
            "mean_latency_seconds": round(sum(r["latency_seconds"] for r in rows) / len(rows), 2),
            "input_tokens": sum(r["input_tokens"] for r in rows),
            "output_tokens": sum(r["output_tokens"] for r in rows),
        }
    report = {
        "created_at": timestamp(),
        "summary": summary,
        "results": results,
        "limitations": [
            f"{len(suite)} paired authored synthetic cases, one run per approach; exploratory.",
            "Same model grades outputs blindly; correlated errors remain.",
            "Tokens and latency measured; dollar cost requires account pricing.",
            "No claims of statistical superiority or independent human review.",
        ],
        "budget": {"reserved_token_limit": 1_200_000, "model_call_limit": 64},
    }
    report["suite"] = "extended-v1" if extended else "original-v1"
    report["approach_order"] = "alternating by case"
    report["model"] = str(getattr(model, "model", "unspecified"))
    target = Path(target or "matchlens/data/evaluation.json")
    if target.exists():
        raise FileExistsError(f"Preserve existing evaluation: {target}")
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(summary), flush=True)
    return report


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--output", default="matchlens/data/evaluation.json")
    args = parser.parse_args()
    if Path(args.output).exists():
        parser.error("Output already exists; choose a new path to preserve prior trials")
    async with model_client() as model:
        await evaluate(model, extended=args.extended, target=args.output)


if __name__ == "__main__":
    asyncio.run(main())
