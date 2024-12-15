import logging
import os
import subprocess
import sys
import requests


VERSION_URL = "https://raw.githubusercontent.com/modestimpala/VotVChaosMod/refs/heads/main/chaosbot_version.txt"
DOWNLOAD_URL = "https://github.com/modestimpala/VotVChaosMod/releases/download/latest/ChaosBot.zip"

logger = logging.getLogger(__name__)

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