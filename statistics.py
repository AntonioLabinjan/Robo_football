"""Match statistics tracking per team."""
from __future__ import annotations
from typing import Dict


class TeamStats:
    def __init__(self):
        self.goals = 0
        self.shots = 0
        self.shots_on_target = 0
        self.passes_completed = 0
        self.passes_failed = 0
        self.possession_time = 0.0
        self.interceptions = 0
        self.steals = 0
        self.total_speed_sample = 0.0
        self.speed_samples = 0
        self.distance_travelled = 0.0

    def avg_speed(self) -> float:
        if self.speed_samples == 0:
            return 0.0
        return self.total_speed_sample / self.speed_samples


class MatchStats:
    def __init__(self, team_names):
        self.stats: Dict[str, TeamStats] = {name: TeamStats() for name in team_names}

    def possession_pct(self):
        total = sum(s.possession_time for s in self.stats.values())
        if total <= 1e-6:
            return {name: 0.0 for name in self.stats}
        return {name: 100.0 * s.possession_time / total for name, s in self.stats.items()}

    def record_speeds(self, team_name: str, robots) -> None:
        s = self.stats[team_name]
        for r in robots:
            s.total_speed_sample += r.vel.length()
            s.speed_samples += 1
        s.distance_travelled = sum(r.distance_travelled for r in robots)
