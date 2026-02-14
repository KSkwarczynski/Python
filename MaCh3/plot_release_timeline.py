#!/usr/bin/env python3

"""
Plot MaCh3 release tags as a function of time, with colour coding:

Major release  : X.0.0
Minor release  : X.Y.0 (Y>0)
Patch release  : X.Y.Z (Z>0)

Output:
    mach3_release_timeline.png
"""

import matplotlib.pyplot as plt
from datetime import datetime

# ----------------------------------------------------------------------
# 🔧 Fill this table as needed (unknown dates can simply be omitted)
# ----------------------------------------------------------------------
data = [
    #("v0.0.0","10-06-2022"),
    ("v1.0.0","09-04-2024"),
    ("v1.1.0","03-09-2024"),
    ("v1.1.1","09-09-2024"),
    ("v1.1.2","11-09-2024"),
    ("v1.1.3","12-09-2024"),
    ("v1.1.4","14-09-2024"),
    ("v1.1.5","19-09-2024"),
    ("v1.1.6","20-09-2024"),
    ("v1.1.7","06-10-2024"),
    ("v1.1.8","07-10-2024"),
    ("v1.2.0","20-11-2024"),
    ("v1.3.1","21-12-2024"),
    ("v1.3.2","10-01-2025"),
    ("v1.3.3","13-01-2025"),
    ("v1.3.4","22-01-2025"),
    ("v1.3.5","24-01-2025"),
    ("v1.3.6","07-02-2025"),
    ("v1.4.0","10-02-2025"),
    ("v1.4.1","12-02-2025"),
    ("v1.4.2","19-02-2025"),
    ("v1.4.3","20-02-2025"),
    ("v1.4.4","21-02-2025"),
    ("v1.4.5","24-02-2025"),
    ("v1.4.6","24-02-2025"),
    ("v1.4.7","27-02-2025"),
    ("v1.4.8","07-03-2025"),
    ("v1.5.0","01-05-2025"),
    ("v2.0.0","14-05-2025"),
    ("v2.1.0","05-06-2025"),
    ("v2.2.0","26-06-2025"),
    ("v2.2.1","14-07-2025"),
    ("v2.2.2","06-08-2025"),
    ("v2.2.3","14-10-2025"),
    ("v2.3.0","13-11-2025"),
    ("v2.3.1","12-12-2025"),
    ("v2.3.2","16-01-2026"),
    ("v2.4.0","04-02-2026"),
    ("v2.4.1","13-02-2026"),
]

# ----------------------------------------------------------------------
# 📦 Helpers
# ----------------------------------------------------------------------
def classify_release(tag):
    """
    Classify semantic version into Major / Minor / Patch.
    """
    version = tag.lstrip("v")
    major, minor, patch = map(int, version.split("."))

    if minor == 0 and patch == 0:
        return "major"
    elif patch == 0:
        return "minor"
    else:
        return "patch"


color_map = {
    "major": "#d62728",  # red
    "minor": "#1f77b4",  # blue
    "patch": "#2ca02c",  # green
}

marker_map = {
    "major": "s",   # square
    "minor": "o",   # circle
    "patch": ".",   # small dot
}

# ----------------------------------------------------------------------
# 📅 Convert + sort by date
# ----------------------------------------------------------------------
parsed = [
    (tag, datetime.strptime(date, "%d-%m-%Y"))
    for tag, date in data
]

parsed.sort(key=lambda x: x[1])

tags  = [p[0] for p in parsed]
dates = [p[1] for p in parsed]
yvals = list(range(1, len(tags)+1))

# ----------------------------------------------------------------------
# 📊 Plot
# ----------------------------------------------------------------------
plt.figure(figsize=(11, 6))

for tag, date, y in zip(tags, dates, yvals):
    rtype = classify_release(tag)

    plt.scatter(
        date,
        y,
        color=color_map[rtype],
        marker=marker_map[rtype],
        s=70 if rtype == "major" else 40,
        zorder=3
    )

# Draw connecting line to guide the eye
plt.plot(dates, yvals, linewidth=1, alpha=0.4, zorder=1)

plt.yticks(yvals, tags)
plt.xlabel("Date")
plt.ylabel("Release Tag")
plt.title("MaCh3 Release History")

# Custom legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0],[0], marker='s', color='w', label='Major',
           markerfacecolor=color_map["major"], markersize=10),
    Line2D([0],[0], marker='o', color='w', label='Minor',
           markerfacecolor=color_map["minor"], markersize=8),
    Line2D([0],[0], marker='.', color=color_map["patch"], label='Patch',
           markersize=12),
]

plt.legend(handles=legend_elements, title="Release Type")
plt.grid(True, linestyle=":", alpha=0.4)
plt.tight_layout()

plt.savefig("mach3_release_timeline.png", dpi=200)
plt.show()

print("Saved → mach3_release_timeline.png")
