import os
import json
import logging
from datetime import datetime
import traceback
from typing import Dict, Optional
from twitchio import CustomReward, CustomRewardRedemption
import aiohttp

from src.dataclass.email_message import EmailCommandProcessor

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
        
        await self.get_broadcaster()
        if self.broadcaster:
            await self.create_rewards()
        else:
            self.logger.error("Failed to get broadcaster. Cannot create rewards.")

    async def check_leftover_rewards(self):
        """Check for and handle any leftover rewards from previous sessions."""
        if not os.path.exists(self.rewards_file):
            self.logger.debug("No rewards file found")
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
                                self.logger.debug(f"Deleted leftover reward: {reward_data['title']}")
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
            else:
                self.logger.debug("No leftover rewards found")
        except Exception as e:
            self.logger.error(f"Error checking leftover rewards: {e}")

    async def get_broadcaster(self):
        """Get broadcaster information."""
        try:
            self.broadcaster = await self.fetch_users(names=[self.config['twitch']['channel']])
            if self.broadcaster:
                self.broadcaster = self.broadcaster[0]
                self.channel_id = self.broadcaster.id
                self.logger.debug(f"Got broadcaster: {self.broadcaster.name} (ID: {self.channel_id})")
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
                parts = line.strip().split('|')
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
        
        if not self.config.get('twitch', {}).get('channel_points', False):
            self.logger.debug("Chaos Command Channel points are disabled. Skipping custom reward creation.")
            return
        # Then create regular command rewards
        commands = self.load_commands()
        enabled_commands_count = sum(1 for cmd in commands if cmd['isEnabledForPoints'])
        if enabled_commands_count > 0:
            self.logger.info(f"Creating {enabled_commands_count} custom channel point rewards...")

        for cmd in commands:
            if cmd['isEnabledForPoints']:
                await self.create_custom_reward(cmd)

    async def create_special_system_rewards(self):
        """Create rewards for special system commands (Email, Shop, Hints)."""
        special_systems = [
            {
                'system': 'emails',
                'title': 'Send Email',
                'description': 'Send an email. User is optional. (Format: subject:<subject> body:<body> user:Dr_Bao)',
                'cost': self.config.get('emails', {}).get('points_cost', 1000),
            },
            {
                'system': 'chatShop',
                'title': 'Buy Shop Item',
                'description': 'Purchase an item from the shop (Enter item name). Item List: https://github.com/modestimpala/VotVChaosMod/blob/main/list_store.txt',
                'cost': self.config.get('chatShop', {}).get('points_cost', 1000)
            },
            {
                'system': 'hints',
                'title': 'Send Hint',
                'description': 'Send a hint to the streamer, optionally with a type. <Format: (type) hint> Possible types: info, warning, error, thought. Ex: (info) This is an info hint.',
                'cost': self.config.get('hints', {}).get('points_cost', 500)
            }
        ]

        
        enabled_systems_count = sum(
            1 for system in special_systems
            if self.config.get(system['system'], {}).get('channel_points', False) and self.config.get(system['system'], {}).get('enabled', False)
        )
        if enabled_systems_count > 0:
            self.logger.info(f"Creating special system rewards (email, chat shop, etc)...")

        for system in special_systems:
            if system['cost'] < 1:
                self.logger.error(f"Invalid cost for {system['system']}. Must be at least 1.")
                continue

            if self.config.get(system['system'], {}).get('channel_points', False) and self.config.get(system['system'], {}).get('enabled', False):
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
                        self.logger.debug(f"Special reward for {system['system']} already exists")
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
                    self.logger.debug(f"Created special reward for {system['system']}")
                    self.save_rewards()

                except Exception as e:
                    self.logger.error(f"Failed to create special reward for {system['system']}: {e}")
                    self.logger.exception("Detailed traceback:")

    async def create_custom_reward(self, command):
        """
        Create a single custom reward or add existing one if duplicate.
        
        Args:
            command (dict): Dictionary containing reward configuration
            
        Returns:
            bool: True if reward creation/retrieval was successful, False otherwise
        """
        if not self.broadcaster:
            self.logger.error("Broadcaster not set. Cannot create custom reward.")
            return False
        
        # Validate point cost
        try:
            point_cost = int(command['pointCost'])
            if point_cost < 1:
                self.logger.error(f"Invalid point cost for command '{command['title']}' - must be at least 1")
                return False
        except (ValueError, KeyError):
            self.logger.error(f"Invalid point cost format for command '{command['title']}'")
            return False

        try:
            self.logger.debug(f"Attempting to create reward with data: {command}")
            
            # Verify OAuth scopes
            scopes = await self.get_scopes()
            if 'channel:manage:redemptions' not in scopes:
                self.logger.error("Missing required OAuth scope: 'channel:manage:redemptions' - get a proper token from https://twitchtokengenerator.com/quick/76EdtsccRT")
                return False
            
            # Check for existing reward in our list
            for cmd_id, reward in self.rewards.items():
                if cmd_id == command['id']:
                    self.logger.debug(f"Reward '{command['title']}' already exists with ID: {cmd_id}")
                    return True
            
            try:
                reward = await self.broadcaster.create_custom_reward(
                    token=self.config['twitch']['oauth_token'],
                    title=command['title'],
                    cost=point_cost,
                    prompt=command['description'],
                    global_cooldown=int(command['pointsCooldown']),
                    input_required=False,
                    redemptions_skip_queue=False
                )
                
                self.rewards[command['id']] = reward
                self.logger.info(f"Successfully created custom reward: '{command['title']}'")
                self.save_rewards()
                return True
                
            except IndexError as e:
                # This catches the specific TwitchIO library bug where it tries to access error.args[2]
                # Check if this was actually a duplicate reward error by looking at the traceback
                tb_str = traceback.format_exc()
                if 'CREATE_CUSTOM_REWARD_DUPLICATE_REWARD' in tb_str:
                    # Fetch existing rewards and find the matching one
                    existing_rewards = await self.broadcaster.get_custom_rewards(token=self.config['twitch']['oauth_token'])
                    for existing_reward in existing_rewards:
                        if existing_reward.title == command['title']:
                            self.rewards[command['id']] = existing_reward
                            self.logger.info(f"Added existing reward '{command['title']}' to rewards list")
                            self.save_rewards()
                            return True
                    self.logger.error(f"Could not find existing reward '{command['title']}' despite duplicate error")
                    return False
                else:
                    self.logger.error(f"Unexpected IndexError while creating reward '{command['title']}': {str(e)}")
                    self.logger.debug(f"Full traceback: {tb_str}")
                    return False
                    
            except Exception as e:
                if 'CREATE_CUSTOM_REWARD_DUPLICATE_REWARD' in str(e):
                    # Fetch existing rewards and find the matching one
                    existing_rewards = await self.broadcaster.get_custom_rewards(token=self.config['twitch']['oauth_token'])
                    for existing_reward in existing_rewards:
                        if existing_reward.title == command['title']:
                            self.rewards[command['id']] = existing_reward
                            self.logger.info(f"Added existing reward '{command['title']}' to rewards list")
                            self.save_rewards()
                            return True
                    self.logger.error(f"Could not find existing reward '{command['title']}' despite duplicate error")
                    return False
                else:
                    self.logger.error(f"Error creating reward '{command['title']}': {str(e)}")
                    self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Unexpected error in create_custom_reward for '{command['title']}': {str(e)}")
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return False

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
                self.logger.debug(f"Channel points redeemed by {event.user.name} for command {command_id}")
                if event.input:
                    if cmd_id == 'emails_points':
                        await self.email_channel_points(event)
                    elif cmd_id == 'chatShop_points':
                        await self.shop_channel_points(event)
                    elif cmd_id == 'hints_points':
                        await self.hint_channel_points(event)
                else:
                    # This is a Chaos Command redemption
                    await self.chaos_command_channel_points(event, command_id)
            else:
                self.logger.warning(f"Received redemption for unknown reward ID: {event.reward.id}")
                await self.refund_redemption(event)

        except Exception as e:
            self.logger.error(f"Error processing channel point redemption: {e}")
            try:
                await self.refund_redemption(event)
            except Exception as refund_error:
                self.logger.error(f"Failed to refund redemption after error: {refund_error}")

    async def email_channel_points(self, event):
        content = event.input
        
        if not any(marker in event.input.lower() for marker in ['subject:', 'body:', 'user:']):
            content = f"subject:{event.user.name} body:{event.input}"
        
        email_processor = EmailCommandProcessor()
        email_message = email_processor.parse_email_string(content)
        if not email_message:
            self.logger.debug(f"Invalid email format: {event.input}")
            await self.refund_redemption(event)
            return
        
        if not email_message.user:
            email_message.user = "user"
            
        await self.email_system.process_email(event.user.name, email_message.subject, email_message.body, None, email_message.user)
        await self.fulfill_redemption(event)

    async def shop_channel_points(self, event):
        if not self.shop_system.is_in_shop_options(event.input):
            self.logger.debug(f"Invalid shop item: {event.input}")
            await self.refund_redemption(event)
            return
        
        await self.shop_system.process_shop(event.input, event.user.name)
        await self.fulfill_redemption(event)

    async def hint_channel_points(self, event):
        await self.hint_system.process_hint(event.input)
        await self.fulfill_redemption(event)

    async def chaos_command_channel_points(self, event, command_id):
        # Handle chaos command redemption
        await self.websocket_handler.process_chaos_command("trigger_chaos", command_id)
        await self.fulfill_redemption(event)
        pass

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
        """Clean up rewards."""
        try:
            await self.remove_all_rewards()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
