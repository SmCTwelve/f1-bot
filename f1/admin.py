"Administrative commands to manage the bot."
import logging
import time
from discord import Colour
from discord.embeds import Embed

from f1.api import check_status
from f1.commands import bot

logger = logging.getLogger(__name__)

# set global time bot started
# store the time as persist in Redis to prevent reset from Dyno refresh
START_TIME = time.time()

# use @bot.command(hidden=True) to not show in help


def get_uptime():
    """Get running time since bot started. Return tuple (days, hours, minutes)."""
    invoke_time = time.time()
    uptime = invoke_time - START_TIME
    days, rem = divmod(uptime, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    return (int(days), int(hours), int(mins), int(secs))


@bot.command()
async def status(ctx, *args):
    """Get the bot status including uptime, API connection, latency and owner."""
    uptime = get_uptime()
    api_status = await check_status()
    app_info = await bot.application_info()
    latency = int(bot.latency * 1000)

    if api_status == 0:
        api_txt = "```glsl\nDown\n```"
    elif api_status == 1:
        api_txt = "```yaml\nGood\n```"
    else:
        api_txt = "```fix\nSlow\n```"

    if bot.is_closed():
        ws_conn = "```glsl\nClosed\n```"
    else:
        ws_conn = "```yaml\nOpen\n```"

    embed = Embed(
        title=f"Status - {app_info.name}",
        description=f"{app_info.description}",
        url="https://github.com/SmCTwelve/f1-bot",
        colour=Colour.teal()
    )
    embed.set_thumbnail(url=app_info.icon_url or "https://i.imgur.com/kvZYOue.png")
    embed.add_field(name='Owner', value=app_info.owner.name, inline=True)
    embed.add_field(name='Source', value="[GitHub](https://github.com/SmCTwelve/f1-bot)", inline=True)
    embed.add_field(name='Ping', value=f'{latency} ms', inline=True)
    embed.add_field(name='Uptime', value=f'{uptime[0]}d, {uptime[1]}h, {uptime[2]}m', inline=True)
    embed.add_field(
        name='Websocket',
        value=ws_conn,
        inline=True
    )
    embed.add_field(name='API Connection', value=api_txt, inline=True)
    await ctx.send(embed=embed)

# stop - owner
# reload - admin

# flush
#   clear out redis cache
#   owner restricted
