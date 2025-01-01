
<p align="center" width="100%">
    <img src="https://raw.githubusercontent.com/modestimpala/VotVChaosMod/refs/heads/main/img/chaos-banner.png">
</p>


<p align="center" width="100%">
<a href="https://discord.gg/Bq7HCMRfjk"><img width="5%" src="https://raw.githubusercontent.com/modestimpala/VotVChaosMod/refs/heads/main/img/discord.png"></a>
</p>

### Twitch Chaos Mod

  
Chaos Mod is an interactive mod that allows Twitch chat to vote on various in-game effects, send emails and shop for items! Experience Chaos with 100 different commands to vote for!

Version 3.1.0: Changed game communication to WebSocket for better reliability (drops 0.7 support) and added a queue system to Chat Shop that processes orders faster when busy.

Version 3.0.0 introduces a full Channel Points integration that lets viewers redeem custom rewards for Chaos Commands, emails, shop items, and hints. These rewards can be configured individually and run alongside regular Twitch voting.

A brand new Direct Mode with an Online Control Panel has been added that runs alongside Twitch Integration. When enabled, it allows sending specific commands directly to players through a web interface.

Each system now runs in "Always On" mode and reloaded/toggled dynamically through the a new dynamic config reloader. The email and shop systems were reworked with improved parsing and verification, a new Small Menu was added to display Chaos status, and 26 Lua scripts were moved to Blueprints for better stability.

See changelog for specific changes.

ChaosMod has automatic installation for the Twitch ChaosBot. A main menu button automatically downloads and runs a pre-built exe making installation a breeze. If you still want to run from source, it can automatically launch the python file for you. 

**If you encounter any issues, *please* report them in the Discord channel or Github issues.** ChaosBot now has improved logging, so please include the log file (VotV\Binaries\Win64\pyChaosMod\logs or VotV\Binaries\Win64\logs) when submitting Twitch issues for easier troubleshooting. 
  

## Features

- Twitch chat voting system

- Channel Point integration

- Offline Mode that randomly runs commands without Twitch Integration

- Direct Mode to send commands over a web interface

- Built in automatic installation of Twitch bot

- Randomized chaos effects, including custom assets

- Highly Customizable

- Email, Hint, and Shop system for viewer interaction - users can send emails to the in-game computer, order items from the shop and send hints of specific types

- Stylish In-game UI to display votes and ChaosMod status

  

## Community

  [GitHub Discussions](https://github.com/modestimpala/VotVChaosMod/discussions)

  [Discord](https://discord.gg/Bq7HCMRfjk)


## Automatic r2modman Setup

    

1. Install ChaosMod and unreal-shimloader


2. Get an OAuth bot token from https://twitchtokengenerator.com/ --- Channel Points / Chat OAuth Quick Link: https://twitchtokengenerator.com/quick/76EdtsccRT


3. Launch the game and configure settings from main menu


4. Launch the ChaosBot from main menu, which will automatically download and extract a pre-built exe, then run it.

If you want to download the exe manually, or run from source, see below.
  

## Manual r2modman Setup

  

1. Install ChaosMod and unreal-shimloader
  

2. Download [ChaosBot.zip](https://github.com/modestimpala/VotVChaosMod/releases/download/latest/ChaosBot.zip) from GitHub releases
    - Optionally, download python source [src_pyChaosMod.zip](https://github.com/modestimpala/VotVChaosMod/releases/download/latest/src_pyChaosMod.zip)

3. Navigate to modded game directory, pa08_00**\WindowsNoEditor\VotV\Binaries\Win64\


4. Place ChaosBot.exe in a folder called "pyChaosMod" inside Win64 folder 
    - Optionally, extract python source into Win64 folder
    - Python source requires psutil package (pip install psutil)


5. Get an OAuth bot token from https://twitchtokengenerator.com/ --- Channel Points / Chat OAuth Quick Link: https://twitchtokengenerator.com/quick/76EdtsccRT


6. Launch the game and configure settings from main menu


7. Launch the ChaosBot from main menu, which will automatically run in order priority: ChaosBot.exe, python Chaosbot.py 
    - Optionally, run the programs from pyChaosMod folder

Folder structure WindowsNoEditor\VotV\Binaries\Win64\pyChaosMod is *essential* for proper functionality 


## Configuration

  
  Use in-game configuration menu to change settings and set Twitch connection info.

  

## Usage

  

1. Start your game with mods enabled, through r2modman or manual setup.


2. Launch ChaosBot from main menu
    - Optionally, launch exe or .py file manually from pyChaosMod folder


3. Either pause the game or open inventory to see buttons to toggle the mod and other functions

    Optional In-game keybinds:

      - F8: Toggle Chaos Mod on/off

      - F7: Manually trigger voting

      - F6: Clear active events, to allow saving and pausing if disabled

      - F3: Toggle email system (if enabled)

  

4. Twitch viewers can vote using numbers in chat during voting periods.

  

5. If enabled, viewers can use the `!email` command to send in-game emails.
    - Format: !email subject:[subject] body:[body]
  

6. If the shop system is enabled, viewers can use the `!shop` command to place orders when the shop is open. This will deduct Points if enabled.
    - [Shop items list](https://github.com/modestimpala/VotVChaosMod/blob/main/list_store.txt)
  

# Showcase

<a href="https://www.youtube.com/watch?v=ygf_yA7nJtU"><img src="https://img.youtube.com/vi/ygf_yA7nJtU/hqdefault.jpg"></a>

<a href="https://www.youtube.com/watch?v=0nfU4AxEBnE"><img src="https://img.youtube.com/vi/0nfU4AxEBnE/hqdefault.jpg"></a>

![image](https://github.com/user-attachments/assets/7d0ec698-d2c9-4774-989c-850344bb03f4) ![image](https://github.com/user-attachments/assets/981ed31e-2923-4a90-9d96-f2166d46d643)


![image](https://github.com/user-attachments/assets/f10e6374-b36c-440b-92c9-1c3cd57a16ae)


https://github.com/user-attachments/assets/4adc4bad-de7b-4fab-8a11-432bc1a9cb42

  

https://github.com/user-attachments/assets/9d8f602b-c36d-4a8f-b708-261537f7ef94

  

Twitch Chatter Email Showcase


https://github.com/user-attachments/assets/e9362855-1803-4733-a60d-bf4571f273f7


Twitch Shopping Showcase
  
  

# Commands

<details>

<summary>Current List of Commands (spoilers)</summary>


- randomEvent
- hiccups
- fling
- rainbowATV
- fossilHounds
- stickDrift
- earthquake
- dirtyWindow
- explodeFridge
- bigRoach
- 5ghorse
- cataracts
- magneticEffect
- flipCamera
- vomit
- pukeDrive
- vomitRandomItem
- pukeStream
- pyramidTime
- kerfurYeet
- redSky
- killAllKerfurs
- spawnKerfurs
- ignitePlayer
- teleportRadioTower
- teleportTurbine
- ragdollPlayer
- superSpeed
- hulkMode
- smokeCig
- 500cigs
- explodePlayer
- badSun
- blackFog
- jellyFishTime
- spawnMeatball
- lowGravity
- spawnZeroGun
- spawnSonicGun
- freeMoney
- skyFallingEvent
- waspAttack
- laserSpam
- caltropsTrap
- spawnMeatballFood
- spawnMaxwell
- spawnKavotia
- wispTeleport
- spawnATV
- insaneATVs
- explodeAllATVs
- fixAllATVs
- smoke500cigs
- deleteActiveSignal
- randomDream
- forceSleep
- takePicture
- starvePlayer
- fullTummy
- doublePoints
- halfPoints
- nauseaEffect
- lsdEffect
- teleportToBaseBalcony
- teleportTopOfBase
- evilEriePlush
- immortalForTime
- bigKel
- tinyKel
- tinyKerfurs
- bigKerfurs
- baseRave
- fishSplosion
- bigLakeFish
- ohFiddlesticks
- forceServerMinigame
- breakRandomServers
- breakRandomGenerator
- fixGenerators
- garbageDay
- spamFlashlight
- madnessCombat
- maxwellBomb
- drainSleep
- addEnergy
- nextbotCharborg
- nextbotJerma
- nextbotWalter
- nextbotGlorpFriend
- jumpscareComputer
- freeBattery
- orderShrimp
- orderDrives
- orderPizza
- orderTV
- orderRadio
- orderBanana
- orderCheese
- fullSleep
- healPlayer
  

</details>
