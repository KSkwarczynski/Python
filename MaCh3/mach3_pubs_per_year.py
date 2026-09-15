#!/usr/bin/env python3
"""
Plot number of MaCh3-related publications per year.

Usage:
    python mach3_pubs_per_year.py
"""

import re
from collections import Counter
import subprocess
import sys

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
# Based on the colours and typography of the MaCh3 logo
# ----------------------------------------------------------------------

MACH3_BLUE = "#428BC5"       # Main "MaCh3" blue
MACH3_NAVY = "#002B45"       # Dark navy used in neutrino scribbles
MACH3_RED = "#A6192E"        # Red
MACH3_ORANGE = "#D35400"     # Orange
MACH3_YELLOW = "#FFB511"     # Yellow

mpl.rcParams.update({
    # Typography
    "font.family": "serif",
    "font.serif": [
        "DejaVu Serif",
        "Times New Roman",
        "Times",
    ],

    # General text
    "text.color": MACH3_NAVY,
    "axes.labelcolor": MACH3_NAVY,
    "axes.titlecolor": MACH3_NAVY,

    # Axes
    "axes.edgecolor": MACH3_NAVY,
    "axes.linewidth": 1.2,

    # Ticks
    "xtick.color": MACH3_NAVY,
    "ytick.color": MACH3_NAVY,

    # Grid
    "grid.color": MACH3_NAVY,
    "grid.alpha": 0.18,

    # Figure
    "figure.facecolor": "white",
    "axes.facecolor": "white",

    # Font sizes
    "axes.titlesize": 17,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 11,
})

# ----------------------------------------------------------------------
# Paste / maintain the publication list here
# ----------------------------------------------------------------------

data = """

The DUNE Collaboration. A Bayesian approach to the long-baseline neutrino oscillation sensitivity of DUNE. *arXiv:2608.04059* (2026).
The T2K Collaboration. Constraining Neutrino Interaction Uncertainties for Neutrino Oscillation Measurements at the T2K Experiment. arXiv:2606.14015 (2026)
The T2K Collaboration. Results from the T2K Experiment on Neutrino Mixing Including a New Far Detector μ-like Sample. Phys. Rev. Lett., 135(26), 261801 (2025).
The T2K Collaboration. Testing T2K’s Bayesian constraints with priors in alternate parameterisations. Eur. Phys. J. C, 85(12), 1414 (2025).
The T2K and NOvA Collaborations. Joint neutrino oscillation analysis from the T2K and NOvA experiments. Nature 646, 818-824 (2025).
The T2K and Super-Kamiokande Collaborations. First joint oscillation analysis of Super-Kamiokande atmospheric and T2K accelerator neutrino data. Phys. Rev. Lett., 134(1), 011801 (2025).
The T2K Collaboration. Measurements of neutrino oscillation parameters from the T2K experiment using 3.6×10²¹ protons on target. Eur. Phys. J. C, 83(9), 782 (2023).
The T2K Collaboration. Constraint on the matter–antimatter symmetry-violating phase in neutrino oscillations. Nature 580, 339–344 (2020).
The T2K Collaboration. Search for CP violation in neutrino and antineutrino oscillations by the T2K experiment with 2.2×10²¹ protons on target. Phys. Rev. Lett., 121(17), 171802 (2018).
The T2K Collaboration. Measurement of neutrino and antineutrino oscillations by the T2K experiment including a new additional sample of νₑ interactions at the far detector. Phys. Rev. D, 96(9), 092006 (2017).
The T2K Collaboration. Combined analysis of neutrino and antineutrino oscillations at T2K. Phys. Rev. Lett., 118(15), 151801 (2017).
The T2K Collaboration. Measurement of muon antineutrino oscillations with an accelerator-produced off-axis beam. Phys. Rev. Lett., 116(18), 181801 (2016).
The T2K Collaboration. Measurements of neutrino oscillation in appearance and disappearance channels by the T2K experiment with 6.6×10²⁰ protons on target. Phys. Rev. D, 91(7), 072010 (2015).
The T2K Collaboration. Measurement of Neutrino Oscillation Parameters from Muon Neutrino Disappearance with an Off-axis Beam. Phys. Rev. Lett. 111, 211803 (2013).
"""

# ----------------------------------------------------------------------
# Extract years
# ----------------------------------------------------------------------

years = re.findall(r"\((\d{4})\)", data)
years = list(map(int, years))

# Count publications per year
counts = Counter(years)

# Build continuous year range
min_year = min(counts)
max_year = max(counts)

all_years = list(range(min_year, max_year + 1))
values = [counts.get(y, 0) for y in all_years]

# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(9, 5))

# Main MaCh3-style curve
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

# Add value labels above points
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

# Title / labels
ax.set_title(
    "Number of MaCh3-related Publications per Year",
    pad=15,
    fontweight="bold",
)

ax.set_xlabel("Year", labelpad=8)
ax.set_ylabel("Number of Publications", labelpad=8)

# X-axis
ax.set_xticks(all_years)
ax.tick_params(axis="x", rotation=45)

# Y-axis: integer ticks
ax.set_ylim(bottom=0)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))

# Subtle horizontal grid
ax.grid(
    True,
    axis="y",
    linestyle="--",
    linewidth=0.8,
    alpha=0.18,
)

# Remove top/right spines for a cleaner modern look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Slightly emphasise left/bottom axes
ax.spines["left"].set_linewidth(1.2)
ax.spines["bottom"].set_linewidth(1.2)

# Keep plot compact and balanced
plt.tight_layout()

# ----------------------------------------------------------------------
# Save to PNG
# ----------------------------------------------------------------------

plt.savefig(
    "mach3_publications_per_year.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white",
)

print("Plot saved as mach3_publications_per_year.png")

# ----------------------------------------------------------------------
# Print table
# ----------------------------------------------------------------------

print("\nPublications per year:")
for y in all_years:
    print(f"{y}: {counts.get(y, 0)}")
