from __future__ import annotations

import argparse
import os
import shutil

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap, Normalize


# ================================================================
# MaCh3 palette
# ================================================================
MACH3_BLUE = "#6C9BC2"
MACH3_DARK_BLUE = "#183B56"
MACH3_RED = "#8C2F39"
MACH3_GOLD = "#D7A629"

BG = "#F7F8FA"
GRID = "#D8DEE6"
WHITE = "#FFFFFF"
TEXT = MACH3_DARK_BLUE

PI = np.pi

PP_CMAP = LinearSegmentedColormap.from_list(
    "mach3_posterior_predictive",
    [
        "#EEF2F5",          # very low occupancy
        MACH3_BLUE,         # MaCh3 blue
        MACH3_DARK_BLUE,    # dark MaCh3 blue
        MACH3_GOLD,         # gold
        MACH3_RED,          # red
    ],
    N=256
)

PP_CMAP.set_under(BG)


# ================================================================
# Toy Neutrino Oscillation Probability
# ================================================================

def oscillation_probability(
    delta_cp: float,
    e_rec: np.ndarray | float,
    A: float = 0.35
) -> np.ndarray | float:
    """
    Toy energy-dependent oscillation probability.

    The weight depends on both delta_CP and reconstructed energy,
    so changing delta_CP changes the shape of the reweighted MC.
    """

    e_rec = np.asarray(
        e_rec,
        dtype=float
    )

    phase = (
        2.1 / (e_rec + 0.45)
        + 0.35 * e_rec
    )

    probability = (
        1.0
        + A
        * np.sin(
            delta_cp + phase
        )
    )

    probability = np.clip(
        probability,
        0.05,
        None
    )

    if probability.ndim == 0:
        return float(probability)

    return probability


# ================================================================
# Toy MC
# ================================================================
def mc_flux(
    x: np.ndarray,
    mu: float = 0.95,
    sigma: float = 0.52
) -> np.ndarray:
    """
    Toy reconstructed-energy MC spectrum.
    """
    return np.exp(
        -0.5
        * ((x - mu) / sigma) ** 2
    )


# ================================================================
# Helper Functions
# ================================================================

def angle_diff(
    x: np.ndarray | float,
    mu: float
) -> np.ndarray | float:

    return (
        (np.asarray(x) - mu + PI)
        % (2 * PI)
        - PI
    )


def log_posterior(
    x: np.ndarray | float
) -> np.ndarray | float:
    """
    Toy periodic, asymmetric delta_CP-like posterior.
    """

    x = np.asarray(
        x,
        dtype=float
    )

    components = []

    for mu, sigma, weight in (
        (-2.18, 0.43, 0.70),
        (-2.65, 0.78, 0.24),
        (2.85, 0.30, 0.06),
    ):

        d = angle_diff(
            x,
            mu
        )

        components.append(
            np.log(weight)
            - 0.5 * (d / sigma) ** 2
            - np.log(sigma)
        )

    stacked = np.stack(
        components,
        axis=0
    )

    m = np.max(
        stacked,
        axis=0
    )

    mix = (
        m
        + np.log(
            np.sum(
                np.exp(
                    stacked - m
                ),
                axis=0
            )
        )
    )

    d_supp = angle_diff(
        x,
        +PI / 2
    )

    penalty = (
        2.7
        * np.exp(
            -0.5
            * (d_supp / 0.38) ** 2
        )
    )

    out = mix - penalty

    if out.ndim == 0:
        return float(out)

    return out


# ================================================================
# Metropolis-Hastings Chain
# ================================================================

def metropolis_chain(
    n_steps: int,
    seed: int = 4,
    start: float = 0.0,
    proposal_sigma: float = 0.40
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray
]:

    rng = np.random.default_rng(
        seed
    )

    x = float(start)

    lp = float(
        log_posterior(x)
    )

    states = [x]
    proposals = []
    accepted = []
    alpha_values = []

    for _ in range(n_steps):

        proposal = (
            x
            + rng.normal(
                0.0,
                proposal_sigma
            )
        )

        proposal = (
            (proposal + PI)
            % (2 * PI)
            - PI
        )

        lp_prop = float(
            log_posterior(
                proposal
            )
        )

        alpha = float(
            np.exp(
                min(
                    0.0,
                    lp_prop - lp
                )
            )
        )

        do_accept = bool(
            rng.random()
            < alpha
        )

        proposals.append(
            proposal
        )

        accepted.append(
            do_accept
        )

        alpha_values.append(
            alpha
        )

        if do_accept:
            x = proposal
            lp = lp_prop

        states.append(
            x
        )

    return (
        np.asarray(states),
        np.asarray(proposals),
        np.asarray(
            accepted,
            dtype=bool
        ),
        np.asarray(alpha_values)
    )


# ================================================================
# Main Animation
# ================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Animate posterior predictive toy MC method."
        )
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=30.0
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=30
    )

    parser.add_argument(
        "--samples-per-second",
        type=float,
        default=2.0,
        help=(
            "Number of posterior-predictive toy MCs "
            "generated per second. Default: 2."
        )
    )

    parser.add_argument(
        "--output",
        default="posterior_predictive.mp4"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=4
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=150
    )

    args = parser.parse_args()

    if (
        args.duration <= 0
        or args.fps <= 0
        or args.samples_per_second <= 0
    ):
        raise SystemExit(
            "duration, fps, and samples-per-second "
            "must be positive."
        )

    # ============================================================
    # Check for ffmpeg
    # ============================================================

    ffmpeg_exe = shutil.which(
        "ffmpeg"
    )

    if ffmpeg_exe is None:

        try:

            import imageio_ffmpeg

            ffmpeg_exe = (
                imageio_ffmpeg
                .get_ffmpeg_exe()
            )

        except ImportError:
            pass

    if ffmpeg_exe is None:

        raise SystemExit(
            "ffmpeg was not found. "
            "Install with pip3 install imageio-ffmpeg "
            "or install ffmpeg system-wide."
        )

    plt.rcParams[
        "animation.ffmpeg_path"
    ] = ffmpeg_exe

    # ============================================================
    # Global Matplotlib typography
    #
    # The referenced MaCh3 animation uses Matplotlib's standard
    # sans-serif typography, with larger bold titles and labels.
    # ============================================================
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titleweight": "bold",
        "axes.labelweight": "normal",
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
    })

    # ============================================================
    # Animation timing
    # ============================================================

    n_frames = max(
        1,
        int(
            round(
                args.duration
                * args.fps
            )
        )
    )

    n_toys = max(
        1,
        int(
            round(
                args.duration
                * args.samples_per_second
            )
        )
    )

    # ============================================================
    # Posterior samples
    # ============================================================

    states, proposals, accepted, alpha = (
        metropolis_chain(
            n_toys,
            seed=args.seed
        )
    )

    # ============================================================
    # Target posterior
    # ============================================================

    xgrid = np.linspace(
        -PI,
        PI,
        1200
    )

    target = np.exp(
        log_posterior(
            xgrid
        )
    )

    target /= np.trapezoid(
        target,
        xgrid
    )

    target /= target.max()

    # ============================================================
    # eREC binning
    # ============================================================

    n_erec_bins = 40

    erec_min = 0.0
    erec_max = 3.0

    erec_edges = np.linspace(
        erec_min,
        erec_max,
        n_erec_bins + 1
    )

    erec_centers = 0.5 * (
        erec_edges[:-1]
        + erec_edges[1:]
    )

    erec_bin_widths = np.diff(
        erec_edges
    )

    # ============================================================
    # Nominal MC prediction
    # ============================================================

    mc_flux_shape = mc_flux(
        erec_centers
    )

    nominal_mc_events = 1000.0

    mc_bin_values = (
        mc_flux_shape
        / mc_flux_shape.sum()
        * nominal_mc_events
    )

    # ============================================================
    # Generate complete toy MC ensemble
    # ============================================================

    toy_mc_predictions = []

    for toy_index in range(
        n_toys
    ):

        delta_cp = states[
            toy_index + 1
        ]

        weights = (
            oscillation_probability(
                delta_cp,
                erec_centers
            )
        )

        toy_prediction = (
            mc_bin_values
            * weights
        )

        toy_mc_predictions.append(
            toy_prediction
        )

    toy_mc_predictions = np.asarray(
        toy_mc_predictions
    )

    # ============================================================
    # Common Y axis for panels 2 and 3
    # ============================================================

    global_ymax = float(
        toy_mc_predictions.max()
    )

    global_ymax *= 1.12

    # ============================================================
    # TH2D Y BINNING
    # ============================================================

    n_y_bins = 100

    y_edges = np.linspace(
        0.0,
        global_ymax,
        n_y_bins + 1
    )

    # ============================================================
    # TH2D storage
    # ============================================================

    predictive_hist = np.zeros(
        (
            n_y_bins,
            n_erec_bins
        ),
        dtype=float
    )

    # ============================================================
    # Preview the complete TH2D to determine a robust Z scale.
    # ============================================================

    z_preview = np.zeros(
        (
            n_y_bins,
            n_erec_bins
        ),
        dtype=float
    )

    for toy_prediction in toy_mc_predictions:

        for x_bin in range(
            n_erec_bins
        ):

            y_value = (
                toy_prediction[
                    x_bin
                ]
            )

            y_bin = (
                np.searchsorted(
                    y_edges,
                    y_value,
                    side="right"
                )
                - 1
            )

            y_bin = int(
                np.clip(
                    y_bin,
                    0,
                    n_y_bins - 1
                )
            )

            z_preview[
                y_bin,
                x_bin
            ] += 1.0

    populated_cells = (
        z_preview[
            z_preview > 0
        ]
    )

    if populated_cells.size > 0:

        # Robust effective maximum.
        #
        # Very rare high-occupancy cells do not stretch the
        # complete colour scale.
        z_max = float(
            np.percentile(
                populated_cells,
                95
            )
        )

        z_max = max(
            1.0,
            z_max
        )

    else:

        z_max = 1.0

    # ============================================================
    # Figure
    # ============================================================

    fig = plt.figure(
        figsize=(13.0, 9.2),
        facecolor=BG
    )

    gs = fig.add_gridspec(
        3,
        1,
        height_ratios=[
            1.0,
            1.0,
            1.60
        ],
        left=0.085,
        right=0.955,
        top=0.92,
        bottom=0.08,
        hspace=0.46
    )

    # ============================================================
    # PANEL 1
    # ============================================================

    ax_target = fig.add_subplot(
        gs[0]
    )

    ax_target.set_xlim(
        -PI,
        PI
    )

    ax_target.set_ylim(
        0,
        1.08
    )

    ax_target.set_title(
        "Target Distribution ($\\delta_{CP}$)",
        fontsize=13,
        fontweight="bold",
        color=TEXT,
        pad=10
    )

    ax_target.set_xticks([
        -PI,
        -PI / 2,
        0,
        PI / 2,
        PI
    ])

    ax_target.set_xticklabels([
        r"$-\pi$",
        r"$-\pi/2$",
        r"$0$",
        r"$+\pi/2$",
        r"$+\pi$"
    ])

    ax_target.set_yticks([])

    ax_target.set_facecolor(
        BG
    )

    ax_target.spines[
        "top"
    ].set_visible(False)

    ax_target.spines[
        "right"
    ].set_visible(False)

    ax_target.spines[
        "left"
    ].set_color(
        GRID
    )

    ax_target.spines[
        "bottom"
    ].set_color(
        GRID
    )

    ax_target.tick_params(
        colors=TEXT,
        labelsize=10.5
    )

    ax_target.grid(
        axis="y",
        color=GRID,
        linewidth=0.8,
        alpha=0.65
    )

    # Target posterior
    target_line, = ax_target.plot(
        xgrid,
        target,
        color=MACH3_DARK_BLUE,
        lw=2.5,
        ls="--",
        alpha=0.38
    )

    # Current delta_CP
    current_delta_line = (
        ax_target.axvline(
            0,
            color=MACH3_RED,
            lw=2.3,
            alpha=0.85,
            ls="--"
        )
    )

    # ============================================================
    # PANEL 2
    # ============================================================

    ax_reweighted = fig.add_subplot(
        gs[1]
    )

    ax_reweighted.set_xlim(
        erec_min,
        erec_max
    )

    ax_reweighted.set_ylim(
        0,
        global_ymax
    )

    ax_reweighted.set_title(
        "Reweighted MC Prediction",
        fontsize=13,
        fontweight="bold",
        color=TEXT,
        pad=10
    )

    ax_reweighted.set_xlabel(
        r"$e_{\rm REC}$ [GeV]",
        fontsize=14,
        color=TEXT,
        labelpad=8
    )

    ax_reweighted.set_ylabel(
        "events",
        fontsize=12.5,
        color=TEXT,
        labelpad=10
    )

    ax_reweighted.set_facecolor(
        BG
    )

    ax_reweighted.spines[
        "top"
    ].set_visible(False)

    ax_reweighted.spines[
        "right"
    ].set_visible(False)

    ax_reweighted.spines[
        "left"
    ].set_color(
        GRID
    )

    ax_reweighted.spines[
        "bottom"
    ].set_color(
        GRID
    )

    ax_reweighted.tick_params(
        colors=TEXT,
        labelsize=10.5
    )

    ax_reweighted.grid(
        axis="y",
        color=GRID,
        linewidth=0.8,
        alpha=0.65
    )

    # ------------------------------------------------------------
    # Current reweighted toy MC only.
    # ------------------------------------------------------------

    reweighted_bars = ax_reweighted.bar(
        erec_centers,
        np.zeros(
            n_erec_bins
        ),
        width=0.90 * erec_bin_widths,
        align="center",
        color=MACH3_GOLD,
        alpha=0.88,
        edgecolor="none"
    )

    # ============================================================
    # PANEL 3
    # ============================================================

    ax_predictive = fig.add_subplot(
        gs[2]
    )

    ax_predictive.set_xlim(
        erec_min,
        erec_max
    )

    # IDENTICAL Y AXIS LIMIT TO PANEL 2.
    ax_predictive.set_ylim(
        0,
        global_ymax
    )

    ax_predictive.set_title(
        "Posterior Predictive Toy MC",
        fontsize=13,
        fontweight="bold",
        color=TEXT,
        pad=10
    )

    ax_predictive.set_xlabel(
        r"$e_{\rm REC}$ [GeV]",
        fontsize=14,
        color=TEXT,
        labelpad=10
    )

    ax_predictive.set_ylabel(
        "toy MC bin content",
        fontsize=12.5,
        color=TEXT,
        labelpad=10
    )

    ax_predictive.set_facecolor(
        BG
    )

    ax_predictive.spines[
        "top"
    ].set_visible(False)

    ax_predictive.spines[
        "right"
    ].set_visible(False)

    ax_predictive.spines[
        "left"
    ].set_color(
        GRID
    )

    ax_predictive.spines[
        "bottom"
    ].set_color(
        GRID
    )

    ax_predictive.tick_params(
        colors=TEXT,
        labelsize=10.5
    )

    ax_predictive.grid(
        axis="y",
        color=GRID,
        linewidth=0.8,
        alpha=0.65
    )

    # ============================================================
    # TH2D-LIKE COLOUR MAP
    #
    # X = eREC
    # Y = toy MC bin content
    # Z = number of toys in each cell
    # ============================================================

    predictive_image = ax_predictive.pcolormesh(
        erec_edges,
        y_edges,
        predictive_hist,
        shading="flat",
        cmap=PP_CMAP,
        norm=Normalize(
            vmin=0,
            vmax=z_max
        )
    )

    # ============================================================
    # RED POSTERIOR-PREDICTIVE MEAN
    # ============================================================

    predictive_mean_line, = ax_predictive.plot(
        erec_centers,
        np.zeros(
            n_erec_bins
        ),
        color=MACH3_RED,
        lw=2.8,
        zorder=10,
        drawstyle="steps-mid"
    )

    # ============================================================
    # TH2D Z AXIS / COLORBAR
    # ============================================================

    colorbar = fig.colorbar(
        predictive_image,
        ax=ax_predictive,
        pad=0.012,
        fraction=0.035
    )

    colorbar.set_label(
        "toy MC occupancy",
        color=TEXT,
        fontsize=10.5
    )

    colorbar.ax.tick_params(
        colors=TEXT,
        labelsize=9
    )

    colorbar.outline.set_edgecolor(
        GRID
    )

    # ============================================================
    # INFO BOX
    # ============================================================

    info_box = FancyBboxPatch(
        (0.77, 0.035),
        0.20,
        0.075,
        transform=fig.transFigure,
        boxstyle=(
            "round,pad=0.012,"
            "rounding_size=0.015"
        ),
        facecolor=WHITE,
        edgecolor=GRID,
        linewidth=1.1
    )

    fig.patches.append(
        info_box
    )

    info = fig.text(
        0.785,
        0.072,
        "",
        color=TEXT,
        fontsize=11.0,
        family="DejaVu Sans Mono",
        va="center"
    )

    # ============================================================
    # Toy accumulation
    # ============================================================

    accumulated_toys = 0

    # ============================================================
    # UPDATE FUNCTION
    # ============================================================

    def update(frame: int):

        nonlocal accumulated_toys

        # --------------------------------------------------------
        # Determine how many toy MCs should exist.
        # --------------------------------------------------------

        desired_toys = min(
            n_toys,
            int(
                np.floor(
                    (
                        frame + 1
                    )
                    / args.fps
                    * args.samples_per_second
                )
            )
            + 1
        )

        desired_toys = max(
            1,
            desired_toys
        )

        # --------------------------------------------------------
        # Add newly generated toys.
        # --------------------------------------------------------

        while (
            accumulated_toys
            < desired_toys
        ):

            toy_index = (
                accumulated_toys
            )

            delta_cp = states[
                toy_index + 1
            ]

            toy_prediction = (
                toy_mc_predictions[
                    toy_index
                ]
            )

            # ====================================================
            # PANEL 1
            # ====================================================

            current_delta_line.set_xdata([
                delta_cp,
                delta_cp
            ])

            # ====================================================
            # PANEL 2
            # ====================================================

            for bar, height in zip(
                reweighted_bars,
                toy_prediction
            ):

                bar.set_height(
                    height
                )

            # ====================================================
            # PANEL 3
            #
            # Fill one TH2D entry per eREC bin.
            # ====================================================

            for x_bin in range(
                n_erec_bins
            ):

                y_value = (
                    toy_prediction[
                        x_bin
                    ]
                )

                y_bin = (
                    np.searchsorted(
                        y_edges,
                        y_value,
                        side="right"
                    )
                    - 1
                )

                y_bin = int(
                    np.clip(
                        y_bin,
                        0,
                        n_y_bins - 1
                    )
                )

                predictive_hist[
                    y_bin,
                    x_bin
                ] += 1.0

            accumulated_toys += 1

        # ========================================================
        # Update TH2D
        # ========================================================

        predictive_image.set_array(
            predictive_hist.ravel()
        )

        # ========================================================
        # Posterior-predictive mean
        #
        # Mean predicted event count in each eREC bin.
        # ========================================================

        if accumulated_toys > 0:

            predictive_mean = (
                np.mean(
                    toy_mc_predictions[
                        :accumulated_toys
                    ],
                    axis=0
                )
            )

        else:

            predictive_mean = np.zeros(
                n_erec_bins
            )

        predictive_mean_line.set_data(
            erec_centers,
            predictive_mean
        )

        # ========================================================
        # Update info
        # ========================================================

        if accumulated_toys > 0:

            used_delta_cp = states[
                accumulated_toys
            ]

        else:

            used_delta_cp = 0.0

        info.set_text(
            f"$\\delta_{{CP}}$: "
            f"{used_delta_cp:.2f}\n"
            f"toy MCs: "
            f"{accumulated_toys:4d}"
        )

        return (
            target_line,
            current_delta_line,
            predictive_image,
            predictive_mean_line,
            info,
            *reweighted_bars
        )

    # ============================================================
    # Create Animation
    # ============================================================

    anim = FuncAnimation(
        fig,
        update,
        frames=n_frames,
        interval=1000 / args.fps,
        blit=False,
        repeat=False
    )

    # ============================================================
    # Save
    # ============================================================

    output_dir = os.path.dirname(
        os.path.abspath(
            args.output
        )
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    writer = FFMpegWriter(
        fps=args.fps,
        codec="libx264",
        bitrate=7000,
        extra_args=[
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart"
        ]
    )

    anim.save(
        args.output,
        writer=writer,
        dpi=args.dpi
    )

    plt.close(fig)

    print(
        f"Wrote {args.output}"
    )

    print(
        f"Generated {n_toys} "
        "posterior-predictive toy MCs"
    )

    print(
        f"TH2D Z-axis scale: 0 to {z_max:.1f} "
        "(95th-percentile effective maximum)"
    )


# ================================================================
# Entry point
# ================================================================

if __name__ == "__main__":
    main()
