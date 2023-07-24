# 🏁 f1-bot

Discord bot to view F1 stats.

## Description

View Formula 1 statistics within Discord using the [Pycord](https://pycord.dev/) library. The bot pulls data from [Ergast](http://ergast.com/mrd/) API and [FastF1](https://github.com/theOehrly/Fast-F1) library. Results are processed using Pandas and matplotlib.

The bot displays a range of data including race results, championship standings, lap times, pitstops and telemetry. Additionally, the bot can output visualisations such as tyre strategy, lap distributions, driver speed comparisons and more.

<p align="center"><img src="https://i.imgur.com/bdd7emE.gif" /></p>

This is a personal hobby project and has not been tested on a large scale. Contributions and suggestions are welcome.

## Installation

The application requires **Python 3.11+**. It is recommended to use the Poetry package manager.

```bash
git clone https://github.com/SmCTwelve/f1-bot.git
cd f1-bot/
poetry install
```

Or download the latest stable [release](https://github.com/SmCTwelve/f1-bot/releases), extract the files and run `poetry install` in the directory.

**After install**:

- Rename `example.config.ini` to `config.ini`
- Refer to [this guide](https://guide.pycord.dev/getting-started/creating-your-first-bot#creating-the-bot-application) to setup a new Discord bot application, obtain your Token and OAuth2 URL.
  - Ensure that your bot has these permissions: https://i.imgur.com/7l1WWTV.png
- Create a `.env` file in the project root containing `BOT_TOKEN=YOUR_BOT_TOKEN`
  - or manually setup an environment variable named `BOT_TOKEN`

## Usage

Run `python -m main.py` from the root. This will start the bot process and attempt to connect with the provided Token. The console will display log messages according to the level specified in `config.ini` and also output to `logs/f1-bot.log`.

Edit `config.ini` to change message display behaviour or restrict the bot to certain Guilds - this will only sync slash commands to the listed servers rather than being globally available (note this prevents the bot commands from being accessed via DM). There may be a delay as Discord syncs the commands if no Guild is listed.

The application relies on caching both to speed up command processing and to respect API limits. Additionally the FastF1 library includes its own data cache. A `/cache` directory will be created in the project root when the bot is run.

# Commands

All commands are implemented as Discord slash commands. Once the commands have synced with your Guild, they can be accessed with `/command-name`.

**Parameters**:

Some commands take parameters to refine the results, such as to filter to a specific driver. All `year` and `round` parameters are optional and if not specified will default to the most recent race. Commands which include lap data will not work for seasons before 2018.

- `round`: This can be the circuit location, GP name or the round number in the season. A partial name will attempt to search for a matching event. E.g. "Bahrain", "Silverstone". Try to be specific to prevent false matches.

- `driver`: Can be the driver's partial name, 3-letter abbreviation or number.

- `session`: Some results can be filtered to a session, e.g. FP1, Sprint, Qualifying etc. by choosing an option from the Discord menu. For Sprint Weekends before 2023, "Sprint Shootout" is the equivalent of "Sprint Qualifying".

e.g.

`/results` - defaults to latest race results

`/results 2023 Spain Qualifying` - specify all parameters

`/results FP1` - year and round default to latest

**Results Availability**

Data is sourced from Ergast API and official F1 timing data (through FastF1) and is typically updated within a few hours of a session.

Ergast considers the "last" round to be the last _complete_ race weekend. So when using commands with the default `round` during a race weekend - e.g. to view qualifying results on a Saturday - the results will refer to the previous round. However, you can still specify the name or number of the `round` in question to get results for the current race weekend if they are available.

## Season

Championship and event schedule related commands.

> #### `/wdc [year]`

View Driver Championship standings.

> #### `/wcc [year]`

View Constructors Championship standings.

> #### `/grid [year]`

View all drivers and teams participating in the season.

> #### `/schedule`

Get the current season calendar.

> #### `/next`

Info and countdown to the next race weekend.

## Stats

Driver and session data.

> #### `/results [year] [round] [session]`

View results classification for the session. Defaults to latest race results with no parameters.

> #### `/pitstops [year] [round] [filter] [driver]`

View pitstop data. By default this shows the fastest pitstop for each driver. Results can be refined by specifying a driver and/or filter. Data unavailable for seasons before 2018.

Filters:

- Ranked (default): Each driver's fastest stop, sorted by duration
- Best: Show only the fastest stop of the race or from the specified driver's stops
- Worst: As above, but for the slowest stop.

> #### `/laptimes [year] [round] [tyre]`

View the fastest lap times for each driver in the race. Results are based on the best recorded laps for each driver. Only seasons >=2018. Select a tyre from the available choices to get the fastest laps on a specific tyre.

> #### `/sectors [year] [round] [tyre]`

View the fastest sector times and speed trap for each driver. Based on recorded quick laps. Optionally filter by tyre compound using the menu selection if there is enough lap data for the tyre. Only season >= 2018.

> #### `/stints [year] [round] [driver]`

View race tyre compound stints and laps driven. Optionally refine results to a specific driver. Only seasons >=2018.

## Visualisations

Commands in this group are prefixed by `/plot <command>` and will output a Discord image file. Some data requiring lap telemetry may take some time to process if results have not yet been cached.

> #### `/plot position [year] [round]`

Show a line plot of driver position changes during the race.

> #### `/plot stints [year] [round]`

Show the tyre stints for each driver as a stacked bar chart.

> #### `/plot fastestlaps [year] [round] [session]`

Compare the delta of each driver's fastest lap as a bar chart.

> #### `/plot track_speed [year] [round] <driver>`

A circuit outline mapped to the driver speed over the lap. Driver is _required_.

> #### `/plot track_sectors <first> <second> [year] [round] [session]`

Compare the fastest driver in each minisector plotted on the track.

> #### `/plot telemetry <driver1> [driver2] [year] [round] [session]`

View telemetry graphs for Speed, Throttle, Brake, Gears, RPM and DRS for up to 2 drivers on their fastest lap.
At least 1 driver is required.

> #### `/plot gains [year] [round]`

Show the number of places gained or lost per driver during the race.

> #### `/plot tyre-choice [year] [round] [session]`

View a pie chart showing distribution of tyre compounds in the session.

> #### `/plot gap <driver1> <driver2> [year] [round]`

Plot the lap time difference between two drivers for all laps, excluding pitstops and slow laps.
Both `first` and `second` must be provided as a driver surname, code or number.

> #### `/plot lap-distribution [year] [round]`

Plot a violin plot and swarm plot showing the distributions of lap times and tyre compound.

> #### `/plot tyre-performance [year] [round]`

View a line graph comparing the average performance of each tyre compound over the life of the tyre.
