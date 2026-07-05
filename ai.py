"""Per-tick robot decision making."""
from __future__ import annotations
import random
import config as cfg
from physics import Vec2
from robot import Action


class RobotAI:
    """Encapsulates decision logic for a single robot. Stateless helper class
    (kept separate so it can later be swapped for RL/planning based agents)."""

    def __init__(self, robot, team, opponents, ball, stats):
        self.robot = robot
        self.team = team
        self.opponents = opponents
        self.ball = ball
        self.stats = stats

    def decide_and_act(self, dt: float) -> None:
        r = self.robot
        ball = self.ball
        dist_to_ball = r.pos.dist_to(ball.pos)

        if ball.possessor is r:
            self._act_with_ball(dt)
            return

        closest_teammate = self._closest_teammate_to_ball()
        i_am_closest = closest_teammate is r or closest_teammate is None

        if ball.possessor is None:
            if i_am_closest:
                r.current_action = Action.CHASE_BALL
                r.move_to(ball.pos, dt)  # always allowed to contest a loose ball
                self._try_pickup()
            else:
                r.current_action = Action.REPOSITION
                r.move_to(self._respect_box_limit(r.home_pos), dt)
        elif ball.possessor.team is r.team:
            r.current_action = Action.REPOSITION
            support_pos = self._support_position()
            r.move_to(self._respect_box_limit(support_pos), dt)
        else:
            if i_am_closest and dist_to_ball < 160:
                r.current_action = Action.MARK
                approach_dist = cfg.ROBOT_RADIUS * 1.1
                if dist_to_ball > approach_dist:
                    offset = (r.pos - ball.pos).normalized() * approach_dist
                    target = ball.pos + offset
                else:
                    target = r.pos
                target = self._respect_box_limit(target)
                r.move_to(target, dt, speed_mult=1.0)
                self._try_steal(dt)
            else:
                r.current_action = Action.DEFEND
                mark_target = self._defensive_position()
                mark_target = self._respect_box_limit(mark_target)
                r.move_to(mark_target, dt)

    def _own_box(self):
        f = self.team.field
        return f.penalty_box_left() if self.team.side == "LEFT" else f.penalty_box_right()

    @staticmethod
    def _point_in_box(pos: Vec2, box) -> bool:
        x0, y0, x1, y1 = box
        return x0 <= pos.x <= x1 and y0 <= pos.y <= y1

    def _teammates_in_box_excluding_self(self, box) -> int:
        r = self.robot
        count = 0
        for mate in self.team.robots:
            if mate is r:
                continue
            if self._point_in_box(mate.pos, box):
                count += 1
        return count

    def _respect_box_limit(self, target: Vec2) -> Vec2:
        """If a target sits inside our own penalty box but MAX_DEFENDERS_IN_BOX
        teammates are already in there, redirect the target to just outside
        the box instead, so at most that many defenders ever camp in it."""
        box = self._own_box()
        if not self._point_in_box(target, box):
            return target
        others = self._teammates_in_box_excluding_self(box)
        if others < cfg.MAX_DEFENDERS_IN_BOX:
            return target
        x0, y0, x1, y1 = box
        margin = cfg.ROBOT_RADIUS + 2
        x, y = target.x, target.y
        dists = {
            "left": x - x0,
            "right": x1 - x,
            "top": y - y0,
            "bottom": y1 - y,
        }
        closest = min(dists, key=dists.get)
        if closest == "left":
            return Vec2(x0 - margin, y)
        if closest == "right":
            return Vec2(x1 + margin, y)
        if closest == "top":
            return Vec2(x, y0 - margin)
        return Vec2(x, y1 + margin)

    def _act_with_ball(self, dt: float) -> None:
        r = self.robot
        goal = self.team.opponent_goal()
        dist_goal = r.pos.dist_to(goal)
        tactics = self.team.tactics
        r.possession_time += dt

        if r.possession_time < 0.35:
            r.current_action = Action.DRIBBLE
            self._dribble(goal, dt)
            return

        if r.possession_time >= cfg.MAX_HOLD_TIME:
            self._force_release(dist_goal, goal, tactics)
            return

        opp_nearby = self._nearest_opponent_dist()
        should_shoot = (dist_goal < tactics.shooting_distance * cfg.SHOOT_RANGE_MULTIPLIER
                         and random.random() < cfg.SHOOT_RATE_PER_SEC * dt)
        pressured = opp_nearby < cfg.ROBOT_RADIUS * 3

        if should_shoot:
            r.current_action = Action.SHOOT
            self._shoot(goal)
            return

        pass_target = self._best_pass_target()
        pass_rate = {"Safe": 0.6, "Short": 0.9, "Direct": 1.2}[tactics.passing_pref]
        if pressured and pass_target is not None and random.random() < pass_rate * dt:
            r.current_action = Action.PASS
            self._pass_to(pass_target)
            return

        r.current_action = Action.DRIBBLE
        self._dribble(goal, dt)

    def _force_release(self, dist_goal: float, goal: Vec2, tactics) -> None:
        """Called once a robot has held the ball for MAX_HOLD_TIME. It must
        get rid of the ball now: shoot if in range, else pass to a teammate,
        else just clear it forward so it can never stall play indefinitely."""
        r = self.robot
        if dist_goal < tactics.shooting_distance * cfg.SHOOT_RANGE_MULTIPLIER:
            r.current_action = Action.SHOOT
            self._shoot(goal)
            return

        pass_target = self._best_pass_target()
        if pass_target is not None:
            r.current_action = Action.PASS
            self._pass_to(pass_target)
            return

        r.current_action = Action.SHOOT
        self._clear_ball(goal)

    def _clear_ball(self, goal: Vec2) -> None:
        """Last-resort release when no pass or shot is available: boot the
        ball toward the opponent's goal so possession can't be held forever."""
        r = self.robot
        direction = (goal - r.pos).normalized()
        r.has_ball = False
        self.ball.kick(direction, cfg.PASS_SPEED, self.team, robot=r)

    def _dribble(self, goal, dt: float) -> None:
        r = self.robot
        direction = (goal - r.pos).normalized()
        target = r.pos + direction * 40
        r.move_to(target, dt, speed_mult=0.8)
        self.ball.pos = r.pos.copy()

    def _try_pickup(self) -> None:
        r = self.robot
        if self.ball.just_kicked_by(r):
            return
        if self.ball.possessor is None and r.pos.dist_to(self.ball.pos) < cfg.POSSESSION_RADIUS:
            self.ball.possessor = r
            r.has_ball = True
            r.possession_time = 0.0

    def _try_steal(self, dt: float) -> None:
        r = self.robot
        ball = self.ball
        if ball.possessor is not None and ball.possessor.team is not r.team:
            if r.pos.dist_to(ball.possessor.pos) < cfg.STEAL_RADIUS:
                steal_rate = 0.3 + self.team.tactics.aggression * 0.5  # per second
                if random.random() < steal_rate * dt:
                    ball.possessor.has_ball = False
                    ball.possessor = None
                    r.possession_time = 0.0
                    self.stats.stats[self.team.name].steals += 1

    def _shoot(self, goal: Vec2) -> None:
        r = self.robot
        direction = (goal - r.pos).normalized()
        jitter = Vec2(random.uniform(-cfg.SHOOT_JITTER, cfg.SHOOT_JITTER),
                       random.uniform(-cfg.SHOOT_JITTER, cfg.SHOOT_JITTER))
        direction = (direction + jitter).normalized()
        r.has_ball = False
        self.ball.kick(direction, cfg.SHOOT_SPEED, self.team, robot=r)
        s = self.stats.stats[self.team.name]
        s.shots += 1
        if abs(direction.y) < 0.35:
            s.shots_on_target += 1

    def _pass_to(self, target_robot) -> None:
        r = self.robot
        direction = (target_robot.pos - r.pos).normalized()
        r.has_ball = False
        self.ball.kick(direction, cfg.PASS_SPEED, self.team, robot=r)
        self.stats.stats[self.team.name].passes_completed += 1

    def _best_pass_target(self):
        r = self.robot
        best = None
        best_score = -1e9
        for mate in self.team.robots:
            if mate is r:
                continue
            d = r.pos.dist_to(mate.pos)
            if d < 30:
                continue
            forward = mate.pos.dist_to(self.team.opponent_goal())
            score = -forward + self._nearest_opponent_dist_to(mate.pos)
            if score > best_score:
                best_score = score
                best = mate
        return best

    def _support_position(self) -> Vec2:
        r = self.robot
        return r.home_pos.copy()

    def _defensive_position(self) -> Vec2:
        r = self.robot
        own_goal = self.team.own_goal()
        ball = self.ball
        blend = 0.3
        return Vec2(
            own_goal.x * (1 - blend) + ball.pos.x * blend,
            own_goal.y * (1 - blend) + ball.pos.y * blend,
        )

    def _closest_teammate_to_ball(self):
        best = None
        best_d = 1e9
        for mate in self.team.robots:
            d = mate.pos.dist_to(self.ball.pos)
            if d < best_d:
                best_d = d
                best = mate
        return best

    def _nearest_opponent_dist(self) -> float:
        return self._nearest_opponent_dist_to(self.robot.pos)

    def _nearest_opponent_dist_to(self, pos: Vec2) -> float:
        best = 1e9
        for opp in self.opponents:
            d = pos.dist_to(opp.pos)
            if d < best:
                best = d
        return best