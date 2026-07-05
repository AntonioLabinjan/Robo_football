"""Autonomous robot player model."""
from __future__ import annotations
from enum import Enum, auto
import config as cfg
from physics import Vec2, move_towards, apply_friction


class Action(Enum):
    CHASE_BALL = auto()
    INTERCEPT = auto()
    DEFEND = auto()
    PASS = auto()
    SHOOT = auto()
    DRIBBLE = auto()
    REPOSITION = auto()
    MARK = auto()


class Robot:
    def __init__(self, robot_id: int, team, home_pos: Vec2):
        self.id = robot_id
        self.team = team
        self.pos = home_pos.copy()
        self.vel = Vec2(0, 0)
        self.direction = Vec2(1, 0)
        self.max_speed = cfg.MAX_SPEED
        self.acceleration = cfg.ACCELERATION
        self.stamina = 100.0
        self.has_ball = False
        self.home_pos = home_pos.copy()
        self.target_pos = home_pos.copy()
        self.current_action = Action.REPOSITION
        self.distance_travelled = 0.0
        self.possession_time = 0.0

    def set_home(self, pos: Vec2) -> None:
        self.home_pos = pos.copy()

    def move_to(self, target: Vec2, dt: float, speed_mult: float = 1.0) -> None:
        self.target_pos = target.copy()
        self.vel = move_towards(self.vel, self.pos, target, self.acceleration, self.max_speed * speed_mult, dt)

    def update_kinematics(self, dt: float) -> None:
        prev = self.pos.copy()
        self.pos = self.pos + self.vel * dt
        if self.vel.length() > 1e-3:
            self.direction = self.vel.normalized()
        else:
            self.vel = apply_friction(self.vel, cfg.FRICTION_ROBOT, dt)
        self.distance_travelled += prev.dist_to(self.pos)

    def clamp_to_field(self, bounds) -> None:
        min_x, min_y, max_x, max_y = bounds
        r = cfg.ROBOT_RADIUS
        self.pos.x = max(min_x + r, min(max_x - r, self.pos.x))
        self.pos.y = max(min_y + r, min(max_y - r, self.pos.y))