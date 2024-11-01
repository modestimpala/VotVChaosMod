import os
import signal
import sys
import psutil
from src.hint_system import HintSystem
from src.twitch.twitch_connection import TwitchConnection
from src.voting_system import VotingSystem
from src.email_system import EmailSystem
from src.shop_system import ShopSystem
from src.utils.config import load_config
import asyncio
import traceback
import logging
from logging.handlers import RotatingFileHandler
from src.direct_mode import DirectModeHandler  
from src.task_manager import TaskManager
import requests
import subprocess

VERSION_URL = "https://raw.githubusercontent.com/modestimpala/VotVChaosMod/refs/heads/3.0.0/chaosbot_version.txt"
DOWNLOAD_URL = "https://github.com/modestimpala/VotVChaosMod/releases/download/latest/ChaosBot.zip"

def check_for_updates(current_version):
    try:
        response = requests.get(VERSION_URL)
        latest_version = response.text.strip()
        return latest_version > current_version
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        return False
    

def check_for_updates(current_version):
    try:
        response = requests.get(VERSION_URL)
        latest_version = response.text.strip()
        return latest_version > current_version
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        return False

def start_update_process():
    try:
        updater_path = os.path.join(os.path.dirname(sys.executable), "ChaosBot_Updater.exe")
        if os.path.exists(updater_path):
            subprocess.Popen([updater_path, sys.executable])
            logger.info("Update process started. Exiting current instance.")
            sys.exit(0)
        else:
            logger.error("Updater executable not found.")
    except Exception as e:
        logger.error(f"Failed to start update process: {e}")

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
        backupCount=5,
        encoding='utf-8'  # Specify UTF-8 encoding
    )
    file_handler.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    console_handler = logging.StreamHandler(sys.stdout)  # Use sys.stdout instead of creating a new StreamHandler
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

async def main():
    logger.info("Starting ChaosBot")
    logger.info("Loading config")
    config = load_config()

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
   
    logger.info("Establishing subsystems")
    
    email_system = EmailSystem(config)
    shop_system = ShopSystem(config)
    hint_system = HintSystem(config)

    voting_system = VotingSystem(config)

    logger.info("Starting Connection")

    task_manager = TaskManager()
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        shutdown_event.set()

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    try:
        tasks = []

        # Start Twitch connection if enabled
        try:
            if config['twitch']['enabled']:
                twitch_connection = TwitchConnection(
                    config, voting_system, email_system, shop_system, hint_system
                )
                tasks.append(
                    asyncio.create_task(
                        task_manager.start_task(
                            "twitch_mode",
                            twitch_connection.start
                        )
                    )
                )
        except KeyError as e:
            logger.error(f'Incorrect config entry in twitch.cfg: {e}')
            logger.error('Please make sure the config file is correct and try again.')
            logger.debug(traceback.format_exc())

        try: 
            # Start Direct Mode if enabled
            if config['direct']['enabled']:
                direct_connection = DirectModeHandler(
                    config, email_system, shop_system, hint_system
                )
                tasks.append(
                    asyncio.create_task(
                        task_manager.start_task(
                            "direct_mode",
                            direct_connection.start
                        )
                    )
                )
        except KeyError as e:
            logger.error(f'Incorrect config entry in direct.cfg: {e}')
            logger.error('Please make sure the config file is correct and try again.')
            logger.debug(traceback.format_exc())

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