import os
import asyncio
from discord.ext import commands

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print('Bot ready')


@bot.event
async def on_message(message):
    print('Message:', message)


@bot.command
async def ping(ctx):
    '''Display the current latency.'''
    await ctx.send(bot.latency)


bot.run(os.getenv('BOT_TOKEN'))
