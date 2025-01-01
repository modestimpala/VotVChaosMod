# 3.1.0

### Changed
- Migrated away from "listen" text/json files for game communication to WebSocket server. Mod no longer supports 0.7. 
  - Hopefully resolves mysterious connection issues where game does not register votes, commands, etc.
  - More info: https://discord.com/channels/1285223290520207411/1285223379598839899/1323558223755870208
- Chat Shop now has an Order Queue
  - Orders are placed every minute if queue available. If queue is above 8 items, the order will be placed within 15 seconds.

# 3.0.0

### Added
- Full channel points system with custom rewards
  - Support for special system rewards (email/shop/hint redemptions)
- Direct Mode with Online Control Panel for sending specific direct commands to players
- Enhanced email support with simple format and improved message parsing
  - Simple format: !email (email) - Subject will be Twitch Username, body is entire message
  - Advanced format still available
  - Added support for specific user email handling (e.g., Dr_Bao)
- Enhanced shop system with item verification
- Implemented new hint system
  - !hint command, Hint channel point redemption
  - Can specify hint type (error, warning, thought)
- "Always On" mode for most systems, enhancing ease-of-use
- Dynamic Config Reloader to reload, enable/disable subsystems on the fly
- New custom console logging setup with color formatting
- Automatic ChaosBot updating system
- New configurable "Small Menu" displaying Chaos status during non-voting periods
- 1 random Glorp Friend Christmas event, 2 random Glorp Friend Random events (secrets)

### Changed
- Updated to 0.8.1
- Config files moved to /cfg subfolder
- Listen files moved to /listen subfolder
- Enhanced voting status checks
- Simplified main Lua loop
- General code cleanup and optimization
- Enhanced error message clarity
- Setting inputs disable/enable based on other settings for clarity
- Moved 26 Lua scripts to Blueprints

### Fixed
- ChaosBot is now launched as Admin to fix issues described by Mimi on Discord
- Fixed issues with incorrect voting options appearing during voting rounds (Thanks Mimi)
- Reduced websocket logging noise (stops logging of sensitive info)
- Added UTF-8 encoding for log files and created custom stream output for console, eliminating bugs from emojis
- Nextbots now follow player when on ATV

# 2.5.0
 Even more overhaul work.

 - Added:
	- Offline Mode
		- Offline mode runs without the external program and randomly executes commands based on configurable options, every set time period it has a chance of running a random command
	- Configurable voting and offline options
		- Each command can now be individually toggled to appear during voting or in offline mode
    - Option to disable voting ticker sound
	- 18 new commands!
    - Debug mode to trigger desired chaos commands manually 
    - Automatic updating of ChaosBot
- Changed:
	- Twitch Bot rework, now uses TwitchIO library
	- Improved Bot Logging
	- Moved several Lua based commands to Blueprints, work will continue to migrate Lua to Blueprints for increased stability
- Fixed:
	- Voting issue where the lowest option would be picked regardless of number of votes
	- Timescale issue, timers are now paused when sleeping or timescale is fast
	- External Lua scripts not working, hopefully this issue did not affect the Lua Commands, but ExecuteCommand errors should be resolved
- Removed:
 	- FastTimeScale command

# 2.0.0

Large overhaul. 

Added:
- Built in-game UI, no longer based on pyglet, same with UI sounds
- In-game settings menu
- Ability to launch or download latest build from game main menu
- Optional pre-built exe
- In-game buttons for hotkey replacements, hotkeys still exist
- 2 new commands (fullSleep, healPlayer)
- Added the ability to disable hard commands (only 4 are deemed "hard" so far)
- DataTables for commands and options
- Punch sound for Charborg Nextbot

Changed:
- Fixed points commands, fullTummy, nextbots, and teleport commands
- Added a timer for pyramidTime to remove after 3-5 mins
- Renamed main.py to ChaosBot.py
- Added utils.py
- Hard coded twitch server info
- Process checks for multiple ChaosBots running, with warnings
- Wait for input before exiting to display errors 


# 1.0.3

- Temporary fix for ATV disabling Chaos

# 1.0.2

- Fixed console window spam if UE4SS console not open

# 1.0.1

- Test command cleanup

# 1.0.0

- Initial Release