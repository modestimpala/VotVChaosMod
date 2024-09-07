import pyglet
from src.game_overlay import GameOverlay

if __name__ == '__main__':
    overlay = GameOverlay()
    pyglet.clock.schedule_interval(overlay.update, 1/60.0)
    pyglet.app.run()