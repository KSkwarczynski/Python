#!/usr/bin/env python3

"""
MaCh3 Collaboration World Map
"""

from io import BytesIO
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import requests


# =============================================================================
# MEMBERS
# =============================================================================

# This is the only list you need to edit when adding new members.
MEMBER_COUNTRIES = [
    "United Kingdom",
    "Poland",
    "Czech Republic",
    "United States of America",
]


# =============================================================================
# OUTPUT
# =============================================================================

OUTPUT_PNG = "mach3_collaboration_map.png"
OUTPUT_PDF = "mach3_collaboration_map.pdf"


# =============================================================================
# MACH3 COLOURS
# =============================================================================

MACH3_BLUE = "#438BC4"
MACH3_NAVY = "#002B45"

# MaCh3 golden/orange used for the title
MACH3_GOLDEN = "#F5A800"

BACKGROUND = "#FFFFFF"
WORLD_COLOUR = "#E8EEF2"
COUNTRY_EDGE = "#FFFFFF"


# =============================================================================
# NATURAL EARTH MAP DATA
# =============================================================================

WORLD_URL = (
    "https://naturalearth.s3.amazonaws.com/"
    "10m_cultural/ne_10m_admin_0_map_units.zip"
)


# =============================================================================
# COUNTRY NAME ALIASES
# =============================================================================

# Natural Earth may use "Czechia" while the member list uses
# "Czech Republic". This makes both work.

NAME_ALIASES = {
    "Czech Republic": {
        "Czechia",
        "Czech Republic",
    },

    "Czechia": {
        "Czechia",
        "Czech Republic",
    },

    "United States of America": {
        "United States of America",
        "United States",
        "USA",
    },

    "United States": {
        "United States of America",
        "United States",
        "USA",
    },

    "United Kingdom": {
        "United Kingdom",
        "UK",
    },

    "UK": {
        "United Kingdom",
        "UK",
    },

    "Poland": {
        "Poland",
    },
}


def matches_country(row, requested_name):
    """
    Check several Natural Earth fields to make country matching robust.
    """

    allowed_names = NAME_ALIASES.get(
        requested_name,
        {requested_name},
    )

    fields_to_check = [
        "NAME",
        "NAME_EN",
        "ADMIN",
        "SOVEREIGNT",
    ]

    for field in fields_to_check:
        if field in row.index:
            value = row[field]

            if value in allowed_names:
                return True

    return False


# =============================================================================
# LOAD MAP
# =============================================================================

response = requests.get(
    WORLD_URL,
    timeout=30,
)

response.raise_for_status()

world = gpd.read_file(
    BytesIO(response.content)
)


# =============================================================================
# IDENTIFY MEMBER COUNTRIES
# =============================================================================

world["is_member"] = world.apply(
    lambda row: any(
        matches_country(row, country)
        for country in MEMBER_COUNTRIES
    ),
    axis=1,
)


# =============================================================================
# BRITISH OVERSEAS TERRITORIES
#
# All territories whose sovereign state is the United Kingdom are treated
# exactly like MaCh3 members.
#
# There is deliberately NO separate territory colour or hatch.
# =============================================================================

if "SOVEREIGNT" in world.columns:

    world["is_british"] = (
        world["SOVEREIGNT"] == "United Kingdom"
    )

    world["is_member"] = (
        world["is_member"]
        | world["is_british"]
    )


# =============================================================================
# REMOVE INTERNAL UK BORDERS
#
# Natural Earth map units can contain England, Scotland, Wales, etc.
# We want the whole UK to visually read as ONE country.
#
# We therefore create a separate dissolved UK geometry for plotting.
# =============================================================================

uk_parts = world[
    world["SOVEREIGNT"] == "United Kingdom"
]

non_uk = world[
    world["SOVEREIGNT"] != "United Kingdom"
].copy()


if not uk_parts.empty:

    # Dissolve all British components into one geometry.
    uk_dissolved = uk_parts.dissolve()

    # British territories remain part of the same MaCh3 member fill.
    uk_dissolved["is_member"] = True

else:
    uk_dissolved = gpd.GeoDataFrame(
        columns=world.columns,
        geometry=[],
        crs=world.crs,
    )


# =============================================================================
# NON-UK MEMBERS
# =============================================================================

non_uk_members = non_uk[
    non_uk["is_member"]
]


# =============================================================================
# FIGURE
# =============================================================================

fig, ax = plt.subplots(
    figsize=(16, 9),
    facecolor=BACKGROUND,
)

ax.set_facecolor(BACKGROUND)


# =============================================================================
# BASE WORLD MAP
# =============================================================================

non_uk.plot(
    ax=ax,
    color=WORLD_COLOUR,
    edgecolor=COUNTRY_EDGE,
    linewidth=0.35,
)


# =============================================================================
# UK AS ONE UNIFIED SHAPE
# =============================================================================

if not uk_dissolved.empty:

    uk_dissolved.plot(
        ax=ax,
        color=MACH3_BLUE,
        edgecolor=MACH3_NAVY,
        linewidth=0.9,
    )


# =============================================================================
# OTHER MACH3 MEMBERS
# =============================================================================

non_uk_members.plot(
    ax=ax,
    color=MACH3_BLUE,
    edgecolor=MACH3_NAVY,
    linewidth=0.9,
)


# =============================================================================
# TITLE
# =============================================================================

ax.text(
    0.5,
    0.955,
    "MaCh3 collaboration",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=30,
    fontweight="bold",
    color=MACH3_GOLDEN,
)


# =============================================================================
# MAP LIMITS
# =============================================================================

ax.set_xlim(-180, 180)
ax.set_ylim(-58, 88)


# =============================================================================
# CLEAN AXES
# =============================================================================

ax.axis("off")


# =============================================================================
# SAVE
# =============================================================================

plt.savefig(
    OUTPUT_PNG,
    dpi=400,
    bbox_inches="tight",
    facecolor=BACKGROUND,
)

plt.savefig(
    OUTPUT_PDF,
    bbox_inches="tight",
    facecolor=BACKGROUND,
)


# =============================================================================
# DISPLAY
# =============================================================================

plt.show()
