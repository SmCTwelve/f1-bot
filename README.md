# 🏁 f1-bot
A Discord bot to view F1 stats.

## Description
A simple bot application incorporating the [discord.py](https://github.com/Rapptz/discord.py/tree/rewrite) library to view Formula 1 statistics within Discord. The bot pulls data from [Ergast](http://ergast.com/mrd/) API using commands invoked by Discord members, displaying data such as championship standings and details about upcoming races.

Please be aware this was originally designed as a personal project and is provided as-is, it has not been tested on a large scale. Effort has been made to ensure the stated functionality. Further contributions or forks are welcome.

<p align="center"><img src="https://i.imgur.com/bdd7emE.gif" /></p>

## Installation
The application requires **Python 3.7+** to be installed.

```bash
$ git clone https://github.com/SmCTwelve/f1-bot.git
$ cd f1-bot/
$ pip install -r requirements.txt
```
Or download the latest stable [release](https://github.com/SmCTwelve/f1-bot/releases), extract the files and run `pip install -r requirements.txt` in the directory.

If using Pipenv you can install from the Pipfile and automatically create a virtual environment:
```bash
$ pipenv install
```



## Creating a Bot User
Open [Discord Developer Portal](https://discordapp.com/developers/applications/) and create a new application. The name will be the username displayed for your Bot. On your application page choose Bot from the settings menu, then click 'Add Bot' to turn your application into a Bot user.

Copy the **Token** of your Bot to the `config.ini` file in the main directory, replacing the value of the `TOKEN` key. **Do not share your token**, treat it like a password.

Alternatively, you can store the Token by setting an environment variable called `BOT_TOKEN` so you can avoid adding it to the config file. The environment variable will be checked first when loading the bot. This is useful if you plan to use a cloud host such as Heroku to store the Token as a config variable on the app.

### Inviting your Bot
To add the bot to a server you need to generate an OAauth2 URL for authentication and permissions.

1. Open the [Application](https://discordapp.com/developers/applications/) page of your Bot and under settings choose OAuth2.
2. In the Scopes section, check 'bot'
3. Scroll down to the Permissions section and enable the features shown [here](https://i.imgur.com/1bQ9xD8.png)
4. The Scopes section will now show a URL representing the scope and permissions your bot has
5. Copy this URL to invite your Bot to a server which you have permission

## Usage
Run the application by executing `python -m bot.py` from the main directory. This will start the bot process and attempt to connect with the provided Token. The console will display log messages to monitor the bot status. `Ctrl + C` will stop the process and close the connection.

A Procfile is included for easy hosting on Heroku as a worker dyno. For other hosting configurations ensure `bot.py` is used as the entry point.

Edit `config.ini` to change the prefix symbol, log messages and to enable/disable sending bot response as DM.

The `/data` directory contains a JSON dump of all drivers archived by Ergast API. This data is used by the application to search driver info. Periodically this may need updated, such as the beginning of a new F1 season with new drivers. To do so simply run `python -m update.py` from the main directory.

## Commands

**Parameters**

Commands which take `season` and `round` parameters will default to the latest race of the current season if omitted. Otherwise, both parameters should be given in the order `season` `round`, with the exception of `wdc`, `wcc` and `grid` commands which only use a `season`.

Commands which take the `driver_id` parameter must be either of the following:
  - Driver code; e.g. HAM, VET
  - Driver number; e.g. 44, 55
  - Ergast API ID; Typically, this is the driver's surnane, e.g. 'alonso', 'vettel'. However, in cases where the surname applies to multiple drivers, the ID will be `firstname_surname`, e.g. 'michael_schumacher', 'max_verstappen'.

Depending on the configuration, some commands will respond with a DM to avoid cluttering the text channel, this can be temporarily overridden for a command by including `no-dm` or `public` in the parameters, e.g. `!f1 wdc no-dm`.

**Usage**

Invoke a command in Discord by typing the prefix `!f1` (symbol can be changed in config) and one of the following subcommands:

- `!f1 help | !f1 help <command>` - Display help text for the available commands

- `!f1 status` - Information about the bot and connection status

- `!f1 github` - A link to this repository.

- `!f1 wdc | drivers [season]` - Display World Driver Championship standings.

- `!f1 wcc | constructors [season]` - Display Constructors Championship standings.

- `!f1 grid [season]` - Return details of all drivers and teams participating in the season.

- `!f1 schedule` - Display the race calendar for the current season.

- `!f1 next` - Show a countdown to the next race and details.

- `!f1 results [<season> <round>]` - Race results for `[round]` in `[season]`.

- `!f1 quali [<season> <round>]` - Qualifying results for `[round]` in `[season]`.

- `!f1 career <driver_id>` - Career stats for the driver.

- `!f1 stops <filter> [<season> <round>]`

  Display pit stops. Data not available for seasons before 2012.

  The `<filter>` parameter is **required** and must be one of the following:
  - `driver_id` - Get all stops for the specified driver
  - `top` - Top 5 fastest pit stops
  - `bottom` -  Bottom 5 slowest pit stops
  - `fastest` - Fastest ranked pit stop
  - `slowest` - Slowest ranked pit stop

- `!f1 best [filter] [<season> <round>]`

  Display best lap time per driver. When searching a specific `season` and `round`, the `[filter]` must be given first. You can use the `all` value if you don't actually want to filter the results. No parameters will return all best laps for the most recent race.

  Options for `[filter]` keyword:
  - `all` - Do not apply filter
  - `top` - Top 5 fastest laps of the race
  - `bottom` -  Bottom 5 slowest laps of the race
  - `fastest` - Fastest ranked lap
  - `slowest` - Slowest ranked lap


**Generating Plots**

The following `!f1 plot` subcommands will generate a chart uploaded as an image to the discord channel:

- `!f1 plot stints [<season> <round>]`

  Plot each driver's race stints and pit stops as a stacked bar chart.
- `!f1 plot fastest [<season> <round>] [drivers]`

  Plot fastest race lap as a bar chart. Both `season` and `round` must be given **before** any `drivers`. Using the command without parameters will return all latest results.
  - `[drivers]` may be multiple drivers to compare separated by a space; not specifying any drivers or using `all` will plot all drivers. Limiting drivers will result in a more legible graph.
  - E.g. `!f1 plot fastest 2019 1 BOT HAM VET`

- `!f1 plot timings [<season> <round>] [drivers]`

  Plot each lap time per lap of the race as a line graph. Both `season` and `round` must be given **before** any `drivers`. Using the command without parameters will return all latest results.
  - `[drivers]` may be multiple drivers to compare separated by a space; not specifying any drivers or using `all` will plot all drivers. Limiting drivers will result in a more legible graph.
  - E.g. `!f1 plot timings 2019 1 BOT HAM VET`

- `!f1 plot position [<season> <round>] [drivers]`

  Plot race position per lap of the race. Both `season` and `round` must be given **before** any `drivers`. Using the command without parameters will return all latest results.
  - `[drivers]` may be multiple drivers to compare separated by a space; not specifying any drivers or using `all` will plot for all drivers. Limiting drivers will result in a more legible graph.
  - E.g. `!f1 plot pos 2019 1 BOT HAM VET`

**NOTICE:** Both `plot timings` and `plot positions` may take some time to process as all lap data must be gathered from the external API. Please avoid excessive use of these commands and wait for the results to finish being processed.

