import asyncio
import time
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
    

    async def handle_connection(self, websocket, path=None):
        """Handle game WebSocket connection."""
        try:
            if self.game_connection is not None:
                try:
                    # Test if existing connection is still alive
                    pong = await self.game_connection.ping()
                    if not pong:
                        logger.debug("Previous game connection is dead, allowing new connection")
                        self.game_connection = None
                    else:
                        logger.warning("Rejecting additional connection attempt - game already connected")
                        return
                except websockets.exceptions.ConnectionClosed:
                    logger.debug("Previous game connection was closed, allowing new connection")
                    self.game_connection = None
            
            self.game_connection = websocket
            logger.info("Game connected to WebSocket server")

            # Handle messages from the game
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.debug(f"Received game message: {data}")

                    if 'type' in data:
                        if data['type'] == 'connection_test':
                            await websocket.send(json.dumps({
                                "type": "connection_test_succ"
                            }))
                        elif data['type'] == 'voting_started':
                            logger.debug("Received voting_started message from game")
                            num_options = data.get('num_options', 0)
                            option_names = data.get('option_names', [])
                            
                            # Validate option names
                            if len(option_names) != num_options:
                                logger.warning(f"Option names count ({len(option_names)}) doesn't match num_options ({num_options})")
                                # Fill missing names with defaults
                                while len(option_names) < num_options:
                                    option_names.append(f"Option {len(option_names) + 1}")
                                # Trim excess names
                                option_names = option_names[:num_options]
                            
                            self.voting_system.set_voting_active(True, num_options, option_names)
                        elif data['type'] == 'voting_ended':
                            logger.debug("Received voting_ended message from game")
                            self.voting_system.set_voting_active(False)
                        elif data['type'] == 'shop_open':
                            logger.debug("Received shop_open message from game")
                            self.shop_system.set_shop_open(True)
                        elif data['type'] == 'shop_close':
                            logger.debug("Received shop_close message from game")
                            self.shop_system.set_shop_open(False)

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
            
    async def process_chaos_command(self, command_type: str, command: str) -> None:
        """
        Processes a chaos command by sending it to the game connection.

        Args:
            command_type (str): The type of the command.
            command (str): The command to be processed.
        """
        if not self.game_connection:
            logger.error("Cannot process command: Game is not connected")
            return
            
        try:
            direct = {
                "type": command_type,
                "command": command,
                "timestamp": time.time(),
            }
            await self.game_connection.send(json.dumps(direct))
        except Exception as e:
            logger.error(f"Failed to send command to game: {str(e)}")
            # Reset game_connection if we can't send to it
            self.game_connection = None

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
            logger.debug(f"Game WebSocket server started on ws://localhost:{self.port}")
            logger.info("Game Connection server started. Waiting for game connection...")

            # Very important
            self.voting_system.set_websocket_handler(self)
            self.shop_system.set_websocket_handler(self)
            self.email_system.set_websocket_handler(self)
            self.hint_system.set_websocket_handler(self)

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

            logger.debug("WebSocket server shutdown complete")
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