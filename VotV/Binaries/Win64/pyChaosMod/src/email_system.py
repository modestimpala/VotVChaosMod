import logging
import time
import json
import os
import asyncio

class EmailSystem:
    def __init__(self, config):
        self.config = config
        self.emails_enabled = False
        self.email_cooldowns = {}
        self.email_cooldown_time = config['emails']['user_cooldown']
        self.master_file = config['files']['emails_master']
        self.twitch_connection = None
        self.direct_connection = None

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
            user="user"

        if ctx is not None:
            # Check if the user is on cooldown
            if twitch_user in self.email_cooldowns:
                time_since_last_email = current_time - self.email_cooldowns[twitch_user]
                if time_since_last_email < self.email_cooldown_time:
                    remaining_cooldown = int(self.email_cooldown_time - time_since_last_email)
                    cooldown_message = f"You're on cooldown. You can send another email in {remaining_cooldown} seconds."
                    await self.twitch_connection.reply(ctx, cooldown_message)
                return

        # If not on cooldown, save the email and update the cooldown
        self.save_email(twitch_user, subject, body, user)
        if ctx is not None:
            self.email_cooldowns[twitch_user] = current_time

    def save_email(self, twitch_user, subject, body, user="user"):
        email_data = {
            "user": user,
            "twitch_user": twitch_user,
            "subject": subject.strip(),
            "body": body.strip(),
            "timestamp": time.time(),
            "processed": False
        }
        
        emails = self.read_master_file()
        emails.append(email_data)
        self.write_master_file(emails)
        
        self.logger.debug(f"Email saved for {twitch_user}")

    def read_master_file(self):
        if os.path.exists(self.master_file):
            with open(self.master_file, 'r') as f:
                return json.load(f)
        return []

    def write_master_file(self, data):
        with open(self.master_file, 'w') as f:
            json.dump(data, f, indent=2)

    def enable_emails(self):
        self.emails_enabled = True
        print("Emails enabled")
    
    def disable_emails(self):
        self.emails_enabled = False
        print("Emails disabled")

    def are_emails_enabled(self):
        return self.emails_enabled
    
    def update_config(self, config):
        self.config = config
        self.email_cooldown_time = config['emails']['user_cooldown']
        self.emails_enabled = config['emails']['enabled']

    def update(self):
        if self.twitch_connection is not None:
            self.emails_enabled = self.config.get('emails', {}).get('enabled', False)
        current_time = time.time()
        for twitch_user, cooldown_time in list(self.email_cooldowns.items()):
            if current_time - cooldown_time >= self.email_cooldown_time:
                del self.email_cooldowns[twitch_user]