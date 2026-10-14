"""Versioned synthetic feed. Event time and arrival order are deliberately different."""

from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from matchlens.domain import Team, stats


class FeedEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    event_id: str = Field(pattern=r"^[a-z0-9-]{1,40}$")
    revision: int = Field(default=1, ge=1, le=10)
    second: int = Field(ge=0, le=5400)
    team: Team
    player: str = Field(max_length=40)
    kind: Literal["pass", "recovery", "shot", "goal", "pressure"]
    possession_id: str = Field(max_length=40)
    x: float = Field(ge=0, le=105)
    y: float = Field(ge=0, le=68)
    end_x: float = Field(ge=0, le=105)
    end_y: float = Field(ge=0, le=68)
    successful: bool = True
    void: bool = False

    @property
    def evidence_id(self):
        return f"{self.event_id}@{self.revision}"


class MatchState:
    def __init__(self):
        self.events: dict[str, FeedEvent] = {}
        self.arrivals: list[FeedEvent] = []

    def ingest(self, event: FeedEvent) -> bool:
        previous = self.events.get(event.event_id)
        if previous and event.revision <= previous.revision:
            if event.revision == previous.revision and event != previous:
                raise ValueError("Conflicting payload at the same event revision")
            return False
        if previous and event.revision != previous.revision + 1:
            raise ValueError("Revision gap")
        if not previous and event.revision != 1:
            raise ValueError("First revision must be one")
        self.events[event.event_id] = event
        self.arrivals.append(event)
        return True

    def snapshot(self, clock: int) -> dict:
        active = sorted(
            (e for e in self.events.values() if not e.void and e.second <= clock),
            key=lambda e: (e.second, e.event_id),
        )
        prior = [e for e in active if e.second < 3480]
        recent = [e for e in active if e.second >= 3480]
        facts = {}
        for label, group in (("before", prior), ("after", recent)):
            for team in Team:
                for kind in ("pass", "recovery", "shot", "goal", "pressure"):
                    relevant = [e for e in group if e.team == team and e.kind == kind]
                    facts[f"{label}.{team.value}.{kind}"] = {
                        "value": len(relevant),
                        "unit": "events",
                        "evidence_ids": [e.evidence_id for e in relevant],
                    }
        for team in Team:
            goals = [e for e in active if e.team == team and e.kind == "goal"]
            facts[f"score.{team.value}"] = {
                "value": len(goals),
                "unit": "goals",
                "evidence_ids": [e.evidence_id for e in goals],
            }
        voids = [e for e in self.events.values() if e.void and e.second <= clock]
        facts["corrections.void_goals"] = {
            "value": sum(e.kind == "goal" for e in voids),
            "unit": "events",
            "evidence_ids": [e.evidence_id for e in voids if e.kind == "goal"],
        }
        facts["window.before_seconds"] = {
            "value": min(180, max(0, clock - 3300 + 1)),
            "unit": "seconds",
            "evidence_ids": [],
        }
        facts["window.after_seconds"] = {
            "value": max(0, clock - 3480 + 1),
            "unit": "seconds",
            "evidence_ids": [],
        }
        evidence = [
            dict(e.model_dump(mode="json"), event_id=e.evidence_id)
            for e in sorted(active + voids, key=lambda e: (e.second, e.event_id))
        ]
        digest = sha256("".join(e.model_dump_json() for e in self.arrivals).encode()).hexdigest()
        return {
            "match": {
                "match_id": "harbor-live",
                "home": "Harbor FC",
                "away": "Summit United",
                "synthetic": True,
                "coverage": "Authored synthetic six-minute event stream",
                "coordinate_system": "105m x 68m; attack-normalized x",
            },
            "window": {"start_second": 3300, "end_second": clock + 1},
            "score": {t.value: facts[f"score.{t.value}"]["value"] for t in Team},
            "stats": stats(active),
            "events": evidence,
            "facts": facts,
            "comparison": {
                "before": stats(prior),
                "after": stats(recent),
                "split_second": 3480,
                "before_seconds": min(180, max(0, clock - 3300 + 1)),
                "after_seconds": max(0, clock - 3480 + 1),
            },
            "revision": len(self.arrivals),
            "evidence_hash": digest,
            "limitations": [
                "Synthetic scenario, not real match footage or tracking.",
                "Counts describe events; they do not establish tactical causality.",
                "Before/after durations may differ during the live stream.",
            ],
        }


def scenario(seed: int = 7) -> list[tuple[int, list[FeedEvent]]]:
    """Six arrival batches: control, turnover, pressure, chance, goal, correction.

    Possession IDs explicitly connect authored passes. A late event and duplicate
    exercise reconciliation; the last batch voids a previously reported goal.
    Seed changes pass coordinates, never the gold-standard counts.
    """
    batches = []
    for phase in range(6):
        base = 3300 + phase * 60
        team = Team.AWAY if phase < 3 else Team.HOME
        prefix = "S" if team == Team.AWAY else "H"
        possession = f"move-{phase}"
        x, y = 22 + (seed + phase * 3) % 15, 16 + (seed * 3 + phase * 7) % 32
        if phase >= 3:
            x = 70 + (seed + phase) % 4
        start_x, start_y = x, y
        events = []
        deltas = (7, 8, 6) if phase >= 3 else (12, 21, 9)
        for step, delta in enumerate(deltas):
            end_x, end_y = x + delta, y + (5 if step % 2 else -3)
            events.append(
                FeedEvent(
                    event_id=f"p-{phase}-{step}",
                    second=base + 6 + step * 8,
                    team=team,
                    player=f"{prefix}{6 + step}",
                    kind="pass",
                    possession_id=possession,
                    x=x,
                    y=y,
                    end_x=end_x,
                    end_y=end_y,
                )
            )
            x, y = end_x, end_y
        if phase >= 3:
            events.insert(
                0,
                FeedEvent(
                    event_id=f"press-{phase}",
                    second=base + 1,
                    team=team,
                    player="H8",
                    kind="pressure",
                    possession_id=possession,
                    x=start_x + 2,
                    y=start_y,
                    end_x=start_x + 2,
                    end_y=start_y,
                ),
            )
            events.insert(
                1,
                FeedEvent(
                    event_id=f"recover-{phase}",
                    second=base + 3,
                    team=team,
                    player="H6",
                    kind="recovery",
                    possession_id=possession,
                    x=start_x,
                    y=start_y,
                    end_x=start_x,
                    end_y=start_y,
                ),
            )
        if phase in (1, 3, 4):
            events.append(
                FeedEvent(
                    event_id=f"finish-{phase}",
                    second=base + 38,
                    team=team,
                    player=f"{prefix}9",
                    kind="goal" if phase == 4 else "shot",
                    possession_id=possession,
                    x=88 + phase,
                    y=29 + phase,
                    end_x=105,
                    end_y=34,
                    successful=phase == 4,
                )
            )
        if phase == 2:
            events.append(batches[0][1][0])  # duplicate delivery
            events.append(
                FeedEvent(
                    event_id="late-pass",
                    second=3350,
                    team=Team.AWAY,
                    player="S10",
                    kind="pass",
                    possession_id="late-move",
                    x=44,
                    y=48,
                    end_x=38,
                    end_y=44,
                    successful=False,
                )
            )
        if phase == 5:
            goal = next(e for e in batches[4][1] if e.kind == "goal")
            events.append(goal.model_copy(update={"revision": 2, "void": True}))
        batches.append((base + 59, events))
    return batches
