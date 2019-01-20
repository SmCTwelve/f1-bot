# 🏁 f1-bot  
A Discord bot to view F1 stats. 

## Description
A simple bot application incorporating the [discord.py](https://github.com/Rapptz/discord.py/tree/rewrite) library to view Formula 1 statistics within Discord. The bot pulls data from [Ergast](http://ergast.com/mrd/) API using commands invoked by Discord members, displaying data such as championship standings and details about upcoming races.

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
See https://discordapp.com/developers/applications/ for the creation of a Discord Bot user and inviting to a server. Copy the Token ID of your Bot account to an environment variable called `BOT_TOKEN` which is read by the application to connect to Discord. 

## Usage
Commands are invoked with the prefix `!` and base `f1` command followed by one of the following subcommands:
```
!help f1                           Display help text for the available commands
!f1 drivers | wdc                  Display the current World Driver Championship standings
!f1 teams | wcc                    Display the current Constructors Championship standings
!f1 schedule | races               Display the race calendar for the current season
!f1 next                           Show a countdown to the next race and details
!f1 grid                           Return details of all drivers and teams participating in the season 
!f1 timings <round>                Display fastest lap times per driver for <round>
!f1 results <round> [quali]        Race or qualifying results for <round>
!f1 career <driver_code>           Career stats for the driver                 
```
More functionality is planned, including lap times, qualifying results, comparisons between drivers and generating visualisations. 
