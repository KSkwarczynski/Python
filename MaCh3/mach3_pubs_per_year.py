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
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Paste / maintain the publication list here
# ----------------------------------------------------------------------
data = """
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
plt.figure(figsize=(8, 4.5))
plt.plot(all_years, values, marker="o")

plt.title("Number of MaCh3-related Publications per Year")
plt.xlabel("Year")
plt.ylabel("Number of Publications")

plt.xticks(all_years, rotation=45)
plt.ylim(bottom=0)
plt.grid(True, axis="y", linestyle="--", alpha=0.4)

plt.tight_layout()

# Save to PNG
plt.savefig("mach3_publications_per_year.png", dpi=200, bbox_inches='tight')
print("Plot saved as mach3_publications_per_year.png")

# ----------------------------------------------------------------------
# Print table
# ----------------------------------------------------------------------
print("\nPublications per year:")
for y in all_years:
    print(f"{y}: {counts.get(y,0)}")
