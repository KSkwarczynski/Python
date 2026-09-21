#!/usr/bin/env python3
"""
Plot number of MaCh3-related publications per year.

The publication list is automatically downloaded from the
MaCh3 GitHub Wiki, so no manual publication list is required.

Usage:
    python mach3_pubs_per_year.py
"""

import re
import subprocess
import sys
from collections import Counter
from urllib.request import Request, urlopen

# Attempt to import matplotlib, install if not found
try:
    import matplotlib.pyplot as plt
    import matplotlib as mpl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt
    import matplotlib as mpl

from matplotlib.ticker import MaxNLocator


# ----------------------------------------------------------------------
# MaCh3-inspired style
# ----------------------------------------------------------------------

MACH3_BLUE = "#428BC5"
MACH3_NAVY = "#002B45"
MACH3_RED = "#A6192E"
MACH3_ORANGE = "#D35400"
MACH3_YELLOW = "#FFB511"

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": [
        "DejaVu Serif",
        "Times New Roman",
        "Times",
    ],

    "text.color": MACH3_NAVY,
    "axes.labelcolor": MACH3_NAVY,
    "axes.titlecolor": MACH3_NAVY,

    "axes.edgecolor": MACH3_NAVY,
    "axes.linewidth": 1.2,

    "xtick.color": MACH3_NAVY,
    "ytick.color": MACH3_NAVY,

    "grid.color": MACH3_NAVY,
    "grid.alpha": 0.18,

    "figure.facecolor": "white",
    "axes.facecolor": "white",

    "axes.titlesize": 17,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 11,
})


# ----------------------------------------------------------------------
# MaCh3 Wiki
# ----------------------------------------------------------------------

WIKI_URL = (
    "https://raw.githubusercontent.com/wiki/"
    "mach3-software/MaCh3/14.-MaCh3-in-the-Field.md"
)


def fetch_publications():
    """
    Download the MaCh3 Wiki page and extract publications.

    Returns
    -------
    publications : list of dict
        Each entry contains:
            author
            title
            year
            raw
    """

    print("Downloading MaCh3 publication list...")
    print(WIKI_URL)

    request = Request(
        WIKI_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (MaCh3 publication plotter)"
        },
    )

    with urlopen(request, timeout=20) as response:
        text = response.read().decode("utf-8")

    # --------------------------------------------------------------
    # Locate the Publications section
    # --------------------------------------------------------------

    start_match = re.search(
        r"^# Publications using MaCh3\s*$",
        text,
        re.MULTILINE,
    )

    if not start_match:
        raise RuntimeError(
            "Could not find '# Publications using MaCh3' "
            "in the MaCh3 Wiki."
        )

    start = start_match.end()

    # Stop at the next major heading, which is currently
    # "# Theses using MaCh3".
    end_match = re.search(
        r"^# Theses using MaCh3\s*$",
        text[start:],
        re.MULTILINE,
    )

    if end_match:
        end = start + end_match.start()
    else:
        end = len(text)

    publications_section = text[start:end]

    # --------------------------------------------------------------
    # Extract publication entries
    # --------------------------------------------------------------

    publications = []

    for line in publications_section.splitlines():

        line = line.strip()

        # Publication entries are Markdown bullet points.
        if not line.startswith("* "):
            continue

        entry = line[2:].strip()

        # Extract year. The Wiki currently uses (**2026**), etc.
        year_match = re.search(r"\((?:\*\*)?(\d{4})(?:\*\*)?\)", entry)

        if not year_match:
            continue

        year = int(year_match.group(1))

        # Remove Markdown formatting.
        clean = entry

        # Remove Markdown links but preserve their text.
        clean = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            clean,
        )

        # Remove emphasis markers.
        clean = clean.replace("**", "")
        clean = clean.replace("*", "")

        # ----------------------------------------------------------
        # Split author and publication title.
        #
        # The Wiki format is approximately:
        #
        # The T2K Collaboration. Publication title. Journal...
        #
        # ----------------------------------------------------------

        author = ""
        title = clean

        parts = clean.split(". ", 1)

        if len(parts) == 2:
            author = parts[0].strip()
            title_and_rest = parts[1].strip()

            # Try to identify where the journal/reference begins.
            #
            # This is deliberately conservative. If we cannot
            # confidently identify it, keep the whole text.
            title = title_and_rest

            # Common journal/reference patterns.
            journal_patterns = [
                r"\.\s+arXiv:",
                r"\.\s+Phys\.",
                r"\.\s+Eur\.",
                r"\.\s+Nature\s",
                r"\.\s+JHEP",
                r"\.\s+J\.",
                r"\.\s+Prog\.",
                r"\.\s+Nucl\.",
                r"\.\s+Rev\.",
            ]

            positions = []

            for pattern in journal_patterns:
                match = re.search(pattern, title_and_rest)
                if match:
                    positions.append(match.start() + 1)

            if positions:
                title = title_and_rest[:min(positions)].strip()

        # Clean up any remaining year from the title.
        title = re.sub(
            r"\s*\((?:\*\*)?\d{4}(?:\*\*)?\)\s*$",
            "",
            title,
        ).strip()

        publications.append({
            "author": author,
            "title": title,
            "year": year,
            "raw": entry,
        })

    if not publications:
        raise RuntimeError(
            "No publications were found. "
            "The structure of the MaCh3 Wiki may have changed."
        )

    return publications


# ----------------------------------------------------------------------
# Download publication list
# ----------------------------------------------------------------------

publications = fetch_publications()


# ----------------------------------------------------------------------
# Print what was found
# ----------------------------------------------------------------------

print()
print(f"Found {len(publications)} publications.")
print()

print("Publications found:")
print("-" * 80)

for pub in publications:
    print(f"{pub['year']}: {pub['title']}")

print("-" * 80)


# ----------------------------------------------------------------------
# Count publications per year
# ----------------------------------------------------------------------

years = [pub["year"] for pub in publications]

counts = Counter(years)

min_year = min(counts)
max_year = max(counts)

all_years = list(range(min_year, max_year + 1))
values = [counts.get(year, 0) for year in all_years]


# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    all_years,
    values,
    color=MACH3_BLUE,
    linewidth=3.0,
    marker="o",
    markersize=7,
    markerfacecolor="white",
    markeredgecolor=MACH3_BLUE,
    markeredgewidth=2.0,
    zorder=3,
)


# ----------------------------------------------------------------------
# Add value labels
# ----------------------------------------------------------------------

for year, value in zip(all_years, values):

    if value > 0:
        ax.annotate(
            str(value),
            (year, value),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=MACH3_NAVY,
        )


# ----------------------------------------------------------------------
# Title / labels
# ----------------------------------------------------------------------

ax.set_title(
    "Number of MaCh3-related Publications per Year",
    pad=15,
    fontweight="bold",
)

ax.set_xlabel(
    "Year",
    labelpad=8,
)

ax.set_ylabel(
    "Number of Publications",
    labelpad=8,
)


# ----------------------------------------------------------------------
# X-axis
# ----------------------------------------------------------------------

ax.set_xticks(all_years)
ax.tick_params(
    axis="x",
    rotation=45,
)


# ----------------------------------------------------------------------
# Y-axis
# ----------------------------------------------------------------------

ax.set_ylim(bottom=0)

ax.yaxis.set_major_locator(
    MaxNLocator(integer=True)
)


# ----------------------------------------------------------------------
# Grid
# ----------------------------------------------------------------------

ax.grid(
    True,
    axis="y",
    linestyle="--",
    linewidth=0.8,
    alpha=0.18,
)


# ----------------------------------------------------------------------
# Spines
# ----------------------------------------------------------------------

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.spines["left"].set_linewidth(1.2)
ax.spines["bottom"].set_linewidth(1.2)


# ----------------------------------------------------------------------
# Layout
# ----------------------------------------------------------------------

plt.tight_layout()


# ----------------------------------------------------------------------
# Save
# ----------------------------------------------------------------------

output_file = "mach3_publications_per_year.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
)

print()
print(f"Plot saved as {output_file}")


# ----------------------------------------------------------------------
# Print table
# ----------------------------------------------------------------------

print()
print("Publications per year:")
print()

for year in all_years:
    print(f"{year}: {counts.get(year, 0)}")
