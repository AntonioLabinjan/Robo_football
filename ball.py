"""Ball entity with simple physics."""
from __future__ import annotations
import config as cfg
from physics import Vec2, apply_friction


class Ball:
    def __init__(self, x: float, y: float):
        self.pos = Vec2(x, y)
        self.vel = Vec2(0, 0)
        self.radius = cfg.BALL_RADIUS
        self.possessor = None  # Robot or None
        self.last_touch_team = None
        self.last_kicker = None
        self.kick_origin = None

    def reset(self, x: float, y: float) -> None:
        self.pos = Vec2(x, y)
        self.vel = Vec2(0, 0)
        self.possessor = None
        self.last_kicker = None
        self.kick_origin = None

    def kick(self, direction: Vec2, speed: float, team, robot=None) -> None:
        d = direction.normalized()
        self.vel = d * min(speed, cfg.BALL_MAX_SPEED)
        self.possessor = None
        self.last_touch_team = team
        self.last_kicker = robot
        self.kick_origin = self.pos.copy()

    def just_kicked_by(self, robot) -> bool:
        """True while `robot` is still too close to its own recent kick to
        be allowed to immediately reclaim the ball."""
        if robot is not self.last_kicker or self.kick_origin is None:
            return False
        return self.pos.dist_to(self.kick_origin) < cfg.POSSESSION_RADIUS * 1.5

    def update(self, dt: float, field_bounds, goal_range=None) -> None:
        if self.possessor is not None:
            self.pos = self.possessor.pos.copy()
            self.vel = Vec2(0, 0)
            return
        self.vel = apply_friction(self.vel, cfg.BALL_FRICTION, dt)
        self.pos = self.pos + self.vel * dt
        in_goal_mouth = False
        if goal_range is not None:
            goal_top, goal_bottom = goal_range
            in_goal_mouth = goal_top <= self.pos.y <= goal_bottom
        self._bounce_bounds(field_bounds, in_goal_mouth)
        self._unstick_from_corner(field_bounds, in_goal_mouth)

    def _unstick_from_corner(self, bounds, in_goal_mouth: bool = False) -> None:
        if in_goal_mouth:
            return
        min_x, min_y, max_x, max_y = bounds
        edge = 25
        near_x = self.pos.x - min_x < edge or max_x - self.pos.x < edge
        near_y = self.pos.y - min_y < edge or max_y - self.pos.y < edge
        if near_x and near_y and self.vel.length() < 15:
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            inward = Vec2(center_x - self.pos.x, center_y - self.pos.y).normalized()
            self.vel = self.vel + inward * 40

    def _bounce_bounds(self, bounds, in_goal_mouth: bool = False) -> None:
        min_x, min_y, max_x, max_y = bounds
        if not in_goal_mouth:
            if self.pos.x - self.radius < min_x:
                self.pos.x = min_x + self.radius
                self.vel.x *= -0.6
            elif self.pos.x + self.radius > max_x:
                self.pos.x = max_x - self.radius
                self.vel.x *= -0.6
        if self.pos.y - self.radius < min_y:
            self.pos.y = min_y + self.radius
            self.vel.y *= -0.6
        elif self.pos.y + self.radius > max_y:
            self.pos.y = max_y - self.radius
            self.vel.y *= -0.6