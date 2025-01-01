import logging
import time
import json
import asyncio

class EmailSystem:
    def __init__(self, config):
        self.config = config
        self.emails_enabled = False
        self.email_cooldowns = {}
        self.email_cooldown_time = config['emails']['user_cooldown']
        self.twitch_connection = None
        self.direct_connection = None
        self.websocket_handler = None
        self.logger = logging.getLogger(__name__)
        self.valid_users = [
            "Dr_Bao",
            "Prof_Lea",
            "Auto",
            "Dr_Max",
            "Dr_Ken",
            "Dr_Ena",
            "Dr_Ula",
            "Dr_Ler",
            "user",
            "Dr_Noa"
        ]

    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler

    def set_twitch_connection(self, twitch_connection):
        self.twitch_connection = twitch_connection

    def set_direct_connection(self, direct_connection):
        self.direct_connection = direct_connection

    async def process_email(self, twitch_user, subject, body, ctx=None, user="user"):
        current_time = time.time()

        # Check if the user is valid
        if user not in self.valid_users and ctx is not None:
            await self.twitch_connection.reply(ctx, "Please use a valid user. e.g Dr_Bao, Dr_Ken...")
            return

        if user not in self.valid_users and self.direct_connection is not None:
            user = "user"

        if ctx is not None:
            # Check if the user is on cooldown
            if twitch_user in self.email_cooldowns:
                time_since_last_email = current_time - self.email_cooldowns[twitch_user]
                if time_since_last_email < self.email_cooldown_time:
                    remaining_cooldown = int(self.email_cooldown_time - time_since_last_email)
                    cooldown_message = f"You're on cooldown. You can send another email in {remaining_cooldown} seconds."
                    await self.twitch_connection.reply(ctx, cooldown_message)
                    return

        # If not on cooldown, send the email through WebSocket
        await self.send_email(twitch_user, subject, body, user)
        
        if ctx is not None:
            self.email_cooldowns[twitch_user] = current_time

    async def send_email(self, twitch_user, subject, body, user="user"):
        """Send email through WebSocket connection."""
        if self.websocket_handler and self.websocket_handler.game_connection:
            email_data = {
                "type": "email",
                "data": {
                    "user": user,
                    "twitch_user": twitch_user,
                    "subject": subject.strip(),
                    "body": body.strip(),
                    "timestamp": time.time()
                }
            }
            
            try:
                await self.websocket_handler.game_connection.send(json.dumps(email_data))
                self.logger.debug(f"Email sent for {twitch_user}")
            except Exception as e:
                self.logger.error(f"Failed to send email through WebSocket: {e}")
        else:
            self.logger.error("WebSocket connection not available")

    def enable_emails(self):
        self.emails_enabled = True
        self.logger.info("Emails enabled")

    def disable_emails(self):
        self.emails_enabled = False
        self.logger.info("Emails disabled")

    def are_emails_enabled(self):
        return self.emails_enabled

    def update_config(self, config):
        self.config = config
        self.email_cooldown_time = config['emails']['user_cooldown']
        self.emails_enabled = config['emails']['enabled']

    def update(self):
        if self.twitch_connection is not None:
            self.emails_enabled = self.config.get('emails', {}).get('enabled', False)
        
        # Clean up expired cooldowns
        current_time = time.time()
        for twitch_user, cooldown_time in list(self.email_cooldowns.items()):
            if current_time - cooldown_time >= self.email_cooldown_time:
                del self.email_cooldowns[twitch_user]