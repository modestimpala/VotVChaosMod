import os
import sys
import requests
import zipfile
import shutil
import time
import logging

VERSION_URL = "https://raw.githubusercontent.com/modestimpala/VotVChaosMod/refs/heads/main/chaosbot_version.txt"
DOWNLOAD_URL = "https://github.com/modestimpala/VotVChaosMod/releases/download/latest/ChaosBot.zip"

logging.basicConfig(filename='updater.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def download_and_install_update(main_exe_path):
    try:
        # Download the zip file
        response = requests.get(DOWNLOAD_URL)
        with open("ChaosBot_new.zip", "wb") as f:
            f.write(response.content)
        
        # Create a temporary directory for extraction
        temp_dir = "temp_update"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract the zip file
        with zipfile.ZipFile("ChaosBot_new.zip", 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the ChaosBot.exe in the extracted files
        for root, dirs, files in os.walk(temp_dir):
            if "ChaosBot.exe" in files:
                new_exe_path = os.path.join(root, "ChaosBot.exe")
                # Wait for the main process to exit
                time.sleep(5)  # Give some time for the main process to fully exit
                # Replace the old executable
                shutil.move(new_exe_path, main_exe_path)
                break
        else:
            raise Exception("ChaosBot.exe not found in the downloaded zip")
        
        # Clean up
        os.remove("ChaosBot_new.zip")
        shutil.rmtree(temp_dir)
        
        logging.info("Update downloaded and installed successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to download and install update: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        logging.error("Main executable path not provided.")
        return

    main_exe_path = sys.argv[1]
    logging.info(f"Starting update process for {main_exe_path}")
    
    if download_and_install_update(main_exe_path):
        logging.info("Update completed successfully. Restarting main application.")
        os.startfile(main_exe_path)
    else:
        logging.error("Update failed.")

if __name__ == "__main__":
    main()