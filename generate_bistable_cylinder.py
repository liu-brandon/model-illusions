"""
Standalone renderer for the SfM nested cylinders stimulus.
Animates dots moving on rotating cylinders and saves to an mp4 video.

Geometry is taken directly from the config (121_SFM_nested_cylinders).
No strinf / simulation dependencies required.

Usage:
    python render_sfm_video.py                        # bistable (no depth cue)
    python render_sfm_video.py --depth_cue            # control: alpha encodes depth
    python render_sfm_video.py --T 5.0                # 5-second clip
    python render_sfm_video.py --fps 60 --T 10        # 60fps, 10 seconds
    python render_sfm_video.py --height 1.2 --rows 7  # taller cylinder, more dot rows
    python render_sfm_video.py --out my_video.mp4
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse

# ── CLI args ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--T",          type=float, default=5.0,               help="Duration in seconds")
parser.add_argument("--fps",        type=int,   default=30,                help="Frames per second")
parser.add_argument("--out",        type=str,   default="sfm_cylinders.mp4", help="Output filename")
parser.add_argument("--dpi",        type=int,   default=150,               help="Resolution (dpi)")
parser.add_argument("--size",       type=int,   default=512,               help="Frame size in pixels (square)")
parser.add_argument("--dot_r",      type=float, default=5.0,               help="Dot radius in points")
parser.add_argument("--bg",         type=str,   default="black",           help="Background colour")
parser.add_argument("--height",     type=float, default=1.0,               help="Cylinder height in world units")
parser.add_argument("--rows",       type=int,   default=10,                help="Number of dot rows along cylinder height")
parser.add_argument("--depth_cue",  type=float, default=1,                help="Enable depth cue: front dots brighter than rear (breaks bistability)")
parser.add_argument("--K0", type=int, default=25, help="Controls number of dots per row (candidate RF locations)")
parser.add_argument("--radii",  type=float, nargs="+", default=[1.5, 1.0],
                    help="Cylinder radii, one per cylinder e.g. --radii 1.5 1.0 0.5")
parser.add_argument("--omegas", type=float, nargs="+", default=[1.5, 1.0],
                    help="Rotation speeds (multiples of pi/2), one per cylinder")
parser.add_argument("--resolution", type=str, default="512x512")
args = parser.parse_args()

# ── Geometry (copied verbatim from config) ────────────────────────────────────
K0     = args.K0
rfxmax = 1.6
# Rs     = (1.5, 1.0)                           # outer, inner cylinder radii
# Omega  = np.array([1.5, 1.0]) * np.pi / 2.0  # rotational speeds (rad/s)

Rs    = tuple(args.radii)
Omega = np.array(args.omegas) * np.pi / 2.0

assert len(args.radii) == len(args.omegas), \
    "Must supply the same number of --radii and --omegas"

rfxloc = np.linspace(rfxmax, -rfxmax, K0 // 2)

phi, Ks = [], []
for ri in Rs:
    rfxloc_i = np.array([x for x in rfxloc if -ri < x <= ri])
    phi += [np.arccos(rfxloc_i / ri), np.arccos(rfxloc_i / ri) + np.pi]
    Ks.append(2 * len(rfxloc_i))
phi += [[0.0]]   # vestibular dummy — excluded from rendering below
phi = np.concatenate(phi)

K = len(phi)

R_unrolled     = np.ones(K)
Omega_unrolled = np.ones(K)
for (om, ri, idxmin, idxmax) in zip(
    Omega, Rs,
    np.cumsum([0] + Ks[:-1]),
    np.cumsum(Ks),
):
    R_unrolled[idxmin:idxmax]     = ri
    Omega_unrolled[idxmin:idxmax] = om

# Drop the vestibular dummy from rendering
vis_mask           = np.ones(K, dtype=bool)
vis_mask[-1]       = False
phi_vis            = phi[vis_mask]
R_vis              = R_unrolled[vis_mask]
Omega_vis          = Omega_unrolled[vis_mask]
is_outer           = R_vis == Rs[0]   # boolean mask over visible dots

# ── Tile dots across cylinder height ─────────────────────────────────────────
# Each equatorial dot is replicated at `rows` evenly-spaced y levels.
# The x-motion is identical for all rows (same phi, same omega).
y_levels = np.linspace(-args.height / 2, args.height / 2, args.rows)

# phi_tiled   = np.tile(phi_vis,   args.rows)   # shape: (rows * K_vis,)
rng = np.random.default_rng(42)
phi_tiled = np.tile(phi_vis, args.rows) + rng.uniform(0, 2 * np.pi, args.rows * len(phi_vis))

R_tiled     = np.tile(R_vis,     args.rows)
Omega_tiled = np.tile(Omega_vis, args.rows)
is_outer_t  = np.tile(is_outer,  args.rows)
y_tiled     = np.repeat(y_levels, len(phi_vis))   # fixed y per dot

n_dots = len(phi_tiled)

# ── Dot position function ─────────────────────────────────────────────────────
def dot_positions(t):
    """Return x (horizontal screen) and z (depth) for all dots at time t."""
    angle = phi_tiled + Omega_tiled * t
    x = R_tiled * np.sin(angle)
    z = R_tiled * np.cos(angle)
    return x, z

# ── Figure setup ──────────────────────────────────────────────────────────────
fig_inches = args.size / args.dpi
fig, ax = plt.subplots(figsize=(fig_inches, fig_inches), facecolor=args.bg)
ax.set_facecolor(args.bg)
ax.set_aspect("equal")
ax.axis("off")

x_margin = Rs[0] * 1.05
y_margin = args.height / 2 * 1.1
ax.set_xlim(-x_margin, x_margin)
ax.set_ylim(-y_margin, y_margin)

# Colours: outer = warm white, inner = cool blue-white (RGBA, alpha set per-frame)
outer_rgba = np.array([0.94, 0.90, 0.80, 1.0])
inner_rgba = np.array([0.53, 0.73, 1.00, 1.0])

# Build initial colour arrays
colors_init = np.where(
    is_outer_t[:, None],
    outer_rgba[None, :],
    inner_rgba[None, :],
)

scat = ax.scatter(
    np.zeros(n_dots), y_tiled,
    s=args.dot_r**2,
    c=colors_init,
    zorder=3,
    linewidths=0,
)

# ── Animation update ──────────────────────────────────────────────────────────
def update(frame):
    t = frame / args.fps
    x, z = dot_positions(t)

    # Alpha: uniform (bistable) or depth-modulated (control condition)
    if args.depth_cue > 0:
        # Map z/r from [-1, +1] → alpha [0.10, 1.0]
        # Front-facing dots (z > 0) are bright; rear (z < 0) are dim
        norm_depth = z / R_tiled          # in [-1, 1]
        alpha = np.clip(0.10 + 0.90 * (norm_depth + 1) / 2, 1 - args.depth_cue, 1.0)
    else:
        # No depth cue → uniform opacity → bistable percept
        alpha = np.ones(n_dots)

    colors = np.where(
        is_outer_t[:, None],
        outer_rgba[None, :],
        inner_rgba[None, :],
    ).copy()
    colors[:, 3] = alpha

    scat.set_offsets(np.column_stack([x, y_tiled]))
    scat.set_facecolors(colors)

    return (scat,)

# ── Render ────────────────────────────────────────────────────────────────────
n_frames = int(args.T * args.fps)
depth_label = "with depth cue" if args.depth_cue else "bistable (no depth cue)"
print(f"Rendering {n_frames} frames  ({args.T}s @ {args.fps}fps)  [{depth_label}]  →  {args.out}")

ani = animation.FuncAnimation(
    fig, update,
    frames=n_frames,
    interval=1000 / args.fps,
    blit=True,
)

writer = animation.FFMpegWriter(fps=args.fps, bitrate=2000,
                                extra_args=["-pix_fmt", "yuv420p", "-vf", f"scale={args.resolution}"])
ani.save(args.out, writer=writer, dpi=args.dpi)
plt.close(fig)
print(f"Done. Saved to: {args.out}")