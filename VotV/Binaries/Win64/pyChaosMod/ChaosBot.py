import signal
import sys
from typing import Optional

import asqlite
from src.game_connection.websocket_handler import WebSocketHandler
from src.hint_system import HintSystem
from src.twitch.twitch_connection import TwitchConnection
from src.voting_system import VotingSystem
from src.email_system import EmailSystem
from src.shop_system import ShopSystem
from src.overlay.overlay_server import OverlayServer  # New import
from src.utils.config import create_config_manager
import asyncio
import traceback
import logging
from src.direct_mode import DirectModeHandler  
from src.task_manager import TaskManager
from src.utils.logging import setup_logging
from src.utils.updating import check_for_updates, start_update_process
from src.utils.process import is_already_running

setup_logging()
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(
        self,
        task_manager: TaskManager,
        voting_system: VotingSystem,
        email_system: EmailSystem,
        shop_system: ShopSystem,
        hint_system: HintSystem
    ):
        self.task_manager = task_manager
        self.voting_system = voting_system
        self.email_system = email_system
        self.shop_system = shop_system
        self.hint_system = hint_system
        
        self.twitch_connection = None
        self.direct_connection = None
        self.websocket_handler = None
        self.overlay_server = None  # OBS overlay server
        self.tasks = []

    async def initialize(self, config):
        # Always start WebSocket server
        await self.start_websocket(config)
        
        # Start overlay server
        await self.start_overlay(config)

        try:
            if config['twitch']['enabled']:
                await self.start_twitch(config)
        except KeyError as e:
            logger.error(f'Incorrect config entry in twitch.cfg: {e}')
            logger.debug(traceback.format_exc())

        try:
            if config['direct']['enabled']:
                await self.start_direct(config)
        except KeyError as e:
            logger.error(f'Incorrect config entry in direct.cfg: {e}')
            logger.debug(traceback.format_exc())

    async def start_websocket(self, config):
        self.websocket_handler = WebSocketHandler(
            config, self.email_system, self.shop_system, self.hint_system, self.voting_system
        )
        self.tasks.append(
            asyncio.create_task(
                self.task_manager.start_task(
                    "websocket_server",
                    self.websocket_handler.start
                )
            )
        )

    async def start_overlay(self, config):
        """Start the overlay server."""
        self.overlay_server = OverlayServer(config, self.voting_system)
        
        # Set the overlay server reference in voting system
        self.voting_system.set_overlay_server(self.overlay_server)
        
        self.tasks.append(
            asyncio.create_task(
                self.task_manager.start_task(
                    "overlay_server",
                    self.overlay_server.start
                )
            )
        )

    async def start_twitch(self, config):
        # Create the TwitchConnection instance
        self.twitch_connection = TwitchConnection(
            config,
            self.voting_system,
            self.email_system,
            self.shop_system,
            self.hint_system
        )

        # Set the websocket handler if available
        if self.websocket_handler:
            self.twitch_connection.set_websocket_handler(self.websocket_handler)

        # Add the task to the task manager
        self.tasks.append(
            asyncio.create_task(
                self.task_manager.start_task(
                    "twitch_mode",
                    self.twitch_connection.start
                )
            )
        )

    async def start_direct(self, config):
        self.direct_connection = DirectModeHandler(
            config, self.email_system, self.shop_system, self.hint_system
        )
        if self.websocket_handler:
            self.direct_connection.set_websocket_handler(self.websocket_handler)
        self.tasks.append(
            asyncio.create_task(
                self.task_manager.start_task(
                    "direct_mode",
                    self.direct_connection.start
                )
            )
        )

    async def update_config(self, new_config):
        old_twitch_enabled = self.twitch_connection is not None
        old_direct_enabled = self.direct_connection is not None
        new_twitch_enabled = new_config['twitch']['enabled']
        new_direct_enabled = new_config['direct']['enabled']

        # Update WebSocket server
        if self.websocket_handler:
            await self.websocket_handler.update_config(new_config)
            
        # Update overlay server
        if self.overlay_server:
            await self.overlay_server.update_config(new_config)

        # Handle Twitch connection changes
        if old_twitch_enabled != new_twitch_enabled:
            if new_twitch_enabled:
                await self.start_twitch(new_config)
            else:
                await self.task_manager.stop_task("twitch_mode")
                if self.twitch_connection:
                    await self.twitch_connection.close()
                    self.twitch_connection = None

        # Handle Direct connection changes
        if old_direct_enabled != new_direct_enabled:
            if new_direct_enabled:
                await self.start_direct(new_config)
            else:
                await self.task_manager.stop_task("direct_mode")
                if self.direct_connection:
                    await self.direct_connection.close()
                    self.direct_connection = None

        # Update existing connections
        if self.direct_connection and new_direct_enabled:
            await self.direct_connection.update_config(new_config)
        if self.twitch_connection and new_twitch_enabled:
            await self.twitch_connection.update_config(new_config)

async def main():
    try:
        logger = setup_logging()
        logger.info("Starting ChaosBot")
        
        # Create and start config manager
        config_manager = await create_config_manager()
        config = config_manager
        
        # Check for updates if enabled
        if config["misc"]["auto_bot_update"]:
            logger.info("Checking for updates...")
            if getattr(sys, 'frozen', False):
                current_version = config.get('version', '0.0.0')
                logger.info(f"Current version: {current_version}")
                if check_for_updates(current_version):
                    logger.info("New version available. Starting update process...")
                    start_update_process()
                else:
                    logger.info("No updates available.")
            else:
                logger.warning("ChaosBot is running in development mode. Automatic updates are disabled.")
        else:
            logger.info("Automatic updates are disabled. Skipping update check.")
    
        logger.info("Establishing subsystems")
        
        # Initialize systems
        email_system = EmailSystem(config)
        shop_system = ShopSystem(config)
        hint_system = HintSystem(config)
        voting_system = VotingSystem(config)

        # Register systems for config updates
        def update_systems(new_config):
            email_system.update_config(new_config)
            shop_system.update_config(new_config)
            hint_system.update_config(new_config)
            voting_system.update_config(new_config)
            asyncio.create_task(connection_manager.update_config(new_config))
        
        config_manager.register_change_callback(update_systems)

        logger.info("Starting Connection")

        task_manager = TaskManager()
        shutdown_event = asyncio.Event()
        
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}")
            # Just set the event and return immediately
            shutdown_event.set()
            
        # Set up signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)

        try:
            # Start connections
            connection_manager = ConnectionManager(
                task_manager=task_manager,
                voting_system=voting_system,
                email_system=email_system,
                shop_system=shop_system,
                hint_system=hint_system
            )
            await connection_manager.initialize(config)
            # Wait for shutdown signal
            await shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"An error occurred in main loop: {e}")
            logger.error("Full traceback:")
            traceback.print_exc()
        finally:
            logger.info("Shutting down task manager...")
            await task_manager.stop_all()
            logger.info("ChaosBot shutdown complete")
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    if is_already_running():
        print("Warning: Another instance of ChaosBot is already running.")
        print("Running multiple instances may cause unexpected behavior.")
        print("Press Enter to continue anyway, or close this window to exit...")
        input()
        print("Continuing with multiple instances...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # This is handled by the signal handler now
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error("Full traceback:")
        traceback.print_exc()
        input() # Wait for user input before closing
    finally:
        logger.info("ChaosBot has exited.")
        sys.exit(0)  # Exit with a zero status code for normal exit

async def shutdown(tasks, signal_received=None):
    if signal_received:
        logger.info(f"Received signal {signal_received}. Shutting down gracefully...")
    else:
        logger.info("Shutting down gracefully...")
    
    # Convert single task to list if necessary
    tasks = [tasks] if not isinstance(tasks, list) else tasks
    
    try:
        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete with a timeout
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Optional: Wait a short time for tasks to clean up
        await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    finally:
        logger.info("ChaosBot has been shut down.")