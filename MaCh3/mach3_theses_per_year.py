#!/usr/bin/env python3
"""
Plot number of MaCh3-related PhD theses per year.

Usage:
    python mach3_theses_per_year.py
"""

import re
from collections import Counter
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Paste / maintain the thesis list here (one entry per line)
# ----------------------------------------------------------------------
data = """
Michael Reh, Analysis of Detector Systematic Uncertainties..., (2025)
Liban Warsame, First Bayesian neutrino oscillation analysis of DUNE, (2025)
Tailin Zhu, Measurement of neutrino oscillation parameters..., (2025)
Menai Lamers James, Development of a boosted decision tree..., (2025)
Andres Lopez Moreno, Reparametrisations of the leptonic mixing matrix..., (2025)
Yashwanth S Prabhu, Expanded νe CC1π+ sample selection..., (2025)
Henry Wallace, Analysis of Neutrino Oscillations..., (2025)
Ewan Miller, Constraining the Flux and Cross Section..., (2025)
Thomas Holvey, New measurements of neutrino oscillation parameters..., (2025)
Alex Carter, Constraining systematic uncertainties..., (2024)
Nauman Akhlaq, Developing the T2K Neutrino Oscillation Analysis..., (2023)
Evan Arthur Gerald Goodman, Combining T2K With Other Experiments..., (2023)
Kamil Skwarczynski, Constraining neutrino cross-section..., (2023)
Charles Naseby, Understanding the impact..., (2023)
Ed Atkin, Neutrino Oscillation Analysis at T2K..., (2023)
Dan Barrow, The sensitivity to oscillation parameters..., (2022)
Artur Sztuc, Standard and non-standard neutrino-antineutrino..., (2021)
Kevin Wood, Measurement of Neutrino Oscillation Parameters..., (2021)
Will Parker, Constraining Systematic Uncertainties at T2K..., (2020)
Tomoyo Yoshida, A study of single charged-pion production..., (2020)
Clarence Wret, Minimising Systematic Uncertainties..., (2019)
Xiaoyue Li, A Joint Analysis of T2K Beam Neutrino..., (2018)
Leïla Haegel, Measurement Of Neutrino Oscillation Parameters..., (2018)
Elder Pinzon, Measurement of Pion-Carbon Cross Sections..., (2018)
Kirsty Duffy, Measurement of the neutrino oscillation parameters..., (2016)
Patrick de Perio, Joint Three-Flavour Oscillation Analysis..., (2014)
Richard Calland, A 3 flavour joint near and far detector neutrino oscillation analysis..., (2014)
Casey Bojechko, Simultaneous Analysis of Near and Far Detector..., (2013)
"""

# ----------------------------------------------------------------------
# Extract years
# ----------------------------------------------------------------------
years = re.findall(r"\((\d{4})\)", data)
years = list(map(int, years))

# Count theses per year
counts = Counter(years)

# Build continuous year range
min_year = min(counts)
max_year = max(counts)
all_years = list(range(min_year, max_year + 1))
values = [counts.get(y, 0) for y in all_years]

# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------
plt.figure(figsize=(8, 4.5))
plt.plot(all_years, values, marker="o")

plt.title("Number of PhD Theses Using MaCh3 per Year")
plt.xlabel("Year")
plt.ylabel("Number of Theses")

plt.xticks(all_years, rotation=45)
plt.ylim(bottom=0)
plt.grid(True, axis="y", linestyle="--", alpha=0.4)

plt.tight_layout()

# Instead of plt.show(), save to PDF
plt.savefig("mach3_theses_per_year.pdf")
print("Plot saved as mach3_theses_per_year.pdf")

# ----------------------------------------------------------------------
# Also print a table (useful for sanity checks / papers)
# ----------------------------------------------------------------------
print("\nTheses per year:")
for y in all_years:
    print(f"{y}: {counts.get(y,0)}")
