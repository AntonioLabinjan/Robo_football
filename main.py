"""Entry point for Robotics Football Simulator."""
import pygame
import config as cfg
from game import Game


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H))
    pygame.display.set_caption("Robotics Football Simulator")
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        real_dt = clock.tick(cfg.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update(real_dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
