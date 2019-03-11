"Administrative commands to manage the bot."
import logging

from f1 import commands

# import in boy.py after commands

# set global time bot started (time.now)
# store the time as persist in Redis to prevent reset from Dyno refresh

# use @bot.command(hidden=True) to now show in help

# status
#   get delta from start time and time of command invoke
#   output as Xd Xh Xm
#   Check if websocket connection is open and show latency
#   Get bot owner
#   Check connection to API

# flush
#   clear out redis cache
#   owner restricted
