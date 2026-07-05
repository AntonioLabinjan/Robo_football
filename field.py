"""Field geometry, boundaries and goal detection."""
from __future__ import annotations
import config as cfg
from physics import Vec2


class Field:
    def __init__(self):
        self.min_x = cfg.MARGIN
        self.min_y = cfg.MARGIN
        self.max_x = cfg.MARGIN + cfg.FIELD_W
        self.max_y = cfg.MARGIN + cfg.FIELD_H
        self.center = Vec2((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)
        self.goal_top = self.center.y - cfg.GOAL_WIDTH / 2
        self.goal_bottom = self.center.y + cfg.GOAL_WIDTH / 2

    def bounds(self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def check_goal(self, ball_pos: Vec2):
        """Return 'LEFT' or 'RIGHT' if ball entered that goal, else None."""
        if self.goal_top <= ball_pos.y <= self.goal_bottom:
            if ball_pos.x - cfg.BALL_RADIUS <= self.min_x - 2:
                return "LEFT"
            if ball_pos.x + cfg.BALL_RADIUS >= self.max_x + 2:
                return "RIGHT"
        return None

    def penalty_box_left(self):
        y0 = self.center.y - cfg.PENALTY_H / 2
        return (self.min_x, y0, self.min_x + cfg.PENALTY_W, y0 + cfg.PENALTY_H)

    def penalty_box_right(self):
        y0 = self.center.y - cfg.PENALTY_H / 2
        return (self.max_x - cfg.PENALTY_W, y0, self.max_x, y0 + cfg.PENALTY_H)
