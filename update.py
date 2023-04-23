import os
import sys
import json
import logging
import asyncio

from f1.api.ergast import get_all_drivers
from f1.config import CACHE_DIR
from f1.errors import MissingDataError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(name)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


async def update_drivers():
    # attempt to download new driver data
    try:
        logger.info('Fetching new drivers...')
        data = await get_all_drivers()
    except MissingDataError:
        logger.error('Could not download driver data; check API status. Exiting.')
        sys.exit(0)

    # check if file exists
    if os.path.isfile(f'{CACHE_DIR}/drivers.json'):
        logger.info('Backing up old driver data...')
        os.replace(f'{CACHE_DIR}/drivers.json', f'{CACHE_DIR}/drivers_old.json')

    # save new data
    with open(f'{CACHE_DIR}/drivers.json', 'w') as f:
        json.dump(data, f)
        logger.info('Drivers updated successfully!')

asyncio.run(update_drivers())
