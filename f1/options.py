"Slash command parameter options."

from discord import Option

RankedPitstopFilter = Option(str, choices=["Best", "Worst", "Ranked"], default="Ranked")

DriverOption = Option(str, default=None, description="Driver number, 3-letter code or surname")

SectorFilter = Option(
    str,
    choices=["Time", "Speed"],
    description="The type of data to show",
    required=True
)

LaptimeFilter = Option(
    str,
    choices=["Fastest", "Slowest", "Top 5", "Bottom 5", "Ranked"],
    default="Ranked")

SeasonOption = Option(
    str,
    default="current",
    description="The season year. Leave blank for the current season")

RoundOption = Option(
    str,
    default="last",
    description="The race name, location or round number. Default is lastest")

SessionOption = Option(
    str,
    choices=[
        "Practice 1",
        "Practice 2",
        "Practice 3",
        "Qualifying",
        "Sprint",
        "Sprint Shootout",
        "Race"
    ],
    default="Race",
    description="The session to view")
