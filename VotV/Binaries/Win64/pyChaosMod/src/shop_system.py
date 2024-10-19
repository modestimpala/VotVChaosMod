import time
import json
import os
import asyncio

class ShopSystem:
    def __init__(self, config):
        self.config = config
        self.user_shop_cooldowns = {}
        self.master_file = config['files']['shops_master']
        self.shop_open_file = config['files']['shopOpen']
        self.shopOpen = True
        self.twitch_connection = None

    def set_twitch_connection(self, twitch_connection):
        self.twitch_connection = twitch_connection

    async def process_shop(self, username, item, ctx):
        if not self.config['chatShop'].get('enabled', False):
            return
       
        current_time = time.time()

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

    def read_master_file(self):
        if os.path.exists(self.master_file):
            with open(self.master_file, 'r') as f:
                return json.load(f)
        return []

    def write_master_file(self, data):
        with open(self.master_file, 'w') as f:
            json.dump(data, f, indent=2)

    def is_shop_open(self):
        return True

    def update(self):
        pass