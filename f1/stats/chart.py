import logging
import asyncio
import matplotlib.pyplot as plt
import numpy as np

from f1.api import get_all_driver_lap_times

logger = logging.getLogger(__name__)


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
    laps = np.array([x['no'] for x in driver1_res['data']])
    driver1_data = np.array([x['time'] for x in driver1_res['data']])
    driver2_data = np.array([x['time'] for x in driver2_res['data']])

    # TODO:
    #   Parse laptime strs as time/datetime
    #   Convert to seconds to plt on Y

    fig, ax = plt.subplots(1, 1)
