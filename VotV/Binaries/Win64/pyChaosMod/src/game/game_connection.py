import asyncio
import websockets
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self, config, email_system, shop_system, hint_system, voting_system):
        self.config = config
        self.email_system = email_system
        self.shop_system = shop_system
        self.hint_system = hint_system
        self.voting_system = voting_system
        self.game_connection = None
        self.server = None
        self.port = config.get('websocket', {}).get('port', 3201)
        self._running = False

    async def handle_connection(self, websocket, path):
        """Handle game WebSocket connection."""
        try:
            if self.game_connection is not None:
                try:
                    # Test if existing connection is still alive
                    pong = await self.game_connection.ping()
                    if not pong:
                        logger.info("Previous game connection is dead, allowing new connection")
                        self.game_connection = None
                    else:
                        logger.warning("Rejecting additional connection attempt - game already connected")
                        return
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Previous game connection was closed, allowing new connection")
                    self.game_connection = None
            
            self.game_connection = websocket
            logger.info("Game connected to WebSocket server")

            # Handle messages from the game
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received game message: {data}")

                    if 'type' in data:
                        if data['type'] == 'connection_test':
                            await websocket.send(json.dumps({
                                "type": "connection_test_succ"
                            }))
                        elif data['type'] == 'voting_started':
                            logger.info("Received voting_started message from game")
                            num_options = data.get('num_options', 0)
                            self.voting_system.set_voting_active(True, num_options)
                        elif data['type'] == 'voting_ended':
                            logger.info("Received voting_ended message from game")
                            self.voting_system.set_voting_active(False)
                        elif data['type'] == 'shop':
                            await self.shop_system.handle_request(data)
                        elif data['type'] == 'hint':
                            await self.hint_system.handle_request(data)
                        elif data['type'] == 'email':
                            await self.email_system.handle_request(data)

                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from game")
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON format"
                    }))

        except websockets.exceptions.ConnectionClosed:
            logger.info("Game connection closed unexpectedly")
        finally:
            self.game_connection = None
            # Make sure voting is stopped if game disconnects
            if self.voting_system.voting_active:
                self.voting_system.set_voting_active(False)
            logger.info("Game disconnected from WebSocket server")

    async def start(self):
        """Start the WebSocket server."""
        if self._running:
            logger.warning("WebSocket server is already running")
            return

        try:
            # Clean up any existing server instance
            if self.server:
                await self.close()

            self._running = True
            self.server = await websockets.serve(
                self.handle_connection,
                "localhost",
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            logger.info(f"Game WebSocket server started on ws://localhost:{self.port}")

            # Very important
            self.voting_system.set_websocket_handler(self)

            # Keep the server running
            await self.server.wait_closed()
            
        except Exception as e:
            self._running = False
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
        finally:
            self._running = False

    async def close(self):
        """Shutdown the WebSocket server."""
        if not self._running:
            return

        try:
            # Close game connection if it exists
            if self.game_connection:
                await self.game_connection.close()
                self.game_connection = None

            # Close the server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                self.server = None

            logger.info("WebSocket server shutdown complete")
        except Exception as e:
            logger.error(f"Error during WebSocket server shutdown: {e}")
        finally:
            self._running = False

    async def update_config(self, new_config):
        """Update the configuration."""
        self.config = new_config
        new_port = new_config.get('websocket', {}).get('port', 3201)
        if new_port != self.port:
            logger.info(f"WebSocket port changed from {self.port} to {new_port}")
            await self.close()
            self.port = new_port
            await self.start()