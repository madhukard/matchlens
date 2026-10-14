"""Deterministic synthetic event data and auditable numerical calculations."""

from enum import StrEnum
from math import hypot
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Team(StrEnum):
    HOME = "harbor"
    AWAY = "summit"


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: str
    second: int = Field(ge=0, le=5400)
    team: Team
    player: str
    kind: Literal["pass", "recovery", "shot", "goal"]
    x: float = Field(ge=0, le=105)
    y: float = Field(ge=0, le=68)
    end_x: float = Field(ge=0, le=105)
    end_y: float = Field(ge=0, le=68)
    successful: bool


class Window(BaseModel):
    start_second: int = Field(default=3300, ge=0, le=5400)
    end_second: int = Field(default=3900, ge=0, le=5400)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_second <= self.start_second:
            raise ValueError("end_second must be greater than start_second")
        return self


MATCH_ID = "harbor-summit-demo"
MATCH = {
    "match_id": MATCH_ID,
    "home": "Harbor FC",
    "away": "Summit United",
    "competition": "MatchLens Exhibition",
    "synthetic": True,
    "duration_seconds": 5400,
    "coordinate_system": "105m x 68m; each team's attacking direction is increasing x",
    "coverage": "Selected illustrative on-ball events, not a complete tracking feed",
}


def generate_events() -> tuple[Event, ...]:
    """Author a reproducible scenario; positions are illustrative, never real tracking."""
    events = []
    for second in range(30, 5400, 45):
        # Synthetic possession episodes. Each episode's three passes stay on one team.
        episode = second // 135
        team = Team.HOME if episode % 2 == 0 else Team.AWAY
        if 3300 <= second <= 3900:
            team = Team.HOME if episode % 4 != 0 else Team.AWAY
        x = 25 + (second // 45 % 5) * 11
        y = 12 + (second // 90 % 4) * 13
        events.append(
            Event(
                event_id=f"e-{second}",
                second=second,
                team=team,
                player=("H" if team == Team.HOME else "S") + str(6 + episode % 5),
                kind="pass",
                x=x,
                y=y,
                end_x=min(x + 14, 104),
                end_y=min(y + 4, 67),
                successful=episode % 7 != 0,
            )
        )
    for second, player in [(3420, "H8"), (3560, "H6"), (3730, "H8")]:
        events.append(
            Event(
                event_id=f"r-{second}",
                second=second,
                team=Team.HOME,
                player=player,
                kind="recovery",
                x=78,
                y=24,
                end_x=78,
                end_y=24,
                successful=True,
            )
        )
    for second, team, player, kind in [
        (1680, Team.AWAY, "S9", "goal"),
        (3460, Team.HOME, "H9", "shot"),
        (3610, Team.HOME, "H10", "shot"),
        (3780, Team.HOME, "H9", "goal"),
        (4920, Team.HOME, "H10", "goal"),
    ]:
        events.append(
            Event(
                event_id=f"s-{second}",
                second=second,
                team=team,
                player=player,
                kind=kind,
                x=91,
                y=30,
                end_x=105,
                end_y=34,
                successful=kind == "goal",
            )
        )
    return tuple(sorted(events, key=lambda event: (event.second, event.event_id)))


EVENTS = generate_events()


def validate_match(match_id: str) -> None:
    if match_id != MATCH_ID:
        raise ValueError("Unknown match_id")


def select_events(window: Window) -> list[Event]:
    # Half-open intervals avoid double counting boundary events between adjacent windows.
    return [e for e in EVENTS if window.start_second <= e.second < window.end_second]


def stats(events: list[Event]) -> dict:
    result = {}
    for team in Team:
        own = [e for e in events if e.team == team]
        passes = [e for e in own if e.kind == "pass"]
        completed = [e for e in passes if e.successful]
        result[team.value] = {
            "passes": len(passes),
            "completed_passes": len(completed),
            "pass_accuracy": round(100 * len(completed) / len(passes), 1) if passes else None,
            "shots": sum(e.kind in ("shot", "goal") for e in own),
            "goals": sum(e.kind == "goal" for e in own),
            "high_recoveries": sum(e.kind == "recovery" and e.x >= 70 for e in own),
            "progressive_passes": sum(e.successful and e.end_x - e.x >= 10 for e in passes),
            "pass_distance_m": round(sum(hypot(e.end_x - e.x, e.end_y - e.y) for e in passes), 1),
        }
    return result


def snapshot(match_id: str = MATCH_ID, start_second: int = 3300, end_second: int = 3900) -> dict:
    validate_match(match_id)
    window = Window(start_second=start_second, end_second=end_second)
    events = select_events(window)
    return {
        "match": MATCH,
        "window": window.model_dump(),
        "stats": stats(events),
        "score": {
            t.value: sum(e.kind == "goal" and e.team == t and e.second < end_second for e in EVENTS)
            for t in Team
        },
        "events": [e.model_dump(mode="json") for e in events],
        "limitations": [
            "Synthetic demonstration; no real Premier League footage or data.",
            "Pass share is not possession. No speed, xG or off-ball pressure is measured.",
        ],
    }
