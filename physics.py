"""Vector math and generic physics helpers."""
from __future__ import annotations
import math
from typing import Tuple


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.y * s)

    __rmul__ = __mul__

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vec2":
        l = self.length()
        if l < 1e-6:
            return Vec2(0, 0)
        return Vec2(self.x / l, self.y / l)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def limit(self, max_len: float) -> "Vec2":
        l = self.length()
        if l > max_len and l > 1e-6:
            f = max_len / l
            return Vec2(self.x * f, self.y * f)
        return self.copy()

    def dist_to(self, o: "Vec2") -> float:
        return math.hypot(self.x - o.x, self.y - o.y)


def apply_friction(velocity: Vec2, friction: float, dt: float) -> Vec2:
    speed = velocity.length()
    if speed <= 1e-6:
        return Vec2(0, 0)
    drop = friction * dt
    new_speed = max(0.0, speed - drop)
    return velocity.normalized() * new_speed


def move_towards(current_vel: Vec2, current_pos: Vec2, target: Vec2, accel: float, max_speed: float, dt: float) -> Vec2:
    desired = (target - current_pos)
    if desired.length() > 1e-6:
        desired = desired.normalized() * max_speed
    steer = (desired - current_vel)
    steer = steer.limit(accel * dt)
    result = current_vel + steer
    return result.limit(max_speed)