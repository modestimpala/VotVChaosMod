import os
import signal
import sys
import psutil
from src.twitch_connection import TwitchConnection
from src.message_handler import MessageHandler
from src.voting_system import VotingSystem
from src.email_system import EmailSystem
from src.shop_system import ShopSystem
from src.utils import load_config
import asyncio
import traceback
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create file handler which logs even debug messages
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, 'chaosbot.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

setup_logging()
logger = logging.getLogger(__name__)


def is_already_running():
    current_process = psutil.Process()
    current_pid = current_process.pid
    current_create_time = current_process.create_time()
    time_tolerance = 2  # 2 seconds of wiggle room

    for process in psutil.process_iter(['name', 'pid', 'create_time', 'cmdline']):
        if process.pid == current_pid:
            continue
        try:
            if process.name().lower() == "chaosbot.exe":
                if current_create_time - process.create_time() > time_tolerance:
                    return True
            if process.name().lower() in ["python.exe", "python"]:
                cmdline = process.cmdline()
                if len(cmdline) > 1 and "chaosbot.py" in cmdline[1].lower():
                    if current_create_time - process.create_time() > time_tolerance:
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

async def shutdown(twitch_connection, signal_received=None):
    if signal_received:
        logger.info(f"Received signal {signal_received}. Shutting down gracefully...")
    else:
        logger.info("Shutting down gracefully...")
    
    try:
        await twitch_connection.close()
    except Exception as e:
        logger.error(f"Error during Twitch connection closure: {e}")
    logger.info("ChaosBot has been shut down.")

async def main():
    logger.info("Starting ChaosBot")
    logger.info("Loading config")
    config = load_config()
   
    logger.info("Establishing subsystems")
    
    email_system = EmailSystem(config)
    shop_system = ShopSystem(config)
    voting_system = VotingSystem(config)
   
    twitch_connection = TwitchConnection(config, voting_system, email_system, shop_system)

    logger.info("Starting Twitch Connection")

    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        shutdown_event.set()

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    try:
        twitch_task = asyncio.create_task(twitch_connection.start())
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        done, pending = await asyncio.wait(
            [twitch_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        if shutdown_task in done:
            logger.info("Shutdown event received, closing Twitch connection...")
            twitch_task.cancel()
            try:
                await twitch_task
            except asyncio.CancelledError:
                pass
        
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"An error occurred during bot execution: {e}")
        logger.error("Full traceback:")
        traceback.print_exc()
    finally:
        await shutdown(twitch_connection)

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