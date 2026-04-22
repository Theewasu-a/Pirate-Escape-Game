"""
Pirate Escape - Main Entry Point
Run: python main.py
Requires: pip install pygame numpy
"""
import pygame
from game.constants import SCREEN_W, SCREEN_H
from game.game_manager import GameManager


def _compute_scale(win_w, win_h):
    """Preserve aspect ratio when fitting the game surface into the window."""
    scale = min(win_w / SCREEN_W, win_h / SCREEN_H)
    scale = max(scale, 0.1)
    sw, sh = int(SCREEN_W * scale), int(SCREEN_H * scale)
    ox, oy = (win_w - sw) // 2, (win_h - sh) // 2
    return scale, sw, sh, ox, oy


def _to_logical(pos, scale, ox, oy):
    if scale <= 0:
        return (0, 0)
    return (int((pos[0] - ox) / scale),
            int((pos[1] - oy) / scale))


def main():
    pygame.init()
    pygame.display.set_caption("Pirate Escape")

    # Resizable window.  We render the game into a fixed internal surface
    # and scale it to the window each frame — keeps gameplay coordinates stable.
    window = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    manager = GameManager(game_surface)

    running = True
    while running:
        dt = clock.tick(60)

        win_w, win_h = window.get_size()
        scale, sw, sh, ox, oy = _compute_scale(win_w, win_h)

        # Update logical mouse position for UI hover tracking
        manager.mouse_pos = _to_logical(pygame.mouse.get_pos(), scale, ox, oy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type == pygame.VIDEORESIZE:
                window = pygame.display.set_mode((event.w, event.h),
                                                 pygame.RESIZABLE)
                continue
            # Remap mouse coordinates to logical space
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                              pygame.MOUSEMOTION):
                lp = _to_logical(event.pos, scale, ox, oy)
                event = pygame.event.Event(event.type, {**event.dict, "pos": lp})
            manager.handle_event(event)

        try:
            manager.update(dt)
        except Exception as e:
            import traceback
            print(f"[ERROR] {e}")
            traceback.print_exc()
            try:
                manager._end_game(f"Crash: {e}")
            except Exception:
                pass
        manager.draw()

        # Blit scaled game surface to window (letterbox black bars if needed)
        window.fill((0, 0, 0))
        if sw > 0 and sh > 0:
            scaled = pygame.transform.smoothscale(game_surface, (sw, sh))
            window.blit(scaled, (ox, oy))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
