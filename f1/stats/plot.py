import logging
import asyncio
import matplotlib.pyplot as plt
import numpy as np

from f1.api import get_all_driver_lap_times
from f1.utils import lap_time_to_seconds


logger = logging.getLogger(__name__)

FIGSIZE = (12, 6)


def plot_data(ax, data1, data2, param_dict):
    """Plot provided data on the Axes.

    Parameters
    ----------
    ax : Axes
        The matplot Axes to draw on
    data1 : array
        The X data to plot
    data2 : array
        The Y data to plot
    param_dict : dict
        Dictionary of kwargs read by ax.plot()
    """
    ax.plot(data1, data2, **param_dict)


async def plot_driver_vs_driver_lap_timings(driver1, driver2, rnd, season):
    """Plot race lap data between two drivers as a line graph.

    Parameters
    ----------
    driver1, driver2 : str
        Valid driver_id e.g. 'alonso', 'di_resta', 'michael_schumacher'
    rnd : int
        The race number in the season
    season : int
        The season to pull data from
    """
    driver1_res, driver2_res = await asyncio.gather(
        get_all_driver_lap_times(driver1, rnd, season),
        get_all_driver_lap_times(driver2, rnd, season),
    )
    laps = np.array([int(x['no']) for x in driver1_res['data']])
    driver1_times = np.array([lap_time_to_seconds(lap['time']) for lap in driver1_res['data']])
    driver2_times = np.array([lap_time_to_seconds(lap['time']) for lap in driver2_res['data']])

    fig = plt.figure(figsize=FIGSIZE)
    plt.plot(laps, driver1_times, figure=fig, label=driver1)
    plt.plot(laps, driver2_times, figure=fig, label=driver2)

    plt.title('Lap Time Comparison')
    plt.xlabel('Laps')
    plt.ylabel('Time (s)')

    plt.savefig('../../fig.png', bbox_inches='tight')
