import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from twitchio import CustomReward, CustomRewardRedemption
import aiohttp

class ChannelPointsMixin:
    """Mixin class to handle channel points rewards."""
    
    async def initialize_channel_points(self):
        """Initialize channel points system."""
        self.rewards: Dict[str, CustomReward] = {}
        self.channel_id = None
        self.broadcaster = None
        self.rewards_file = self.config.get('files', {}).get('channel_points', 'channel_point_rewards.json')

        #check if rewards file exists, if not create it
        if not os.path.exists(self.rewards_file):
            with open(self.rewards_file, 'w') as f:
                json.dump({}, f)
        
        # Check for leftover rewards from previous sessions
        await self.check_leftover_rewards()
        
        if self.config.get('twitch', {}).get('channel_points', False):
            await self.get_broadcaster()
            if self.broadcaster:
                await self.create_rewards()
            else:
                self.logger.error("Failed to get broadcaster. Cannot create rewards.")

    async def check_leftover_rewards(self):
        """Check for and handle any leftover rewards from previous sessions."""
        if not os.path.exists(self.rewards_file):
            return

        try:
            with open(self.rewards_file, 'r') as f:
                stored_rewards = json.load(f)
            
            if stored_rewards:
                self.logger.warning("Found leftover channel point rewards from previous session!")
                
                # If channel points are disabled, we should still offer cleanup
                if not self.config.get('twitch', {}).get('channel_points', False):
                    self.logger.warning("Channel points are currently disabled, but leftover rewards exist.")
                
                self.logger.warning("Would you like to delete these rewards? Type 'yes' to confirm:")
                response = input().lower().strip()
                
                if response == 'yes':
                    try:
                        # Temporarily get broadcaster info for cleanup
                        await self.get_broadcaster()
                        
                        # Fetch and delete each reward
                        for cmd_id, reward_data in stored_rewards.items():
                            reward = await self.get_existing_reward(reward_data['reward_id'])
                            if reward:
                                await reward.delete(token=self.config['twitch']['oauth_token'])
                                self.logger.info(f"Deleted leftover reward: {reward_data['title']}")
                            else:
                                self.logger.warning(f"Reward {reward_data['reward_id']} no longer exists")
                        
                        self.clear_rewards_file()
                        self.logger.info("Successfully cleaned up leftover rewards.")
                    except Exception as e:
                        self.logger.error(f"Failed to clean up leftover rewards: {e}")
                    finally:
                        # Reset if we're not using channel points
                        if not self.config.get('twitch', {}).get('channel_points', False):
                            self.broadcaster = None
                            self.rewards = {}
                else:
                    self.logger.info("Skipping reward cleanup.")
        except Exception as e:
            self.logger.error(f"Error checking leftover rewards: {e}")

    async def get_broadcaster(self):
        """Get broadcaster information."""
        try:
            self.broadcaster = await self.fetch_users(names=[self.config['twitch']['channel']])
            if self.broadcaster:
                self.broadcaster = self.broadcaster[0]
                self.channel_id = self.broadcaster.id
                self.logger.info(f"Got broadcaster: {self.broadcaster.name} (ID: {self.channel_id})")
            else:
                self.logger.error(f"No user found for channel: {self.config['twitch']['channel']}")
        except Exception as e:
            self.logger.error(f"Failed to get broadcaster: {e}")

    def save_rewards(self):
        """Save current reward IDs to file."""
        try:
            # We only save the IDs and command IDs, not the full CustomReward objects
            reward_data = {
                cmd_id: {
                    'reward_id': reward.id,
                    'title': reward.title,
                    'cost': reward.cost
                }
                for cmd_id, reward in self.rewards.items()
            }
            
            with open(self.rewards_file, 'w') as f:
                json.dump(reward_data, f)
            self.logger.debug("Saved reward IDs to file")
        except Exception as e:
            self.logger.error(f"Failed to save reward IDs to file: {e}")

    def clear_rewards_file(self):
        """Clear the rewards file."""
        try:
            if os.path.exists(self.rewards_file):
                os.remove(self.rewards_file)
                self.logger.debug("Cleared rewards file")
        except Exception as e:
            self.logger.error(f"Failed to clear rewards file: {e}")

    def load_commands(self):
        """Load commands from commands file."""
        commands = []
        commands_file = self.config['files']['commands']
        
        if not os.path.exists(commands_file):
            self.logger.error(f"Commands file not found: {commands_file}")
            return commands

        with open(commands_file, 'r') as file:
            for line in file:
                parts = line.strip().split(';')
                if len(parts) == 6:
                    command = {
                        'title': parts[0],
                        'id': parts[1],
                        'description': parts[2],
                        'pointCost': int(parts[3]),
                        'isEnabledForPoints': parts[4].lower() == 'true',
                        'pointsCooldown': int(parts[5])
                    }
                    commands.append(command)
                else:
                    # TODO: fix ";fling" command returning invalid format
                    self.logger.warning(f"Invalid command format: {line.strip()}")
        return commands
    
    async def get_existing_reward(self, reward_id: str) -> Optional[CustomReward]:
        """Fetch an existing reward by ID."""
        try:
            if self.broadcaster:
                rewards = await self.broadcaster.get_custom_rewards(token=self.config['twitch']['oauth_token'])
                return next((r for r in rewards if r.id == reward_id), None)
        except Exception as e:
            self.logger.error(f"Failed to fetch existing reward {reward_id}: {e}")
        return None

    async def create_rewards(self):
        """Create channel point rewards."""
        # First create special system rewards if enabled
        await self.create_special_system_rewards()
        
        # Then create regular command rewards
        commands = self.load_commands()
        for cmd in commands:
            if cmd['isEnabledForPoints']:
                await self.create_custom_reward(cmd)

    async def create_special_system_rewards(self):
        """Create rewards for special system commands (Email, Shop, Hints)."""
        special_systems = [
            {
                'system': 'emails',
                'title': 'Send Email',
                'description': 'Send an email (Format: subject: <subject> body: <body> (optional user:Dr_Bao, etc) )',
                'cost': self.config.get('email', {}).get('points_cost', 1000)
            },
            {
                'system': 'chatShop',
                'title': 'Buy Shop Item',
                'description': 'Purchase an item from the shop (Enter item name)',
                'cost': self.config.get('shop', {}).get('points_cost', 1000)
            },
            {
                'system': 'hints',
                'title': 'Send Hint',
                'description': 'Send a hint to the streamer, optionally with a type. Format: (type) hint',
                'cost': self.config.get('hint', {}).get('points_cost', 500)
            }
        ]

        for system in special_systems:
            if self.config.get(system['system'], {}).get('channel_points', False):
                command = {
                    'id': f"{system['system']}_points",
                    'title': system['title'],
                    'description': system['description'],
                    'pointCost': system['cost'],
                    'pointsCooldown': self.config.get(system['system'], {}).get('points_cooldown', 0),
                    'isEnabledForPoints': True
                }
                
                try:
                    # Check if reward already exists
                    existing_reward = None
                    for cmd_id, reward in self.rewards.items():
                        if cmd_id == command['id']:
                            existing_reward = reward
                            break

                    if existing_reward:
                        self.logger.info(f"Special reward for {system['system']} already exists")
                        continue

                    reward = await self.broadcaster.create_custom_reward(
                        token=self.config['twitch']['oauth_token'],
                        title=command['title'],
                        cost=int(command['pointCost']),
                        prompt=command['description'],
                        global_cooldown=int(command['pointsCooldown']),
                        input_required=True,  # Special commands always require input
                        redemptions_skip_queue=False
                    )

                    self.rewards[command['id']] = reward
                    self.logger.info(f"Created special reward for {system['system']}")
                    self.save_rewards()

                except Exception as e:
                    self.logger.error(f"Failed to create special reward for {system['system']}: {e}")
                    self.logger.exception("Detailed traceback:")

    async def create_custom_reward(self, command):
        """Create a single custom reward."""
        if not self.broadcaster:
            self.logger.error("Broadcaster not set. Cannot create custom reward.")
            return

        try:
            self.logger.debug(f"Attempting to create reward with data: {command}")
            
            scopes = await self.get_scopes()
            if 'channel:manage:redemptions' not in scopes:
                self.logger.error("OAuth token is missing the 'channel:manage:redemptions' scope.")
                return

            # Check if reward already exists
            existing_reward = None
            for cmd_id, reward in self.rewards.items():
                if cmd_id == command['id']:
                    existing_reward = reward
                    break

            if existing_reward:
                self.logger.info(f"Reward {command['title']} already exists")
                return

            reward = await self.broadcaster.create_custom_reward(
                token=self.config['twitch']['oauth_token'],
                title=command['title'],
                cost=int(command['pointCost']),
                prompt=command['description'],
                global_cooldown=int(command['pointsCooldown']),
                input_required=False,  # Regular commands don't require input by default
                redemptions_skip_queue=False
            )
            
            self.rewards[command['id']] = reward
            self.logger.info(f"Created custom reward: {command['title']}")
            
            # Save rewards after each creation
            self.save_rewards()
            
        except Exception as e:
            self.logger.error(f"Failed to create custom reward for {command['title']}: {e}")
            self.logger.exception("Detailed traceback:")

    async def get_scopes(self):
        """Validate OAuth token and get its scopes."""
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
        
    async def handle_redemption(self, event):
        """Handle a channel point redemption."""
        try:
            # Find the command ID associated with this reward
            command_id = None
            for cmd_id, reward in self.rewards.items():
                if reward.id == event.reward.id:
                    command_id = cmd_id
                    break

            if command_id:
                self.logger.info(f"Channel points redeemed by {event.user.name} for command {command_id}")
                if event.input:
                    self.logger.info(f"User input: {event.input}")
                await self.fulfill_redemption(event)
            else:
                self.logger.warning(f"Received redemption for unknown reward ID: {event.reward.id}")
                await self.refund_redemption(event)

        except Exception as e:
            self.logger.error(f"Error processing channel point redemption: {e}")
            try:
                await self.refund_redemption(event)
            except Exception as refund_error:
                self.logger.error(f"Failed to refund redemption after error: {refund_error}")

    async def fulfill_redemption(self, event):
        """Mark a redemption as fulfilled."""
        try:
            # Create a CustomRewardRedemption object with all required fields
            redemption = CustomRewardRedemption(
                {
                    'id': event.id,
                    'user_id': str(event.user.id),
                    'channel_id': str(event.channel_id),
                    'broadcaster_id': str(event.channel_id),
                    'reward_id': event.reward.id,
                    'user_login': event.user.name,
                    'user_name': event.user.name,
                    'user_input': event.input or '',  # Add user input, empty string if None
                    'status': 'unfulfilled',
                    'redeemed_at': event.timestamp.isoformat()
                },
                self._http,
                event.reward
            )
            
            await redemption.fulfill(token=self.config['twitch']['oauth_token'])
            self.logger.debug(f"Fulfilled redemption {event.id} for user {event.user.name}")
        except Exception as e:
            self.logger.error(f"Failed to fulfill redemption {event.id}: {e}")

    async def refund_redemption(self, event):
        """Refund/cancel a redemption."""
        try:
            # Create a CustomRewardRedemption object with all required fields
            redemption = CustomRewardRedemption(
                {
                    'id': event.id,
                    'user_id': str(event.user.id),
                    'channel_id': str(event.channel_id),
                    'broadcaster_id': str(event.channel_id),
                    'reward_id': event.reward.id,
                    'user_login': event.user.name,
                    'user_name': event.user.name,
                    'user_input': event.input or '',  # Add user input, empty string if None
                    'status': 'unfulfilled',
                    'redeemed_at': event.timestamp.isoformat()
                },
                self._http,
                event.reward
            )
            
            await redemption.refund(token=self.config['twitch']['oauth_token'])
            self.logger.debug(f"Refunded redemption {event.id} for user {event.user.name}")
        except Exception as e:
            self.logger.error(f"Failed to refund redemption {event.id}: {e}")

    async def remove_all_rewards(self):
        """Remove all channel point rewards."""
        if not self.broadcaster:
            self.logger.error("Broadcaster not set. Cannot remove custom rewards.")
            return

        for command_id, reward in list(self.rewards.items()):
            try:
                await reward.delete(token=self.config['twitch']['oauth_token'])
                self.logger.info(f"Removed custom reward: {reward.title}")
                del self.rewards[command_id]
            except Exception as e:
                self.logger.error(f"Failed to remove custom reward {reward.title}: {e}")
        
        # Clear the rewards file after successful removal
        self.clear_rewards_file()


    async def close(self):
        """Clean up PubSub connection and rewards."""
        try:
            if self.pubsub:
                await self.pubsub.disconnect()
                self.logger.info("Disconnected from PubSub")
            await self.remove_all_rewards()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
