# 🏁 f1-bot
A Discord bot to view F1 stats.

## Description
A simple bot application incorporating the [discord.py](https://github.com/Rapptz/discord.py/tree/rewrite) library to view Formula 1 statistics within Discord. The bot pulls data from [Ergast](http://ergast.com/mrd/) API using commands invoked by Discord members, displaying data such as championship standings and details about upcoming races.

For now please consider this bot experimental and WIP.

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
See https://discordapp.com/developers/applications/ for the creation of a Discord Bot user and inviting to a server. Copy the **Token ID** of your Bot account to an environment variable called `BOT_TOKEN` which is read by the application to connect to Discord.

Run the application by executing `python -m bot.py` from the main directory. The console will display log messages to monitor the bot status.

A Procfile is included for easy hosting on Heroku as a worker dyno. For other hosting configurations ensure `bot.py` is used as the entry point.

## Usage
Commands are invoked with the prefix `!` and base `f1` command followed by one of the following subcommands:
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
