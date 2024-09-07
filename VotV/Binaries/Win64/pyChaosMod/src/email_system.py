import time
import json
import os
from src.twitch_connection import TwitchConnection

class EmailSystem:
    def __init__(self, config, twitch_connection):
        self.config = config
        self.emails_enabled = False
        self.email_cooldowns = {}
        self.email_cooldown_time = config['emails']['user_cooldown']
        self.twitch_connection = twitch_connection

    def process_email(self, username, subject, body):
        current_time = time.time()

        if body == "No body":
            TwitchConnection.send_message(self.twitch_connection, f"@{username} To send emails, type !email subject:<subject> body:<body>")
            return

        # Check if the user is on cooldown
        if username in self.email_cooldowns:
            time_since_last_email = current_time - self.email_cooldowns[username]
            if time_since_last_email < self.email_cooldown_time:
                remaining_cooldown = int(self.email_cooldown_time - time_since_last_email)
                cooldown_message = f"@{username} You're on cooldown. You can send another email in {remaining_cooldown} seconds."
                TwitchConnection.send_message(self.twitch_connection, cooldown_message)
                return

        # If not on cooldown, save the email and update the cooldown
        self.save_email(username, subject, body)
        self.email_cooldowns[username] = current_time

    def save_email(self, username, subject, body):
        email_data = {
            "username": username,
            "subject": subject.strip(),
            "body": body.strip(),
            "timestamp": time.time()
        }
        
        filename = f"./emails/{username}_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(email_data, f, indent=2)
        
        print(f"Email saved: {filename}")

    def enable_emails(self):
        self.emails_enabled = True
        print("Emails enabled")
    
    def disable_emails(self):
        self.emails_enabled = False
        print("Emails disabled")

    def update(self):
        self.emails_enabled = os.path.exists(self.config['files']['emails_enable'])
        current_time = time.time()
        for username, cooldown_time in list(self.email_cooldowns.items()):
            if current_time - cooldown_time >= self.email_cooldown_time:
                del self.email_cooldowns[username]
