# 🏁 f1-bot
A Discord bot to view F1 stats.

## Description
A simple bot application incorporating the [discord.py](https://github.com/Rapptz/discord.py/tree/rewrite) library to view Formula 1 statistics within Discord. The bot pulls data from [Ergast](http://ergast.com/mrd/) API using commands invoked by Discord members, displaying data such as championship standings and details about upcoming races.

Please be aware this was originally designed as a personal project and is provided as-is, it has not been tested on a large scale. Effort has been made to ensure the stated functionality. Further contributions or forks are welcome.

## Installation
The application requires **Python 3.7+** to be installed.

```bash
$ git clone https://github.com/SmCTwelve/f1-bot.git
$ cd f1-bot/
$ pip install -r requirements.txt
```

Or if using Pipenv you can install from the Pipfile and automatically create a virtual environment:
```bash
$ pipenv install
```
In the main directory, rename `example_config.ini` to `config.ini`.
Do not share this file publicly once you have renamed it as it will contain your bot Token.

## Creating a Bot User
Open [Discord Developer Portal](https://discordapp.com/developers/applications/) and create a new application. The name will be the username displayed for your Bot. On your application page choose Bot from the settings menu, then click 'Add Bot' to turn your application into a Bot user.

Copy the **Token** of your Bot to the `config.ini` file in the main directory, replacing the value of the `TOKEN` key. **Do not share your token**, treat it like a password.

### Inviting your Bot
To add the bot to a server you need to generate an OAauth2 URL for authentication and permissions.

1. Open the [Application](https://discordapp.com/developers/applications/) page of your Bot and under settings choose OAuth2.
2. At the bottom under Scopes, check bot
3. Scroll down further to Permissions and enable the features shown [here](https://i.imgur.com/1bQ9xD8.png)
4. Scroll back up to Scopes and copy the URL to invite your Bot to a server which you have permission

## Usage
Run the application by executing `python -m bot.py` from the main directory. The console will display log messages to monitor the bot status.

A Procfile is included for easy hosting on Heroku as a worker dyno. For other hosting configurations ensure `bot.py` is used as the entry point.

## Commands
Commands are invoked with the prefix `!` (can be changed in config) and base `f1` command followed by one of the following subcommands:
```
!help f1                           Display help text for the available commands
!f1 drivers | wdc                  Display the current World Driver Championship standings
!f1 teams | wcc                    Display the current Constructors Championship standings
!f1 schedule | races               Display the race calendar for the current season
!f1 next                           Show a countdown to the next race and details
!f1 grid                           Return details of all drivers and teams participating in the season
!f1 timings [round, [season]]      Display fastest lap times per driver for [round] in [season]
!f1 results [round, [season]]      Race results for [round] in [season]
!f1 quali [round, [season]]        Qualifying results for [round] in [season]
!f1 career <driver_id>             Career stats for the driver
```

Commands which take `round` and `season` parameters will default to the latest race of the current season if omitted. If only the `round` parameter is provided, then `season` will be the current season. Otherwise, both parameters should be given in the order `round` `season`.

Commands which take the `driver_id` parameter must be a valid ID used by the Ergast API. Typically, this is the driver's surnane, e.g. 'alonso', 'vettel'. However, in cases where the surname applies to multiple drivers, the ID will typically be `firstname_surname`, e.g. 'michael_schumacher', 'max_verstappen'. A future update will add the ability to provide the driver code such as 'HAM' instead for easier use.

More functionality is planned, including lap time comparisons between drivers, component usage and generating plots.
