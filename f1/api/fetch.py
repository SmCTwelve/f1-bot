"""
Perform asyncronous web requests.
"""
import logging
from datetime import timedelta

import aiohttp
from aiohttp_client_cache import CachedSession, SQLiteBackend

from f1.config import CACHE_DIR

BASE_URL = 'http://ergast.com/api/f1'
SESSION_TIMEOUT = 120

logger = logging.getLogger(__name__)

# Disable caching e.g. for testing
use_cache = True

cache = SQLiteBackend(
    cache_name=f"{CACHE_DIR}/fetch_aiohttp_cache.sqlite",
    expire_after=timedelta(days=2),
    urls_expire_after={
        f"{BASE_URL}/drivers": timedelta(weeks=1),
        f"{BASE_URL}/drivers/*": 3600,
        f"{BASE_URL}/current/last/*": 600,
        f"{BASE_URL}/current/next": 600,
    },
    allowed_methods=("GET", "POST"),
)


def _is_xml(res): return 'application/xml' in res.content_type


def _is_json(res): return 'application/json' in res.content_type


async def _send_request(session, url):
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
            if _is_xml(res):
                content = await res.read()
            elif _is_json(res):
                content = await res.json()
            else:
                content = await res.text()
            return content


async def fetch(url):
    """Request the url and await response. Returns response content or None."""
    tmout = aiohttp.ClientTimeout(total=SESSION_TIMEOUT)
    try:
        async with CachedSession(cache=cache, timeout=tmout) as session:
            if use_cache:
                return await _send_request(session, url)

            # Temporarily disable cache for this request
            async with session.disabled():
                uncached_res = await _send_request(session, url)
                return uncached_res

    except aiohttp.ClientError as e:
        logger.error(e)
        return None
