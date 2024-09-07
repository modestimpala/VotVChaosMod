import os
import threading
import pyglet
import json
import time
from pyglet import gl
from src.twitch_connection import TwitchConnection
from src.message_handler import MessageHandler
from src.voting_system import VotingSystem
from src.email_system import EmailSystem
from src.shop_system import ShopSystem
from src.sound_manager import SoundManager
from src.utils import load_config
from src.utils import is_chaos_enabled

class GameOverlay(pyglet.window.Window):
    def __init__(self):
        self.config_json = load_config()
        display = pyglet.canvas.get_display()
        screen = display.get_default_screen()
        super().__init__(self.config_json['overlay']['width'], self.config_json['overlay']['height'], 
                         style=pyglet.window.Window.WINDOW_STYLE_OVERLAY,
                         vsync=False)

        self.set_location(int((screen.width - self.width) / 2), 10)
        self.set_exclusive_mouse(False)
        self.set_exclusive_keyboard(False)
        self.is_chaos_enabled_file = self.config_json['files']['enable']
        
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self.twitch_connection = TwitchConnection(self.config_json)
        self.email_system = EmailSystem(self.config_json, self.twitch_connection)
        self.shop_system = ShopSystem(self.config_json, self.twitch_connection)
        self.sound_manager = SoundManager()
        self.voting_system = VotingSystem(self.config_json, self.sound_manager)
        
        self.message_handler = MessageHandler(self.voting_system, self.email_system, self.shop_system, self.sound_manager)
        
        
        self.background = self.create_background()
        
        pyglet.clock.schedule_interval(self.update, self.config_json['update_interval'])
        threading.Thread(target=self.check_ue4ss_triggers, daemon=True).start()

    def create_background(self):
        batch = pyglet.graphics.Batch()
        background_color = (0, 0, 0, 128)
        pyglet.shapes.Rectangle(0, 0, self.width, self.height, 
                                color=background_color, 
                                batch=batch)
        return batch

    def update(self, dt):
        messages = self.twitch_connection.get_messages()
        for message in messages:
            self.message_handler.handle_message(message)
        
        self.voting_system.update()
        self.shop_system.update()
        self.email_system.update()

    def on_draw(self):
        self.clear()
        self.background.draw()
        self.draw_overlay()

    def draw_overlay(self):
        
        if not is_chaos_enabled(self.config_json):
            self.draw_text("Chaos Mod (Disabled)", 18, self.width // 2, self.height // 2)
        elif self.voting_system.voting_active:
            remaining = int(self.voting_system.vote_end_time - time.time())
            self.draw_text(f"Voting Time: {remaining}s", 16, self.width // 2, self.height - 20)
            for i, command in enumerate(self.voting_system.current_options):
                votes = self.voting_system.votes.get(i + 1, 0)
                # Display combined commands in a single line
                command_name = command['name'].replace(' + ', ' & ')
                self.draw_text(f"{i + 1}. {command_name}: {votes}", 14, self.width // 2, self.height - 50 - i * 25)
            self.draw_text(f"Total Votes: {len(self.voting_system.voters)}", 12, self.width // 2, self.height - 50 - (len(self.voting_system.current_options) * 25))
        elif self.voting_system.winner and time.time() < self.voting_system.winner_display_end_time:
            # Display combined winner commands in a single line
            winner_name = self.voting_system.winner.replace(' + ', ' & ')
            self.draw_text(f"Chaos Effect: {winner_name}", 18, self.width // 2, self.height - 30)
            if self.voting_system.winner_trigger_text:
                self.draw_text(self.voting_system.winner_trigger_text, 16, self.width // 2, self.height - 60)
        else:
            self.draw_text(f"Chaos Mod (Cooldown)", 18, self.width // 2, self.height // 2)
        
        # Draw email status
        if self.config_json['emails']['enabled']:
            if self.email_system.emails_enabled:
                self.draw_text("Emails Enabled", 16, self.width // 2, 20)
            else:
                self.draw_text("Emails Disabled", 16, self.width // 2, 20)
        if self.config_json['chatShop']['enabled']:
            if self.shop_system.shop_open:
                remaining_time = int(self.shop_system.shop_close_time - time.time())
                self.draw_text(f"Shop Open: {remaining_time}s", 16, self.width // 2, 40)
            else:
                self.draw_text(f"Shop Closed", 16, self.width // 2, 40)
        pass

    def draw_text(self, text, font_size, x, y):
        label = pyglet.text.Label(text,
                          font_name='Arial', font_size=font_size,
                          x=x, y=y,
                          anchor_x='center', anchor_y='center')
        label.color = (255, 255, 255, 255)
        label.draw()

    def check_ue4ss_triggers(self):
        vote_file = self.config_json['files']['vote_trigger']
        
        while True:
            
            if os.path.exists(vote_file):
                os.remove(vote_file)
                self.voting_system.trigger_voting()
            
            time.sleep(0.1)

            self.email_system.emails_enabled = os.path.exists(self.config_json['files']['emails_enable'])