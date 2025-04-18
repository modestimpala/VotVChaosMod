import asyncio
import logging
import re
from typing import Optional, Dict, Any

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator, UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatCommand
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.helper import first

from src.twitch.channel_points_mixin import ChannelPointsMixin


class TwitchConnection(ChannelPointsMixin):
    """Class to handle the Twitch connection for the bot using twitchAPI."""

    def __init__(self, config, voting_system, email_system, shop_system, hint_system):
        self.voting_system = voting_system
        self.email_system = email_system
        self.shop_system = shop_system
        self.hint_system = hint_system

        self.shop_system.set_twitch_connection(self)
        self.email_system.set_twitch_connection(self)

        self.websocket_handler = None
        self.config = config
        self.message_queue = asyncio.Queue()
        self.is_connected = False
        self.should_run = True
        self.vote_pattern = re.compile(r"^\d+\s*$")

        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Twitch Connection...")

        # Check if required config is set
        if (self.config['twitch']['app_id'] == 'notset' or
                self.config['twitch']['app_secret'] == 'notset' or
                self.config['twitch']['channel'] == 'notset'):
            raise ValueError("Twitch App ID, App Secret, or channel not set in config file")

        # These will be set during initialization
        self.twitch = None
        self.eventsub = None
        self.chat = None
        self.channel_id = None
        self.user_id = None

        # Initialize rewards dict for ChannelPointsMixin
        self.rewards = {}

    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler

    async def start(self):
        """Start the Twitch connection."""
        self.logger.info("Starting Twitch Connection...")
        try:
            # Initialize Twitch API
            await self.initialize_twitch_api()

            # Keep the bot running
            while self.should_run:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Twitch Connection start was cancelled")
        except Exception as e:
            self.logger.exception(f"Error in Twitch connection: {e}")
            raise
        finally:
            self.logger.info("Twitch Connection closing...")
            await self.close()

    async def initialize_twitch_api(self):
        """Initialize the Twitch API client and authentication."""
        try:
            # Create Twitch instance
            self.twitch = await Twitch(self.config['twitch']['app_id'], self.config['twitch']['app_secret'])

            # Set up authentication scopes based on needed features
            required_scopes = [
                AuthScope.CHAT_READ,
                AuthScope.CHAT_EDIT
            ]

            # Add channel points scopes if enabled
            if self.is_channel_points_enabled():
                required_scopes.extend([
                    AuthScope.CHANNEL_READ_REDEMPTIONS,
                    AuthScope.CHANNEL_MANAGE_REDEMPTIONS
                ])

            # Authenticate the user
            auth = UserAuthenticator(self.twitch, required_scopes)
            token, refresh_token = await auth.authenticate()
            await self.twitch.set_user_authentication(token, required_scopes, refresh_token)

            # Get channel ID for the configured channel - FIX: Use first() helper for async generator
            channel_user = await first(self.twitch.get_users(logins=[self.config['twitch']['channel']]))
            if not channel_user:
                raise ValueError(f"Could not find channel: {self.config['twitch']['channel']}")

            self.channel_id = channel_user.id

            # Get bot's user ID
            bot_user = await first(self.twitch.get_users())
            if not bot_user:
                raise ValueError("Could not get authenticated user information")

            self.user_id = bot_user.id

            # Set up Chat
            await self.initialize_chat()

            # Set up EventSub for channel points if enabled
            if self.is_channel_points_enabled():
                await self.initialize_eventsub()
                # Initialize channel points from the mixin
                await self.initialize_channel_points()

            self.is_connected = True
            self.logger.info(
                f"Successfully initialized Twitch API connection for channel: {self.config['twitch']['channel']}")

            # Set up prefix if needed
            if self.config.get('twitch', {}).get('prefix', None):
                self.chat.set_prefix(self.config['twitch']['prefix'])

        except Exception as e:
            self.logger.exception(f"Failed to initialize Twitch API: {e}")
            raise

    async def initialize_chat(self):
        """Initialize the chat connection."""
        try:
            # Create chat instance
            self.chat = await Chat(self.twitch)

            # Register event handlers
            self.chat.register_event(ChatEvent.READY, self.on_ready)
            self.chat.register_event(ChatEvent.MESSAGE, self.on_message)

            # Register commands
            self.chat.register_command('shop', self.shop_command)
            self.chat.register_command('email', self.email_command)
            self.chat.register_command('hint', self.hint_command)

            # Start the chat connection
            self.chat.start()
            self.logger.info("Chat connection started successfully")

        except Exception as e:
            self.logger.exception(f"Failed to initialize chat: {e}")
            raise

    async def initialize_eventsub(self):
        """Initialize EventSub WebSocket for channel points and other events."""
        try:
            # Create EventSub WebSocket instance
            self.eventsub = EventSubWebsocket(self.twitch)
            self.eventsub.start()

            # Subscribe to channel points redemption events
            await self.eventsub.listen_channel_points_custom_reward_redemption_add(
                self.channel_id,
                self.on_channel_points_redemption_add
            )

            self.logger.info("EventSub WebSocket initialized successfully")

        except Exception as e:
            self.logger.exception(f"Failed to initialize EventSub WebSocket: {e}")
            raise

    async def on_ready(self, ready_event: EventData):
        """Handler for when the chat bot is ready."""
        self.logger.info(f'Chat bot is ready, joining channel: {self.config["twitch"]["channel"]}')
        await ready_event.chat.join_room(self.config['twitch']['channel'])

        # Start tasks
        loop = asyncio.get_event_loop()
        loop.create_task(self.process_message_queue())
        loop.create_task(self.update_systems())

        self.logger.info("ChaosBot is now running...")
        self.logger.info("Use Ctrl+C to stop the bot gracefully.")

        if self.is_channel_points_enabled():
            self.logger.info(
                "Channel points are enabled. You must use Ctrl+C to stop the bot to remove rewards properly.")

    async def on_message(self, msg: ChatMessage):
        """Handler for chat messages."""
        # Process potential vote
        if self.vote_pattern.search(msg.text):
            self.voting_system.process_vote(msg.user.name, int(msg.text))

    async def shop_command(self, cmd: ChatCommand):
        """Handler for shop command."""
        parts = cmd.text.split(maxsplit=1)
        item = parts[1] if len(parts) > 1 else None

        if self.config.get('chatShop', {}).get('channel_points', False):
            await cmd.reply("Please use channel points to interact with the shop.")
            return

        if item is None:
            await cmd.reply(
                f"You can order items from the shop using !shop <item>. The shop is currently {'open' if self.shop_system.is_shop_open() else 'closed'}.")
            return

        if not self.shop_system.is_shop_open():
            await cmd.reply(f"The shop is currently closed. Please wait for it to open.")
            return

        await self.shop_system.process_shop(item, cmd.user.name, cmd)

    async def email_command(self, cmd: ChatCommand):
        """Handler for email command."""
        from src.dataclass.email_message import EmailCommandProcessor

        if self.config.get('emails', {}).get('channel_points', False):
            await cmd.reply("Please use channel points to send emails.")
            return

        if not self.email_system.are_emails_enabled():
            await cmd.reply("Emails are currently disabled.")
            return

        # Get the content after the command
        parts = cmd.text.split(maxsplit=1)
        content = parts[1] if len(parts) > 1 else ""

        # Handle simple format e.g. "!email hello"
        if content and not any(marker in content.lower() for marker in ['subject:', 'body:', 'user:']):
            content = f"subject:{cmd.user.name} body:{content}"

        # Parse the email message
        email_processor = EmailCommandProcessor()
        email_message = email_processor.parse_email_string(content)

        if not email_message:
            await cmd.reply(
                "To send emails, use either:\n1. Simple format: !email your message\n2. Detailed format: !email subject:<email subject> body:<email body> user:<username>")
            return

        if not email_message.user:
            email_message.user = "user"

        await self.email_system.process_email(cmd.user.name, email_message.subject, email_message.body, cmd,
                                              email_message.user)

    async def hint_command(self, cmd: ChatCommand):
        """Handler for hint command."""
        parts = cmd.text.split(maxsplit=1)
        hint_text = parts[1] if len(parts) > 1 else ""

        if not hint_text:
            await cmd.reply("Please provide a hint text.")
            return

        if self.config.get('hints', {}).get('channel_points', False):
            await cmd.reply("Please use channel points to send hints.")
            return

        await self.hint_system.process_hint(hint_text, None, cmd)

    # Override mixin's method to use our implementation
    async def on_channel_points_redemption_add(self, event: ChannelPointsCustomRewardRedemptionAddEvent):
        """Handler for channel points redemption events."""
        self.logger.debug(f"Received channel points redemption: {event}")

        # Call the mixin's implementation
        await ChannelPointsMixin.on_channel_points_redemption_add(self, event)

    async def update_systems(self):
        """Update the various systems in the bot."""
        while self.should_run:
            self.email_system.update()
            await asyncio.sleep(1 / 15)  # Update at 15 FPS

    async def process_message_queue(self):
        """Process the message queue."""
        while self.should_run:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                self.logger.debug(f"Processing message from queue: {message}")
                await self.send_message(message)
                self.message_queue.task_done()
            except asyncio.TimeoutError:
                pass  # This allows the loop to check should_run regularly

    async def queue_message(self, message):
        """Queue a message to be sent."""
        self.logger.debug(f"Queueing message: {message}")
        await self.message_queue.put(message)

    async def send_message(self, message):
        """Send a message to the Twitch chat."""
        self.logger.debug(f"Sending message: {message}")
        if self.chat and self.chat.is_ready():
            await self.chat.send_message(self.config['twitch']['channel'], message)
        else:
            self.logger.warning("Cannot send message: Chat not ready")

    def get_messages(self):
        """Get all messages from the message queue."""
        self.logger.debug("Getting all messages from the message queue")
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get_nowait())
        return messages

    def is_connected_to_twitch(self):
        """Check if the bot is connected to Twitch."""
        self.logger.debug(f"Checking if connected to Twitch: {self.is_connected}")
        return self.is_connected

    def is_channel_points_enabled(self):
        """Check if channel points features are enabled."""
        return (self.config.get('twitch', {}).get('channel_points', False) or
                self.config.get('chatShop', {}).get('channel_points', False) or
                self.config.get('emails', {}).get('channel_points', False) or
                self.config.get('hints', {}).get('channel_points', False))

    async def update_config(self, new_config):
        """Update the config for the bot and handle any necessary cleanup or initialization."""
        old_channel_points_enabled = self.is_channel_points_enabled()

        # Update the config
        self.config = new_config

        new_channel_points_enabled = self.is_channel_points_enabled()

        # Handle channel points changes
        if old_channel_points_enabled != new_channel_points_enabled:
            if new_channel_points_enabled and self.is_connected:
                # Enabling channel points
                self.logger.info("Channel points being enabled - initializing rewards...")
                try:
                    # Reinitialize Twitch API with updated scopes
                    await self.close()
                    await self.initialize_twitch_api()
                except Exception as e:
                    self.logger.error(f"Error initializing channel points: {e}")
            elif old_channel_points_enabled and not new_channel_points_enabled:
                # Disabling channel points
                self.logger.info("Channel points being disabled - cleaning up rewards...")
                try:
                    await self.remove_all_rewards()
                    # Reinitialize Twitch API with updated scopes
                    await self.close()
                    await self.initialize_twitch_api()
                    self.logger.info("Channel points cleanup completed successfully")
                except Exception as e:
                    self.logger.error(f"Error cleaning up channel points: {e}")

    async def close(self):
        """Clean up and close connections."""
        self.logger.info("Test Closing Twitch Connection...")
        self.should_run = False

        # Remove channel point rewards if enabled
        if self.is_channel_points_enabled():
            try:
                await self.remove_all_rewards()
                self.logger.info("Channel points rewards removed successfully")
            except Exception as e:
                self.logger.error(f"Error removing channel points rewards: {e}")

        # Close EventSub if it exists
        if self.eventsub:
            try:
                await self.eventsub.stop()
                self.logger.info("EventSub WebSocket closed")
            except Exception as e:
                self.logger.error(f"Error closing EventSub: {e}")

        # Close Chat if it exists
        if self.chat:
            try:
                self.chat.stop()
                self.logger.info("Chat connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Chat: {e}")

        # Close Twitch API connection
        if self.twitch:
            try:
                await self.twitch.close()
                self.logger.info("Twitch API connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Twitch API: {e}")

        # Clean up message queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except asyncio.QueueEmpty:
                break

        self.is_connected = False
        self.logger.info("Twitch Connection closed.")