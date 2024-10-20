import time
import json
import os
import asyncio

class HintSystem:
    def __init__(self, config):
        self.config = config
        self.hints_enabled = True
        self.hint_cooldowns = {}
        self.master_file = config['files']['hints_master']
        self.twitch_connection = None

    def set_twitch_connection(self, twitch_connection):
        self.twitch_connection = twitch_connection

    def set_direct_connection(self, direct_connection):
        self.direct_connection = direct_connection


    async def process_hint(self, type, hint, ctx):
        if not self.hints_enabled:
            return
        
        current_time = time.time()

        # Check if the user is on cooldown
        if self.twitch_connection is not None:
            if ctx.author.name in self.hint_cooldowns:
                time_since_last_hint = current_time - self.hint_cooldowns[ctx.author.name]
                if time_since_last_hint < self.config['hints']['user_cooldown']:
                    remaining_cooldown = int(self.config['hints']['user_cooldown'] - time_since_last_hint)
                    cooldown_message = f"You're on cooldown. You can send another hint in {remaining_cooldown} seconds."
                    await self.twitch_connection.reply(ctx, cooldown_message)
                    return

        hints = self.read_master_file()
        hints.append({
            "type": type,
            "hint": hint,
            "timestamp": time.time(),
            "processed": False
        })

        self.write_master_file(hints)

        if self.twitch_connection is not None:
            self.hint_cooldowns[ctx.author.name] = current_time


    def read_master_file(self):
        if os.path.exists(self.master_file):
            with open(self.master_file, 'r') as f:
                return json.load(f)
        return []

    def write_master_file(self, data):
        with open(self.master_file, 'w') as f:
            json.dump(data, f, indent=2)