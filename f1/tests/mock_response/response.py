"""Mock test responses from Ergast API."""
from . import models

# Possible responses
responses = {
    'driver_standings': models.driver_standings,
    'constructor_standings': models.constructor_standings,
    'driver_info_xml': models.driver_info_xml,
    'grid': models.grid,
    'race_schedule': models.race_schedule,
    'race_results': models.race_results,
    'qualifying_results': models.qualifying_results,
    'driver_wins': models.driver_wins,
    'driver_poles': models.driver_poles,
    'driver_championships': models.driver_championships,
    'driver_seaons': models.driver_seasons,
    'driver_teams': models.driver_teams,
    'all_laps': models.all_laps,
    'driver1_laps': models.driver1_laps,
    'driver2_laps': models.driver2_laps,
    'driver_seasons': models.driver_seasons,
    'best_laps': models.best_laps,
    'pitstops': models.pitstops,
    'all_standings_for_driver': models.all_standings_for_driver,
}


def generate_res(body):
    """Wraps `body` in XML parent tags to mirror API response."""
    return f'<?xml version="1.0" encoding="utf-8"?><MRData total="1">{body}</MRData>'


def get_mock_response(res_type):
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
            - 'all_laps'
            - 'driver1_laps'
            - 'driver2_laps'
            - 'best_laps'
            - 'pitsops'
            - 'all_standings_for_driver'
    """
    if res_type is None:
        return None
    return generate_res(responses.get(res_type, ''))
