import time
import json
import random
import os
from src.twitch_connection import TwitchConnection

class ShopSystem:
    def __init__(self, config, twitch_connection):
        self.config = config
        self.shop_open = False
        self.shop_close_time = 0
        self.next_shop_open_time = time.time() + self.get_next_shop_interval()
        self.user_shop_cooldowns = {}
        self.twitch_connection = twitch_connection
        self.master_file = config['files']['shops_master']

    def get_next_shop_interval(self):
        return random.randint(self.config['chatShop']['minOpenInterval'], 
                              self.config['chatShop']['maxOpenInterval'])

    def process_shop(self, username, item):
        if self.config['chatShop']['enabled'] == False:
            return
        
        current_time = time.time()

        if not item:
            TwitchConnection.send_message(self.twitch_connection, f"@{username} You can order items from the shop using !shop <item>")
            return

        if not self.shop_open:
            TwitchConnection.send_message(self.twitch_connection, f"@{username} The shop is currently closed. Please wait for it to open.")
            return

        # Check user cooldown
        if username in self.user_shop_cooldowns:
            time_since_last_use = current_time - self.user_shop_cooldowns[username]
            if time_since_last_use < self.config['chatShop']['userCooldown']:
                remaining_cooldown = int(self.config['chatShop']['userCooldown'] - time_since_last_use)
                TwitchConnection.send_message(self.twitch_connection, f"@{username} You're on cooldown. You can use the shop again in {remaining_cooldown} seconds.")
                return

        # Process the shop request
        shop_data = {
            "username": username,
            "item": item if item else "general",
            "timestamp": current_time,
            "processed": False
        }

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
        
    def open_shop(self):
        self.shop_open = True
        self.shop_close_time = time.time() + self.config['chatShop']['openDuration']
        announcement = self.config['chatShop']['announcementMessage'].format(duration=self.config['chatShop']['openDuration'])
        TwitchConnection.send_message(self.twitch_connection, announcement)
        print("Shop opened")

    def close_shop(self):
        self.shop_open = False
        self.next_shop_open_time = time.time() + self.get_next_shop_interval()
        TwitchConnection.send_message(self.twitch_connection, "The shop is now closed!")
        print("Shop closed")
        # Clear user cooldowns when the shop closes
        self.user_shop_cooldowns.clear()

    def update(self):
        if self.config['chatShop']['enabled'] == False:
            return

        current_time = time.time()

        if self.shop_open and current_time >= self.shop_close_time:
            self.close_shop()

        if not self.shop_open and current_time >= self.next_shop_open_time:
            self.open_shop()