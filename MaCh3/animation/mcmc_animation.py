from __future__ import annotations

import argparse
import math
import os
import shutil

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

# MaCh3-inspired palette.
MACH3_BLUE = "#6C9BC2"
MACH3_DARK_BLUE = "#183B56"
MACH3_RED = "#8C2F39"
MACH3_GOLD = "#D7A629"
BG = "#F7F8FA"
GRID = "#D8DEE6"
WHITE = "#FFFFFF"
TEXT = MACH3_DARK_BLUE
PI = np.pi


def angle_diff(x: np.ndarray | float, mu: float) -> np.ndarray | float:
    return (np.asarray(x) - mu + PI) % (2 * PI) - PI


def log_posterior(x: np.ndarray | float) -> np.ndarray | float:
    """Toy periodic, asymmetric delta_CP-like posterior."""
    x = np.asarray(x, dtype=float)
    components = []
    for mu, sigma, weight in (
        (-2.18, 0.43, 0.70),
        (-2.65, 0.78, 0.24),
        (2.85, 0.30, 0.06),
    ):
        d = angle_diff(x, mu)
        components.append(np.log(weight) - 0.5 * (d / sigma) ** 2 - np.log(sigma))

    stacked = np.stack(components, axis=0)
    m = np.max(stacked, axis=0)
    mix = m + np.log(np.sum(np.exp(stacked - m), axis=0))

    d_supp = angle_diff(x, +PI / 2)
    penalty = 2.7 * np.exp(-0.5 * (d_supp / 0.38) ** 2)
    out = mix - penalty
    return float(out) if out.ndim == 0 else out


def metropolis_chain(
    n_steps: int,
    seed: int = 4,
    start: float = 0.0,
    proposal_sigma: float = 0.40,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = float(start)
    lp = float(log_posterior(x))

    states = [x]
    proposals = []
    accepted = []
    alpha_values = []

    for _ in range(n_steps):
        proposal = x + rng.normal(0.0, proposal_sigma)
        proposal = (proposal + PI) % (2 * PI) - PI
        lp_prop = float(log_posterior(proposal))
        alpha = float(np.exp(min(0.0, lp_prop - lp)))
        do_accept = bool(rng.random() < alpha)

        proposals.append(proposal)
        accepted.append(do_accept)
        alpha_values.append(alpha)

        if do_accept:
            x = proposal
            lp = lp_prop
        states.append(x)

    return (
        np.asarray(states),
        np.asarray(proposals),
        np.asarray(accepted, dtype=bool),
        np.asarray(alpha_values),
    )


def circular_kde(samples: np.ndarray, xgrid: np.ndarray, bandwidth: float = 0.11) -> np.ndarray:
    if samples.size == 0:
        return np.zeros_like(xgrid)
    d = angle_diff(xgrid[:, None], samples[None, :]) / bandwidth
    y = np.exp(-0.5 * d * d).sum(axis=1)
    y /= samples.size * bandwidth * np.sqrt(2.0 * np.pi)
    return y


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate a 1D delta_CP-like MCMC posterior.")
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="Overall chain speed multiplier (default: 1.0)",
    )
    parser.add_argument(
        "--transition-time", type=float, default=10.0,
        help="Seconds spent in the proposal/decision view before switching to trace history (default: 10)",
    )
    parser.add_argument("--output", default="mcmc_posterior.mp4")
    parser.add_argument("--seed", type=int, default=4)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()

    if args.duration <= 0 or args.fps <= 0 or args.speed <= 0 or args.transition_time < 0:
        raise SystemExit("duration, fps, speed and transition-time must be valid positive/non-negative values")

    ffmpeg_exe = shutil.which("ffmpeg")
    if ffmpeg_exe is None and imageio_ffmpeg is not None:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    if ffmpeg_exe is None:
        raise SystemExit(
            "ffmpeg was not found. Install with `pip3 install imageio-ffmpeg` "
            "or install ffmpeg system-wide."
        )
    plt.rcParams["animation.ffmpeg_path"] = ffmpeg_exe

    # ------------------------------------------------------------------
    # Timing:
    #   Act 1 = fixed 10 s (or less if the whole movie is shorter)
    #   Act 2 = remainder of movie, deliberately much faster.
    # ------------------------------------------------------------------
    n_frames = max(1, int(round(args.duration * args.fps)))
    slow_frames = max(
        0,
        min(n_frames, int(round(min(args.transition_time, args.duration) * args.fps))),
    )
    fast_frames = max(0, n_frames - slow_frames)

    # Slow first act: proposal move -> hold -> decision -> settle.
    slow_phase_frames = max(6, int(round(args.fps / 3.0)))
    slow_frames_per_step = 4 * slow_phase_frames
    slow_steps = (
        max(1, int(math.ceil(slow_frames / slow_frames_per_step * args.speed)))
        if slow_frames else 0
    )

    # Fast second act: ~3x faster than the first act by default.
    # Each proposal gets only a few frames, so the posterior grows rapidly.
    fast_phase_frames = max(1, int(round(args.fps / 10.0)))
    fast_frames_per_step = 4 * fast_phase_frames
    fast_steps = (
        max(1, int(math.ceil(fast_frames / fast_frames_per_step * args.speed)))
        if fast_frames else 0
    )

    total_chain_steps = max(1, slow_steps + fast_steps)
    states, proposals, accepted, alpha = metropolis_chain(total_chain_steps, seed=args.seed)

    xgrid = np.linspace(-PI, PI, 1200)
    target = np.exp(log_posterior(xgrid))
    target /= np.trapezoid(target, xgrid)
    target /= target.max()

    fig = plt.figure(figsize=(13.0, 7.2), facecolor=BG)
    gs = fig.add_gridspec(
        2, 1, height_ratios=[1.18, 2.55],
        left=0.085, right=0.965, top=0.89, bottom=0.15, hspace=0.22,
    )
    ax_prop = fig.add_subplot(gs[0])
    ax_post = fig.add_subplot(gs[1])

    # ------------------------------------------------------------------
    # TOP PANEL
    # ------------------------------------------------------------------
    # It now has TWO distinct modes with TWO different axis definitions.
    # Act 1: x = delta_CP, y = likelihood-like landscape.
    # Act 2: x = MCMC step, y = delta_CP.
    # ------------------------------------------------------------------
    ax_prop.set_xlim(-PI, PI)
    ax_prop.set_ylim(0, 1.05)
    ax_prop.set_yticks([])
    ax_prop.set_ylabel("proposal", color=TEXT, fontsize=11.5, labelpad=10)

    for ax in (ax_prop, ax_post):
        ax.set_facecolor(BG)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(colors=TEXT, labelsize=10.5)
        ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.65)

    # Proposal landscape: ONLY visible during Act 1.
    target_top, = ax_prop.plot(
        xgrid, 0.14 + 0.54 * target,
        color=MACH3_DARK_BLUE, lw=2.4, alpha=0.34, ls="--",
    )
    current_dot, = ax_prop.plot([], [], "o", ms=11,
                                color=MACH3_BLUE, mec=WHITE, mew=1.7, zorder=7)
    proposal_dot, = ax_prop.plot([], [], "o", ms=13,
                                 color=MACH3_GOLD, mec=WHITE, mew=1.8, zorder=8)

    arrow = ax_prop.annotate(
        "", xy=(0, 0.70), xytext=(0, 0.70),
        arrowprops=dict(arrowstyle="-|>", color=MACH3_GOLD, lw=2.6,
                        mutation_scale=16),
        zorder=6,
    )

    current_label = ax_prop.text(0, 0.86, "current", ha="center", va="bottom",
                                 fontsize=9.5, color=MACH3_BLUE, fontweight="bold")
    proposal_label = ax_prop.text(0, 0.86, "proposal", ha="center", va="bottom",
                                  fontsize=9.5, color=MACH3_GOLD, fontweight="bold")
    decision = ax_prop.text(0.98, 0.88, "", transform=ax_prop.transAxes,
                            ha="right", va="top", fontsize=13.5,
                            fontweight="bold", color=TEXT)
    accept_prob = ax_prop.text(0.98, 0.58, "", transform=ax_prop.transAxes,
                               ha="right", va="top", fontsize=10.5,
                               color=TEXT, alpha=0.78,
                               family="DejaVu Sans Mono")

    # Trace history: x = step number, y = parameter value.
    trace_line, = ax_prop.plot([], [], color=MACH3_DARK_BLUE, lw=1.6, alpha=0.58, zorder=4)
    trace_accepts, = ax_prop.plot([], [], "o", ms=4.2, color=MACH3_BLUE, alpha=0.78, zorder=5)
    trace_current, = ax_prop.plot([], [], "o", ms=9.5, color=MACH3_GOLD, mec=WHITE, mew=1.5, zorder=6)

    trace_title = ax_prop.text(
        0.015, 0.94, "MCMC trace",
        transform=ax_prop.transAxes, ha="left", va="top",
        fontsize=13, fontweight="bold", color=TEXT, alpha=0.0,
    )
    trace_subtitle = ax_prop.text(
        0.015, 0.76, "parameter value vs. MCMC step",
        transform=ax_prop.transAxes, ha="left", va="top",
        fontsize=10.5, color=TEXT, alpha=0.0,
    )
    step_label = ax_prop.text(
        0.98, 0.90, "", transform=ax_prop.transAxes,
        ha="right", va="top", fontsize=10.5, color=TEXT, alpha=0.0,
        family="DejaVu Sans Mono",
    )

    # Tick settings for the trace-mode y axis.
    trace_yticks = [-PI, -PI / 2, 0, PI / 2, PI]
    trace_yticklabels = [r"$-\pi$", r"$-\pi/2$", r"$0$", r"$+\pi/2$", r"$+\pi$"]

    # ------------------------------------------------------------------
    # BOTTOM PANEL: posterior stays in parameter space in both acts.
    # ------------------------------------------------------------------
    ax_post.set_xlim(-PI, PI)
    ax_post.set_ylim(0, 1.08)
    ax_post.set_xlabel(r"$\delta_{CP}$  [rad]", fontsize=14, color=TEXT, labelpad=10)
    ax_post.set_ylabel("posterior density", fontsize=12.5, color=TEXT, labelpad=10)
    ax_post.set_xticks([-PI, -PI / 2, 0, PI / 2, PI])
    ax_post.set_xticklabels([r"$-\pi$", r"$-\pi/2$", r"$0$", r"$+\pi/2$", r"$+\pi$"])

    fig.text(0.085, 0.945, "Markov Chain Monte Carlo", fontsize=25,
             fontweight="bold", color=TEXT)
    fig.text(0.085, 0.912,
             "Propose → accept/reject → accumulate samples",
             fontsize=12.5, color=TEXT, alpha=0.78)

    target_line, = ax_post.plot(
        xgrid, target, color=MACH3_DARK_BLUE, lw=2.5, ls="--", alpha=0.38,
    )
    posterior_line, = ax_post.plot(
        [], [], color=MACH3_BLUE, lw=4.5, solid_capstyle="round",
    )
    sample_ticks, = ax_post.plot([], [], "|", color=MACH3_BLUE, ms=16,
                                 alpha=0.70, mew=1.25)

    legend_handles = [
        Line2D([], [], color=MACH3_DARK_BLUE, lw=2.5, ls="--", alpha=0.5,
               label="target distribution"),
        Line2D([], [], color=MACH3_BLUE, lw=4.5,
               label="posterior from accepted samples"),
    ]
    ax_post.legend(handles=legend_handles, loc="upper left",
                   frameon=False, fontsize=10.5)

    info_box = FancyBboxPatch(
        (0.77, 0.035), 0.20, 0.09, transform=fig.transFigure,
        boxstyle="round,pad=0.012,rounding_size=0.015",
        facecolor=WHITE, edgecolor=GRID, linewidth=1.1,
    )
    fig.patches.append(info_box)
    info = fig.text(0.785, 0.080, "", color=TEXT, fontsize=11.0,
                    family="DejaVu Sans Mono", va="center")

    def set_trace_mode_axes() -> None:
        """Switch the top axis from proposal-space to a true MCMC trace."""
        ax_prop.set_xlim(0, max(1, total_chain_steps))
        ax_prop.set_ylim(-PI, PI)
        ax_prop.set_xlabel("MCMC step", fontsize=12, color=TEXT, labelpad=7)
        ax_prop.set_ylabel(r"$\delta_{CP}$ [rad]", fontsize=11.5, color=TEXT, labelpad=10)
        ax_prop.set_xticks(np.linspace(0, total_chain_steps, min(7, total_chain_steps + 1), dtype=int))
        ax_prop.set_yticks(trace_yticks)
        ax_prop.set_yticklabels(trace_yticklabels)
        ax_prop.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.45)

    def set_proposal_mode_axes() -> None:
        """Restore the proposal-space axes used in Act 1."""
        ax_prop.set_xlim(-PI, PI)
        ax_prop.set_ylim(0, 1.05)
        ax_prop.set_xlabel(r"$\delta_{CP}$ [rad]", fontsize=12, color=TEXT, labelpad=7)
        ax_prop.set_ylabel("proposal", color=TEXT, fontsize=11.5, labelpad=10)
        ax_prop.set_xticks([-PI, -PI / 2, 0, PI / 2, PI])
        ax_prop.set_xticklabels([r"$-\pi$", r"$-\pi/2$", r"$0$", r"$+\pi/2$", r"$+\pi$"])
        ax_prop.set_yticks([])
        ax_prop.grid(axis="x", alpha=0.0)

    def update(frame: int):
        in_slow_act = frame < slow_frames

        if in_slow_act and slow_steps:
            # ----------------------------------------------------------
            # ACT 1: slow, explanatory proposal animation.
            # ----------------------------------------------------------
            set_proposal_mode_axes()

            step_idx = min(frame // slow_frames_per_step, slow_steps - 1)
            within = frame % slow_frames_per_step
            phase = within // slow_phase_frames
            k = within % slow_phase_frames
            u = k / max(1, slow_phase_frames - 1)

            current = states[step_idx]
            proposal = proposals[step_idx]
            did_accept = bool(accepted[step_idx])
            a = float(alpha[step_idx])

            y_current = float(0.14 + 0.54 * np.interp(current, xgrid, target))
            y_prop = float(0.14 + 0.54 * np.interp(proposal, xgrid, target))

            # Hide trace-mode artists completely.
            trace_line.set_data([], [])
            trace_accepts.set_data([], [])
            trace_current.set_data([], [])
            trace_title.set_alpha(0.0)
            trace_subtitle.set_alpha(0.0)
            step_label.set_alpha(0.0)

            if phase == 0:
                d = float(angle_diff(proposal, current))
                x_prop = (current + d * (u * 0.96) + PI) % (2 * PI) - PI
                y_prop_anim = float(0.14 + 0.54 * np.interp(x_prop, xgrid, target))
                decision.set_text("")
                accept_prob.set_text("")
            elif phase == 1:
                x_prop, y_prop_anim = proposal, y_prop
                decision.set_text("")
                accept_prob.set_text(f"acceptance probability  {a:5.2f}")
            elif phase == 2:
                x_prop, y_prop_anim = proposal, y_prop
                decision.set_text("ACCEPT" if did_accept else "REJECT")
                decision.set_color(MACH3_BLUE if did_accept else MACH3_RED)
                accept_prob.set_text(f"acceptance probability  {a:5.2f}")
            else:
                if did_accept:
                    x_prop, y_prop_anim = proposal, y_prop
                else:
                    d_back = float(angle_diff(current, proposal))
                    x_prop = (proposal + d_back * u + PI) % (2 * PI) - PI
                    y_prop_anim = float(0.14 + 0.54 * np.interp(x_prop, xgrid, target))
                accept_prob.set_text("")
                if k == slow_phase_frames - 1:
                    decision.set_text("")

            current_dot.set_data([current], [y_current])
            proposal_dot.set_data([x_prop], [y_prop_anim])
            current_label.set_position((current, min(0.99, y_current + 0.055)))
            current_label.set_visible(True)
            proposal_label.set_position((x_prop, min(0.99, y_prop_anim + 0.055)))
            proposal_label.set_visible(abs(float(angle_diff(x_prop, current))) > 0.025)

            if phase in (0, 1, 2) and abs(float(angle_diff(x_prop, current))) > 0.018:
                arrow.xy = (x_prop, 0.70)
                arrow.set_position((current, 0.70))
                arrow.set_visible(True)
            else:
                arrow.set_visible(False)

            completed = min(step_idx + (1 if phase == 3 else 0), slow_steps)
            samples = proposals[:completed][accepted[:completed]]

        else:
            # ----------------------------------------------------------
            # ACT 2: FAST, CLEAN MCMC TRACE.
            # Top: x=step, y=delta_CP.
            # No proposal dot, no proposal landscape, no proposal labels.
            # ----------------------------------------------------------
            set_trace_mode_axes()

            fast_frame = max(0, frame - slow_frames)
            if fast_steps:
                fast_step_idx = min(fast_frame // fast_frames_per_step, fast_steps - 1)
                within = fast_frame % fast_frames_per_step
                phase = within // fast_phase_frames
            else:
                fast_step_idx = 0
                phase = 3

            step_idx = min(slow_steps + fast_step_idx, total_chain_steps - 1)

            # Hide proposal-specific artists.
            target_top.set_alpha(0.0)
            current_dot.set_data([], [])
            proposal_dot.set_data([], [])
            arrow.set_visible(False)
            current_label.set_visible(False)
            proposal_label.set_visible(False)
            decision.set_text("")
            accept_prob.set_text("")

            # Trace includes the current state at each MCMC step.
            trace_end = min(total_chain_steps + 1, step_idx + 2)
            trace_steps = np.arange(trace_end)
            trace_values = states[:trace_end]

            trace_line.set_data(trace_steps, trace_values)

            # Accepted moves are the points where state i+1 differs from state i
            # because proposal i was accepted.
            acc_indices = np.flatnonzero(accepted[: max(0, trace_end - 1)]) + 1
            if acc_indices.size:
                trace_accepts.set_data(acc_indices, states[acc_indices])
            else:
                trace_accepts.set_data([], [])

            trace_current.set_data([trace_steps[-1]], [trace_values[-1]])
            trace_title.set_alpha(1.0)
            trace_subtitle.set_alpha(0.72)
            step_label.set_alpha(0.75)
            step_label.set_text(f"step {trace_steps[-1]:4d}")

            completed = min(trace_end - 1, total_chain_steps)
            samples = proposals[:completed][accepted[:completed]]

        # Restore target landscape in proposal mode only.
        if in_slow_act and slow_steps:
            target_top.set_alpha(0.34)

        # --------------------------------------------------------------
        # Shared bottom posterior.
        # --------------------------------------------------------------
        dpost = circular_kde(samples, xgrid, bandwidth=0.105)
        if dpost.max() > 0:
            dpost /= dpost.max()
        posterior_line.set_data(xgrid, dpost)
        if samples.size:
            sample_ticks.set_data(samples, np.full(samples.shape, 0.026))
        else:
            sample_ticks.set_data([], [])

        if completed:
            info.set_text(
                f"accepted samples  {samples.size:4d}\n"
                f"acceptance rate   {100.0 * accepted[:completed].mean():5.1f}%"
            )
        else:
            info.set_text("accepted samples     0\nacceptance rate       —")

        return (
            current_dot, proposal_dot, current_label, proposal_label,
            arrow, decision, accept_prob, trace_line, trace_accepts, trace_current,
            trace_title, trace_subtitle, step_label, posterior_line, sample_ticks, info,
        )

    # Ensure the first frame is in proposal mode even when transition-time is 0.
    if slow_frames == 0:
        target_top.set_alpha(0.0)

    anim = FuncAnimation(
        fig, update, frames=n_frames,
        interval=1000 / args.fps, blit=False, repeat=False,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    writer = FFMpegWriter(
        fps=args.fps, codec="libx264", bitrate=7000,
        extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    anim.save(args.output, writer=writer, dpi=args.dpi)
    plt.close(fig)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
