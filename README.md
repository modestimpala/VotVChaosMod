
# VotVChaosMod

  

### Twitch Chaos Mod

  
Chaos Mod is an interactive mod that allows Twitch chat to vote on various in-game effects, send emails and shop for items! Experience Chaos with over 80 different commands to vote for!

With version 2.0, ChaosMod now has automatic installation for the Twitch ChaosBot. A main menu button automatically downloads and runs a pre-built exe making installation a breeze. If you still want to run from source, it can automatically launch the python file for you. 

ChaosMod 2.0 also introduces a new built-in game UI, replacing the pyglet system - with in-game settings and main menu improvements! Other key additions include new commands, DataTables for commands and options, and the ability to disable "hard" commands. The update also features various command fixes, code organization, and more. See changelog for a more comprehensive review. 
  

## Features

- Built in automatic installation of Twitch bot

- Twitch chat voting system

- Randomized chaos effects, including custom assets

- Customizable voting duration and cooldown

- Email system and Shop system for viewer interaction

- Stylish In-game UI to display votes and ChaosMod status

  

### Community

  [GitHub Discussions](https://github.com/modestimpala/VotVChaosMod/discussions)

  

## Automatic r2modman Setup

    

1. Install ChaosMod and unreal-shimloader


2. Get an OAuth bot token from https://twitchtokengenerator.com/


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


5. Get an OAuth bot token from https://twitchtokengenerator.com/


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
  

# Overlay

  

Overlay is now built into the game, no configuration needed. 

  

# Showcase

![image](https://github.com/user-attachments/assets/7d0ec698-d2c9-4774-989c-850344bb03f4) ![image](https://github.com/user-attachments/assets/981ed31e-2923-4a90-9d96-f2166d46d643)


![image](https://github.com/user-attachments/assets/f10e6374-b36c-440b-92c9-1c3cd57a16ae)


https://github.com/user-attachments/assets/4adc4bad-de7b-4fab-8a11-432bc1a9cb42

  

Chaos Showcase

  
  

https://github.com/user-attachments/assets/9d8f602b-c36d-4a8f-b708-261537f7ef94

  

Twitch Chatter Email Showcase


https://github.com/user-attachments/assets/e9362855-1803-4733-a60d-bf4571f273f7


Twitch Shopping Showcase
  
  

# Commands

<details>

<summary>Current List of Commands (spoilers)</summary>

  





- 500cigs

- addEnergy

- badSun

- baseRave

- bigKel

- bigKerfurs

- bigLakeFish

- blackFog

- breakRandomGenerator

- breakRandomServers

- caltropsTrap

- deleteActiveSignal

- doublePoints

- drainSleep

- evilEriePlush

- explodeAllATVs

- explodePlayer

- fastTimeScale

- fishSplosion

- fixAllATVs

- fixGenerators

- forceServerMinigame

- forceSleep

- freeBattery

- freeMoney

- fullTummy

- garbageDay

- halfPoints

- hulkMode

- ignitePlayer

- immortalForTime

- insaneATVs

- jellyFishTime

- jumpscareComputer

- kerfurYeet

- killAllKerfurs

- laserSpam

- lowGravity

- lsdEffect

- madnessCombat

- maxwellBomb

- nauseaEffect

- nextbotCharborg

- nextbotGlorpFriend

- nextbotJerma

- nextbotWalter

- normalATVs

- ohFiddlesticks

- orderBanana

- orderCheese

- orderDrives

- orderPizza

- orderRadio

- orderShrimp

- orderTV

- pyramidTime

- ragdollPlayer

- randomDream

- redSky

- skyFallingEvent

- smoke500cigs

- smokeCig

- spamFlashlight

- spawnATV

- spawnFunGuy

- spawnKavotia

- spawnKerfurs

- spawnMaxwell

- spawnMeatball

- spawnMeatballFood

- spawnSonicGun

- spawnZeroGun

- starvePlayer

- superSpeed

- takePicture

- teleportRadioTower

- teleportToBaseBalcony

- teleportTopOfBase

- teleportTurbine

- tinyKel

- tinyKerfurs

- waspAttack

- wispTeleport

- fullSleep

- healPlayer

  
  

</details>
