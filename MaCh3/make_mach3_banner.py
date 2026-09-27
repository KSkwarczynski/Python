#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib import patheffects


# ---------------------------------------------------------------------------
# Palette tuned to the supplied MaCh3 logo/reference image.
# In the logo:
#   nu_e   = red
#   nu_mu  = orange
#   nu_tau = yellow
# ---------------------------------------------------------------------------

NAVY = "#00324A"        # MCMC trajectories
MACH3_BLUE = "#438BC8"   # MaCh3 logo text
RED = "#A5111C"          # nu_e
ORANGE = "#D35400"      # nu_mu: darker burnt orange, as in the logo
YELLOW = "#FFB400"      # nu_tau: bright yellow, clearly separated from nu_mu
WHITE = "#FFFFFF"
BG = WHITE

# ---------------------------------------------------------------------------
# Reproducible MCMC-style cloud
# ---------------------------------------------------------------------------
def draw_mcmc_cloud(ax, *, rng: np.random.Generator, center=(0.145, 0.505),
                    width=0.23, height=0.67, n=230) -> None:
    """Draw a dense bundle of hand-tuned random-walk-like closed traces."""
    cx, cy = center

    for i in range(n):
        t = np.linspace(0, 2 * np.pi, 520)
        ring = rng.random()

        if ring < 0.22:
            sx = rng.uniform(0.82, 1.25)
            sy = rng.uniform(0.78, 1.24)
            lw = rng.uniform(0.75, 1.15)
            alpha = rng.uniform(0.72, 0.90)
        else:
            sx = rng.uniform(0.30, 1.00)
            sy = rng.uniform(0.28, 1.00)
            lw = rng.uniform(0.45, 0.95)
            alpha = rng.uniform(0.50, 0.82)

        f1 = rng.integers(1, 4)
        f2 = rng.integers(2, 7)
        p1 = rng.uniform(0, 2 * np.pi)
        p2 = rng.uniform(0, 2 * np.pi)
        wobble = rng.uniform(0.02, 0.11)

        x = np.cos(t + p1) + wobble * np.cos(f1 * t + p2)
        y = np.sin(t + p2) + wobble * np.sin(f2 * t + p1)

        theta = rng.normal(0.0, 0.26)
        c, s = np.cos(theta), np.sin(theta)
        xr = c * x - s * y
        yr = s * x + c * y

        if rng.random() < 0.10:
            xr *= rng.uniform(1.05, 1.45)
            yr *= rng.uniform(1.05, 1.40)

        x_plot = cx + (width / 2) * sx * xr
        y_plot = cy + (height / 2) * sy * yr

        ax.plot(
            x_plot, y_plot,
            color=NAVY, lw=lw, alpha=alpha,
            solid_capstyle="round", zorder=2
        )


# ---------------------------------------------------------------------------
# MaCh3 logo text
# ---------------------------------------------------------------------------
def draw_mach3_logo(
    ax,
    *,
    center=(0.127, 0.50),
    fontsize=40,
    color=MACH3_BLUE,
    font_family="DejaVu Serif",
    white_stroke_pt=2.05,
) -> None:
    """Draw MaCh3 text with the reference's blue-fill / white-outline look."""
    cx, cy = center

    ax.text(
        cx,
        cy,
        "MaCh3",
        fontsize=fontsize,
        fontweight="bold",
        color=color,
        family=font_family,
        ha="center",
        va="center",
        zorder=9,
        clip_on=False,
        path_effects=[
            patheffects.withStroke(
                linewidth=white_stroke_pt,
                foreground=WHITE,
            )
        ],
    )



# ---------------------------------------------------------------------------
# Neutrino source + oscillation curves
# ---------------------------------------------------------------------------
def draw_neutrino_oscillations(ax, *, source_x: float, source_y: float,
                               right_x: float = 0.945) -> None:
    x = np.linspace(source_x, right_x, 1500)
    u = (x - source_x) / (right_x - source_x)

    ramp = 0.14 + 0.86 * (1.0 - np.exp(-u * 11.0))
    baseline_amp = 0.135

    # Logo colours:
    #   nu_e   -> red
    #   nu_mu  -> orange
    #   nu_tau -> yellow
    tracks = [
        (RED,    0.00, +0.20, 1.78),
        (ORANGE, 2.12, +0.00, 1.35),
        (YELLOW, 4.35, -0.20, 1.96),
    ]

    ys = []
    for color, phase, offset, cycles in tracks:
        phase_curve = (
            2 * np.pi * cycles * u
            + phase
            + 0.12 * np.sin(2 * np.pi * u)
        )
        y = source_y + 0.008 * np.sin(
            2 * np.pi * u * 1.3 + phase
        )
        y += ramp * baseline_amp * np.sin(phase_curve)
        y += offset * u
        ys.append(y)

        ax.plot(
            x, y, color=color, lw=2.0,
            zorder=6, solid_capstyle="round"
        )

    marker_u = (0.22, 0.45, 0.66, 0.83)
    for (color, _, _, _), y in zip(tracks, ys):
        for mu in marker_u:
            idx = int(mu * (len(x) - 1))
            ax.scatter(
                x[idx], y[idx],
                s=55, color=color, edgecolor="none", zorder=8
            )

    label_specs = [
        (ys[0][-1], r"$\nu_e$", RED, 0.017),
        (ys[1][-1], r"$\nu_\mu$", ORANGE, 0.000),
        (ys[2][-1], r"$\nu_\tau$", YELLOW, -0.015),
    ]
    for y_end, label, color, dy in label_specs:
        ax.text(
            right_x + 0.018, y_end + dy, label,
            fontsize=24, fontweight="bold", color=color,
            va="center", ha="left",
            family="STIXGeneral", zorder=10
        )


# ---------------------------------------------------------------------------
# Main banner
# ---------------------------------------------------------------------------
def make_banner(width_px: int = 1800, height_px: int = 520,
                seed: int = 17,
                output: str = "mach3_banner.png",
                show_mach3: bool = True) -> Path:
    dpi = 180
    fig = plt.figure(
        figsize=(width_px / dpi, height_px / dpi),
        dpi=dpi, facecolor=BG
    )
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rng = np.random.default_rng(seed)

    # The MCMC cloud and neutrino source share exactly the same centre.
    cloud_center = (0.125, 0.50)

    draw_mcmc_cloud(
        ax,
        rng=rng,
        center=cloud_center,
        width=0.12,
        height=0.60,
        n=80,
    )

    # Optional MaCh3 logo lettering directly over the cloud.
    if show_mach3:
        draw_mach3_logo(
            ax,
            center=cloud_center,
            fontsize=40,
        )

    # Neutrino starts at the centre of the MCMC cloud.
    sx, sy = cloud_center

    draw_neutrino_oscillations(
        ax,
        source_x=sx,
        source_y=sy,
        right_x=0.942,
    )

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out,
        dpi=dpi,
        facecolor=BG,
        edgecolor="none",
        bbox_inches=None,
        pad_inches=0,
    )
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", default="mach3_banner.png")
    parser.add_argument("--width", type=int, default=1800)
    parser.add_argument("--height", type=int, default=340)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--mach3",
        dest="show_mach3",
        action="store_true",
        default=True,
        help="show MaCh3 text over the MCMC cloud (default)",
    )
    parser.add_argument(
        "--no-mach3",
        dest="show_mach3",
        action="store_false",
        help="do not show MaCh3 text",
    )
    args = parser.parse_args()

    path = make_banner(
        args.width,
        args.height,
        args.seed,
        args.output,
        show_mach3=args.show_mach3,
    )
    print(f"Wrote {path.resolve()}")


if __name__ == "__main__":
    main()
