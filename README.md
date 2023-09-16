# 🏁 f1-bot

Discord bot to view F1 stats.

## Description

Delve into the world of Formula 1 data and enhance your server with powerful commands for F1 enthusiasts. No more searching Twitter and Reddit for results and analysis; do it right within Discord!

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

[View command examples](https://github.com/SmCTwelve/f1-bot/wiki/Command-Usage-and-Examples)

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

If using Docker you can manage the cache separately by attatching a volume.

# Commands

### [View command documentation](https://github.com/SmCTwelve/f1-bot/wiki/Command-Usage-and-Examples)

The bot uses Discord slash commands. Once the commands have synced with your Guild, they can be accessed with `/command-name`.

#### **Result Availability**

Data is sourced from [Ergast API](https://ergast.com/mrd/) and official F1 timing data (through [FastF1](https://github.com/theOehrly/Fast-F1)) and is typically updated within a few hours of a session.

Ergast considers the _"last"_ round to be the last **complete** race weekend. Therefore, when using commands with the default `round` in the middle of a race weekend - e.g. to view qualifying results on a Saturday - the results will refer to the previous round. However, you can still specify the name or number of the `round` in question to get results for the current race weekend if they are available.

Data is based on quick laps with a threshold of 105%. This means that some compounds may not appear on the graph even if they were used in the race because the times were too slow. Additionally, track conditions, incidents and weather will influence the accuracy of the tyre life metrics.
