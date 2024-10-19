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

    def set_twitch_connection(self, twitch_connection):
        self.twitch_connection = twitch_connection

    async def process_email(self, username, subject, body, ctx):
        # If not on cooldown, save the email and update the cooldown
        self.save_email(username, subject, body)

    def save_email(self, username, subject, body):
        email_data = {
            "username": username,
            "subject": subject.strip(),
            "body": body.strip(),
            "timestamp": time.time(),
            "processed": False
        }
        
        emails = self.read_master_file()
        emails.append(email_data)
        self.write_master_file(emails)
        
        print(f"Email saved for {username}")

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

    def update(self):
        self.emails_enabled = os.path.exists(self.config['files']['emails_enable'])
        current_time = time.time()
        for username, cooldown_time in list(self.email_cooldowns.items()):
            if current_time - cooldown_time >= self.email_cooldown_time:
                del self.email_cooldowns[username]