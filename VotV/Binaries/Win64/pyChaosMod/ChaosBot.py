import sys
import time
import psutil
from src.twitch_connection import TwitchConnection
from src.message_handler import MessageHandler
from src.voting_system import VotingSystem
from src.email_system import EmailSystem
from src.shop_system import ShopSystem
from src.utils import load_config

def is_already_running():
    current_process = psutil.Process()
    for process in psutil.process_iter(['name', 'cmdline']):
        if process.pid == current_process.pid:
            continue
        try:
            if process.name().lower() == "chaosbot.exe":
                return True
            if process.name().lower() == "python.exe" or process.name().lower() == "python":
                cmdline = process.cmdline()
                if len(cmdline) > 1 and "chaosbot.py" in cmdline[1].lower():
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def main():
    print("Starting ChaosBot")
    print("Loading config")
    config = load_config()
   
    print("Establishing subsystems")
    twitch_connection = TwitchConnection(config)
    while not twitch_connection.is_connected_to_twitch():
        print("Waiting for Twitch connection...")
        time.sleep(1)
    print("Connected to Twitch!")
    email_system = EmailSystem(config, twitch_connection)
    shop_system = ShopSystem(config, twitch_connection)
    voting_system = VotingSystem(config)
   
    message_handler = MessageHandler(voting_system, email_system, shop_system)
   
    print("Starting main loop, press Ctrl+C to exit")
    print("ChaosBot is now running, press F8 in game to start the chaos! Press F7 to manually trigger voting.")
    while True:
        messages = twitch_connection.get_messages()
        for message in messages:
            message_handler.handle_message(message)
       
        voting_system.update()
        shop_system.update()
        email_system.update()
       
        time.sleep(1/15)  # Update at 15 FPS

if __name__ == "__main__":
    if is_already_running():
        print("Warning: Another instance of ChaosBot is already running.")
        print("Running multiple instances may cause unexpected behavior.")
        print("Press Enter to continue anyway, or close this window to exit...")
        input()
        print("Continuing with multiple instances...")
    
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Press Enter to exit...")
        input()  # This will pause the program until the user presses Enter
        sys.exit(1)  # Exit with a non-zero status code to indicate an error