'''
Perform asyncronous web requests.
'''
import aiohttp


async def check_response(response):


async def send_request(session, url):
    '''Request the url and await response.'''
    async with session.get(url) as resp:
        print(resp.status)
        return await resp.text()


async def fetch(url):
    async with aiohttp.ClientSession() as session:
        response = await send_request(session, url)

# use discord.py event loop, simply await functions from here
