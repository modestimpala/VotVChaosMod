import os
import json
import logging
from datetime import datetime
import traceback
from typing import Dict, Optional, List
import asyncio

from twitchAPI.helper import first
from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.type import CustomRewardRedemptionStatus


class ChannelPointsMixin:
    """Mixin class to handle channel points rewards with twitchAPI."""

    async def initialize_channel_points(self):
        """Initialize channel points system."""
        self.rewards: Dict[str, dict] = {}
        self.channel_id = None
        self.rewards_file = self.config.get('files', {}).get('channel_points', 'channel_point_rewards.json')

        # Check if rewards file exists, if not create it
        if not os.path.exists(self.rewards_file):
            with open(self.rewards_file, 'w') as f:
                json.dump({}, f)

        # Check for leftover rewards from previous sessions
        await self.check_leftover_rewards()

        # Get channel ID if needed (should be set during twitch API initialization)
        if not self.channel_id and hasattr(self, 'twitch') and self.twitch:
            await self.get_channel_id()

        if self.channel_id:
            await self.create_rewards()
        else:
            self.logger.error("Failed to get channel ID. Cannot create rewards.")

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
                        # Temporarily ensure we have a channel ID for cleanup
                        if not self.channel_id and hasattr(self, 'twitch') and self.twitch:
                            await self.get_channel_id()

                        # Fetch and delete each reward
                        for cmd_id, reward_data in stored_rewards.items():
                            if self.twitch:
                                await self.twitch.delete_custom_reward(self.channel_id, reward_data['reward_id'])
                                self.logger.debug(f"Deleted leftover reward: {reward_data['title']}")
                            else:
                                self.logger.warning(
                                    f"Cannot delete reward {reward_data['reward_id']}: Twitch API not initialized")

                        self.clear_rewards_file()
                        self.logger.info("Successfully cleaned up leftover rewards.")
                    except Exception as e:
                        self.logger.error(f"Failed to clean up leftover rewards: {e}")
                        self.logger.debug(traceback.format_exc())
                else:
                    self.logger.info("Skipping reward cleanup.")
            else:
                self.logger.debug("No leftover rewards found")
        except Exception as e:
            self.logger.error(f"Error checking leftover rewards: {e}")
            self.logger.debug(traceback.format_exc())

    async def get_channel_id(self):
        """Get channel ID using twitchAPI."""
        try:
            # Get channel ID from twitchAPI
            channel_user = await first(self.twitch.get_users(logins=[self.config['twitch']['channel']]))
            if channel_user:
                self.channel_id = channel_user.id
                self.logger.debug(f"Got channel ID: {self.channel_id}")
            else:
                self.logger.error(f"No user found for channel: {self.config['twitch']['channel']}")
        except Exception as e:
            self.logger.error(f"Failed to get channel ID: {e}")
            self.logger.debug(traceback.format_exc())

    def save_rewards(self):
        """Save current reward IDs to file."""
        try:
            # Save the rewards data
            reward_data = {
                cmd_id: {
                    'reward_id': reward.get('id'),
                    'title': reward.get('title'),
                    'cost': reward.get('cost')
                }
                for cmd_id, reward in self.rewards.items()
                if reward.get('id')  # Only save rewards with an ID
            }

            with open(self.rewards_file, 'w') as f:
                json.dump(reward_data, f)
            self.logger.debug("Saved reward IDs to file")
        except Exception as e:
            self.logger.error(f"Failed to save reward IDs to file: {e}")
            self.logger.debug(traceback.format_exc())

    def clear_rewards_file(self):
        """Clear the rewards file."""
        try:
            if os.path.exists(self.rewards_file):
                os.remove(self.rewards_file)
                self.logger.debug("Cleared rewards file")
        except Exception as e:
            self.logger.error(f"Failed to clear rewards file: {e}")
            self.logger.debug(traceback.format_exc())

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

    async def get_existing_reward(self, reward_id: str) -> Optional[dict]:
        """Fetch an existing reward by ID using twitchAPI."""
        try:
            if self.twitch and self.channel_id:
                # Get all custom rewards
                rewards = await self.twitch.get_custom_reward(self.channel_id, reward_id)
                if rewards:
                    return rewards[0].to_dict()  # Convert TwitchObject to dict
            return None
        except Exception as e:
            self.logger.error(f"Failed to fetch existing reward {reward_id}: {e}")
            self.logger.debug(traceback.format_exc())
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
            if self.config.get(system['system'], {}).get('channel_points', False) and self.config.get(system['system'],
                                                                                                      {}).get('enabled',
                                                                                                              False)
        )

        if enabled_systems_count > 0:
            self.logger.info(f"Creating special system rewards (email, chat shop, etc)...")

        for system in special_systems:
            if system['cost'] < 1:
                self.logger.error(f"Invalid cost for {system['system']}. Must be at least 1.")
                continue

            if self.config.get(system['system'], {}).get('channel_points', False) and self.config.get(system['system'],
                                                                                                      {}).get('enabled',
                                                                                                              False):
                command = {
                    'id': f"{system['system']}_points",
                    'title': system['title'],
                    'description': system['description'],
                    'pointCost': system['cost'],
                    'pointsCooldown': self.config.get(system['system'], {}).get('points_cooldown', 0),
                    'isEnabledForPoints': True
                }

                try:
                    # Check if reward with this ID already exists in our list
                    if command['id'] in self.rewards:
                        self.logger.debug(f"Special reward for {system['system']} already exists")
                        continue

                    # Create the reward
                    result = await self.twitch.create_custom_reward(
                        broadcaster_id=self.channel_id,
                        title=command['title'],
                        cost=command['pointCost'],
                        prompt=command['description'],
                        is_global_cooldown_enabled=(command['pointsCooldown'] > 0),
                        global_cooldown_seconds=command['pointsCooldown'] if command['pointsCooldown'] > 0 else None,
                        is_user_input_required=True,  # Special commands always require input
                        should_redemptions_skip_request_queue=False
                    )

                    # Store the reward data
                    self.rewards[command['id']] = result.to_dict()
                    self.logger.debug(f"Created special reward for {system['system']}")
                    self.save_rewards()

                except Exception as e:
                    if "CREATE_CUSTOM_REWARD_DUPLICATE_REWARD" in str(e):
                        # Handle duplicate reward by getting it
                        try:
                            rewards = await self.twitch.get_custom_reward(self.channel_id)
                            for reward in rewards:
                                if reward.title == command['title']:
                                    self.rewards[command['id']] = reward.to_dict()
                                    self.logger.info(f"Added existing reward '{command['title']}' to rewards list")
                                    self.save_rewards()
                                    break
                        except Exception as fetch_error:
                            self.logger.error(f"Error fetching duplicate reward: {fetch_error}")
                    else:
                        self.logger.error(f"Failed to create special reward for {system['system']}: {e}")
                        self.logger.debug(traceback.format_exc())

    async def create_custom_reward(self, command):
        """
        Create a single custom reward or add existing one if duplicate.

        Args:
            command (dict): Dictionary containing reward configuration

        Returns:
            bool: True if reward creation/retrieval was successful, False otherwise
        """
        if not self.channel_id or not hasattr(self, 'twitch') or not self.twitch:
            self.logger.error("Twitch API or channel ID not set. Cannot create custom reward.")
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

            # Check for existing reward in our list
            if command['id'] in self.rewards:
                self.logger.debug(f"Reward '{command['title']}' already exists with ID: {command['id']}")
                return True

            # Create the reward using twitchAPI
            try:
                result = await self.twitch.create_custom_reward(
                    broadcaster_id=self.channel_id,
                    title=command['title'],
                    cost=point_cost,
                    prompt=command['description'],
                    is_global_cooldown_enabled=(command['pointsCooldown'] > 0),
                    global_cooldown_seconds=command['pointsCooldown'] if command['pointsCooldown'] > 0 else None,
                    is_user_input_required=False,
                    should_redemptions_skip_request_queue=False
                )

                self.rewards[command['id']] = result.to_dict()
                self.logger.info(f"Successfully created custom reward: '{command['title']}'")
                self.save_rewards()
                return True

            except Exception as e:
                if "CREATE_CUSTOM_REWARD_DUPLICATE_REWARD" in str(e):
                    # Handle duplicate reward by getting it
                    try:
                        rewards = await self.twitch.get_custom_reward(self.channel_id)
                        for reward in rewards:
                            if reward.title == command['title']:
                                self.rewards[command['id']] = reward.to_dict()
                                self.logger.info(f"Added existing reward '{command['title']}' to rewards list")
                                self.save_rewards()
                                return True
                    except Exception as fetch_error:
                        self.logger.error(f"Error fetching duplicate reward: {fetch_error}")
                        return False
                else:
                    self.logger.error(f"Error creating reward '{command['title']}': {str(e)}")
                    self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                    return False

        except Exception as e:
            self.logger.error(f"Unexpected error in create_custom_reward for '{command['title']}': {str(e)}")
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return False

    async def on_channel_points_redemption_add(self, event: ChannelPointsCustomRewardRedemptionAddEvent):
        """Handle a channel point redemption event from EventSub."""
        try:
            redemption = event.event
            reward_id = redemption.reward.id

            # Find the command ID associated with this reward
            command_id = None
            for cmd_id, reward in self.rewards.items():
                if reward.get('id') == reward_id:
                    command_id = cmd_id
                    break

            if command_id:
                self.logger.debug(f"Channel points redeemed by {redemption.user_name} for command {command_id}")

                if redemption.user_input:
                    # Special system rewards
                    if command_id == 'emails_points':
                        await self.email_channel_points(redemption)
                    elif command_id == 'chatShop_points':
                        await self.shop_channel_points(redemption)
                    elif command_id == 'hints_points':
                        await self.hint_channel_points(redemption)
                else:
                    # This is a Chaos Command redemption
                    await self.chaos_command_channel_points(redemption, command_id)
            else:
                self.logger.warning(f"Received redemption for unknown reward ID: {reward_id}")
                await self.refund_redemption(redemption)

        except Exception as e:
            self.logger.error(f"Error processing channel point redemption: {e}")
            self.logger.debug(traceback.format_exc())
            try:
                await self.refund_redemption(redemption)
            except Exception as refund_error:
                self.logger.error(f"Failed to refund redemption after error: {refund_error}")
                self.logger.debug(traceback.format_exc())

    async def email_channel_points(self, redemption):
        """Process email channel points redemption."""
        from src.dataclass.email_message import EmailCommandProcessor

        content = redemption.user_input

        if not any(marker in content.lower() for marker in ['subject:', 'body:', 'user:']):
            content = f"subject:{redemption.user_name} body:{content}"

        email_processor = EmailCommandProcessor()
        email_message = email_processor.parse_email_string(content)
        if not email_message:
            self.logger.debug(f"Invalid email format: {redemption.user_input}")
            await self.refund_redemption(redemption)
            return

        if not email_message.user:
            email_message.user = "user"

        await self.email_system.process_email(redemption.user_name, email_message.subject, email_message.body, None,
                                              email_message.user)
        await self.fulfill_redemption(redemption)

    async def shop_channel_points(self, redemption):
        """Process shop channel points redemption."""
        if not self.shop_system.is_in_shop_options(redemption.user_input):
            self.logger.debug(f"Invalid shop item: {redemption.user_input}")
            await self.refund_redemption(redemption)
            return

        self.logger.debug(f"Processing shop item: {redemption.user_input}")
        await self.shop_system.process_shop(redemption.user_input, redemption.user_name)
        await self.fulfill_redemption(redemption)

    async def hint_channel_points(self, redemption):
        """Process hint channel points redemption."""
        await self.hint_system.process_hint(redemption.user_input)
        await self.fulfill_redemption(redemption)

    async def chaos_command_channel_points(self, redemption, command_id):
        """Process chaos command channel points redemption."""
        # Handle chaos command redemption
        if hasattr(self, 'websocket_handler') and self.websocket_handler:
            await self.websocket_handler.process_chaos_command("trigger_chaos", command_id)
        await self.fulfill_redemption(redemption)

    async def fulfill_redemption(self, redemption):
        """Mark a redemption as fulfilled using twitchAPI."""
        try:
            await self.twitch.update_redemption_status(
                broadcaster_id=self.channel_id,
                reward_id=redemption.reward.id,
                redemption_ids=[redemption.id],
                status=CustomRewardRedemptionStatus.FULFILLED
            )
            self.logger.debug(f"Fulfilled redemption {redemption.id} for user {redemption.user_name}")
        except Exception as e:
            self.logger.error(f"Failed to fulfill redemption {redemption.id}: {e}")
            self.logger.debug(traceback.format_exc())

    async def refund_redemption(self, redemption):
        """Refund/cancel a redemption using twitchAPI."""
        try:
            await self.twitch.update_redemption_status(
                broadcaster_id=self.channel_id,
                reward_id=redemption.reward.id,
                redemption_ids=[redemption.id],
                status=CustomRewardRedemptionStatus.CANCELED
            )
            self.logger.debug(f"Refunded redemption {redemption.id} for user {redemption.user_name}")
        except Exception as e:
            self.logger.error(f"Failed to refund redemption {redemption.id}: {e}")
            self.logger.debug(traceback.format_exc())

    async def remove_all_rewards(self):
        """Remove all channel point rewards."""
        if not self.channel_id or not hasattr(self, 'twitch') or not self.twitch:
            self.logger.error("Twitch API or channel ID not set. Cannot remove custom rewards.")
            return

        for command_id, reward in list(self.rewards.items()):
            try:
                await self.twitch.delete_custom_reward(
                    broadcaster_id=self.channel_id,
                    reward_id=reward.get('id')
                )
                self.logger.info(f"Removed custom reward: {reward.get('title')}")
                del self.rewards[command_id]
            except Exception as e:
                self.logger.error(f"Failed to remove custom reward {reward.get('title')}: {e}")
                self.logger.debug(traceback.format_exc())

        # Clear the rewards file after successful removal
        self.clear_rewards_file()