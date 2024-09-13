import time
import json
import os
from src.twitch_connection import TwitchConnection

class ShopSystem:
    def __init__(self, config, twitch_connection):
        self.config = config
        self.user_shop_cooldowns = {}
        self.twitch_connection = twitch_connection
        self.master_file = config['files']['shops_master']
        self.shop_open_file = config['files']['shopOpen']
        self.shopOpen = False

    def process_shop(self, username, item):
        if not self.config['chatShop'].get('enabled', False):
            return
       
        current_time = time.time()

        if not item:
            TwitchConnection.send_message(self.twitch_connection, f"@{username} You can order items from the shop using !shop <item>")
            return

        if not self.is_shop_open():
            TwitchConnection.send_message(self.twitch_connection, f"@{username} The shop is currently closed. Please wait for it to open.")
            return

        # Check user cooldown
        if username in self.user_shop_cooldowns:
            time_since_last_use = current_time - self.user_shop_cooldowns[username]
            if time_since_last_use < self.config['chatShop'].get('usercooldown', 300):  # Default 5 minutes cooldown
                remaining_cooldown = int(self.config['chatShop']['usercooldown'] - time_since_last_use)
                TwitchConnection.send_message(self.twitch_connection, f"@{username} You're on cooldown. You can use the shop again in {remaining_cooldown} seconds.")
                return

        # Process the shop request
        shop_data = {
            "username": username,
            "item": item,
            "timestamp": current_time,
            "processed": False
        }

        print(f"Shop order processed for {username}: {item}")
        orders = self.read_master_file()
        orders.append(shop_data)
        self.write_master_file(orders)

        # Update user's cooldown
        self.user_shop_cooldowns[username] = current_time

    def read_master_file(self):
        if os.path.exists(self.master_file):
            with open(self.master_file, 'r') as f:
                return json.load(f)
        return []

    def write_master_file(self, data):
        with open(self.master_file, 'w') as f:
            json.dump(data, f, indent=2)

    def is_shop_open(self):
        if os.path.exists(self.shop_open_file):
            with open(self.shop_open_file, 'r') as f:
                return f.read().strip().lower() == 'true'
        return False

    def update(self):
        # if the shop just opened, broadcast a message
        if self.is_shop_open() and not self.shopOpen:
            announcement = self.config['chatShop']['announcement_message'].format(duration=self.config['chatShop']['open_duration'])
            TwitchConnection.send_message(self.twitch_connection, announcement)
            self.shopOpen = True
        elif not self.is_shop_open() and self.shopOpen:
            self.shopOpen = False
        pass