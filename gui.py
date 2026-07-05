"""Side panel, top bar and button widgets."""
from __future__ import annotations
from typing import Callable, List, Tuple
import pygame
import config as cfg


class Button:
    def __init__(self, rect: pygame.Rect, label: str, callback: Callable[[], None]):
        self.rect = rect
        self.label = label
        self.callback = callback
        self.hover = False

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, screen, font) -> None:
        color = (70, 130, 200) if self.hover else (50, 90, 150)
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (10, 10, 10), self.rect, 1, border_radius=6)
        text = font.render(self.label, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=self.rect.center))


class GUI:
    def __init__(self, screen: pygame.Surface, game):
        self.screen = screen
        self.game = game
        self.font = pygame.font.SysFont("consolas", 16)
        self.font_bold = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 13)
        self.buttons: List[Button] = []
        self._build_buttons()

    def _build_buttons(self) -> None:
        panel_x = cfg.MARGIN * 2 + cfg.FIELD_W
        y = 60
        w, h, gap = 110, 32, 8
        labels = [
            ("Start", self.game.start),
            ("Pause", self.game.pause),
            ("Resume", self.game.resume),
            ("Restart", self.game.restart),
            ("Reset Match", self.game.reset_match),
        ]
        for i, (label, cb) in enumerate(labels):
            rect = pygame.Rect(panel_x + 10, y + i * (h + gap), w, h)
            self.buttons.append(Button(rect, label, cb))

        speed_y = y + len(labels) * (h + gap) + 20
        for i, spd in enumerate(cfg.SIM_SPEEDS):
            rect = pygame.Rect(panel_x + 10 + (i % 3) * 40, speed_y + (i // 3) * 34, 36, 28)
            self.buttons.append(Button(rect, f"{spd}x", lambda s=spd: self.game.set_speed(s)))

    def handle_event(self, event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self) -> None:
        self._draw_top_bar()
        self._draw_side_panel()
        for b in self.buttons:
            b.draw(self.screen, self.font)

    def _draw_top_bar(self) -> None:
        rect = pygame.Rect(0, 0, cfg.SCREEN_W, 50)
        pygame.draw.rect(self.screen, cfg.COLOR_PANEL, rect)
        g = self.game
        minutes = int(g.time_remaining // 60)
        seconds = int(g.time_remaining % 60)
        timer_text = f"{minutes:02d}:{seconds:02d}"
        score_text = f"{g.team_blue.name} {g.team_blue.score} - {g.team_red.score} {g.team_red.name}"
        state_text = g.state

        t1 = self.font_bold.render(timer_text, True, cfg.COLOR_TEXT)
        t2 = self.font_bold.render(score_text, True, cfg.COLOR_TEXT)
        t3 = self.font.render(state_text, True, (180, 180, 180))
        self.screen.blit(t1, (20, 14))
        self.screen.blit(t2, (cfg.SCREEN_W // 2 - t2.get_width() // 2, 14))
        self.screen.blit(t3, (cfg.SCREEN_W - t3.get_width() - 20, 17))

    def _draw_side_panel(self) -> None:
        panel_x = cfg.MARGIN * 2 + cfg.FIELD_W
        rect = pygame.Rect(panel_x, 50, cfg.SCREEN_W - panel_x, cfg.SCREEN_H - 50)
        pygame.draw.rect(self.screen, cfg.COLOR_PANEL, rect)

        y = 60 + 5 * (32 + 8) + 20 + 70
        self.screen.blit(self.font.render("Tactics:", True, cfg.COLOR_TEXT), (panel_x + 10, y))
        y += 22
        for team, color in ((self.game.team_blue, cfg.COLOR_BLUE), (self.game.team_red, cfg.COLOR_RED)):
            t = team.tactics
            lines = [
                f"{team.name} ({team.side})",
                f" Aggr:{t.aggression:.2f} Form:{t.formation}",
                f" Bias:{t.attack_bias} Pass:{t.passing_pref}",
            ]
            for line in lines:
                surf = self.font_small.render(line, True, color)
                self.screen.blit(surf, (panel_x + 10, y))
                y += 16
            y += 6

        y += 6
        self.screen.blit(self.font.render("Live Stats:", True, cfg.COLOR_TEXT), (panel_x + 10, y))
        y += 22
        poss = self.game.stats.possession_pct()
        for team in (self.game.team_blue, self.game.team_red):
            s = self.game.stats.stats[team.name]
            lines = [
                f"{team.name}: Poss {poss[team.name]:.0f}%",
                f" Shots {s.shots} (OT {s.shots_on_target})",
                f" Pass ok/fail {s.passes_completed}/{s.passes_failed}",
                f" Steals {s.steals} Interc {s.interceptions}",
                f" AvgSpd {s.avg_speed():.1f} Dist {s.distance_travelled:.0f}",
            ]
            for line in lines:
                surf = self.font_small.render(line, True, cfg.COLOR_TEXT)
                self.screen.blit(surf, (panel_x + 10, y))
                y += 15
            y += 8
