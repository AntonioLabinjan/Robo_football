"""Team: roster, tactics, formation home-position computation."""
from __future__ import annotations
from typing import List
import config as cfg
from physics import Vec2
from robot import Robot
from formations import get_layout


class Tactics:
    def __init__(self, aggression: float = 0.5, attack_bias: str = "Balanced",
                 passing_pref: str = "Short", shooting_distance: float = 260.0,
                 formation: str = "2-2-1"):
        self.aggression = aggression
        self.attack_bias = attack_bias
        self.passing_pref = passing_pref
        self.shooting_distance = shooting_distance
        self.formation = formation


class Team:
    def __init__(self, name: str, side: str, color, tactics: Tactics, field):
        self.name = name
        self.side = side  # "LEFT" or "RIGHT" defending side
        self.color = color
        self.tactics = tactics
        self.field = field
        self.robots: List[Robot] = []
        self.score = 0
        self._build_roster()

    def _build_roster(self) -> None:
        layout = get_layout(self.tactics.formation)
        self.robots = []
        for i, (xf, yf) in enumerate(layout):
            pos = self._layout_to_world(xf, yf)
            r = Robot(i + 1, self, pos)
            self.robots.append(r)

    def _layout_to_world(self, xf: float, yf: float) -> Vec2:
        min_x, min_y, max_x, max_y = self.field.bounds()
        if self.side == "RIGHT":
            xf = 1.0 - xf
        x = min_x + xf * (max_x - min_x)
        y = min_y + yf * (max_y - min_y)
        return Vec2(x, y)

    def opponent_goal(self) -> Vec2:
        min_x, min_y, max_x, max_y = self.field.bounds()
        cy = (min_y + max_y) / 2
        if self.side == "LEFT":
            return Vec2(max_x, cy)
        return Vec2(min_x, cy)

    def own_goal(self) -> Vec2:
        min_x, min_y, max_x, max_y = self.field.bounds()
        cy = (min_y + max_y) / 2
        if self.side == "LEFT":
            return Vec2(min_x, cy)
        return Vec2(max_x, cy)

    def update_home_positions(self, ball_pos: Vec2) -> None:
        """Shift home positions slightly toward the ball for dynamic shape."""
        layout = get_layout(self.tactics.formation)
        min_x, min_y, max_x, max_y = self.field.bounds()
        bias_shift = {"Defensive": -0.06, "Balanced": 0.0, "Offensive": 0.08}[self.tactics.attack_bias]
        max_pull = 55.0
        for robot, (xf, yf) in zip(self.robots, layout):
            base = self._layout_to_world(xf, yf)
            pull = (ball_pos - base) * 0.15
            pull = pull.limit(max_pull)
            shift_x = bias_shift * (max_x - min_x)
            new_home = base + pull + Vec2(shift_x if self.side == "LEFT" else -shift_x, 0)
            robot.set_home(new_home)

    def apply_formation(self, formation: str) -> None:
        self.tactics.formation = formation

    def reset_positions(self) -> None:
        layout = get_layout(self.tactics.formation)
        for robot, (xf, yf) in zip(self.robots, layout):
            pos = self._layout_to_world(xf, yf)
            robot.pos = pos.copy()
            robot.vel = Vec2(0, 0)
            robot.set_home(pos)