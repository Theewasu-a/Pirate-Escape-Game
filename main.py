"""
Pirate Escape - Main Entry Point
Run: python main.py
Requires: pip install pygame
"""
import pygame
from game_manager import GameManager


def main():
    pygame.init()
    pygame.display.set_caption("Pirate Escape")
    screen = pygame.display.set_mode((480, 700))
    clock  = pygame.time.Clock()
    manager = GameManager(screen)

    running = True
    while running:
        dt = clock.tick(60)  # ms since last frame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            manager.handle_event(event)
        manager.update(dt)
        manager.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
