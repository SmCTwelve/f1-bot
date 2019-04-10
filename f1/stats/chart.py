import logging
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
from cycler import cycler
from operator import itemgetter

import f1.config as cfg
from f1.utils import lap_time_to_seconds, filter_laps_by_driver
from f1.api import get_driver_info

logger = logging.getLogger(__name__)

FIGSIZE = (12, 6)

# COLOR MAPS
colors = [
    '#c06c84', '#6c5b7b', '#acc6aa', '#71a0a5', '#7C90A0', '#e9b44c', '#9b2915', '#bf4342',
    '#98b06f', '#33658a', '#79cdc9', '#a29c9b', '#442b48', '#f26c4f', '#ddcc5a', '#6457a6',
    '#806443', '#7c90a0', '#eba07b', '#86bbd8', '#1A936F', '#2F4550',
]

colors1 = ['#588B8B', '#E9B44C', '#9B2915', '#442B48', '#98B06F']

colors2 = ['#6DD3CE', '#C8E9A0', '#F7A278', '#A13D63', '#351E29']

colors3 = ['#c06c84', '#6c5b7b', '#acc6aa', '#71a0a5']

colors4 = ['#c06c84', '#86BBD8', '#33658A', '#acc6aa', '#F26419']

warm = ['#4F000B', '#720026', '#CE4257', '#FF7F51', '#FF9B54']

# Set default color cycler for plot instances e.g. stacked bars
plt.rcParams['axes.prop_cycle'] = cycler(color=colors)


def save_figure(fig, path=cfg.OUT_DIR, name='plot.png'):
    """Save the figure as a file."""
    fig.savefig(os.path.join(path, name), bbox_inches='tight')
    logger.info(f"Figure saved at {os.path.join(path, name)}")


def plot_all_driver_laps(lap_timings):
    """Plot all race lap times for the driver(s) as a line graph and output a file.

    Parameters
    ----------
    `lap_timings` : dict
        The dict returned by `api.get_all_laps_for_driver()`
        or filtered laps from `utils.filter_laps_by_driver()`.
    """
    # Get data arrays
    laps = np.array(list(lap_timings['data'].keys()), int)
    # Get all the drivers from the first lap
    drivers = [x['id'] for x in lap_timings['data'][1]]

    # Plot data
    fig = plt.figure(figsize=FIGSIZE)

    # Reshape data from per lap to per driver
    # Get each driver:value pair
    for i, driver in enumerate(drivers, 0):
        driver_info = get_driver_info(driver)
        # Get only the data for current driver
        filtered_laps = filter_laps_by_driver(lap_timings, [driver])
        # Get the times for each lap and convert to seconds
        # or fill with 0 if there is no data for that lap (e.g. retired)
        times = np.array([
            lap_time_to_seconds(lap[0]['Time']) if lap else None
            for lap in filtered_laps['data'].values()
        ], object)
        # Plot the drivers lap times
        plt.plot(laps, times, figure=fig, label=driver_info['code'])

    plt.title(f"Lap Times {lap_timings['race']} ({lap_timings['season']})")
    plt.xlabel("Lap")
    plt.ylabel("Time (s)")
    plt.grid(axis='y')
    plt.legend(bbox_to_anchor=(1, 1), loc='upper left')

    save_figure(fig, name='plot_laps.png')


def plot_race_pos(lap_timings):
    """Plot line graph visualising race position change per driver.

    `lap_timings` : dict
        lap:timings pairs for each lap and driver, respectively, as returned by `api.get_all_laps`
        or filtered laps from `utils.filter_laps_by_driver()`.
    """
    laps = np.array(list(lap_timings['data'].keys()), int)
    # Get all the drivers from the first lap
    drivers = [x['id'] for x in lap_timings['data'][1]]

    fig = plt.figure(figsize=FIGSIZE)

    # Reshape data from per lap to per driver
    # Get each driver:value pair
    for i, driver in enumerate(drivers, 0):
        driver_info = get_driver_info(driver)
        # Get only the data for current driver
        filtered_laps = filter_laps_by_driver(lap_timings, [driver])
        # Add the race pos per lap to the list of positions for the current driver
        positions = np.array([
            int(x[0]['Pos']) if x else None
            for x in filtered_laps['data'].values()
        ], dtype=object)
        # Plot the drivers positions
        plt.plot(laps, positions, figure=fig, label=driver_info['code'])

    plt.title(f"Race position - {lap_timings['race']} ({lap_timings['season']})")
    plt.xlabel('Lap')
    plt.yticks(np.arange(1, len(drivers)))
    plt.ylabel('Position')
    plt.gca().invert_yaxis()
    plt.gca().tick_params(axis='y', right=True, left=True, labelleft=True, labelright=True)
    plt.legend(title='Drivers', bbox_to_anchor=(-0.05, 1.04), loc='upper right')

    save_figure(fig, name='plot_pos.png')


def plot_best_laps(timings):
    """Plot each driver's best lap in as a bar chart and output a file.

    `timings` : dict
        Return value of `api.get_best_laps`
    """
    race, sn = timings['race'], timings['season']
    drivers = [x['Driver'] for x in timings['data']]
    times = [lap_time_to_seconds(x['Time']) for x in timings['data']]

    fig = plt.figure(figsize=FIGSIZE)
    y_pos = np.arange(len(drivers))
    plt.barh(y_pos, times, figure=fig, height=0.5, align='center')

    plt.title(f"Best Laps Per Driver {race} ({sn})")
    plt.ylabel('Drivers')
    plt.yticks(y_pos, labels=drivers)
    plt.gca().invert_yaxis()
    plt.xlabel('Time (s)')
    plt.xlim(left=min(times) - 1, right=max(times) + 1)
    plt.gca().get_xaxis().set_minor_locator(AutoMinorLocator())
    plt.grid(True, axis='x')

    save_figure(fig, name='plot_fastest.png')


def plot_pitstops(stops):
    """Plot each driver pitstop in the race.

    `stops` : dict
        Return value of `api.get_pitstops`
    """
    race, season = stops['race'], stops['season']

    # sort the dataset so plots are stacked in order of stop number
    # y-axis, labels and plots should follow the order of the sorted data
    ordered_stops = sorted(stops['data'], key=itemgetter('Stop_no'))

    # get max number of stops and laps of race
    total_stints = max([s['Stop_no'] for s in ordered_stops])
    total_laps = int(stops['total_laps'])

    stint_labels = []

    # remove driver repetitions for labels and y-axis
    drivers = []
    for stop in ordered_stops:
        if stop['Driver'] not in drivers:
            drivers.append(stop['Driver'])

    # get y-axis index positions for the data
    rows = np.arange(len(drivers))

    # store previous stop lap for each driver to calculate stint length and
    # x-pos to place next bar segment
    prev_stops = np.zeros(len(rows), int)

    fig = plt.figure(figsize=FIGSIZE)

    # Drivers whose stints should not be updated on further iterations, e.g.
    # if a driver has no more stops, further loop iterations should skip them
    not_to_update = []

    # Loop over drivers and stops, plot the stint lengths as bar segment
    stop_num = 1
    while stop_num <= total_stints:
        stint_labels.append(f"Stint {stop_num}")
        # Store stint lenghts as zeros and update the index per driver
        # Stint length is current stop lap - previous stop lap, or finish lap if no more stints
        stint_lengths = np.zeros(len(rows), int)
        # Temp store the stop laps for each driver to update prev_stops with the new stop lap,
        # or keep the old one if the driver did not stop
        stop_laps = np.array(prev_stops, int)

        # Iterate drivers and stops
        for i, d in enumerate(drivers, 0):
            # Check if driver should be skipped
            if d not in not_to_update:
                found = False
                for s in ordered_stops:
                    # Update the stint length for the driver if they stopped
                    if s['Stop_no'] == stop_num and s['Driver'] == d:
                        found = True
                        stint_lengths[i] = s['Lap'] - prev_stops[i]
                        stop_laps[i] = s['Lap']
                # Driver had no more stops, so stint length should be to end of race
                # and driver skipped on next iteration
                if not found or stop_num == total_stints:
                    stint_lengths[i] = total_laps - prev_stops[i]
                    not_to_update.append(d)
        # Plot next bar segment for each driver
        plt.barh(rows, stint_lengths, height=0.5, left=prev_stops, align='center', figure=fig)
        # Update previous stop laps and increment stop number
        prev_stops = np.array(stop_laps, int)
        stop_num += 1

    plt.title(f"Pit stops - {race} ({season})")
    plt.ylabel('Driver')
    plt.yticks(rows, labels=drivers)
    plt.xlabel('Lap')
    plt.xticks(np.arange(0, total_laps, 10))
    plt.gca().get_xaxis().set_minor_locator(AutoMinorLocator())
    plt.grid(True, which='major', axis='x')
    plt.legend(stint_labels, bbox_to_anchor=(1, 1), loc='upper left')

    save_figure(fig, name='plot_pitstops.png')
