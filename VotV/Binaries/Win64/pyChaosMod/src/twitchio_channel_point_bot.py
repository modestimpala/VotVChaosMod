import asyncio
import twitchio
from twitchio.ext import commands
import logging
import os
import aiohttp

class ChannelPointBot(commands.Bot):
    def __init__(self, config, message_handler):
        self.config = config
        self.message_handler = message_handler
        self.channel_name = config['twitch']['channel']
        self.commands_file = config['files']['commands']
        self.rewards = {}
        self.channel_id = None
        self.broadcaster = None
        
        super().__init__(
            token=config['twitch']['oauth_token'],
            client_id=config['twitch']['client_id'],
            nick=config['twitch']['bot_username'],
            prefix='!',
            initial_channels=[self.channel_name]
        )
        
        self.logger = logging.getLogger(__name__)

    async def event_ready(self):
        self.logger.info(f'TwitchIO Bot logged in as | {self.nick}')
        await self.get_broadcaster()
        if self.broadcaster:
            await self.create_rewards()
        else:
            self.logger.error("Failed to get broadcaster. Cannot create rewards.")

    async def get_broadcaster(self):
        try:
            self.broadcaster = await self.fetch_users(names=[self.channel_name])
            if self.broadcaster:
                self.broadcaster = self.broadcaster[0]
                self.channel_id = self.broadcaster.id
                self.logger.info(f"Got broadcaster: {self.broadcaster.name} (ID: {self.channel_id})")
            else:
                self.logger.error(f"No user found for channel: {self.channel_name}")
        except Exception as e:
            self.logger.error(f"Failed to get broadcaster: {e}")

    async def create_rewards(self):
        commands = self.load_commands()
        for cmd in commands:
            if cmd['isEnabledForPoints']:
                await self.create_custom_reward(cmd)

    def load_commands(self):
        commands = []
        if not os.path.exists(self.commands_file):
            self.logger.error(f"Commands file not found: {self.commands_file}")
            return commands

        with open(self.commands_file, 'r') as file:
            for line in file:
                parts = line.strip().split(';')
                if len(parts) == 8:
                    command = {
                        'title': parts[0],
                        'id': parts[1],
                        'description': parts[2],
                        'pointCost': int(parts[3]),
                        'isEnabledForPoints': parts[4].lower() == 'true',
                        'pointsCooldown': int(parts[5]),
                        'enabled': parts[6].lower() == 'true',
                        'chance': float(parts[7])
                    }
                    commands.append(command)
                else:
                    self.logger.warning(f"Invalid command format: {line.strip()}")
        return commands

    async def create_custom_reward(self, command):
        if not self.broadcaster:
            self.logger.error("Broadcaster not set. Cannot create custom reward.")
            return

        try:
            self.logger.debug(f"Attempting to create reward with data: {command}")
            
            # Check if the bot has the necessary scope
            scopes = await self.get_scopes()
            if 'channel:manage:redemptions' not in scopes:
                self.logger.error("OAuth token is missing the 'channel:manage:redemptions' scope.")
                return

            reward = await self.broadcaster.create_custom_reward(
                token=self.config['twitch']['oauth_token'],
                title=command['title'],
                cost=int(command['pointCost']),
                prompt=command['description'],
                global_cooldown=int(command['pointsCooldown']),
                redemptions_skip_queue=False
            )
            self.rewards[command['id']] = reward.id
            self.logger.info(f"Created custom reward: {command['title']}")
        except Exception as e:
            self.logger.error(f"Failed to create custom reward for {command['title']}: {e}")
            self.logger.exception("Detailed traceback:")

# Add this method to check the OAuth token scopes
    async def get_scopes(self):
        try:
            url = 'https://id.twitch.tv/oauth2/validate'
            headers = {
                'Authorization': f'OAuth {self.config["twitch"]["oauth_token"]}'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('scopes', [])
                    else:
                        self.logger.error(f"Failed to validate OAuth token. Status: {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error validating OAuth token: {e}")
            return []

    async def event_raw_usernotice(self, channel, tags):
        if tags.get('msg-id') == 'reward-redeemed':
            await self.handle_redemption(tags)

    async def handle_redemption(self, tags):
        reward_id = tags.get('custom-reward-id')
        command_id = next((cmd_id for cmd_id, rwd_id in self.rewards.items() if rwd_id == reward_id), None)
        if command_id:
            # Here we pass the redemption to your existing message handler
            self.message_handler.handle_channel_point_redemption(command_id, tags)

    async def remove_all_rewards(self):
        if not self.broadcaster:
            self.logger.error("Broadcaster not set. Cannot remove custom rewards.")
            return

        for command_id, reward_id in self.rewards.items():
            try:
                await self.broadcaster.delete_custom_reward(reward_id)
                self.logger.info(f"Removed custom reward: {command_id}")
            except Exception as e:
                self.logger.error(f"Failed to remove custom reward {command_id}: {e}")
        self.rewards.clear()

async def run_bot(bot):
    await bot.start()

async def stop_bot(bot):
    await bot.remove_all_rewards()
    await bot.close()

def create_channel_point_bot(config, message_handler):
    return ChannelPointBot(config, message_handler)