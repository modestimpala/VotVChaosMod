import re
import logging
import asyncio
from src.twitch.pubsub_mixin import PubSubMixin
from src.twitch.channel_points_mixin import ChannelPointsMixin
from src.dataclass.email_message import EmailCommandProcessor
from twitchio.ext import commands, pubsub


class TwitchConnection(commands.Bot, ChannelPointsMixin, PubSubMixin):
    """Class to handle the Twitch connection for the bot."""
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

        if self.config['twitch']['oauth_token'] == 'notset' or self.config['twitch']['channel'] == 'notset':
            raise ValueError("Twitch OAuth token, bot username, or channel not set in config file")
        
        super().__init__(
            token=self.config['twitch']['oauth_token'],
            prefix='!',
            initial_channels=[f"#{self.config['twitch']['channel']}"]
        )
        
    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler

    async def start(self):
        """Start the Twitch connection."""
        self.logger.info("Starting Twitch Connection...")
        try:
            await super().start()
            self.logger.info("Twitch Connection started successfully")
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

    async def update_systems(self):
        """Update the various systems in the bot."""
        while self.should_run:
            self.email_system.update()
            await asyncio.sleep(1/15)  # Update at 15 FPS

    async def event_ready(self):
        self.logger.info(f'Logged in as | {self.nick}')
        self.is_connected = True

        await self.initialize_channel_points()
        await self.initialize_pubsub()

        self.loop.create_task(self.process_message_queue())
        self.loop.create_task(self.update_systems())
        self.logger.info("ChaosBot is now running...")
        self.logger.info("Use Ctrl+C to stop the bot gracefully.")
        
        if self.config.get('twitch', {}).get('channel_points', False) or self.config.get('chatShop', {}).get('channel_points', False) or self.config.get('emails', {}).get('channel_points', False) or self.config.get('hints', {}).get('channel_points', False):
            self.logger.info("Channel points are enabled. You must use Ctrl+C to stop the bot to remove rewards properly.")

    async def event_pubsub_channel_points(self, event: pubsub.PubSubChannelPointsMessage):
        """Handle channel point redemption events from PubSub."""
        self.logger.debug(f"Received channel points event: {event}")
        
        await self.handle_redemption(event)

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

    async def event_message(self, ctx):
        if ctx.echo:
            return
        await self.handle_commands(ctx)
        self.vote_pattern.search(ctx.content)
        if self.vote_pattern.search(ctx.content):
            self.voting_system.process_vote(ctx.author.name, int(ctx.content))

    async def reply(self, ctx, message):
        """Reply to a ctx message in the Twitch chat."""
        self.logger.debug(f"Replying to {ctx.author.name} with message: {message}")
        await ctx.reply(message)

    async def send_message(self, message):
        """Send a message to the Twitch chat."""
        self.logger.debug(f"Sending message: {message}")
        channel = self.get_channel(self.config['twitch']['channel'])
        await channel.send(message)

    def get_messages(self):
        """Get all messages from the message queue."""
        self.logger.debug("Getting all messages from the message queue")
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages

    @commands.command()
    async def shop(self, ctx, item : str | None):
        """Command to interact with the shop system."""
        self.logger.debug(f"Shop command invoked by {ctx.author.name} with item: {item}")
        if self.config.get('chatShop', {}).get('channel_points', False):
            await ctx.reply("Please use channel points to interact with the shop.")
            return
        if item is None:
            await ctx.reply(f"You can order items from the shop using !shop <item>. The shop is currently {'open' if self.shop_system.is_shop_open() else 'closed'}.")
            return
        if not self.shop_system.is_shop_open():
            await ctx.reply(f"The shop is currently closed. Please wait for it to open.")
            return
        await self.shop_system.process_shop(item, ctx.author.name, ctx)

    @commands.command()
    async def email(self, ctx: commands.Context):
        """Command to send emails."""
        self.logger.debug(f"Email command invoked by {ctx.author.name}")
        if self.config.get('emails', {}).get('channel_points', False):
            await ctx.reply("Please use channel points to send emails.")
            return
        if not self.email_system.are_emails_enabled():
            await ctx.reply("Emails are currently disabled.")
            return

        # Remove the command name from the message
        content = ctx.message.content.split(maxsplit=1)[1] if len(ctx.message.content.split()) > 1 else ""

         # Handle simple format e.g. "!email hello"
        if content and not any(marker in content.lower() for marker in ['subject:', 'body:', 'user:']):
            content = f"subject:{ctx.author.name} body:{content}"
        
        # Parse the email message
        email_processor = EmailCommandProcessor()
        email_message = email_processor.parse_email_string(content)
        
        if not email_message:
            await ctx.reply("To send emails, use either:\n1. Simple format: !email your message\n2. Detailed format: !email subject:<email subject> body:<email body> user:<username>")
            return
        
        if not email_message.user:
            email_message.user = "user"
        
        await self.email_system.process_email(ctx.author.name, email_message.subject, email_message.body, ctx, email_message.user)

    @commands.command()
    async def hint(self, ctx: commands.Context, hint_text: str):
        """Command to send hints."""
        self.logger.debug(f"Hint command invoked by {ctx.author.name} with hint: {hint_text}")
        if self.config.get('hints', {}).get('channel_points', False):
            await ctx.reply("Please use channel points to send hints.")
            return
        await self.hint_system.process_hint(hint_text, None, ctx)


    def is_connected_to_twitch(self):
        """Check if the bot is connected to Twitch."""
        self.logger.debug(f"Checking if connected to Twitch: {self.is_connected}")
        return self.is_connected
    
    async def update_config(self, new_config):
        """Update the config for the bot and handle any necessary cleanup or initialization."""
        old_channel_points_enabled = self.config.get('twitch', {}).get('channel_points', False)
        new_channel_points_enabled = new_config.get('twitch', {}).get('channel_points', False)

        # Update the config after handling all changes
        self.config = new_config

        # Handle channel points changes
        if old_channel_points_enabled and not new_channel_points_enabled:
            # Disabling channel points
            self.logger.info("Channel points being disabled - cleaning up rewards...")
            try:
                await self.remove_all_rewards()
                self.logger.info("Channel points cleanup completed successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning up channel points: {e}")
        elif not old_channel_points_enabled and new_channel_points_enabled and self.is_connected:
            # Enabling channel points
            self.logger.info("Channel points being enabled - initializing rewards...")
            try:
                await self.initialize_channel_points()
                await self.initialize_pubsub()
                self.logger.info("Channel points initialization completed successfully")
            except Exception as e:
                self.logger.error(f"Error initializing channel points: {e}")
        
        
    
    async def close(self):
        """Clean up and close connections."""
        self.logger.info("Closing Twitch Connection...")
        self.should_run = False

        await self.remove_all_rewards()

        # Close websocket connection
        if hasattr(self, '_ws') and self._ws:
            await self._ws.close()
            self._ws = None

        while not self.message_queue.empty():
            try:
                await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                break

        try:
            await self._websocket.close() if hasattr(self, '_websocket') else None
            await super().close()
        except Exception as e:
            self.logger.exception(f"Error closing Twitch connection: {e}")
        
        self.is_connected = False
        self.logger.info("Twitch Connection closed.")



