import asyncio
import logging
import os
import websockets
import json
import webbrowser
import ssl

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

        self.email_system.set_direct_connection(self)
        self.shop_system.set_direct_connection(self)
        
    def set_websocket_handler(self, websocket_handler):
        self.websocket_handler = websocket_handler

    async def start(self):
        """Establishes a WebSocket connection to the Chaos control panel."""
        server_url = "wss://votv.moddy.dev/chaos/ws"
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  

        try:
            self.websocket = await websockets.connect(
                server_url, 
                ssl=ssl_context
            )
            logger.info(f"Connected to Panel Server")
            
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

                await self.handle_messages()
            else:
                logger.error("Failed to create session")
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")

    async def handle_messages(self):
        """Handles incoming messages from the WebSocket server."""
        while True:  # Add reconnection loop
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
                                if self.websocket and self.websocket:
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
                logger.warning("WebSocket connection closed, attempting to reconnect...")
                await asyncio.sleep(5)  # Wait before reconnecting
                try:
                    await self.start()  # Attempt to reconnect
                except Exception as e:
                    logger.error(f"Failed to reconnect: {str(e)}")
                    await asyncio.sleep(5)  # Wait before next attempt
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await asyncio.sleep(5)


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
        while True:
            try:
                if not os.path.exists('./png/panelPhoto.txt'):
                    await asyncio.sleep(6)
                    continue

                with open('./png/panelPhoto.txt', 'r') as f:
                    base64_string = f.read().strip()
                
                # Only send if image changed
                if base64_string != last_image and self.websocket and self.captcha_verified and self.websocket:
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


# The main function in chaosbot.py would initialize this handler if directMode is True