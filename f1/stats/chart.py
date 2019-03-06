import logging
import matplotlib.pyplot as plt
import numpy as np

import f1.config as cfg
from f1.utils import lap_time_to_seconds


logger = logging.getLogger(__name__)

FIGSIZE = (12, 6)


def save_figure(fig, path=cfg.OUT_DIR, name='plot.png'):
    """Save the figure as a file."""
    fig.savefig(f'{path}/{name}', bbox_inches='tight')


async def plot_all_driver_laps(driver_laps):
    """Plot all race lap times for the driver as a line graph and output a file.

    Parameters
    ----------
    `driver_laps` : dict
        The dict returned by `api.get_all_driver_lap_times()`.
    """
    # Get data arrays
    times = np.array([lap_time_to_seconds(lap['Time']) for lap in driver_laps['data']])
    laps = np.array([int(x['No']) for x in driver_laps['data']])

    # Plot data
    fig = plt.figure(figsize=FIGSIZE)
    plt.plot(laps, times, figure=fig, label=driver_laps['driver']['code'])

    plt.title(f"Lap Times {driver_laps['race']} ({driver_laps['season']})")
    plt.xlabel("Lap")
    plt.ylabel("Time (s)")
    plt.ylim(bottom=50.0)
    plt.legend()

    save_figure(fig)


async def plot_driver_vs_driver_lap_timings(driver1_laps, driver2_laps):
    """Plot race lap data between two drivers as a line graph and output file.

    Parameters
    ----------
    `driver1_laps`, `driver2_laps` : dict
        Return dict from `api.get_all_driver_lap_times`
    """
    # Get data arrays for plot
    race, sn = driver1_laps['race'], driver1_laps['season']
    laps = np.array([int(x['No']) for x in driver1_laps['data']])
    driver1_times = np.array([lap_time_to_seconds(lap['Time']) for lap in driver1_laps['data']])
    driver2_times = np.array([lap_time_to_seconds(lap['Time']) for lap in driver2_laps['data']])

    # Create plot
    fig = plt.figure(figsize=FIGSIZE)
    plt.plot(laps, driver1_times, figure=fig, label=driver1_laps['driver']['code'])
    plt.plot(laps, driver2_times, figure=fig, label=driver2_laps['driver']['code'])

    plt.title(f"Lap Time Comparison {race} ({sn})")
    plt.xlabel('Lap')
    plt.ylabel('Time (s)')
    plt.ylim(bottom=50.0)
    plt.legend()

    save_figure(fig)


async def plot_best_laps(timings):
    """Plot each driver's best lap in as a bar chart and output a file.

    `timings` : dict
        Return value of `api.get_best_laps`
    """
    race, sn = timings['race'], timings['season']
    drivers = [x['Driver'] for x in timings['data']]
    times = [lap_time_to_seconds(x['Time']) for x in timings['data']]

    fig = plt.figure(figsize=FIGSIZE)
    y_pos = np.arange(len(drivers))
    plt.barh(y_pos, times, figure=fig, align='center')

    plt.title(f"Best Laps Per Driver {race} ({sn})")
    plt.ylabel('Drivers')
    plt.yticks(y_pos, labels=drivers)
    plt.xlabel('Time (s)')
    plt.xlim(left=min(times) - 2)
    plt.grid(True, axis='x')

    save_figure(fig)
