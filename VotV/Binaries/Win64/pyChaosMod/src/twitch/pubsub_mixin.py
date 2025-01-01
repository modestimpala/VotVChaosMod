import asyncio
import logging
from twitchio.ext import pubsub
from typing import Optional

class PubSubMixin:
    """Mixin class to handle PubSub functionality."""
    
    async def initialize_pubsub(self):
        """Initialize PubSub connection."""
        self.pubsub = None
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