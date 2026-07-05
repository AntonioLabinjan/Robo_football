"""Rendering: field, robots, ball."""
from __future__ import annotations
import pygame
import config as cfg
from field import Field


class Renderer:
    def __init__(self, screen: pygame.Surface, field: Field):
        self.screen = screen
        self.field = field
        self.font_small = pygame.font.SysFont("consolas", 12)

    def draw_field(self) -> None:
        f = self.field
        rect = pygame.Rect(f.min_x, f.min_y, f.max_x - f.min_x, f.max_y - f.min_y)
        pygame.draw.rect(self.screen, cfg.COLOR_FIELD, rect)
        pygame.draw.rect(self.screen, cfg.COLOR_LINE, rect, 2)

        pygame.draw.line(self.screen, cfg.COLOR_LINE, (f.center.x, f.min_y), (f.center.x, f.max_y), 2)
        pygame.draw.circle(self.screen, cfg.COLOR_LINE, (int(f.center.x), int(f.center.y)), cfg.CENTER_CIRCLE_R, 2)
        pygame.draw.circle(self.screen, cfg.COLOR_LINE, (int(f.center.x), int(f.center.y)), 3)

        lx0, ly0, lx1, ly1 = f.penalty_box_left()
        pygame.draw.rect(self.screen, cfg.COLOR_LINE, pygame.Rect(lx0, ly0, lx1 - lx0, ly1 - ly0), 2)
        rx0, ry0, rx1, ry1 = f.penalty_box_right()
        pygame.draw.rect(self.screen, cfg.COLOR_LINE, pygame.Rect(rx0, ry0, rx1 - rx0, ry1 - ry0), 2)

        pygame.draw.rect(self.screen, (200, 200, 200),
                          pygame.Rect(f.min_x - cfg.GOAL_DEPTH, f.goal_top, cfg.GOAL_DEPTH, cfg.GOAL_WIDTH), 2)
        pygame.draw.rect(self.screen, (200, 200, 200),
                          pygame.Rect(f.max_x, f.goal_top, cfg.GOAL_DEPTH, cfg.GOAL_WIDTH), 2)

    def draw_robot(self, robot) -> None:
        color = cfg.COLOR_BLUE if robot.team.side == "LEFT" else cfg.COLOR_RED
        # use actual team color assigned
        color = robot.team.color
        pos = (int(robot.pos.x), int(robot.pos.y))
        pygame.draw.circle(self.screen, color, pos, cfg.ROBOT_RADIUS)
        pygame.draw.circle(self.screen, (10, 10, 10), pos, cfg.ROBOT_RADIUS, 2)
        label = self.font_small.render(str(robot.id), True, (255, 255, 255))
        rect = label.get_rect(center=pos)
        self.screen.blit(label, rect)

    def draw_ball(self, ball) -> None:
        pos = (int(ball.pos.x), int(ball.pos.y))
        pygame.draw.circle(self.screen, cfg.COLOR_BALL, pos, cfg.BALL_RADIUS)
        pygame.draw.circle(self.screen, (60, 60, 20), pos, cfg.BALL_RADIUS, 1)
