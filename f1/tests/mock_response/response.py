"""Mock test responses from Ergast API."""
from . import models

# Possible responses
responses = {
    'driver_standings': models.driver_standings,
    'constructor_standings': models.constructor_standings,
    'driver_info': models.driver_info,
    'grid': models.grid,
    'race_schedule': models.race_schedule,
    'race_results': models.race_results,
    'qualifying_results': models.qualifying_results,
    'driver_wins': models.driver_wins,
    'driver_poles': models.driver_poles,
    'driver_championships': models.driver_championships,
    'driver_seaons': models.driver_seasons,
    'driver_teams': models.driver_teams,
}


def generate_res(body):
    """Wraps `body` in XML parent tags to mirror API response."""
    return f'<?xml version="1.0" encoding="utf-8"?><MRData total="30">{body}</MRData>'


async def get_mock_response(res_type):
    """Generates a mock XML response string as received from API.

    Returns a mock XML string of the expected response which matches the `res_type`
    or None if no match found to simulate missing data.

    Parameters
    -----------
    res_type : str
        Type of API response expected:
            - 'driver_standings'
            - 'constructor_standings'
            - 'driver_info'
            - 'grid' (all drivers and teams)
            - 'race_schedule'
            - 'race_results'
            - 'qualifying_results'
            - 'driver_career'
            - 'driver_wins'
            - 'driver_poles'
            - 'driver_championships'
            - 'driver_seasons'
            - 'driver_teams'
    """
    return responses.get(res_type, None)
