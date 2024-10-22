import asyncio
import logging
from twitchio.ext import pubsub
from typing import Optional

class PubSubMixin:
    """Mixin class to handle PubSub functionality."""
    
    async def initialize_pubsub(self):
        """Initialize PubSub connection."""
        self.pubsub = None
        if self.config.get('twitch', {}).get('channel_points', False):
            await self.setup_pubsub()

    async def setup_pubsub(self):
        """Set up PubSub connection for channel points."""
        try:
            self.pubsub = pubsub.PubSubPool(self)

            # Set up the channel points topic
            topics = [
                pubsub.channel_points(self.config['twitch']['oauth_token'])[int(self.channel_id)]
            ]
            
            await self.pubsub.subscribe_topics(topics)
            self.logger.info("Successfully subscribed to channel points PubSub topics")
        except Exception as e:
            self.logger.error(f"Failed to setup PubSub: {e}")

    async def close_pubsub(self):
        """Close PubSub connection."""
        try:
            if self.pubsub:
                self.logger.info("Disconnected from PubSub")
        except Exception as e:
            self.logger.error(f"Error closing PubSub connection: {e}")