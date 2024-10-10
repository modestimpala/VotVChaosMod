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