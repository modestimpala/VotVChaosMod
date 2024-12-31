import logging
import time
import json
import asyncio

class ShopSystem:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.user_shop_cooldowns = {}
        self.shop_open = False
        self.websocket_handler = None
        self.twitch_connection = None
        self.direct_connection = None

    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler

    def set_twitch_connection(self, twitch_connection):
        self.twitch_connection = twitch_connection

    def set_direct_connection(self, direct_connection):
        self.direct_connection = direct_connection

    async def process_shop(self, item, username="direct", ctx=None, amount=1):
        """Process a shop request from either Twitch chat or direct connection."""
        if not self.config['chatShop'].get('enabled', False):
            return

        if not self.shop_open and username != "direct":
            if ctx and self.twitch_connection:
                await self.twitch_connection.reply(ctx, "The shop is currently closed.")
            return

        current_time = time.time()

        # Handle Twitch-specific checks
        if ctx is not None:
            # Check user cooldown
            if username in self.user_shop_cooldowns:
                time_since_last_use = current_time - self.user_shop_cooldowns[username]
                if time_since_last_use < self.config['chatShop'].get('usercooldown', 300):
                    remaining_cooldown = int(self.config['chatShop']['usercooldown'] - time_since_last_use)
                    await self.twitch_connection.reply(ctx, f"You're on cooldown. You can use the shop again in {remaining_cooldown} seconds.")
                    return

        # Send shop request to game
        if self.websocket_handler and self.websocket_handler.game_connection:
            try:
                shop_data = {
                    "type": "shop_request",
                    "username": username,
                    "item": item,
                    "amount": amount,
                    "timestamp": current_time
                }
                await self.websocket_handler.game_connection.send(json.dumps(shop_data))
                self.logger.debug(f"Shop request sent for {username}: {item}")

                # Update user's cooldown for Twitch users
                if ctx is not None:
                    self.user_shop_cooldowns[username] = current_time

            except Exception as e:
                self.logger.error(f"Failed to send shop request: {e}")

    def set_shop_open(self, is_open):
        """Set shop open status and handle announcements."""
        if self.shop_open == is_open:
            return

        self.shop_open = is_open
        
        # Announce shop status changes in Twitch chat if configured
        if self.twitch_connection and not self.config.get('chatShop', {}).get('channel_points', False):
            if is_open:
                announcement = self.config['chatShop']['announcement_message'].format(
                    duration=self.config['chatShop']['open_duration']
                )
                asyncio.create_task(self.twitch_connection.queue_message(announcement))
            # Could add a shop closing announcement here if desired

    def update_config(self, config):
        """Update configuration."""
        self.config = config

    def is_shop_open(self):
        """Check if the shop is open."""
        return self.shop_open