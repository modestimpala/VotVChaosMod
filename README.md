
# VotVChaosMod

  

### Twitch Chaos Mod

  

Chaos Mod is an interactive mod that allows Twitch chat to vote on various in-game effects, send emails and shop for items! Experience Chaos with over 80 different commands to vote for!

  

This mod requires partial manual installation and will *not* work without the external Python program. Please read the instructions below for installation.

You need [pyChaosMod](https://github.com/modestimpala/VotVChaosMod/releases/download/1.0.2/pyChaosMod.zip) installed in Win64 folder. *Please read the instructions below for installation.*

  

## Features

  

- Twitch chat voting system

- Randomized chaos effects, including custom assets

- Customizable voting duration and cooldown

- Email system and Shop system for viewer interaction

- Overlay display for voting and results

  

### Community

  [GitHub Discussions](https://github.com/modestimpala/VotVChaosMod/discussions)
  
  Discord Thread
  

## r2modman Setup

  

1. Ensure you have the following dependencies installed:

- Python 3.x

- Pyglet library (pip install pyglet)

  

2. Install ChaosMod and unreal-shimloader

  

3. Download [pyChaosMod.zip](https://github.com/modestimpala/VotVChaosMod/releases/download/1.0.2/pyChaosMod.zip) from GitHub releases

  

4. Navigate to active r2modman game directory, pa08_00**\WindowsNoEditor\VotV\Binaries\Win64\

  

5. Place folder pyChaosMod into Win64 directory

  

6. Get an OAuth bot token from https://twitchtokengenerator.com/

  

7. Edit `config.json` with your OAuth token and channel settings, changing settings as needed

  

## Manual Setup

  

1. Ensure you have the following dependencies installed:

- Python 3.x

- Pyglet library (pip install pyglet)

- UE4SS (Unreal Engine 4 Scripting System)

  

2. Download [VotV.zip](https://github.com/modestimpala/VotVChaosMod/releases/download/1.0.2/VotV.zip) from GitHub releases

  

3. Navigate to modded game directory, pa08_00**\WindowsNoEditor\

  

4. Place folder VotV folder into WindowsNoEditor directory


5. Ensure pyChaosMod is located in Win64 directory, if not, download [pyChaosMod.zip](https://github.com/modestimpala/VotVChaosMod/releases/download/1.0.2/pyChaosMod.zip) from GitHub releases


6. Get an OAuth bot token from https://twitchtokengenerator.com/


7. Edit `config.json` with your OAuth token and channel settings, changing settings as needed

  

## Configuration

  

Edit the `config.json` file to customize the mod settings:

  

```json

{

  {

  "twitch": {

    "server": "irc.chat.twitch.tv",

    "port": 6667,

    "oauth_token": "oauth:[your oath token]", -  fill  with  info  from  https://twitchtokengenerator.com/

    "bot_username":  "[your bot username]",

    "channel": "[your channel name]"

  },

  "voting": {

    "duration": 30, -  how  long  voting  remains  active

    "cooldown_min": 60, -  min  cooldown  time

    "cooldown_max": 180, -  max  cooldown  time,  cooldown  time  is  a  random  time  inbetween  the  two

    "num_options": 4, -  number  of  options  to  vote  for

    "command_cooldown_rounds": 3, -  how  long  a  command  is  unavailable  after  winning

    "reset_cooldown_after_rounds": 6, -  reset  all  cooldowns  after  a  certain  #  of  rounds

    "combine_commands_chance": 0.1  -  how  often  commands  will  be  combined  with  another  command, 0.1  is  10%  chance

  },

    "emails": {

    "enabled": true, -  set  to  false  to  completely  disable  email  system

    "user_cooldown": 180  -  how  often  a  single  user  can  send  emails

  },

    "chatShop": {

    "enabled": true, -  set  to  false  to  completely  disable  shop  system

    "minOpenInterval": 180, -  min  open  interval

    "maxOpenInterval": 600, -  max  open  interval,  open  time  will  occur  randomly  between  the  two  numbers

    "openDuration": 30, -  how  long  the  shop  should  be  open

    "announcementMessage": "The shop is now open for {duration} seconds!", -  the  twitch  broadcast  chat  message  to  let  users  know  the  shop  is  open

    "userCooldown": 180  -  how  often  a  single  user  can  shop  for  items

  }

}

Do not change files section.

```

  

## Usage

  

1. Start your game with UE4SS enabled, through r2modman or manual setup.


2. Run `run.bat` or `python ./main.py` inside pyChaosMod dir to start the overlay and Twitch integration.


3. In-game controls:

- F8: Toggle Chaos Mod on/off

- F7: Manually trigger voting

- F6: Clear active events, to allow saving and pausing if disabled

- F3: Toggle email system (if enabled)

  

4. Twitch viewers can vote using numbers in chat during voting periods.

  

5. If enabled, viewers can use the `!email` command to send in-game emails.

  

6. If the shop system is enabled, viewers can use the `!shop` command to place orders when the shop is open. This will deduct Points.

  

# Overlay

  

Overlay will not display over Fullscreen game. You will have to either run it in windowed mode (Ctrl+Enter to change) or rely on Overlay seen on OBS.

  

I think it would be better to run the game Fullscreen so you don't immediately see what people are voting for.

  

Add a new Game Capture and target "[python.exe] .\main.py", right click on it and go to properties and enable "Allow Transparency" and "Premultiplied Alpha", then add a Color Source behind the Overlay that's light grey or something with an alpha source of ~155

  

Configure OBS to pick up "[python.exe] .\twitchChaos.py" audio.

  

# Showcase

  

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

  
  

</details>
