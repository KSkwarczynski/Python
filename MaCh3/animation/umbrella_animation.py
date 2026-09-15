from __future__ import annotations

import argparse
import os
import shutil

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import FancyBboxPatch


# ================================================================
# MaCh3-inspired palette
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


# ================================================================
# Toy posterior in delta_CP
# ================================================================

def angle_diff(
    x: np.ndarray | float,
    mu: float
) -> np.ndarray | float:
    """
    Periodic angular difference in [-pi, pi).
    """

    return (
        (np.asarray(x) - mu + PI)
        % (2 * PI)
        - PI
    )


def log_posterior(
    x: np.ndarray | float
) -> np.ndarray | float:
    """
    Toy periodic, asymmetric delta_CP posterior.

    The +pi/2 region is deliberately suppressed so that the
    advantage of umbrella sampling is visually obvious.
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

    # Deliberate suppression around +pi/2.
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
# Normalisation helpers
# ================================================================

def normalize_density(
    y: np.ndarray,
    x: np.ndarray
) -> np.ndarray:
    """
    Normalize positive function to unit integral.
    """

    area = np.trapezoid(
        y,
        x
    )

    if area <= 0:
        return np.zeros_like(y)

    return y / area


def normalize_plot(
    y: np.ndarray
) -> np.ndarray:
    """
    Normalize a curve to max = 1 for plotting.
    """

    maximum = np.max(
        y
    )

    if maximum <= 0:
        return np.zeros_like(y)

    return y / maximum


# ================================================================
# Umbrella potential
# ================================================================

def umbrella_potential(
    theta: np.ndarray,
    center: float,
    kappa: float
) -> np.ndarray:
    """
    Periodic harmonic umbrella potential:

        U_k(theta) = 0.5 * kappa * d(theta, center)^2
    """

    d = angle_diff(
        theta,
        center
    )

    return (
        0.5
        * kappa
        * d**2
    )


# ================================================================
# Biased umbrella distribution
# ================================================================

def biased_distribution(
    theta: np.ndarray,
    target_density: np.ndarray,
    center: float,
    kappa: float
) -> np.ndarray:
    """
    Actual distribution sampled by umbrella k:

        q_k(theta)
        proportional to
        p(theta) exp[-U_k(theta)]

    This is what is shown in panel 2.
    """

    potential = umbrella_potential(
        theta,
        center,
        kappa
    )

    biased = (
        target_density
        * np.exp(
            -potential
        )
    )

    return normalize_density(
        biased,
        theta
    )


# ================================================================
# WHAM reconstruction
# ================================================================

def wham_reconstruct(
    histograms: np.ndarray,
    n_samples: np.ndarray,
    potentials: np.ndarray,
    n_iterations: int = 250,
    tolerance: float = 1e-9
) -> np.ndarray:
    """
    Simple WHAM reconstruction.

    Parameters
    ----------
    histograms:
        shape = (n_windows, n_bins)

    n_samples:
        number of samples accumulated in each umbrella

    potentials:
        U_k(theta_j)

    Returns
    -------
    p:
        estimated unbiased posterior probability per theta bin
    """

    active = (
        n_samples > 0
    )

    if not np.any(active):

        return np.zeros(
            histograms.shape[1]
        )

    H = histograms[
        active
    ]

    N = n_samples[
        active
    ]

    U = potentials[
        active
    ]

    n_active = len(
        N
    )

    n_bins = histograms.shape[1]

    # ------------------------------------------------------------
    # Initial estimate
    # ------------------------------------------------------------

    total_hist = H.sum(
        axis=0
    )

    if total_hist.sum() <= 0:

        return np.zeros(
            n_bins
        )

    p = (
        total_hist
        / total_hist.sum()
    )

    # Free-energy offsets.
    f = np.zeros(
        n_active
    )

    # ------------------------------------------------------------
    # WHAM iterations
    # ------------------------------------------------------------

    for _ in range(
        n_iterations
    ):

        old_p = p.copy()

        # --------------------------------------------------------
        # Estimate free-energy offsets.
        # --------------------------------------------------------

        for k in range(
            n_active
        ):

            denominator_k = np.sum(
                p
                * np.exp(
                    -U[k]
                )
            )

            if denominator_k > 0:

                f[k] = -np.log(
                    denominator_k
                )

        # --------------------------------------------------------
        # WHAM denominator.
        # --------------------------------------------------------

        denominator = np.zeros(
            n_bins
        )

        for k in range(
            n_active
        ):

            denominator += (
                N[k]
                * np.exp(
                    f[k]
                    - U[k]
                )
            )

        numerator = H.sum(
            axis=0
        )

        p_new = np.zeros(
            n_bins
        )

        valid = (
            denominator > 0
        )

        p_new[valid] = (
            numerator[valid]
            / denominator[valid]
        )

        total = p_new.sum()

        if total > 0:

            p_new /= total

        p = p_new

        difference = np.max(
            np.abs(
                p - old_p
            )
        )

        if difference < tolerance:

            break

    return p


# ================================================================
# Main
# ================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Animate umbrella sampling of a delta_CP posterior."
        )
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=40.0
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=30
    )

    parser.add_argument(
        "--samples-per-second",
        type=float,
        default=8.0,
        help=(
            "Number of biased samples added per second."
        )
    )

    parser.add_argument(
        "--samples-per-window",
        type=int,
        default=50,
        help=(
            "Number of samples assigned to each umbrella window."
        )
    )

    parser.add_argument(
        "--output",
        default="umbrella_sampling_delta_cp.mp4"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=7
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
        or args.samples_per_window <= 0
    ):

        raise SystemExit(
            "duration, fps, samples-per-second, and "
            "samples-per-window must be positive."
        )

    # ============================================================
    # FFmpeg
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
    # MaCh3 typography
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

    # ============================================================
    # delta_CP grid
    # ============================================================

    n_bins = 240

    theta_edges = np.linspace(
        -PI,
        PI,
        n_bins + 1
    )

    theta = 0.5 * (
        theta_edges[:-1]
        + theta_edges[1:]
    )

    theta_width = np.diff(
        theta_edges
    )

    # ============================================================
    # Target posterior
    # ============================================================

    target_raw = np.exp(
        log_posterior(
            theta
        )
    )

    target_density = normalize_density(
        target_raw,
        theta
    )

    target_plot = normalize_plot(
        target_density
    )

    # ============================================================
    # Umbrella windows
    #
    # More windows + stronger bias so that even the suppressed
    # region around +pi/2 is deliberately sampled.
    # ============================================================

    n_windows = 8

    kappa = 8.0

    window_spacing = (
        2 * PI
        / n_windows
    )

    # Centres placed evenly around the periodic circle.
    window_centers = (
        np.linspace(
            -PI,
            PI,
            n_windows,
            endpoint=False
        )
        + 0.5 * window_spacing
    )

    window_centers = (
        (window_centers + PI)
        % (2 * PI)
        - PI
    )

    # ============================================================
    # Umbrella potentials and biased distributions
    # ============================================================

    potentials = np.zeros(
        (
            n_windows,
            n_bins
        )
    )

    biased_distributions = np.zeros(
        (
            n_windows,
            n_bins
        )
    )

    for k in range(
        n_windows
    ):

        potentials[k] = (
            umbrella_potential(
                theta,
                window_centers[k],
                kappa
            )
        )

        biased_distributions[k] = (
            biased_distribution(
                theta,
                target_density,
                window_centers[k],
                kappa
            )
        )

    # ============================================================
    # Generate biased samples for every umbrella
    # ============================================================

    rng = np.random.default_rng(
        args.seed
    )

    all_samples = []

    for k in range(
        n_windows
    ):

        pdf = (
            biased_distributions[k]
            * theta_width
        )

        pdf /= pdf.sum()

        samples = rng.choice(
            theta,
            size=args.samples_per_window,
            p=pdf
        )

        all_samples.append(
            samples
        )

    all_samples = np.asarray(
        all_samples
    )

    total_samples = (
        n_windows
        * args.samples_per_window
    )

    # ============================================================
    # Accumulated umbrella histograms
    # ============================================================

    accumulated_hist = np.zeros(
        (
            n_windows,
            n_bins
        ),
        dtype=float
    )

    accumulated_counts = np.zeros(
        n_windows,
        dtype=int
    )

    # ============================================================
    # Figure
    #
    # 4 panels:
    #
    # 1. Target posterior
    # 2. Umbrella windows / biased sampling
    # 3. Combined biased distribution
    # 4. Unbiased WHAM reconstruction
    # ============================================================

    fig = plt.figure(
        figsize=(13.0, 11.4),
        facecolor=BG
    )

    gs = fig.add_gridspec(
        4,
        1,
        height_ratios=[
            0.95,
            1.10,
            1.15,
            1.15
        ],
        left=0.085,
        right=0.955,
        top=0.91,
        bottom=0.075,
        hspace=0.44
    )

    # ============================================================
    # Common style helper
    # ============================================================

    def style_axis(
        ax,
        title: str,
        xlabel: str | None = None,
        ylabel: str | None = None
    ):

        ax.set_xlim(
            -PI,
            PI
        )

        ax.set_facecolor(
            BG
        )

        ax.set_title(
            title,
            fontsize=13,
            fontweight="bold",
            color=TEXT,
            pad=9
        )

        if xlabel is not None:

            ax.set_xlabel(
                xlabel,
                fontsize=13,
                color=TEXT,
                labelpad=8
            )

        if ylabel is not None:

            ax.set_ylabel(
                ylabel,
                fontsize=11.5,
                color=TEXT,
                labelpad=9
            )

        ax.spines[
            "top"
        ].set_visible(False)

        ax.spines[
            "right"
        ].set_visible(False)

        ax.spines[
            "left"
        ].set_color(
            GRID
        )

        ax.spines[
            "bottom"
        ].set_color(
            GRID
        )

        ax.tick_params(
            colors=TEXT,
            labelsize=10
        )

        ax.grid(
            axis="y",
            color=GRID,
            linewidth=0.8,
            alpha=0.65
        )

    def set_delta_ticks(
        ax
    ):

        ax.set_xticks([
            -PI,
            -PI / 2,
            0,
            PI / 2,
            PI
        ])

        ax.set_xticklabels([
            r"$-\pi$",
            r"$-\pi/2$",
            r"$0$",
            r"$+\pi/2$",
            r"$+\pi$"
        ])

    # ============================================================
    # PANEL 1
    # ============================================================

    ax_target = fig.add_subplot(
        gs[0]
    )

    style_axis(
        ax_target,
        r"Target Posterior ($\delta_{CP}$)",
        r"$\delta_{CP}$",
        r"$p(\delta_{CP})$"
    )

    ax_target.set_ylim(
        0,
        1.08
    )

    set_delta_ticks(
        ax_target
    )

    target_line, = ax_target.plot(
        theta,
        target_plot,
        color=MACH3_DARK_BLUE,
        lw=2.7,
        ls="--",
        alpha=0.45
    )

    current_window_line = (
        ax_target.axvline(
            window_centers[0],
            color=MACH3_RED,
            lw=2.4,
            ls="--",
            alpha=0.90
        )
    )

    # ============================================================
    # PANEL 2
    #
    # Actual biased distribution of the current umbrella:
    #
    # q_k(theta) ∝ p(theta) exp[-U_k(theta)]
    # ============================================================

    ax_windows = fig.add_subplot(
        gs[1]
    )

    style_axis(
        ax_windows,
        r"Umbrella Sampling: Biased Distributions",
        r"$\delta_{CP}$",
        r"$q_k(\delta_{CP})$"
    )

    ax_windows.set_ylim(
        0,
        1.10
    )

    set_delta_ticks(
        ax_windows
    )

    # ------------------------------------------------------------
    # Target shown faintly so students can see the effect of
    # deliberately biasing away from the target distribution.
    # ------------------------------------------------------------

    target_reference_line, = ax_windows.plot(
        theta,
        target_plot,
        color=MACH3_DARK_BLUE,
        lw=1.8,
        ls="--",
        alpha=0.18
    )

    # ------------------------------------------------------------
    # Each umbrella's ACTUAL biased distribution.
    # ------------------------------------------------------------

    window_lines = []

    for k in range(
        n_windows
    ):

        biased_shape = normalize_plot(
            biased_distributions[k]
        )

        line, = ax_windows.plot(
            theta,
            biased_shape,
            color=MACH3_BLUE,
            lw=2.0,
            alpha=0.32
        )

        window_lines.append(
            line
        )

    # ------------------------------------------------------------
    # Current biased distribution
    # ------------------------------------------------------------

    current_biased_shape = (
        normalize_plot(
            biased_distributions[0]
        )
    )

    current_biased_line, = (
        ax_windows.plot(
            theta,
            current_biased_shape,
            color=MACH3_GOLD,
            lw=3.0,
            alpha=0.95,
            zorder=7
        )
    )

    # ------------------------------------------------------------
    # Actual samples from current / previously sampled windows.
    # ------------------------------------------------------------

    sample_points = ax_windows.scatter(
        [],
        [],
        s=22,
        color=MACH3_RED,
        alpha=0.65,
        edgecolors="none",
        zorder=10
    )

    # ============================================================
    # PANEL 3
    #
    # Combined biased ensemble.
    #
    # Importantly:
    #
    # NO umbrella correction is applied here.
    #
    # Therefore this should NOT look like the target posterior.
    # ============================================================

    ax_biased = fig.add_subplot(
        gs[2]
    )

    style_axis(
        ax_biased,
        "Combined Biased Distribution",
        r"$\delta_{CP}$",
        "biased sample density"
    )

    ax_biased.set_ylim(
        0,
        1.08
    )

    set_delta_ticks(
        ax_biased
    )

    combined_biased_line, = ax_biased.step(
        theta,
        np.zeros(
            n_bins
        ),
        where="mid",
        color=MACH3_GOLD,
        lw=2.8
    )

    # True target, for comparison.
    biased_target_line, = ax_biased.plot(
        theta,
        target_plot,
        color=MACH3_DARK_BLUE,
        lw=2.0,
        ls="--",
        alpha=0.28
    )

    # ============================================================
    # PANEL 4
    #
    # WHAM removes the umbrella bias.
    # ============================================================

    ax_unbiased = fig.add_subplot(
        gs[3]
    )

    style_axis(
        ax_unbiased,
        "Unbiased Posterior Reconstruction",
        r"$\delta_{CP}$",
        r"$p(\delta_{CP})$"
    )

    ax_unbiased.set_ylim(
        0,
        1.08
    )

    set_delta_ticks(
        ax_unbiased
    )

    # True posterior.
    unbiased_target_line, = ax_unbiased.plot(
        theta,
        target_plot,
        color=MACH3_DARK_BLUE,
        lw=2.4,
        ls="--",
        alpha=0.38
    )

    # WHAM estimate.
    unbiased_line, = ax_unbiased.plot(
        theta,
        np.zeros_like(theta),
        color=MACH3_BLUE,
        lw=3.0,
        alpha=0.95
    )

    # Sample rug.
    reconstruction_rug = ax_unbiased.scatter(
        [],
        [],
        s=10,
        color=MACH3_GOLD,
        alpha=0.30,
        edgecolors="none",
        zorder=5
    )

    # ============================================================
    # Information box
    # ============================================================

    info_box = FancyBboxPatch(
        (0.735, 0.025),
        0.225,
        0.065,
        transform=fig.transFigure,
        boxstyle=(
            "round,pad=0.012,"
            "rounding_size=0.015"
        ),
        facecolor=WHITE,
        edgecolor=GRID,
        linewidth=1.0
    )

    fig.patches.append(
        info_box
    )

    info = fig.text(
        0.752,
        0.057,
        "",
        color=TEXT,
        fontsize=10.5,
        family="DejaVu Sans Mono",
        va="center"
    )

    # ============================================================
    # Stage label
    # ============================================================

    stage_text = fig.text(
        0.085,
        0.955,
        "",
        color=TEXT,
        fontsize=15,
        fontweight="bold",
        va="center"
    )

    # ============================================================
    # UPDATE
    # ============================================================

    def update(
        frame: int
    ):

        # --------------------------------------------------------
        # Determine how many samples should be accumulated.
        # --------------------------------------------------------

        desired_samples = min(
            total_samples,
            max(
                1,
                int(
                    np.floor(
                        (
                            frame + 1
                        )
                        / args.fps
                        * args.samples_per_second
                    )
                )
            )
        )

        # --------------------------------------------------------
        # Add newly generated samples.
        # --------------------------------------------------------

        while (
            accumulated_counts.sum()
            < desired_samples
        ):

            total_so_far = int(
                accumulated_counts.sum()
            )

            window_index = (
                total_so_far
                // args.samples_per_window
            )

            if window_index >= n_windows:
                break

            sample_index = (
                accumulated_counts[
                    window_index
                ]
            )

            if (
                sample_index
                >= args.samples_per_window
            ):
                continue

            sample = (
                all_samples[
                    window_index,
                    sample_index
                ]
            )

            # ----------------------------------------------------
            # Histogram this sample in its umbrella-specific
            # histogram.
            # ----------------------------------------------------

            bin_index = (
                np.searchsorted(
                    theta_edges,
                    sample,
                    side="right"
                )
                - 1
            )

            bin_index = int(
                np.clip(
                    bin_index,
                    0,
                    n_bins - 1
                )
            )

            accumulated_hist[
                window_index,
                bin_index
            ] += 1.0

            accumulated_counts[
                window_index
            ] += 1

        # ========================================================
        # Current umbrella
        # ========================================================

        active_windows = np.where(
            accumulated_counts > 0
        )[0]

        if len(active_windows) == 0:

            current_window = 0

        else:

            current_window = (
                active_windows[-1]
            )

        current_center = (
            window_centers[
                current_window
            ]
        )

        # ========================================================
        # PANEL 1
        # ========================================================

        current_window_line.set_xdata([
            current_center,
            current_center
        ])

        # ========================================================
        # PANEL 2
        # ========================================================

        # Highlight current umbrella.
        for k in range(
            n_windows
        ):

            if k == current_window:

                window_lines[
                    k
                ].set_color(
                    MACH3_GOLD
                )

                window_lines[
                    k
                ].set_alpha(
                    0.95
                )

            elif accumulated_counts[k] > 0:

                window_lines[
                    k
                ].set_color(
                    MACH3_BLUE
                )

                window_lines[
                    k
                ].set_alpha(
                    0.72
                )

            else:

                window_lines[
                    k
                ].set_color(
                    MACH3_BLUE
                )

                window_lines[
                    k
                ].set_alpha(
                    0.30
                )

        current_biased_shape = (
            normalize_plot(
                biased_distributions[
                    current_window
                ]
            )
        )

        current_biased_line.set_ydata(
            current_biased_shape
        )

        # --------------------------------------------------------
        # Show actual samples.
        #
        # Only samples from the currently active and previously
        # completed umbrellas are shown.
        # --------------------------------------------------------

        sample_x = []
        sample_y = []

        display_rng = np.random.default_rng(
            args.seed + 5000
        )

        for k in active_windows:

            count = accumulated_counts[
                k
            ]

            if count <= 0:
                continue

            samples = all_samples[
                k,
                :count
            ]

            sample_x.extend(
                samples.tolist()
            )

            sample_y.extend(
                display_rng.uniform(
                    0.03,
                    0.92,
                    size=count
                ).tolist()
            )

        if sample_x:

            sample_points.set_offsets(
                np.column_stack([
                    sample_x,
                    sample_y
                ])
            )

        else:

            sample_points.set_offsets(
                np.empty(
                    (0, 2)
                )
            )

        # ========================================================
        # PANEL 3
        #
        # Simply combine the biased ensembles.
        #
        # No correction is applied.
        # ========================================================

        combined_counts = (
            accumulated_hist.sum(
                axis=0
            )
        )

        total_combined = (
            combined_counts.sum()
        )

        if total_combined > 0:

            combined_density = (
                combined_counts
                / total_combined
                / theta_width
            )

            combined_density = (
                normalize_density(
                    combined_density,
                    theta
                )
            )

            combined_plot = (
                normalize_plot(
                    combined_density
                )
            )

        else:

            combined_plot = np.zeros(
                n_bins
            )

        combined_biased_line.set_ydata(
            combined_plot
        )

        # ========================================================
        # PANEL 4
        #
        # WHAM reconstruction.
        # ========================================================

        if accumulated_counts.sum() > 0:

            wham = wham_reconstruct(
                accumulated_hist,
                accumulated_counts,
                potentials,
                n_iterations=150
            )

            if wham.sum() > 0:

                wham_density = (
                    wham
                    / theta_width
                )

                wham_density /= (
                    np.trapezoid(
                        wham_density,
                        theta
                    )
                )

                wham_plot = normalize_plot(
                    wham_density
                )

            else:

                wham_plot = np.zeros_like(
                    theta
                )

        else:

            wham_plot = np.zeros_like(
                theta
            )

        unbiased_line.set_ydata(
            wham_plot
        )

        # ========================================================
        # Reconstruction sample rug
        # ========================================================

        reconstruction_x = []
        reconstruction_y = []

        for k in active_windows:

            count = accumulated_counts[
                k
            ]

            if count <= 0:
                continue

            samples = all_samples[
                k,
                :count
            ]

            reconstruction_x.extend(
                samples.tolist()
            )

            reconstruction_y.extend(
                np.full(
                    count,
                    0.035
                ).tolist()
            )

        if reconstruction_x:

            reconstruction_rug.set_offsets(
                np.column_stack([
                    reconstruction_x,
                    reconstruction_y
                ])
            )

        else:

            reconstruction_rug.set_offsets(
                np.empty(
                    (0, 2)
                )
            )

        # ========================================================
        # Information box
        # ========================================================

        info.set_text(
            f"umbrella: "
            f"{current_window + 1}"
            f"/{n_windows}\n"
            f"samples: "
            f"{accumulated_counts.sum():4d}"
        )

        # ========================================================
        # Stage label
        # ========================================================

        if current_window == 0:

            stage = (
                "1.  Bias the first region and sample"
            )

        elif current_window < n_windows - 1:

            stage = (
                "2.  Deliberately sample low-probability regions"
            )

        else:

            stage = (
                "3.  Combine overlapping biased ensembles"
            )

        if (
            accumulated_counts.sum()
            == total_samples
        ):

            stage = (
                "4.  Remove the umbrella bias → posterior"
            )

        stage_text.set_text(
            stage
        )

        # ========================================================
        # Return artists
        # ========================================================

        return (
            target_line,
            current_window_line,
            target_reference_line,
            current_biased_line,
            combined_biased_line,
            biased_target_line,
            unbiased_target_line,
            unbiased_line,
            sample_points,
            reconstruction_rug,
            info,
            stage_text,
            *window_lines
        )

    # ============================================================
    # Create animation
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

    plt.close(
        fig
    )

    print(
        f"Wrote {args.output}"
    )

    print(
        f"Generated {total_samples} "
        f"biased samples across "
        f"{n_windows} umbrella windows"
    )


# ================================================================
# Entry point
# ================================================================

if __name__ == "__main__":
    main()
