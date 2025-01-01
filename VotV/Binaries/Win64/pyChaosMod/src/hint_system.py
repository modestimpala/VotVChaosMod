import time
import json
import re
import logging
from typing import Tuple, Optional

class HintSystem:
    VALID_TYPES = {'info', 'warning', 'error', 'thought'}
    
    def __init__(self, config):
        self.config = config
        self.hint_cooldowns = {}
        self.twitch_connection = None
        self.websocket_handler = None
        self.logger = logging.getLogger(__name__)
        
    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler
        
    def set_twitch_connection(self, twitch_connection):
        self.twitch_connection = twitch_connection
        
    def set_direct_connection(self, direct_connection):
        self.direct_connection = direct_connection
    
    @staticmethod
    def parse_hint(hint_text: str) -> Tuple[str, str]:
        """
        Parse a hint string in the format "(type) hint_message"
        Valid types are: info, warning, error, thought
        If no type is specified or type is invalid, defaults to "info"
        """
        pattern = r'^\s*\((\w+)\)\s*(.+)$'
        
        match = re.match(pattern, hint_text)
        if match:
            hint_type = match.group(1).lower()
            hint_message = match.group(2).strip()
            
            # Validate hint type
            if hint_type in HintSystem.VALID_TYPES:
                return hint_type, hint_message
        
        # If no match or invalid type, return default type with original message
        return "info", hint_text.strip()
        
    async def process_hint(self, type_or_full_hint: str, hint: Optional[str] = None, ctx=None):
        """
        Process a hint. Can be called in two ways:
        1. process_hint(full_hint, ctx=ctx) - parses the full hint string
        2. process_hint(type, hint, ctx) - traditional way with separate type and hint
        """
        if not self.config['hints'].get('enabled', False):
            return
            
        current_time = time.time()
        
        # Check if we're getting a full hint string or separate type and hint
        if hint is None:
            # We're getting a full hint string
            hint_type, hint_message = self.parse_hint(type_or_full_hint)
        else:
            # We're getting separate type and hint
            hint_type = type_or_full_hint
            hint_message = hint
            # Validate the explicitly provided type
            if hint_type not in HintSystem.VALID_TYPES:
                hint_type = "info"
        
        # Check cooldown if we have a Twitch context
        if ctx is not None:
            if ctx.author.name in self.hint_cooldowns:
                time_since_last_hint = current_time - self.hint_cooldowns[ctx.author.name]
                if time_since_last_hint < self.config['hints']['user_cooldown']:
                    remaining_cooldown = int(self.config['hints']['user_cooldown'] - time_since_last_hint)
                    cooldown_message = f"You're on cooldown. You can send another hint in {remaining_cooldown} seconds."
                    await self.twitch_connection.reply(ctx, cooldown_message)
                    return
        
        # Send the hint through WebSocket
        await self.send_hint(hint_type, hint_message)
        
        # Update cooldown if we have a Twitch context
        if self.twitch_connection is not None and ctx is not None:
            self.hint_cooldowns[ctx.author.name] = current_time

    async def send_hint(self, hint_type: str, hint_message: str):
        """Send hint through WebSocket connection."""
        if self.websocket_handler and self.websocket_handler.game_connection:
            hint_data = {
                "type": "hint",
                "data": {
                    "type": hint_type,
                    "hint": hint_message,
                    "timestamp": time.time()
                }
            }
            
            try:
                await self.websocket_handler.game_connection.send(json.dumps(hint_data))
                self.logger.debug(f"Hint sent: {hint_type} - {hint_message}")
            except Exception as e:
                self.logger.error(f"Failed to send hint through WebSocket: {e}")
        else:
            self.logger.error("WebSocket connection not available")
    
    def update_config(self, config):
        self.config = config