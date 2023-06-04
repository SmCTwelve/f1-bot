# 🏁 f1-bot

Discord bot to view F1 stats.

**V2 WIP**

## Description

This bot application uses the [Pycord](https://pycord.dev/) library to view Formula 1 data within Discord. The bot pulls data from [Ergast](http://ergast.com/mrd/) API and [FastF1](https://github.com/theOehrly/Fast-F1) library.

This is a personal hobby project and has not been tested on a large scale. Contributions and suggestions are welcome.

<p align="center"><img src="https://i.imgur.com/bdd7emE.gif" /></p>

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

## Commands
