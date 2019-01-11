'''
Perform asyncronous web requests.
'''
import aiohttp
import logging

SESSION_TIMEOUT = 30

logger = logging.getLogger(__name__)


async def send_request(session, url):
    '''Attempt to request the URL. Returns response object if successful.'''
    logger.info('GET {}'.format(url))
    async with session.get(url) as res:
        logger.info('Response HTTP/{}'.format(res.status))
        if res.status == 200:
            return res
        else:
            logger.warn('Problem fetching request. Failed with HTTP/{} {}'.format(res.status, res.reason))
            return None


async def fetch(url):
    '''Request the url and await response.'''
    tmout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=tmout) as session:
            res = await send_request(session, url)
            return await res.text()
    except aiohttp.ClientError as e:
        logger.error(e)
        return None
