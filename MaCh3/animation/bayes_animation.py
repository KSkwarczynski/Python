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
# Toy Bayesian Model
# ================================================================

def prior_distribution(
    theta: np.ndarray,
    mu: float = 0.0,
    sigma: float = 2.0
) -> np.ndarray:
    """
    Broad Gaussian prior.
    """

    return np.exp(
        -0.5
        * ((theta - mu) / sigma) ** 2
    )


def likelihood_distribution(
    theta: np.ndarray,
    data_value: float = 1.1,
    sigma: float = 0.65
) -> np.ndarray:
    """
    Toy Gaussian likelihood representing a measurement.
    """

    return np.exp(
        -0.5
        * ((theta - data_value) / sigma) ** 2
    )


def normalize_curve(
    y: np.ndarray,
    x: np.ndarray
) -> np.ndarray:
    """
    Normalize a positive curve to unit integral.
    """

    integral = np.trapezoid(
        y,
        x
    )

    if integral <= 0:
        return np.zeros_like(y)

    return y / integral


def normalize_to_max(
    y: np.ndarray
) -> np.ndarray:
    """
    Normalize only for plotting so the maximum is 1.
    """

    maximum = np.max(y)

    if maximum <= 0:
        return np.zeros_like(y)

    return y / maximum


# ================================================================
# Main animation
# ================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Animate prior -> likelihood -> posterior "
            "Bayesian construction."
        )
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=12.0
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=30
    )

    parser.add_argument(
        "--output",
        default="prior_likelihood_posterior.mp4"
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
    ):
        raise SystemExit(
            "duration and fps must be positive."
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
    # Global typography / style
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
    # Parameter axis
    # ============================================================

    theta = np.linspace(
        -4.0,
        4.0,
        1200
    )

    # ============================================================
    # Build distributions
    # ============================================================

    prior = prior_distribution(
        theta
    )

    likelihood = likelihood_distribution(
        theta
    )

    # Normalize prior and likelihood independently.
    prior = normalize_curve(
        prior,
        theta
    )

    likelihood = normalize_curve(
        likelihood,
        theta
    )

    # ============================================================
    # Bayes theorem
    #
    # p(theta | D) proportional to
    #
    # p(theta) * p(D | theta)
    # ============================================================

    posterior = (
        prior
        * likelihood
    )

    posterior = normalize_curve(
        posterior,
        theta
    )

    # ============================================================
    # Plot-normalized versions
    # ============================================================

    prior_plot = normalize_to_max(
        prior
    )

    likelihood_plot = normalize_to_max(
        likelihood
    )

    posterior_plot = normalize_to_max(
        posterior
    )

    # ============================================================
    # Important values
    # ============================================================

    prior_mean = 0.0
    data_value = 1.1

    posterior_mode = theta[
        np.argmax(
            posterior
        )
    ]

    # ============================================================
    # Figure
    # ============================================================

    fig = plt.figure(
        figsize=(13.0, 8.4),
        facecolor=BG
    )

    gs = fig.add_gridspec(
        3,
        1,
        height_ratios=[
            1.0,
            1.0,
            1.0
        ],
        left=0.085,
        right=0.955,
        top=0.91,
        bottom=0.09,
        hspace=0.44
    )

    # ============================================================
    # Common axis styling
    # ============================================================

    def style_axis(
        ax,
        title: str,
        ylabel: str
    ):

        ax.set_xlim(
            theta.min(),
            theta.max()
        )

        ax.set_ylim(
            0.0,
            1.08
        )

        ax.set_title(
            title,
            fontsize=13,
            fontweight="bold",
            color=TEXT,
            pad=10
        )

        ax.set_ylabel(
            ylabel,
            fontsize=12,
            color=TEXT,
            labelpad=10
        )

        ax.set_facecolor(
            BG
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
            labelsize=10.5
        )

        ax.grid(
            axis="y",
            color=GRID,
            linewidth=0.8,
            alpha=0.65
        )

    # ============================================================
    # PANEL 1 — PRIOR
    # ============================================================

    ax_prior = fig.add_subplot(
        gs[0]
    )

    style_axis(
        ax_prior,
        "Prior Distribution",
        r"$p(\theta)$"
    )

    ax_prior.set_xticks(
        [-4, -2, 0, 2, 4]
    )

    ax_prior.set_xticklabels([
        "-4",
        "-2",
        "0",
        "+2",
        "+4"
    ])

    ax_prior.set_xlabel(
        r"$\theta$",
        fontsize=13,
        color=TEXT,
        labelpad=8
    )

    prior_line, = ax_prior.plot(
        theta,
        np.zeros_like(theta),
        color=MACH3_BLUE,
        lw=3.0,
        alpha=0.95
    )

    prior_marker = ax_prior.axvline(
        prior_mean,
        color=MACH3_DARK_BLUE,
        lw=1.8,
        ls="--",
        alpha=0.55
    )

    # ============================================================
    # PANEL 2 — LIKELIHOOD
    # ============================================================

    ax_likelihood = fig.add_subplot(
        gs[1]
    )

    style_axis(
        ax_likelihood,
        "Likelihood from Data",
        r"$p(D\,|\,\theta)$"
    )

    ax_likelihood.set_xticks(
        [-4, -2, 0, 2, 4]
    )

    ax_likelihood.set_xticklabels([
        "-4",
        "-2",
        "0",
        "+2",
        "+4"
    ])

    ax_likelihood.set_xlabel(
        r"$\theta$",
        fontsize=13,
        color=TEXT,
        labelpad=8
    )

    likelihood_line, = ax_likelihood.plot(
        theta,
        np.zeros_like(theta),
        color=MACH3_GOLD,
        lw=3.0,
        alpha=0.95
    )

    data_marker = ax_likelihood.axvline(
        data_value,
        color=MACH3_RED,
        lw=2.2,
        ls="--",
        alpha=0.85
    )

    # ============================================================
    # PANEL 3 — POSTERIOR
    # ============================================================

    ax_posterior = fig.add_subplot(
        gs[2]
    )

    style_axis(
        ax_posterior,
        "Posterior Distribution",
        r"$p(\theta\,|\,D)$"
    )

    ax_posterior.set_xticks(
        [-4, -2, 0, 2, 4]
    )

    ax_posterior.set_xticklabels([
        "-4",
        "-2",
        "0",
        "+2",
        "+4"
    ])

    ax_posterior.set_xlabel(
        r"$\theta$",
        fontsize=13,
        color=TEXT,
        labelpad=8
    )

    posterior_line, = ax_posterior.plot(
        theta,
        np.zeros_like(theta),
        color=MACH3_DARK_BLUE,
        lw=3.0,
        alpha=0.95
    )

    posterior_marker = ax_posterior.axvline(
        posterior_mode,
        color=MACH3_RED,
        lw=2.2,
        ls="--",
        alpha=0.0
    )

    # ============================================================
    # Posterior fill
    #
    # Create the FINAL fill once.
    #
    # We animate its opacity rather than attempting to mutate
    # the PolyCollection geometry. This is robust across
    # Matplotlib versions.
    # ============================================================

    posterior_fill = ax_posterior.fill_between(
        theta,
        0.0,
        posterior_plot,
        color=MACH3_BLUE,
        alpha=0.0
    )

    # ============================================================
    # Equation / information box
    # ============================================================

    equation_box = FancyBboxPatch(
        (0.68, 0.035),
        0.28,
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
        equation_box
    )

    equation_text = fig.text(
        0.695,
        0.072,
        "",
        color=TEXT,
        fontsize=11.5,
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
    # Animation helper
    # ============================================================

    def smoothstep(
        x: float
    ) -> float:

        x = np.clip(
            x,
            0.0,
            1.0
        )

        return (
            x * x * (3.0 - 2.0 * x)
        )

    # ============================================================
    # UPDATE FUNCTION
    # ============================================================

    def update(
        frame: int
    ):

        progress = (
            frame
            / max(
                1,
                n_frames - 1
            )
        )

        # --------------------------------------------------------
        # Initialise reveal amounts.
        # --------------------------------------------------------

        prior_amount = 0.0
        likelihood_amount = 0.0
        posterior_amount = 0.0

        # ========================================================
        # PHASE 1 — PRIOR
        # ========================================================

        if progress < 0.25:

            local = (
                progress
                / 0.25
            )

            prior_amount = smoothstep(
                local
            )

            stage = (
                "1.  Start with the prior"
            )

        # ========================================================
        # PHASE 2 — LIKELIHOOD
        # ========================================================

        elif progress < 0.50:

            prior_amount = 1.0

            local = (
                (progress - 0.25)
                / 0.25
            )

            likelihood_amount = smoothstep(
                local
            )

            stage = (
                "2.  Add information from the data"
            )

        # ========================================================
        # PHASE 3 — POSTERIOR
        # ========================================================

        elif progress < 0.75:

            prior_amount = 1.0
            likelihood_amount = 1.0

            local = (
                (progress - 0.50)
                / 0.25
            )

            posterior_amount = smoothstep(
                local
            )

            stage = (
                "3.  Combine prior × likelihood"
            )

        # ========================================================
        # PHASE 4 — FINAL HOLD
        # ========================================================

        else:

            prior_amount = 1.0
            likelihood_amount = 1.0
            posterior_amount = 1.0

            stage = (
                "Posterior = prior × likelihood"
            )

        # ========================================================
        # PANEL 1
        # ========================================================

        prior_line.set_ydata(
            prior_plot
            * prior_amount
        )

        # ========================================================
        # PANEL 2
        # ========================================================

        likelihood_line.set_ydata(
            likelihood_plot
            * likelihood_amount
        )

        # ========================================================
        # PANEL 3
        # ========================================================

        posterior_current = (
            posterior_plot
            * posterior_amount
        )

        posterior_line.set_ydata(
            posterior_current
        )

        # --------------------------------------------------------
        # Posterior fill
        #
        # Fade in when the posterior is being formed.
        # --------------------------------------------------------

        posterior_fill.set_alpha(
            0.18
            * posterior_amount
        )

        # ========================================================
        # Posterior mode marker
        # ========================================================

        posterior_marker.set_alpha(
            0.0
            if posterior_amount < 0.5
            else 0.85
        )

        # ========================================================
        # Equation box
        # ========================================================

        if progress < 0.25:

            equation_text.set_text(
                r"$p(\theta)$"
            )

        elif progress < 0.50:

            equation_text.set_text(
                r"$p(D|\theta)$"
            )

        else:

            equation_text.set_text(
                r"$p(\theta|D)"
                r"\propto "
                r"p(\theta)\,p(D|\theta)$"
            )

        # ========================================================
        # Stage label
        # ========================================================

        stage_text.set_text(
            stage
        )

        # ========================================================
        # Return artists
        # ========================================================

        return (
            prior_line,
            likelihood_line,
            posterior_line,
            posterior_fill,
            posterior_marker,
            equation_text,
            stage_text
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
    # Save animation
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


# ================================================================
# Entry point
# ================================================================

if __name__ == "__main__":
    main()
