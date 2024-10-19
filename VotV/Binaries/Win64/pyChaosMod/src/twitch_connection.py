import queue
import re
import logging
from logging.handlers import RotatingFileHandler
import os
import asyncio
from twitchio.ext import commands

class TwitchConnection(commands.Bot):
    def __init__(self, config, voting_system, email_system, shop_system):

        self.voting_system = voting_system
        self.email_system = email_system
        self.shop_system = shop_system

        self.shop_system.set_twitch_connection(self)
        self.email_system.set_twitch_connection(self)

        self.config = config
        self.message_queue = asyncio.Queue()

        self.is_connected = False
        self.should_run = True

        self.vote_pattern = re.compile(r"^\d+\s*$")
        
        self.logger = logging.getLogger(__name__)

        self.logger.info("Initializing Twitch Connection...")

        self.commands_list = []

        #load commands from command_list.txt
        with open("command_list.txt", "r") as f:
            for line in f:
                self.commands_list.append(line.strip())

        if self.config['twitch']['oauth_token'] == 'notset' or self.config['twitch']['bot_username'] == 'notset' or self.config['twitch']['channel'] == 'notset':
            raise ValueError("Twitch OAuth token, bot username, or channel not set in config file")
        
        super().__init__(
            token=self.config['twitch']['oauth_token'],
            prefix='!',
            initial_channels=[f"#{self.config['twitch']['channel']}"]
        )

    async def start(self):
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
        while self.should_run:
            self.voting_system.update()
            self.email_system.update()
            self.shop_system.update()
            await asyncio.sleep(1/15)  # Update at 15 FPS

    async def event_ready(self):
        self.logger.info(f'Logged in as | {self.nick}')
        self.is_connected = True
        self.loop.create_task(self.process_message_queue())
        self.loop.create_task(self.update_systems())
        self.logger.info("ChaosBot is now running...")
        self.logger.info("Use Ctrl+C to stop the bot gracefully.")

    async def process_message_queue(self):
        while self.should_run:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.send_message(message)
                self.message_queue.task_done()
            except asyncio.TimeoutError:
                pass  # This allows the loop to check should_run regularly
    
    async def queue_message(self, message):
        await self.message_queue.put(message)

    async def event_message(self, ctx):
        if ctx.echo:
            return
        await self.handle_commands(ctx)
        #self.vote_pattern.search(ctx.content)
        #if self.vote_pattern.search(ctx.content):
            #self.voting_system.process_vote(ctx.author.name, int(ctx.content))

    async def reply(self, ctx, message):
        await ctx.reply(message)

    async def send_message(self, message):
        channel = self.get_channel(self.config['twitch']['channel'])
        await channel.send(message)

    def get_messages(self):
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages

    @commands.command()
    async def activate(self, ctx, effect : str | None):
        if effect is None:
            await ctx.reply("To activate an effect, type !activate <effect>.")
            return
        if effect not in self.commands_list:
            await ctx.reply(f"Effect {effect} not found.")
            return
        #wipe command.txt and write the effect to it
        with open("command.txt", "w") as f:
            f.write(effect)


    @commands.command()
    async def shop(self, ctx, item : str | None):
        if item is None:
            await ctx.reply(f"You can order items from the shop using !shop <item>. The shop is currently {'open' if self.shop_system.is_shop_open() else 'closed'}.")
            return
        if not self.shop_system.is_shop_open():
            await ctx.reply(f"The shop is currently closed. Please wait for it to open.")
            return
        await self.shop_system.process_shop(ctx.author.name, item, ctx)

    @commands.command()
    async def email(self, ctx: commands.Context):
        if not self.email_system.are_emails_enabled():
            await ctx.reply("Emails are currently disabled.")
            return

        # Remove the command name from the message
        content = ctx.message.content.split(maxsplit=1)[1] if len(ctx.message.content.split()) > 1 else ""

        # Try to split the content into subject and body
        try:
            subject, body = content.split("body:", 1)
            subject = subject.replace("subject:", "").strip()
            body = body.strip()
        except ValueError:
            await ctx.reply("To send emails, type !email subject:<email subject> body:<email body>")
            return

        if not subject or not body:
            await ctx.reply("Both subject and body are required. Type !email for help.")
            return
        await self.email_system.process_email(ctx.author.name, subject, body, ctx)


    def is_connected_to_twitch(self):
        return self.is_connected
    
    async def close(self):
        self.logger.info("Closing Twitch Connection...")
        self.should_run = False
        # Wait for queued messages to be sent
        while not self.message_queue.empty():
            try:
                await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                break
        # Close the underlying connection
        try:
            await super().close()
        except Exception as e:
            self.logger.exception(f"Error closing Twitch connection: {e}")
        self.logger.info("Twitch Connection closed.")



        