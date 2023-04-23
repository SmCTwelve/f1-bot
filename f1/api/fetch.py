"""
Perform asyncronous web requests.
"""
import aiohttp
import logging

SESSION_TIMEOUT = 120

logger = logging.getLogger(__name__)


def is_xml(res): return 'application/xml' in res.content_type


def is_json(res): return 'application/json' in res.content_type


async def send_request(session, url):
    """Attempt to request the URL. Returns content of the Response if successful or None."""
    logger.info('GET {}'.format(url))
    # open connection context, all response handling must be within
    async with session.get(url) as res:
        logger.info('Response HTTP/{}'.format(res.status))
        if res.status != 200:
            logger.warning('Problem fetching request. Failed with HTTP/{} {}'.format(res.status, res.reason))
            return None
        # check response type, file streaming should be handled seperately
        else:
            if is_xml(res):
                content = await res.read()
            elif is_json(res):
                content = await res.json()
            else:
                content = await res.text()
            return content


async def fetch(url):
    """Request the url and await response. Returns response content or None."""
    tmout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=tmout) as session:
            res = await send_request(session, url)
            return res
    except aiohttp.ClientError as e:
        logger.error(e)
        return None
