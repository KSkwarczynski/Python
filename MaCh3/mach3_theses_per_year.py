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
Michael Reh, Analysis of Detector Systematic Uncertainties Using Atmospheric Neutrinos in a Novel Markov Chain Monte Carlo Framework for T2K Data Runs 1-11, (2025)
Liban Warsame, First Bayesian neutrino oscillation analysis of DUNE, (2025)
Tailin Zhu, Measurement of neutrino oscillation parameters at T2K using new neutral current pion samples and probing future sensitivities with Hyper-Kamiokande, (2025)
Menai Lamers James, Development of a boosted decision tree antineutrino photon near detector sample for T2K, and design of the Hyper-Kamiokande outer detector and DAQ, (2025)
Andres Lopez Moreno, Reparametrisations of the leptonic mixing matrix for neutrino oscillation analysis in the T2K experiment, (2025)
Henry Wallace, Analysis of Neutrino Oscillations at Current and Future Accelerator Neutrino Experiments, (2025)
Ewan Miller, Constraining the Flux and Cross Section Uncertainties for the T2K Experiment Using ND280 Data, (2025)
Thomas Holvey, New measurements of neutrino oscillation parameters and development of novel interaction uncertainties at current and future long-baseline experiments, (2024)
Yashwanth S Prabhu, Expanded νe CC1π+ sample selection and improved systematic treatments for neutrino oscillation parameter determination with T2K data, (2024)
Alex Carter, Constraining systematic uncertainties using T2K Near Detector with X and Y FGD2 scintillator layers information in Markov chain Monte Carlo framework, (2024)
Nauman Akhlaq, Developing the T2K Neutrino Oscillation Analysis by Using Pion Samples at the Near Detector, (2023)
Evan Arthur Gerald Goodman, Combining T2K With Other Experiments to Better Constrain Oscillation Parameters, (2023)
Kamil Skwarczynski, Constraining neutrino cross-section and flux models using T2K Near Detector with proton information in Markov chain Monte Carlo framework, (2023)
Charles Naseby, Understanding the impact of an expanded neutral current pion production model on long-baseline oscillation analyses at T2K, (2023)
Ed Atkin, Neutrino Oscillation Analysis at the T2K experiment including studies of new uncertainties on interactions involving additional final state hadrons, (2023)
Dan Barrow, The sensitivity to oscillation parameters from a simultaneous beam and atmospheric neutrino analysis that combines the T2K and SK experiments, (2022)
Artur Sztuc, Standard and non-standard neutrino-antineutrino oscillation analyses and event reconstruction studies using Markov chain Monte Carlo methods at T2K, (2021)
Kevin Wood, Measurement of Neutrino Oscillation Parameters with T2K Data Corresponding to 3.6 × 10^21 Protons on Target Using a Bayesian Framework, (2021)
Will Parker, Constraining Systematic Uncertainties at T2K using Near Detector Data, (2020)
Tomoyo Yoshida, A study of single charged-pion production events at Super-Kamiokande induced by charged-current interaction of T2K-beam muon neutrinos, (2020)
Clarence Wret, Minimising Systematic Uncertainties in the T2K Experiment Using Near-Detector and External Data, (2019)
Xiaoyue Li, A Joint Analysis of T2K Beam Neutrino and Super-Kamiokande Sub-GeV Atmospheric Neutrino Data, (2018)
Leïla Haegel, Measurement Of Neutrino Oscillation Parameters Using Neutrino And Antineutrino Data Of The T2K Experiment, (2018)
Elder Pinzon, Measurement of Pion-Carbon Cross Sections at DUET and Measurement of Neutrino Oscillation Parameters at the T2K Experiment, (2018)
Kirsty Duffy, Measurement of the neutrino oscillation parameters sin2θ23, ∆m232, sin2θ13, and δCP in neutrino and antineutrino oscillation at T2K, (2016)
Patrick de Perio, Joint Three-Flavour Oscillation Analysis of Numu Disappearance and Nue Appearance in the T2K Neutrino Beam, (2014)
Richard Calland, A 3 flavour joint near and far detector neutrino oscillation analysis at T2K, (2014)
Casey Bojechko, Simultaneous Analysis of Near and Far Detector Samples of the T2K Experiment to Measure Muon Neutrino Disappearance, (2013)
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
