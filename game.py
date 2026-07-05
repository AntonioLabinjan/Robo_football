"""Game orchestration: state machine, fixed-timestep simulation, kickoff, goals."""
from __future__ import annotations
import pygame
import config as cfg
from physics import Vec2
from field import Field
from ball import Ball
from team import Team, Tactics
from ai import RobotAI
from statistics import MatchStats
from renderer import Renderer
from gui import GUI


class GameState:
    SETUP = "SETUP"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    GOAL = "GOAL"
    FINISHED = "FINISHED"


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.field = Field()

        blue_tactics = Tactics(aggression=0.6, attack_bias="Balanced", passing_pref="Short",
                                shooting_distance=260, formation="2-2-1")
        red_tactics = Tactics(aggression=0.5, attack_bias="Balanced", passing_pref="Safe",
                               shooting_distance=240, formation="1-3-1")

        self.team_blue = Team("BLUE", "LEFT", cfg.COLOR_BLUE, blue_tactics, self.field)
        self.team_red = Team("RED", "RIGHT", cfg.COLOR_RED, red_tactics, self.field)

        self.ball = Ball(self.field.center.x, self.field.center.y)
        self.stats = MatchStats([self.team_blue.name, self.team_red.name])

        self.state = GameState.SETUP
        self.time_remaining = cfg.MATCH_SECONDS
        self.sim_speed = 1.0
        self.goal_message_timer = 0.0
        self.stall_timer = 0.0
        self.last_ball_pos = Vec2(self.ball.pos.x, self.ball.pos.y)
        self.foul_timers = {}

        self.renderer = Renderer(screen, self.field)
        self.gui = GUI(screen, self)
        self.font_end_title = pygame.font.SysFont("consolas", 36, bold=True)
        self.font_end_score = pygame.font.SysFont("consolas", 24)
        self.font_goal = pygame.font.SysFont("consolas", 40, bold=True)

    # ---- Button callbacks ----
    def start(self) -> None:
        if self.state in (GameState.SETUP, GameState.FINISHED):
            self._full_reset()
            self.state = GameState.RUNNING

    def pause(self) -> None:
        if self.state == GameState.RUNNING:
            self.state = GameState.PAUSED

    def resume(self) -> None:
        if self.state == GameState.PAUSED:
            self.state = GameState.RUNNING

    def restart(self) -> None:
        self._full_reset()
        self.state = GameState.RUNNING

    def reset_match(self) -> None:
        self._full_reset()
        self.state = GameState.SETUP

    def set_speed(self, speed: float) -> None:
        self.sim_speed = speed

    def _full_reset(self) -> None:
        self.team_blue.score = 0
        self.team_red.score = 0
        self.time_remaining = cfg.MATCH_SECONDS
        self.stats = MatchStats([self.team_blue.name, self.team_red.name])
        self.team_blue.reset_positions()
        self.team_red.reset_positions()
        self.ball.reset(self.field.center.x, self.field.center.y)
        self.stall_timer = 0.0
        self.last_ball_pos = Vec2(self.ball.pos.x, self.ball.pos.y)
        self.foul_timers = {}

    def _kickoff(self) -> None:
        self.team_blue.reset_positions()
        self.team_red.reset_positions()
        self.ball.reset(self.field.center.x, self.field.center.y)

    # ---- Event handling ----
    def handle_event(self, event) -> None:
        self.gui.handle_event(event)

    # ---- Simulation ----
    def update(self, real_dt: float) -> None:
        if self.state == GameState.GOAL:
            self.goal_message_timer -= real_dt
            if self.goal_message_timer <= 0:
                self._kickoff()
                self.state = GameState.RUNNING
            return
        if self.state != GameState.RUNNING:
            return
        dt = real_dt * self.sim_speed
        steps = max(1, int(round(self.sim_speed)))
        step_dt = dt / steps
        for _ in range(steps):
            self._simulate_step(step_dt)
        self._update_stats(dt)
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.time_remaining = 0
            self.state = GameState.FINISHED

    def _simulate_step(self, dt: float) -> None:
        self.team_blue.update_home_positions(self.ball.pos)
        self.team_red.update_home_positions(self.ball.pos)

        for robot in self.team_blue.robots:
            ai = RobotAI(robot, self.team_blue, self.team_red.robots, self.ball, self.stats)
            ai.decide_and_act(dt)
        for robot in self.team_red.robots:
            ai = RobotAI(robot, self.team_red, self.team_blue.robots, self.ball, self.stats)
            ai.decide_and_act(dt)

        all_robots = self.team_blue.robots + self.team_red.robots
        bounds = self.field.bounds()
        for r in all_robots:
            r.update_kinematics(dt)
            r.clamp_to_field(bounds)

        self._update_fouls(dt)
        self._resolve_robot_collisions(all_robots)
        self._enforce_penalty_box_limits()
        goal_range = (self.field.goal_top, self.field.goal_bottom)
        self.ball.update(dt, bounds, goal_range)
        self._check_goal()
        self._watch_for_stall(dt)

    def _update_fouls(self, dt: float) -> None:
        """Two opposing robots touching for over FOUL_CONTACT_SECONDS is a
        foul: whichever of the pair did not have the ball gets pushed back,
        and the ball carrier is forced to pass to their nearest teammate."""
        contact_dist = cfg.ROBOT_RADIUS * 2
        live_pairs = set()
        for a in self.team_blue.robots:
            for b in self.team_red.robots:
                if a.pos.dist_to(b.pos) >= contact_dist:
                    continue
                key = (a, b)
                live_pairs.add(key)
                elapsed = self.foul_timers.get(key, 0.0) + dt
                if elapsed >= cfg.FOUL_CONTACT_SECONDS:
                    self._call_foul(a, b)
                    elapsed = 0.0
                self.foul_timers[key] = elapsed
        # reset timers for pairs no longer touching
        for key in list(self.foul_timers.keys()):
            if key not in live_pairs:
                del self.foul_timers[key]

    def _call_foul(self, a, b) -> None:
        carrier, offender = (a, b) if self.ball.possessor is a else (b, a) if self.ball.possessor is b else (None, None)
        if carrier is None:
            return  # no one had the ball, nothing to penalize
        direction = (offender.pos - carrier.pos)
        direction = direction.normalized() if direction.length() > 1e-6 else Vec2(1, 0)
        offender.pos = offender.pos + direction * cfg.FOUL_PUSHBACK
        mates = [m for m in carrier.team.robots if m is not carrier]
        nearest = min(mates, key=lambda m: m.pos.dist_to(carrier.pos), default=None)
        if nearest is None:
            return
        pass_dir = (nearest.pos - carrier.pos)
        pass_dir = pass_dir.normalized() if pass_dir.length() > 1e-6 else Vec2(1, 0)
        carrier.has_ball = False
        self.ball.kick(pass_dir, cfg.PASS_SPEED, carrier.team, robot=carrier)
        self.stats.stats[carrier.team.name].passes_completed += 1

    def _enforce_penalty_box_limits(self) -> None:
        """Hard rule: at most cfg.MAX_DEFENDERS_IN_BOX teammates may occupy
        their own penalty box at once. The AI already steers robots to avoid
        overcrowding, but loose-ball scrambles can still shove extras in
        faster than they can be steered out, so this guarantees the limit
        actually holds at every tick. The ball carrier (if any) is exempt,
        since teleporting it would also snap the ball's visible position."""
        for team in (self.team_blue, self.team_red):
            box = self.field.penalty_box_left() if team.side == "LEFT" else self.field.penalty_box_right()
            x0, y0, x1, y1 = box
            inside = [r for r in team.robots if x0 <= r.pos.x <= x1 and y0 <= r.pos.y <= y1]
            carrier = self.ball.possessor
            if carrier in inside:
                inside.remove(carrier)
            if len(inside) <= cfg.MAX_DEFENDERS_IN_BOX:
                continue
            inside.sort(key=lambda r: r.pos.dist_to(self.ball.pos))
            excess = inside[cfg.MAX_DEFENDERS_IN_BOX:]
            margin = cfg.ROBOT_RADIUS + 2
            for r in excess:
                dists = {"left": r.pos.x - x0, "right": x1 - r.pos.x,
                         "top": r.pos.y - y0, "bottom": y1 - r.pos.y}
                closest = min(dists, key=dists.get)
                if closest == "left":
                    r.pos.x = x0 - margin
                elif closest == "right":
                    r.pos.x = x1 + margin
                elif closest == "top":
                    r.pos.y = y0 - margin
                else:
                    r.pos.y = y1 + margin

    def _watch_for_stall(self, dt: float) -> None:
        """If the ball hasn't meaningfully moved for a while (a jam/pile-up
        near a wall or corner), force it loose toward the field center so
        play can't lock up permanently."""
        moved = self.ball.pos.dist_to(self.last_ball_pos)
        self.stall_timer += dt
        if moved > 30.0:
            self.stall_timer = 0.0
            self.last_ball_pos = self.ball.pos.copy()

        if self.stall_timer > 6.0:
            self.team_blue.reset_positions()
            self.team_red.reset_positions()
            self.ball.reset(self.field.center.x, self.field.center.y)
            self.stall_timer = 0.0
            self.last_ball_pos = self.ball.pos.copy()

    def _resolve_robot_collisions(self, robots) -> None:
        n = len(robots)
        min_dist = cfg.ROBOT_RADIUS * 2
        for i in range(n):
            for j in range(i + 1, n):
                a, b = robots[i], robots[j]
                d = a.pos.dist_to(b.pos)
                if 0 < d < min_dist:
                    overlap = (min_dist - d) / 2
                    direction = (a.pos - b.pos).normalized()
                    a.pos = a.pos + direction * overlap
                    b.pos = b.pos - direction * overlap

    def _check_goal(self) -> None:
        result = self.field.check_goal(self.ball.pos)
        if result is None:
            return
        if result == "LEFT":
            self.team_red.score += 1
            self.stats.stats[self.team_red.name].goals += 1
        else:
            self.team_blue.score += 1
            self.stats.stats[self.team_blue.name].goals += 1
        self.state = GameState.GOAL
        self.goal_message_timer = 1.5

    def _update_stats(self, dt: float) -> None:
        self.stats.record_speeds(self.team_blue.name, self.team_blue.robots)
        self.stats.record_speeds(self.team_red.name, self.team_red.robots)
        if self.ball.possessor is not None:
            team_name = self.ball.possessor.team.name
            self.stats.stats[team_name].possession_time += dt

    # ---- Rendering ----
    def draw(self) -> None:
        self.screen.fill(cfg.COLOR_BG)
        self.renderer.draw_field()
        for r in self.team_blue.robots:
            self.renderer.draw_robot(r)
        for r in self.team_red.robots:
            self.renderer.draw_robot(r)
        self.renderer.draw_ball(self.ball)
        self.gui.draw()
        if self.state == GameState.FINISHED:
            self._draw_end_screen()

    def _draw_end_screen(self) -> None:
        overlay = pygame.Surface((cfg.SCREEN_W, cfg.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        text = self.font_end_title.render("MATCH FINISHED", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=(cfg.SCREEN_W // 2, cfg.SCREEN_H // 2 - 30)))
        score = self.font_end_score.render(
            f"{self.team_blue.name} {self.team_blue.score} - {self.team_red.score} {self.team_red.name}",
            True, (255, 255, 255))
        self.screen.blit(score, score.get_rect(center=(cfg.SCREEN_W // 2, cfg.SCREEN_H // 2 + 15)))