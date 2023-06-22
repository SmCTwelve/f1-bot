# 🏁 f1-bot

Discord bot to view F1 stats.

## Description

View Formula 1 statistics within Discord using the [Pycord](https://pycord.dev/) library. The bot pulls data from [Ergast](http://ergast.com/mrd/) API and [FastF1](https://github.com/theOehrly/Fast-F1) library. 

Displays a range of data including race results, championship standings, lap times, pitstops and telemetry. Additionally, the bot can output visualisations such as tyre strategy, lap distributions, driver speed comparisons and more.

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

Some commands take specific parameters to refine the results, such as to filter to a specific driver. All `year` and `round` parameters are optional and if not specified will default to the most recent race. Commands which include lap data will not work for seasons before 2018.

- `round`: This can be the circuit location, GP name or the round number of the season. A partial name will attempt to search for a matching event. E.g. "Bahrain", "Silverstone".

- `driver`: Can be a partial driver name, 3-letter abbreviation or number.

- `session`: Some results can be filtered to a session, e.g. FP1, Sprint, Qualifying etc. by choosing an option from the Discord menu. For Sprint Weekends before 2023, "Sprint Shootout" is the equivilent of "Sprint Qualifying".

e.g.

`/results` - defaults to latest race results

`/results 2023 Spain Qualifying` - specify all parameters

`/results FP1` - year and round default to latest

## Season

Championship and event schedule related commands.

`/wdc [year]`

View Driver Championship standings.

`/wcc [year]`

View Constructors Championship standings.

`/grid [year]`

View all drivers and teams participating in the season.

`/schedule`

Get the current season calendar.

`/next`

Info and countdown to the next race weekend.

## Stats

Driver and session data.

`/results [year] [round] [session]`

View results classification for the session. Defaults to latest race results with no parameters.

`/pitstops [year] [round] [filter] [driver]`

View pitstop data. By default this shows the fastest pitstop for each driver. Results can be refined by specifying a driver and/or filter. Data unavailable for seasons before 2018.

Filters:

- Ranked (default): Each driver's fastest stop, sorted by duration
- Best: Show only the fastest stop of the race or from the specified driver's stops
- Worst: As above, but for the slowest stop.

`/laptimes [year] [round] [filter]`

View lap times for each driver in the race. Results are based on the best recorded lap for each driver. From this data, results can be narrowed using the filter. Only seasons >=2018

Filters:

- Ranked (default): Sort all drivers by their time
- Top 5: Show the top five results based on fastest laps
- Bottom 5: Show the slowest five drivers based on fastest laps
- Fastest: Only show the top fastest lap
- Slowest: Only show the bottom fastest lap

`/stints [year] [round] [driver]`

View race tyre compound stints and laps driven. Optionally refine results to a specific driver. Only seasons >=2018.

## Visualisations

Commands in this group are prefixed by `/plot <command>` and will output a Discord image file. Some data requiring lap telemetry may take some time to process if results have not yet been cached.

`/plot position [year] [round]`

Show a line plot of driver position changes during the race.

`/plot stints [year] [round]`

Show a stacked bar graph for each driver and their tyre stints.

`/plot fastestlap [year] [round] [session]`

Display the fastest lap delta for each driver as a bar plot.

`/plot trackspeed [year] [round] <driver>`

Show the drivers fastest lap speed telemetry mapped to the track. Driver is _required_.

`/plot speed [year] [round] [ [drv1] [drv2] [drv3] [drv4] ]`

Plot driver speed telemetry and distance to compare performance in different sectors.
At least 1 driver must be specified, up to a maximum of 4.

`/plot gains [year] [round]`

Show the number of places gained or lost per driver during the race.

`/plot tyre-choice [year] [round] [session]`

View a pie chart showing distribution of tyre compounds in the session.

`/plot gapdiff [first] [second] [year] [round]`

Plot the lap time difference between two drivers for all laps, excluding pitstops and slow laps.
Both `first` and `second` must be provided as a driver name, code or number.

`/plot lap-distribution [year] [round]`

Plot a violin plot and swarm plot showing the distributions of lap times and tyre compound.

`/plot tyre-performance [year] [round]`

View a line graph comparing the aggregate performance of each tyre compound over the life of the tyre.
