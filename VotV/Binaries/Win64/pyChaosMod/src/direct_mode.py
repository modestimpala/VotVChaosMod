import asyncio
import logging
import os
import websockets
import json
import webbrowser
import ssl

from src.utils.chaos_file_handler import ChaosFileHandler

logger = logging.getLogger(__name__)

class DirectModeHandler:
    def __init__(self, config, email_system, shop_system, hint_system):
        self.config = config
        self.email_system = email_system
        self.shop_system = shop_system
        self.hint_system = hint_system
        self.websocket = None
        self.session_key = None
        self.captcha_verified = False

        self.email_system.set_direct_connection(self)
        self.shop_system.set_direct_connection(self)

        self.file_handler = ChaosFileHandler(config['files']['direct_master'])
        

    async def start(self):
        server_url = "wss://votv.moddy.dev/chaos/ws"
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  

        try:
            self.websocket = await websockets.connect(
                server_url, 
                ssl=ssl_context
            )
            logger.info(f"Connected to WebSocket server at {server_url}")
            
            # Request a new session with panel username
            await self.websocket.send(json.dumps({
                "action": "request_session",
                "panelUsername": self.config['direct']['panel_username']
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
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if data.get("action") == "captcha_verified":
                    self.captcha_verified = True
                    logger.info("Captcha verified. Control panel is now accessible.")
                    panel_url = f"https://votv.moddy.dev/chaos/panel/{self.session_key}"
                    logger.info(f"Control panel URL: {panel_url}")
                    if self.config.get('direct', {}).get('publish_panel', False):
                        logger.warning("Publishing to AriralChat. Your session will be publicly visible to others.")
                        await self.websocket.send(json.dumps({
                            "action": "publish_ariralchat",
                            "key": self.session_key
                        }))

                    if self.config['direct']['panel_photos']:
                        asyncio.create_task(self.send_panel_image())
                elif data.get("action") == "command" and self.captcha_verified:
                    await self.handle_command(data.get("command"), data.get("params"))
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")

    async def handle_command(self, command, params):
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
            await self.shop_system.process_shop(params.get('item'), None, "direct", params.get('quantity'))
        elif command == "send_hint":
            logger.debug("Send hint command received:", params)
            await self.hint_system.process_hint(params.get('type'), params.get('text'), None)
        elif command == "trigger_chaos":
            logger.debug("Chaos command received:", params)
            await self.process_chaos_command("trigger_chaos", params.get('command'))
        elif command == "trigger_event":
            logger.debug("Event command received:", params)
            await self.process_chaos_command("trigger_event", params.get('event'))
        # Add more command handlers as needed
        logger.info(f"Processed command: {command} with params: {params}")

    async def send_panel_image(self):
        last_image = None
        while True:
            try:
                if not os.path.exists('./png/panelPhoto.txt'):
                    await asyncio.sleep(6)
                    continue

                with open('./png/panelPhoto.txt', 'r') as f:
                    base64_string = f.read().strip()
                
                # Only send if image changed
                if base64_string != last_image and self.websocket and self.captcha_verified:
                    await self.websocket.send(json.dumps({
                        "action": "update_panel_image",
                        "image": base64_string  # Send original without compression
                    }))
                    last_image = base64_string
                
                await asyncio.sleep(6)
            except Exception as e:
                logger.error(f"Error sending panel image: {e}")
                await asyncio.sleep(6)

    async def close(self):
        if self.websocket:
            await self.websocket.close()
        logger.info("DirectModeHandler closed")

    async def process_chaos_command(self, type, command):
        await self.file_handler.process_chaos_command(type, command)

# The main function in chaosbot.py would initialize this handler if directMode is True