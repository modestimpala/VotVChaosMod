import asyncio
import logging
import os
import websockets
import json
import webbrowser
import ssl
import time

logger = logging.getLogger(__name__)

class DirectModeHandler:
    """Handles the direct mode connection to the Chaos control panel."""
    
    def __init__(self, config, email_system, shop_system, hint_system):
        self.config = config
        self.email_system = email_system
        self.shop_system = shop_system
        self.hint_system = hint_system
        self.websocket = None
        self.session_key = None
        self.captcha_verified = False
        self.websocket_handler = None
        
        # Connection management variables
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5  # Maximum number of reconnection attempts
        self.last_connection_attempt = 0
        self.connection_cooldown = 60  # Cooldown period in seconds
        self.server_status_file = ".server_status"  # File to track server status
        self._connection_active = False
        self._is_running = False
        self._cooldown_logged = False

        self.email_system.set_direct_connection(self)
        self.shop_system.set_direct_connection(self)
        
    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler

    async def start(self):
        """Establishes a WebSocket connection to the Chaos control panel."""
        if self._is_running:
            return  # Prevent multiple instances of the connection loop
            
        self._is_running = True
        
        try:
            while True:
                if not await self._attempt_connection():
                    # If connection attempt returned False, we should wait before trying again
                    await asyncio.sleep(10)  # Check status every 10 seconds
                else:
                    # If connection was successful and then closed, we'll reach here
                    # The _attempt_connection function handles all the message processing
                    # So if we're here, it means the connection was closed and we should
                    # try reconnecting (unless max attempts reached)
                    if self.reconnect_attempts >= self.max_reconnect_attempts:
                        logger.error("Maximum reconnection attempts reached. Stopping reconnection attempts.")
                        self._mark_server_down()
                        # Wait for 1 hour before allowing connection attempts again
                        await asyncio.sleep(3600)
                        self.reconnect_attempts = 0
                        self._cooldown_logged = False
                    else:
                        # Connection was closed, will retry in next loop
                        pass
        finally:
            self._is_running = False

    async def _attempt_connection(self):
        """Attempts to connect to the server. Returns True if connected successfully."""
        # Check if we need to respect cooldown
        current_time = time.time()
        time_since_last_attempt = current_time - self.last_connection_attempt
        
        if time_since_last_attempt < self.connection_cooldown:
            if not self._cooldown_logged:
                wait_time = self.connection_cooldown - time_since_last_attempt
                logger.info(f"Connection on cooldown. Waiting {wait_time:.0f} seconds")
                self._cooldown_logged = True
            # Sleep for the remaining cooldown time
            await asyncio.sleep(1)  # Just sleep a bit, we'll check again in the main loop
            return False
            
        # Reset cooldown log flag
        self._cooldown_logged = False
            
        # Check if server is known to be down
        if self._is_server_down():
            # Only log once per hour
            if not hasattr(self, '_last_down_log') or (time.time() - self._last_down_log) > 3600:
                logger.warning("Server is known to be down. Not attempting connection.")
                self._last_down_log = time.time()
            await asyncio.sleep(5)  # Wait before checking again
            return False
            
        self.last_connection_attempt = current_time
        server_url = "wss://votv.moddy.dev/chaos/ws"
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  

        try:
            logger.info(f"Attempting to connect to Panel Server ({self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
            self.websocket = await websockets.connect(
                server_url, 
                ssl=ssl_context
            )
            logger.info(f"Connected to Panel Server")
            self._connection_active = True
            self.reconnect_attempts = 0  # Reset attempt counter on successful connection
            
            # Request a new session with panel username
            await self.websocket.send(json.dumps({
                "action": "request_session",
                "panelUsername": self.config['direct']['panel_username'],
                "panelCooldown": self.config['direct'].get('panel_cooldown', 0)
            }))
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("action") == "session_created":
                self.session_key = data.get("key")
                captcha_url = f"https://votv.moddy.dev/chaos/panel/{self.session_key}/captcha"
                logger.info(f"Opening captcha page: {captcha_url}")
                webbrowser.open(captcha_url)

                # This will keep running until the connection is closed
                await self.handle_messages()
                
                # If we reach here, the connection was closed
                self._connection_active = False
                return True
            else:
                logger.error("Failed to create session")
                self._connection_active = False
                self.reconnect_attempts += 1
                return False
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            self._connection_active = False
            self.reconnect_attempts += 1
            
            # Mark server as down if we exceed max attempts
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error("Maximum reconnection attempts reached. Marking server as down.")
                self._mark_server_down()
            
            return False

    def _is_server_down(self):
        """Check if server has been marked as down"""
        if os.path.exists(self.server_status_file):
            with open(self.server_status_file, 'r') as f:
                status_time = float(f.read().strip())
                # Consider server down for 1 hour (3600 seconds)
                return (time.time() - status_time) < 3600
        return False
        
    def _mark_server_down(self):
        """Mark the server as down"""
        with open(self.server_status_file, 'w') as f:
            f.write(str(time.time()))

    async def handle_messages(self):
        """Handles incoming messages from the WebSocket server."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    if data.get("action") == "captcha_verified":
                        self.captcha_verified = True
                        logger.info("Captcha verified. Control panel is now accessible.")
                        panel_url = f"https://votv.moddy.dev/chaos/panel/{self.session_key}"
                        logger.info(f"Control panel URL: {panel_url}")
                        if self.config.get('direct', {}).get('publish_panel', False):
                            if self.websocket:
                                await self.websocket.send(json.dumps({
                                    "action": "publish_ariralchat",
                                    "key": self.session_key
                                }))
                            else:
                                logger.error("WebSocket not connected when trying to publish")

                        if self.config['direct']['panel_photos']:
                            asyncio.create_task(self.send_panel_image())
                    elif data.get("action") == "command" and self.captcha_verified:
                        await self.handle_command(data.get("command"), data.get("params"))
                    elif data.get("action") == "publish_success":
                        logger.info("Successfully published to AriralChat")
                    elif data.get("action") == "publish_error":
                        logger.error("Failed to publish to AriralChat.")
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {message}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed.")
            self._connection_active = False
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            self._connection_active = False


    async def handle_command(self, command, params):
        """Handles commands received from the WebSocket server."""
        if not self.websocket:
            logger.error("WebSocket connection is not active")
            return

        try:
            if command == "send_email":
                subject = params.get('subject')
                content = params.get('content')
                user_type = params.get('userType')
                if subject and content and user_type:
                    await self.email_system.process_email("direct", subject, content, None, user_type)
                else:
                    logger.error("Missing parameters for send_email command")
            elif command == "shop_action":
                logger.debug("Shop action command received:", params)
                await self.shop_system.process_shop(params.get('item'), "direct", None, params.get('quantity'))
            elif command == "send_hint":
                logger.debug("Send hint command received:", params)
                await self.hint_system.process_hint(params.get('type'), params.get('text'), None)
            elif command == "trigger_chaos":
                logger.debug("Chaos command received:", params)
                await self.process_chaos_command("trigger_chaos", params.get('command'))
            elif command == "trigger_event":
                logger.debug("Event command received:", params)
                await self.process_chaos_command("trigger_event", params.get('event'))
            logger.debug(f"Processed command: {command} with params: {params}")
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            # Log full error details for debugging
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

    async def send_panel_image(self):
        """Sends the panel image to the WebSocket server."""
        last_image = None
        while self._connection_active and self.websocket and self.captcha_verified:
            try:
                if not os.path.exists('./png/panelPhoto.txt'):
                    await asyncio.sleep(6)
                    continue

                with open('./png/panelPhoto.txt', 'r') as f:
                    base64_string = f.read().strip()
                
                # Only send if image changed
                if base64_string != last_image and self._connection_active:
                    await self.websocket.send(json.dumps({
                        "action": "update_panel_image",
                        "image": base64_string 
                    }))
                    last_image = base64_string
                
                await asyncio.sleep(6)
            except Exception as e:
                logger.error(f"Error sending panel image: {e}")
                await asyncio.sleep(6)
        
    async def update_config(self, new_config):
        """Updates the configuration settings."""
        self.config = new_config

    async def close(self):
        """Closes the WebSocket connection."""
        self._connection_active = False
        if self.websocket:
            await self.websocket.close()
        logger.info("DirectModeHandler closed")

    async def process_chaos_command(self, command_type, command):
        """Processes chaos commands through the WebSocket connection."""
        try:
            if not self.websocket_handler:
                logger.error("WebSocket handler not set, cannot process command")
                return
                
            if not hasattr(self.websocket_handler, 'process_chaos_command'):
                logger.error("WebSocket handler doesn't have process_chaos_command method")
                return
                
            await self.websocket_handler.process_chaos_command(command_type, command)
        except Exception as e:
            logger.error(f"Error processing chaos command: {str(e)}")
            # Log full error details for debugging
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")