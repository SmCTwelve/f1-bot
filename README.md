# 🏁 f1-bot

Discord bot to view F1 stats.

## Description

Delve into the world of Formula 1 data and enhance your server with powerful commands for F1 enthusiasts. 🏎️ No more searching Twitter and Reddit for results and analysis; do it right within Discord!

Want to know who had the longest stint on Medium tyres? Which teammate is faster in different track sectors? How consistent is Alonso on which compound? When will Ferrari stop throwing? Answer all your questions (well, most of them) and generate your own insight with this handy bot.

🔧 This is a personal hobby project and has not been tested on a large scale. Contributions and suggestions are appreciated.

Developed with [Pycord](https://pycord.dev/), the bot harnesses the excellent data from [Ergast](http://ergast.com/mrd/) API and the [FastF1](https://github.com/theOehrly/Fast-F1) library with further analysis using Pandas and matplotlib.

### Features

🏁 View results from any season<br />
🏆 Championship standings<br />
⏱️ Lap times and pitstops<br />
🏎️ Car telemetry<br />
📊 Driver statistics

Plus generate charts 📈 to compare car performance, laptime distribution, tyre compounds, position gains, race stints and more!

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
  - Ensure that your bot has [these permissions](https://i.imgur.com/7l1WWTV.png)
- Create a `.env` file in the project root containing `BOT_TOKEN=YOUR_BOT_TOKEN`
  - or manually setup an environment variable on your host named `BOT_TOKEN`

A basic Docker config is included for convenience which is suitable for running on a VPS with an attatched cache volume.

## Usage

First activate the virtual environment (skip if using Docker) from the project root with `poetry shell`.

To start the bot run `python -m main`. This will attempt to connect using the env Token (see installation above).

The console will display log messages according to the level specified in `config.ini` and also output to `logs/f1-bot.log`.

Edit `config.ini` to change message display behaviour or restrict the bot to certain Guilds - this will only sync slash commands to the listed servers rather than being globally available (note this will prevent commands being accessible via DM). There may be a delay or some commands missing as Discord syncs the commands to your server.

### Cache

The application relies on caching both to speed up command processing and to respect API limits. Additionally the FastF1 library includes its own data cache.

A `/cache` directory will be created in the project root when the bot is running. This may become large over time with session telemetry (~100 MB per race weekend). You can manually delete the `/cache` folder or specific subfolders, or a script is provided in the root directory: `python -m flushcache`. Make sure the bot is not running. A new cache will be created during the next startup.

If using Docker you manage the cache separately by attatching a volume.

# Commands

All commands are implemented as Discord slash commands. Once the commands have synced with your Guild, they can be accessed with `/command-name`.

**Parameters**:

Some commands take parameters to refine the results, such as to filter to a specific driver. All `year` and `round` parameters are optional and if not specified will default to the most recent race. Commands which include lap data will not work for seasons before 2018.

- `round`: This can be the circuit location, GP name or the round number in the season. A partial name will attempt to search for a matching event. E.g. "Bahrain", "Silverstone". Try to be specific to prevent false matches.

- `driver`: Can be the driver surname, 3-letter abbreviation or number.

- `session`: Some results can be filtered to a session, e.g. FP1, Sprint, Qualifying etc. by choosing an option from the Discord menu. For Sprint Weekends before 2023, "Sprint Shootout" is the equivalent of "Sprint Qualifying".

e.g.

`/results` - defaults to latest race results

`/results 2023 Spain Qualifying` - specify all parameters

`/results FP1` - year and round default to latest

**Results Availability**

Data is sourced from Ergast API and official F1 timing data (through FastF1) and is typically updated within a few hours of a session.

Ergast considers the "last" round to be the last _complete_ race weekend. Therefore, when using commands with the default `round` in the middle of a race weekend - e.g. to view qualifying results on a Saturday - the results will refer to the previous round. However, you can still specify the name or number of the `round` in question to get results for the current race weekend if they are available.

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

View the fastest lap times for each driver in the race. Based on valid PB laps for each driver. Only seasons >=2018.
Select a tyre from the available choices to get the fastest laps on a specific compound.

> #### `/sectors [year] [round] [tyre]`

View the fastest sector times and speed trap for each driver. Based on valid quick laps. Optionally filter by tyre compound using the menu selection if there is enough lap data for the tyre.
Only season >= 2018.

> #### `/stints [year] [round]`

View race tyre stints and laps driven. Optionally refine results to a specific driver. Only seasons >=2018.

## Visualisations

Commands in this group are prefixed by `/plot <command>` and will output a Discord image file.

Lap telemetry may take some time to process if results have not been cached.

> #### `/plot position [year] [round]`

Show a line plot of driver position changes during the race.

> #### `/plot stints [year] [round]`

Show the tyre stints for each driver as a stacked bar chart.

> #### `/plot fastestlaps [year] [round] [session]`

Compare the delta of each driver's fastest lap as a bar chart.

> #### `/plot track-speed [year] [round] <driver>`

A circuit outline mapped to the driver speed over the lap. Driver is _required_.

> #### `/plot track-sectors <first> <second> [year] [round] [session]`

Compare fastest minisector between two drivers plotted on the track.

> #### `/plot telemetry <driver1> [driver2] [year] [round] [session]`

View telemetry graphs for Speed, Throttle, Brake, Gears, RPM and DRS for up to 2 drivers on their fastest lap.
At least 1 driver is required.

> #### `/plot gains [year] [round]`

Show the number of positions gained or lost per driver during the race.

> #### `/plot tyre-choice [year] [round] [session]`

View a pie chart showing distribution of tyre compounds in the session.

> #### `/plot gap <driver1> <driver2> [year] [round]`

Plot the lap time difference between two drivers accross all laps, excluding pitstops and slow laps.
Both `first` and `second` must be provided as a driver surname, code or number.

> #### `/plot lap-distribution [year] [round]`

Plot a violin plot and swarm plot showing the distributions of lap times and tyre compound.

> #### `/plot tyre-performance [year] [round]`

View a line graph comparing the average performance of each tyre compound over the life of the tyre.
