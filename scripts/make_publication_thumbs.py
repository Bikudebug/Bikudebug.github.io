#!/usr/bin/env python3
"""Generate the thumbnails used on /publications/ and /projects/.

The publication originals were sports GIFs, several of them enormous
(diving_star.gif was 10.4 MB, BackFlop_diving.gif 4.9 MB) for a slot the page
renders at 190x120. Each is a small schematic of what the work actually does,
drawn in one shared style so both lists read as a set. Projects that are the
same work as a paper reuse that paper's thumbnail.

Every thumbnail is written twice: a still PNG, and an animated GIF in which the
action plays out inside the frame. Each drawing function takes a progress
argument `u` running 0 -> 1, and the frame at u=1 is the still. That is the
whole discipline of the animation: nothing is invented for the last frame, so
the GIF settles onto the composition the still already had, holds it, and
replays. The action is a loop of a clip, not a decoration bolted on top.

Run from the repository root:
    python scripts/make_publication_thumbs.py
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

IMAGES = Path(__file__).resolve().parent.parent / "images"

# 2x the 190x120 slot in the publication list, for high-DPI screens
W, H = 760, 480
S = 2

BG = (246, 248, 250)      # --global-code-background-color
INK = (9, 105, 218)       # --global-link-color
FADE = (152, 187, 230)
GROUND = (188, 198, 208)
LABEL = (31, 35, 40)
MUTED = (122, 132, 142)
DANGER = (207, 34, 46)    # the one non-blue accent, for the flagged defect

# Joint coordinates below are given in a LOCAL_W x LOCAL_H box, y downwards.
# The lowest ankle sits near y=125, so a box height of 132 puts the feet on the
# ground line rather than floating above it.
LOCAL_W, LOCAL_H = 100, 132

BONES = [
    ("neck", "pelvis"),
    ("neck", "elbow_r"), ("elbow_r", "wrist_r"),
    ("neck", "elbow_l"), ("elbow_l", "wrist_l"),
    ("pelvis", "knee_r"), ("knee_r", "ankle_r"),
    ("pelvis", "knee_l"), ("knee_l", "ankle_l"),
]

JOINTS = ("pelvis", "elbow_r", "wrist_r", "elbow_l", "wrist_l",
          "knee_r", "ankle_r", "knee_l", "ankle_l")

# Animation. GIF_W x GIF_H is the 190x120 slot at 2x, which is what the still
# PNG is drawn for as well; the frames are rendered on the full 760x480 canvas
# and scaled down, so the GIF and the PNG are the same drawing at the same size.
#
# GIF_MS x GIF_FRAMES is roughly 1.8s of motion, then the last frame is held for
# GIF_HOLD_MS. The hold is the point: a figure in continuous motion in a 190px
# box on a list of ten of them is unreadable, and the composition the still was
# designed as is the thing worth looking at. So each loop plays the action once,
# comes to rest on the still, and waits.
GIF_W, GIF_H = 380, 240
GIF_FRAMES = 26
GIF_MS = 70
GIF_HOLD_MS = 1800
GIF_COLORS = 96


# --------------------------------------------------------------------------- #
# drawing helpers
# --------------------------------------------------------------------------- #

def font(size, bold=True):
    names = ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf") if bold else \
            ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


# --------------------------------------------------------------------------- #
# animation helpers
#
# Every one of these is written so that its value at u=1 is exactly what the
# still drew. That is what lets the same code produce both files, and it is why
# `fade` starts from BG rather than using real transparency: on a flat
# background a colour walked out of BG reads as a fade-in, costs no alpha
# channel, and lands on the still's own colour when it arrives.
# --------------------------------------------------------------------------- #

def clamp(t, lo=0.0, hi=1.0):
    return lo if t < lo else hi if t > hi else t


def ease(t):
    """Smoothstep. Used per phase, so the figure settles into each pose."""
    t = clamp(t)
    return t * t * (3 - 2 * t)


def stage(u, start, end):
    """Progress through one stage of the loop, 0 before it and 1 after it."""
    return ease((u - start) / (end - start)) if end > start else float(u >= end)


def fade(colour, t):
    """`colour` emerging from the page background. t=1 is the colour itself."""
    return lerp(BG, colour, clamp(t))


def morph(a, b, t):
    """Interpolate two pose dicts joint by joint."""
    return {k: (a[k][0] + (b[k][0] - a[k][0]) * t,
                a[k][1] + (b[k][1] - a[k][1]) * t)
            for k in a if k in b}


def offset_pose(pose, a, b, t):
    """`pose` displaced by t of the a -> b movement, joint by joint.

    Lets one authored movement be applied to several different figures, which is
    how the retrieved neighbours perform the query's motion without each of them
    needing a second keyframe written out by hand.
    """
    return {k: (pose[k][0] + (b[k][0] - a[k][0]) * t,
                pose[k][1] + (b[k][1] - a[k][1]) * t)
            for k in pose if k in a and k in b}


def mid_point(p0, p1, t):
    return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)


def relay(u, count, lead=0.16):
    """How a phase strip of `count` cells fills in. A generator of the cells
    that exist yet, as (index, progress through this cell's move, opacity).

    The strip animates as a relay, not as one figure walking across it. Cell 0
    appears; every cell after it appears holding the pose the cell before it
    finished on, and then moves out of that pose into its own. So the movement
    is handed along the strip and no figure ever leaves its own cell.

    The first draft did have a single figure travel the whole width, depositing
    a copy in each cell. It was wrong: a cell is only about a fifth wider than
    the figure standing in it, so in transit the traveller sat squarely on top
    of the copy it had just left, and the mesh-bodied strips turned into a
    two-headed blot halfway through every phase.
    """
    slot = (1 - lead) / max(1, count - 1)
    for i in range(count):
        start = 0.0 if i == 0 else lead + slot * (i - 1)
        span = lead if i == 0 else slot
        if u < start:
            return
        run = clamp((u - start) / span)
        yield i, ease(run), min(1.0, run / 0.45)


def relay_pose(poses, i, progress):
    """The pose cell `i` holds: out of its predecessor's pose and into its own."""
    return morph(poses[max(i - 1, 0)], poses[i], progress)


def canvas():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def chrome(d, title, caption, baseline, caption_y=None):
    """Title top-left, caption under the baseline. Shared by every thumbnail."""
    d.text((20 * S, 12 * S), title, font=font(19 * S), fill=LABEL)
    d.text((20 * S, caption_y if caption_y is not None else baseline + 9 * S),
           caption, font=font(12 * S), fill=MUTED)


def dashed(d, p0, p1, colour, width, dash=6 * S, gap=6 * S):
    x0, y0 = p0
    x1, y1 = p1
    total = math.hypot(x1 - x0, y1 - y0)
    if total == 0:
        return
    ux, uy = (x1 - x0) / total, (y1 - y0) / total
    pos = 0.0
    while pos < total:
        end = min(pos + dash, total)
        d.line([(x0 + ux * pos, y0 + uy * pos), (x0 + ux * end, y0 + uy * end)],
               fill=colour, width=width)
        pos = end + gap


def skeleton(d, pose, ox, oy, bw, bh, colour, lw=None, head_r=6.5, joint_r=None):
    """Map a pose from its local box onto the canvas and stroke it."""
    def pt(joint):
        x, y = pose[joint]
        return (ox + x / LOCAL_W * bw, oy + y / LOCAL_H * bh)

    lw = lw or max(2, int(3 * S))
    for a, b in BONES:
        if a in pose and b in pose:
            d.line([pt(a), pt(b)], fill=colour, width=lw)

    # The head radius comes off the *height* mapping. Cells are much narrower
    # than they are tall, so scaling it by bw shrinks the head to a pinhead in
    # the four-phase layouts while leaving it correct in the wide ones. Kept
    # deliberately small: BONES has no shoulder line, so a larger circle reaches
    # down to the neck joint and the arms look like they sprout from the jaw.
    # Filled with the background so it occludes limbs drawn behind it - that is
    # what lets the inverted diver reach both arms straight past the head
    # instead of having to swing them wide around it.
    hx, hy = pt("head")
    r = head_r / LOCAL_H * bh
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=BG, outline=colour, width=lw)

    # BONES has no head-neck edge (it would strike through the circle on
    # upright figures), so stroke the neck from the circle's edge instead -
    # without it the head floats free on any tilted or inverted pose.
    nx, ny = pt("neck")
    dist = math.hypot(nx - hx, ny - hy)
    if dist > r:
        ux, uy = (nx - hx) / dist, (ny - hy) / dist
        d.line([(hx + ux * r, hy + uy * r), (nx, ny)], fill=colour, width=lw)

    jr = joint_r or max(2, int(2.2 * S))
    for joint in JOINTS:
        if joint in pose:
            jx, jy = pt(joint)
            d.ellipse([jx - jr, jy - jr, jx + jr, jy + jr], fill=colour)
    return pt


def bezier(p0, control, p1, t):
    """Quadratic interpolation, for a path that has to bend around something."""
    return tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b
                 for a, c, b in zip(p0, control, p1))


def curve_at(p0, p1, lift, t):
    """The point at `t` along the same quadratic arc dotted_curve draws."""
    cx = (p0[0] + p1[0]) / 2
    cy = (p0[1] + p1[1]) / 2 - lift
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t ** 2 * p1[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t ** 2 * p1[1])


def dotted_curve(d, p0, p1, lift, colour, width, dots=22, upto=1.0):
    """A dotted quadratic arc from p0 to p1, `lift` pixels above the chord.

    `upto` truncates it, so the path can be laid down behind a ball in flight
    rather than being there before the ball has been struck.
    """
    r = max(1, int(width))
    for i in range(dots + 1):
        t = i / dots
        if t > upto or i % 2:
            continue
        x, y = curve_at(p0, p1, lift, t)
        d.ellipse([x - r, y - r, x + r, y + r], fill=colour)


def arrow(d, x0, x1, y, colour):
    d.line([(x0, y), (x1, y)], fill=colour, width=max(2, int(2 * S)))
    d.polygon([(x1 + 7 * S, y), (x1, y - 5 * S), (x1, y + 5 * S)], fill=colour)


def timeline(d, x0, x1, y, h, segments, ticks=True):
    """An outlined track with filled segments given as (start, end, colour).

    A segment may carry a fourth item, the fraction of itself that has been
    found so far: it then grows out of its own start, and its boundary ticks
    only appear once it is complete. An empty track is a track the detector has
    not run on yet, which is where every animated timeline here begins.
    """
    d.rounded_rectangle([x0, y, x1, y + h], radius=5 * S,
                        outline=GROUND, width=max(2, int(1.6 * S)))
    span = x1 - x0
    for segment in segments:
        start, end, colour = segment[:3]
        grown = start + (end - start) * (segment[3] if len(segment) > 3 else 1.0)
        px0, px1 = x0 + span * start, x0 + span * grown
        if px1 - px0 < 2:
            continue
        # A bar narrower than its own corner radius cannot be rounded, and the
        # first frames of a growing segment are exactly that.
        d.rounded_rectangle([px0, y + 3 * S, px1, y + h - 3 * S],
                            radius=min(3 * S, (px1 - px0) / 2), fill=colour)
    if ticks:
        for segment in segments:
            if len(segment) > 3 and segment[3] < 0.999:
                continue
            for frac in segment[:2]:
                x = x0 + span * frac
                dashed(d, (x, y + h + 4 * S), (x, y + h + 30 * S), GROUND,
                       max(1, int(1.2 * S)), dash=4 * S, gap=4 * S)


def implement(d, anchor, angle_deg, back, fwd, colour, width, bounds=None):
    """A straight implement (javelin) through `anchor` at `angle_deg`."""
    ax, ay = anchor
    dx, dy = math.cos(math.radians(angle_deg)), -math.sin(math.radians(angle_deg))
    p0 = (ax - dx * back, ay - dy * back)
    p1 = (ax + dx * fwd, ay + dy * fwd)
    if bounds:
        lo_x, hi_x = bounds
        p0 = (min(max(p0[0], lo_x), hi_x), p0[1])
        p1 = (min(max(p1[0], lo_x), hi_x), p1[1])
    d.line([p0, p1], fill=colour, width=width)


def phase_grid(d, n, pad_x, pad_top, baseline, divider=True):
    """Ground line plus dashed dividers; returns the cell width."""
    usable = W - 2 * pad_x
    cell = usable / n
    d.line([(pad_x, baseline), (W - pad_x, baseline)],
           fill=GROUND, width=max(2, int(1.5 * S)))
    if divider:
        for i in range(1, n):
            x = pad_x + cell * i
            dashed(d, (x, pad_top - 6 * S), (x, baseline), GROUND,
                   max(1, int(1.2 * S)))
    return cell


def sequence(title, caption, poses, extras=None, water=False, u=1.0):
    """The shared left-to-right phase layout used by the motion thumbnails.

    Animated, the cells take the movement up one after another - see relay().
    `extras` is handed a fractional position along the whole sequence rather
    than an integer index, so an implement in the hand swings and releases with
    the figure instead of jumping between four fixed states.
    """
    img, d = canvas()
    pad_x, pad_top = 20 * S, 38 * S
    baseline = H - 30 * S
    cell = phase_grid(d, len(poses), pad_x, pad_top, baseline)
    box_h = baseline - pad_top

    if water:
        # The diver stands on a board over the first cell and is airborne over
        # the rest, so only the water gets a wavy line - a flat rule all the way
        # across would read as him standing on the pool surface.
        d.rectangle([pad_x, baseline - 2 * S, W - pad_x, baseline + 3 * S], fill=BG)
        d.line([(pad_x, baseline), (pad_x + cell * 0.95, baseline)],
               fill=GROUND, width=max(3, int(2.5 * S)))
        step = 10 * S
        x = pad_x + cell
        up = True
        while x < W - pad_x:
            nx = min(x + step, W - pad_x)
            d.line([(x, baseline + (2 * S if up else -2 * S)),
                    (nx, baseline + (-2 * S if up else 2 * S))],
                   fill=GROUND, width=max(2, int(1.5 * S)))
            x, up = nx, not up

    for i, progress, alpha in relay(u, len(poses)):
        colour = fade(lerp(FADE, INK, i / max(1, len(poses) - 1)), alpha)
        ox = pad_x + cell * i + cell * 0.08
        bw = cell * 0.84
        pt = skeleton(d, relay_pose(poses, i, progress),
                      ox, pad_top, bw, box_h, colour)
        if extras:
            extras(d, max(i - 1, 0) + progress if i else 0.0,
                   pt, colour, ox, bw, pad_top, box_h)

    chrome(d, title, caption, baseline)
    return img


def save(img, name):
    path = IMAGES / name
    img.save(path, optimize=True)
    print(f"  {name:28s} {path.stat().st_size / 1024:6.1f} KB")


def save_gif(draw, name, frames=GIF_FRAMES, colors=GIF_COLORS):
    """Render `draw(u)` for u across 0..1 and write it as a looping GIF.

    One palette is built from every frame at once and then forced onto all of
    them. Quantising each frame on its own picks a slightly different set of
    colours for each, which both defeats the frame-to-frame differencing that
    keeps these files small and makes the background shimmer as it plays.

    The finished still leads and carries the long hold, and the motion runs
    behind it: u = 1, then u = 0 .. just under 1, then round again. Perceptually
    that is the same loop either way round - settle, hold, replay - but it puts
    the complete picture in frame one, so anything that shows a GIF without
    playing it shows the composition rather than an empty background. The join
    back to the front is seamless because the frame after the last one is u = 1.
    """
    order = [1.0] + [k / frames for k in range(frames)]
    seq = [draw(u).resize((GIF_W, GIF_H), Image.LANCZOS) for u in order]

    strip = Image.new("RGB", (GIF_W, GIF_H * len(seq)))
    for i, frame in enumerate(seq):
        strip.paste(frame, (0, i * GIF_H))
    palette = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    flat = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in seq]

    path = IMAGES / name
    flat[0].save(path, save_all=True, append_images=flat[1:], loop=0,
                 duration=[GIF_HOLD_MS] + [GIF_MS] * (len(flat) - 1),
                 optimize=True)
    print(f"  {name:28s} {path.stat().st_size / 1024:6.1f} KB  "
          f"{len(flat)} frames")


def emit(draw, stem):
    """Write both files for one thumbnail: the still, and the loop."""
    save(draw(1.0), stem + ".png")
    save_gif(draw, stem + ".gif")


# --------------------------------------------------------------------------- #
# 3D mesh body - used only by the two Apollo Sports dashboard thumbnails
#
# Both of those pipelines lift a single video to a body mesh, so their figures
# are drawn as shaded volumes under a wire grid instead of as stick skeletons.
# They still take the same pose dicts as skeleton(): the shoulder and hip
# corners of the trunk are derived from the neck-pelvis axis, so nothing has to
# be re-authored to switch a figure between the two styles.
# --------------------------------------------------------------------------- #

# Half-widths across the body at each joint. These are given on the *height*
# scale, like the head radius in skeleton(), and converted through bh - a cell
# is much narrower than it is tall, so widths taken off bw would give a fat body
# in the wide layouts and a snake in the phase grids. The numbers are ordinary
# human proportions: shoulders a quarter of standing height, an upper arm a
# twelfth of it.
MESH_R = dict(neck=13.0, pelvis=10.5, shoulder=4.2, elbow=3.4, wrist=2.6,
              hip=5.0, knee=4.0, ankle=2.6, foot=2.2)

# How far out along the shoulder / hip line each limb hangs from the spine.
# Both are set so that the joint plus the limb's own radius still falls inside
# the trunk: a cap that pokes out past the silhouette has no wire on it, and
# reads as a bare lump stuck to the shoulder on any pose whose arm crosses the
# body instead of leaving it.
MESH_ATTACH = dict(shoulder=8.5, hip=5.2)


def _pale(colour, t):
    """A fill for a volume: t=0 is the page background, t=1 the wire colour."""
    return lerp(BG, colour, t)


def mesh_limb(d, p0, p1, r0, r1, fill, wire, lw, rings=2):
    """One tapered segment - a filled volume, rounded ends, rings across it.

    The rings bow toward the far end rather than being drawn straight across.
    Straight cross-lines read as a ladder; a bowed one reads as a band round
    something round, which is the whole point of drawing a mesh and not a bone.
    """
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    edge_a = [(p0[0] + nx * r0, p0[1] + ny * r0), (p1[0] + nx * r1, p1[1] + ny * r1)]
    edge_b = [(p0[0] - nx * r0, p0[1] - ny * r0), (p1[0] - nx * r1, p1[1] - ny * r1)]
    d.polygon(edge_a + edge_b[::-1], fill=fill)
    # rounded ends, so two consecutive segments meet without a notch at the joint
    for (cx, cy), r in ((p0, r0), (p1, r1)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)

    thin = max(1, int(lw * 0.6))
    d.line(edge_a, fill=wire, width=lw)
    d.line(edge_b, fill=wire, width=lw)
    for i in range(1, rings + 1):
        t = i / (rings + 1)
        cx, cy = p0[0] + dx * t, p0[1] + dy * t
        r = r0 + (r1 - r0) * t
        d.line([(cx + nx * r, cy + ny * r),
                (cx + ux * r * 0.6, cy + uy * r * 0.6),
                (cx - nx * r, cy - ny * r)], fill=wire, width=thin, joint="curve")


def mesh_trunk(d, neck, pelvis, r_top, r_bot, fill, wire, lw, rows=3, cols=3):
    """The torso as a quad from the shoulder line to the hip line, gridded."""
    dx, dy = pelvis[0] - neck[0], pelvis[1] - neck[1]
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux

    sl = (neck[0] + nx * r_top, neck[1] + ny * r_top)
    sr = (neck[0] - nx * r_top, neck[1] - ny * r_top)
    hl = (pelvis[0] + nx * r_bot, pelvis[1] + ny * r_bot)
    hr = (pelvis[0] - nx * r_bot, pelvis[1] - ny * r_bot)

    def P(u, v):
        top = (sl[0] + (sr[0] - sl[0]) * u, sl[1] + (sr[1] - sl[1]) * u)
        bot = (hl[0] + (hr[0] - hl[0]) * u, hl[1] + (hr[1] - hl[1]) * u)
        return (top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v)

    d.polygon([sl, sr, hr, hl], fill=fill)
    thin = max(1, int(lw * 0.6))
    for i in range(1, rows):
        v = i / rows
        mid = P(0.5, v)
        d.line([P(0, v), (mid[0] + ux * r_top * 0.45, mid[1] + uy * r_top * 0.45),
                P(1, v)], fill=wire, width=thin, joint="curve")
    for i in range(1, cols):
        u = i / cols
        d.line([P(u, 0), P(u, 1)], fill=wire, width=thin)
    d.line([sl, sr], fill=wire, width=lw)
    d.line([hl, hr], fill=wire, width=lw)
    d.line([sl, hl], fill=wire, width=lw)
    d.line([sr, hr], fill=wire, width=lw)


def mesh_head(d, centre, r, fill, wire, lw):
    """A head as a small sphere: two wire circles inside the silhouette."""
    cx, cy = centre
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=wire, width=lw)
    # Below roughly 13 canvas px the two inner circles stop reading as latitude
    # and longitude and just fill the head in, so they are dropped instead.
    if r > 6.5 * S:
        thin = max(1, int(lw * 0.6))
        d.ellipse([cx - r * 0.44, cy - r, cx + r * 0.44, cy + r],
                  outline=wire, width=thin)
        d.ellipse([cx - r, cy - r * 0.36, cx + r, cy + r * 0.36],
                  outline=wire, width=thin)


def mesh_figure(d, pose, ox, oy, bw, bh, colour, scale=1.0, head_r=8.0,
                facing=1, shadow_at=None, alpha=1.0):
    """Draw a pose as a shaded body mesh. Returns the local->canvas mapper.

    The trail side is drawn first in a darker fill, then the trunk over it, then
    the lead side: opaque fills do the occlusion, which is what makes the body
    read as one solid volume rather than as a wireframe of everything at once.
    """
    def pt(joint):
        x, y = pose[joint]
        return (ox + x / LOCAL_W * bw, oy + y / LOCAL_H * bh)

    def r(key):
        return MESH_R[key] / LOCAL_H * bh * scale

    lw = max(2, int(1.8 * S))
    neck, pelvis = pt("neck"), pt("pelvis")
    tdx, tdy = pelvis[0] - neck[0], pelvis[1] - neck[1]
    tl = math.hypot(tdx, tdy) or 1
    tnx, tny = -tdy / tl, tdx / tl  # points to screen left on an upright figure

    def attach(base, key, side):
        w = MESH_ATTACH[key] / LOCAL_H * bh * scale * (1 if side == "l" else -1)
        # Shoulders are tucked a little way down the spine. Level with the
        # shoulder line, the rounded cap of the upper arm stands above it and
        # reads as a shoulder pad rather than as a deltoid.
        along = 0.12 * tl if key == "shoulder" else 0.0
        return (base[0] + tnx * w + tdx / tl * along,
                base[1] + tny * w + tdy / tl * along)

    if shadow_at is not None:
        ax = (pt("ankle_l")[0] + pt("ankle_r")[0]) / 2
        sx, sy = bw * 0.30, 4.5 * S
        # `alpha` is only here for the shadow. Everywhere else a figure fades by
        # being handed a paler `colour`, but the shadow is not drawn in the
        # figure's colour, so without this it would snap in under a body that is
        # still arriving.
        d.ellipse([ax - sx, shadow_at - sy, ax + sx, shadow_at + sy],
                  fill=fade(lerp(BG, GROUND, 0.75), alpha))

    def side_limbs(side, fill):
        sh = attach(neck, "shoulder", side)
        hip = attach(pelvis, "hip", side)
        mesh_limb(d, sh, pt("elbow_" + side), r("shoulder"), r("elbow"),
                  fill, colour, lw)
        mesh_limb(d, pt("elbow_" + side), pt("wrist_" + side), r("elbow"),
                  r("wrist"), fill, colour, lw, rings=1)
        mesh_limb(d, hip, pt("knee_" + side), r("hip"), r("knee"), fill, colour, lw)
        ankle = pt("ankle_" + side)
        mesh_limb(d, pt("knee_" + side), ankle, r("knee"), r("ankle"),
                  fill, colour, lw)
        mesh_limb(d, ankle, (ankle[0] + facing * r("ankle") * 2.4, ankle[1]),
                  r("ankle"), r("foot"), fill, colour, lw, rings=0)

    # Three tones, darkest at the back. The near side is deliberately a shade
    # darker than the trunk as well: a golf finish or a forehand swings the near
    # arm right across the chest, and drawn in the trunk's own tone it merges
    # into it and takes the trunk's outline with it.
    side_limbs("l", _pale(colour, 0.44))
    mesh_trunk(d, neck, pelvis, r("neck"), r("pelvis"),
               _pale(colour, 0.26), colour, lw)
    mesh_head(d, pt("head"), head_r / LOCAL_H * bh, _pale(colour, 0.20),
              colour, lw)
    side_limbs("r", _pale(colour, 0.35))
    return pt


def orbit(d, centre, rx, ry, colour, width):
    """A ring under the figure with an arrow head running down its right side.

    Stands in for the dashboard's orbit control: a mesh you can turn is the one
    claim a still frame of a 3D reconstruction cannot make on its own. Drawn as
    a continuous outline rather than a dotted one - dotted, it dissolves into a
    few grey specks by the time the thumbnail is down to 190px.
    """
    cx, cy = centre
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
              outline=colour, width=max(2, int(width)))
    # The head goes at the right extreme, where the tangent to a ground-plane
    # ellipse is vertical, so pointing it straight down runs along the ring. It
    # is kept off the near arc: there the ring passes under the feet, and an
    # arrow head landing on them reads as a dropped object.
    hx, hy = cx + rx, cy
    d.polygon([(hx, hy + 10 * S), (hx - 5.5 * S, hy - 2 * S),
               (hx + 5.5 * S, hy - 2 * S)], fill=colour)


# --------------------------------------------------------------------------- #
# 1. Throwing4 - four phases of a throw
# --------------------------------------------------------------------------- #

THROW_POSES = [
    dict(head=(50, 18), neck=(50, 32), pelvis=(50, 68),
         elbow_r=(62, 44), wrist_r=(71, 35), elbow_l=(38, 46), wrist_l=(30, 56),
         knee_r=(62, 95), ankle_r=(67, 125), knee_l=(36, 92), ankle_l=(29, 124)),
    dict(head=(52, 15), neck=(52, 29), pelvis=(50, 65),
         elbow_r=(66, 38), wrist_r=(78, 30), elbow_l=(38, 40), wrist_l=(27, 34),
         knee_r=(64, 90), ankle_r=(74, 121), knee_l=(34, 94), ankle_l=(24, 123)),
    dict(head=(50, 17), neck=(50, 30), pelvis=(52, 67),
         elbow_r=(66, 22), wrist_r=(81, 10), elbow_l=(34, 38), wrist_l=(23, 28),
         knee_r=(62, 92), ankle_r=(69, 124), knee_l=(38, 94), ankle_l=(30, 124)),
    dict(head=(48, 19), neck=(48, 32), pelvis=(52, 69),
         elbow_r=(34, 35), wrist_r=(22, 27), elbow_l=(60, 41), wrist_l=(70, 49),
         knee_r=(66, 93), ankle_r=(77, 121), knee_l=(40, 96), ankle_l=(30, 124)),
]


def throwing4(u=1.0):
    def shot(d, i, pt, colour, ox, bw, oy, bh):
        if i >= 2.9:            # released, and out of the cell
            return
        if i <= 2:              # in the hand, through the wind-up and the cock
            wx, wy = pt("wrist_r")
        else:
            # Between the cock and the recovery the shot is in the air. It
            # leaves along the line the hand was travelling, up and to the
            # right, and is off the canvas by the time the arm has come down.
            t = i - 2
            wx, wy = ox + bw * (0.81 + 1.15 * t), oy + bh * (0.076 - 0.05 * t)
        r = 5 / LOCAL_W * bw
        d.ellipse([wx - r, wy - r, wx + r, wy + r], fill=colour)

    return sequence("Throwing4", "phase-aligned throwing sequence",
                    THROW_POSES, extras=shot, u=u)


# --------------------------------------------------------------------------- #
# 2. Javelin - biomechanical phases, athlete facing right
# --------------------------------------------------------------------------- #

JAVELIN_POSES = [
    # run-up, javelin carried alongside the head at shoulder height
    dict(head=(52, 18), neck=(52, 32), pelvis=(50, 68),
         elbow_r=(42, 44), wrist_r=(32, 42), elbow_l=(62, 42), wrist_l=(70, 50),
         knee_r=(64, 92), ankle_r=(72, 120), knee_l=(36, 92), ankle_l=(28, 122)),
    # plant, torso leaning back, throwing arm fully withdrawn
    dict(head=(48, 22), neck=(48, 36), pelvis=(44, 70),
         elbow_r=(34, 42), wrist_r=(22, 46), elbow_l=(60, 38), wrist_l=(70, 30),
         knee_r=(66, 92), ankle_r=(78, 120), knee_l=(32, 96), ankle_l=(22, 124)),
    # release, arm extended up and forward. The head sits back and left of the
    # throwing shoulder so the raised elbow clears the head circle - drawn any
    # closer, the arm and javelin line up into a skewer through the face.
    dict(head=(38, 16), neck=(48, 34), pelvis=(50, 68),
         elbow_r=(64, 26), wrist_r=(78, 12), elbow_l=(32, 44), wrist_l=(22, 52),
         knee_r=(62, 92), ankle_r=(68, 122), knee_l=(38, 94), ankle_l=(30, 124)),
    # recovery, javelin already in flight
    dict(head=(50, 20), neck=(50, 34), pelvis=(50, 70),
         elbow_r=(62, 44), wrist_r=(72, 54), elbow_l=(38, 44), wrist_l=(30, 52),
         knee_r=(60, 94), ankle_r=(66, 122), knee_l=(40, 94), ankle_l=(34, 124)),
]

# (angle, tail length, tip length) as fractions of the cell width. The release
# frame gets almost no tail: the javelin is leaving the hand, and a long tail
# there runs straight through the athlete's head.
JAVELIN_SPEAR = [(10, 0.20, 0.40), (20, 0.16, 0.42), (34, 0.03, 0.44), None]


def javelin(u=1.0):
    def spear(d, i, pt, colour, ox, bw, oy, bh):
        lw = max(2, int(2.2 * S))
        bounds = (ox - bw * 0.06, ox + bw * 1.02)
        if i <= 2:
            # Carried, withdrawn, then thrown: the three states are three points
            # on one continuous rotation, so the angle and the two lengths are
            # simply interpolated and the javelin swings up with the arm.
            j = min(int(i), 1)
            f = i - j
            angle, back, fwd = (a + (b - a) * f for a, b
                                in zip(JAVELIN_SPEAR[j], JAVELIN_SPEAR[j + 1]))
            implement(d, pt("wrist_r"), angle, bw * back, bw * fwd,
                      colour, lw, bounds)
        else:
            # Released. It slides out of the hand it left - the tail grows as
            # the tip pulls away - and flattens towards its flight angle, which
            # is the state the recovery cell was already drawn in.
            t = i - 2
            hand = (ox + bw * 0.78, oy + bh * 12 / LOCAL_H)
            anchor = mid_point(hand, (ox + bw * 0.55, oy + bh * 0.015), t)
            implement(d, anchor, 34 + (16 - 34) * t,
                      bw * (0.03 + 0.31 * t), bw * (0.44 - 0.10 * t),
                      colour, lw, bounds)

    return sequence("Javelin", "biomechanical phase segmentation",
                    JAVELIN_POSES, extras=spear, u=u)


# --------------------------------------------------------------------------- #
# 3. Diving - takeoff, tuck, open, entry
# --------------------------------------------------------------------------- #

DIVE_POSES = [
    # takeoff: upright on the board, arms spread
    dict(head=(50, 24), neck=(50, 40), pelvis=(50, 76),
         elbow_r=(70, 40), wrist_r=(88, 34), elbow_l=(30, 40), wrist_l=(12, 34),
         knee_r=(56, 100), ankle_r=(56, 124), knee_l=(44, 100), ankle_l=(44, 124)),
    # pike: folded at the hips, hands reaching for the toes
    dict(head=(24, 42), neck=(34, 54), pelvis=(52, 84),
         elbow_r=(46, 44), wrist_r=(64, 36), elbow_l=(44, 50), wrist_l=(62, 42),
         knee_r=(70, 58), ankle_r=(82, 34), knee_l=(66, 64), ankle_l=(78, 40)),
    # open: straight body rotating head-down through the descent
    dict(head=(30, 90), neck=(38, 78), pelvis=(58, 50),
         elbow_r=(52, 74), wrist_r=(64, 80), elbow_l=(30, 62), wrist_l=(20, 54),
         knee_r=(72, 32), ankle_r=(84, 16), knee_l=(68, 36), ankle_l=(80, 20)),
    # entry: inverted and vertical, arms streamlined past the head
    dict(head=(50, 100), neck=(50, 86), pelvis=(50, 50),
         elbow_r=(58, 112), wrist_r=(54, 128), elbow_l=(42, 112), wrist_l=(46, 128),
         knee_r=(54, 30), ankle_r=(54, 8), knee_l=(46, 30), ankle_l=(46, 8)),
]


def diving(u=1.0):
    def splash(d, i, pt, colour, ox, bw, oy, bh):
        # Nothing until the entry is nearly finished, then the two spouts throw
        # out from the point of entry. Held to the last fifth of the last phase:
        # a splash that starts while the diver is still opening reads as him
        # hitting the water on his back.
        entry = len(DIVE_POSES) - 1
        t = (i - (entry - 0.45)) / 0.45
        if t <= 0:
            return
        t = min(t, 1.0)
        x = ox + bw * 0.50
        y = oy + bh                      # the water line
        lw = max(2, int(1.8 * S))
        for side in (-1, 1):
            d.line([(x + side * 5 * S * t, y),
                    (x + side * 12 * S * t, y - 9 * S * t)],
                   fill=colour, width=lw)

    return sequence("Diving", "unsupervised temporal segmentation",
                    DIVE_POSES, extras=splash, water=True, u=u)


# --------------------------------------------------------------------------- #
# 4. UTAL-GNN - skeleton graph on the left, localized segments on the right
# --------------------------------------------------------------------------- #

GNN_POSE = dict(head=(50, 20), neck=(50, 36), pelvis=(50, 72),
                elbow_r=(66, 46), wrist_r=(76, 30), elbow_l=(34, 46),
                wrist_l=(24, 62), knee_r=(62, 96), ankle_r=(66, 124),
                knee_l=(38, 96), ankle_l=(34, 124))

# extra graph edges, drawn thin, to show it is a graph and not just a stick man
GRAPH_EDGES = [("wrist_r", "head"), ("wrist_l", "head"), ("wrist_r", "pelvis"),
               ("knee_r", "knee_l"), ("ankle_l", "pelvis"), ("elbow_r", "elbow_l")]


def utal_gnn(u=1.0):
    img, d = canvas()
    pad_top = 40 * S
    baseline = H - 30 * S
    box_h = baseline - pad_top

    # --- left: the spatio-temporal graph over a skeleton
    ox, bw = 18 * S, 120 * S
    pt = skeleton(d, GNN_POSE, ox, pad_top, bw, box_h, INK)

    # A charge runs along the extra edges one after another and off the end of
    # them, which is message passing over the graph: the thing the network
    # actually does, and the only part of it a still cannot show. It leaves
    # every edge back in FADE, so the last frame is the still.
    for k, (a, b) in enumerate(GRAPH_EDGES):
        lit = max(0.0, 1.0 - abs(6.2 * u - 0.85 * k))
        d.line([pt(a), pt(b)], fill=lerp(FADE, INK, lit),
               width=max(1, int(1.4 * S)) + (1 if lit > 0.6 else 0))

    for joint in JOINTS:  # not the head - a dot inside the circle reads as an eye
        jx, jy = pt(joint)
        r = max(2, int(2.6 * S))
        d.ellipse([jx - r, jy - r, jx + r, jy + r], fill=INK)

    # --- arrow across to the timeline
    ax0, ax1 = ox + bw + 8 * S, ox + bw + 34 * S
    ay = pad_top + box_h * 0.5
    arrow(d, ax0, ax1, ay, MUTED)

    # --- right: a timeline the two action segments are localized onto, each
    # growing out of its own start once the charge has passed through the graph
    timeline(d, ax1 + 16 * S, W - 20 * S, pad_top + box_h * 0.34, 26 * S,
             ((0.08, 0.36, FADE, stage(u, 0.34, 0.62)),
              (0.52, 0.90, INK, stage(u, 0.58, 0.92))))

    chrome(d, "UTAL-GNN", "graph embeddings to action boundaries", baseline)
    return img


# --------------------------------------------------------------------------- #
# 5. BoxingVI - two boxers plus a labelled annotation track
# --------------------------------------------------------------------------- #

BOXER_LEAD = dict(head=(52, 22), neck=(52, 38), pelvis=(50, 74),
                  elbow_r=(70, 40), wrist_r=(92, 36), elbow_l=(40, 44),
                  wrist_l=(48, 34), knee_r=(62, 98), ankle_r=(70, 126),
                  knee_l=(36, 96), ankle_l=(26, 126))

BOXER_GUARD = dict(head=(48, 22), neck=(48, 38), pelvis=(50, 74),
                   elbow_r=(32, 46), wrist_r=(40, 32), elbow_l=(64, 46),
                   wrist_l=(56, 32), knee_r=(38, 98), ankle_r=(30, 126),
                   knee_l=(64, 96), ankle_l=(74, 126))

# The same boxer a moment earlier: the lead glove cocked at the cheek, weight
# still back on the trail leg. The animation is the straight this pose throws,
# so BOXER_LEAD is not a stance - it is the end of a punch, and the still was
# always the frame at contact.
BOXER_WIND = dict(head=(50, 24), neck=(50, 40), pelvis=(48, 75),
                  elbow_r=(62, 48), wrist_r=(58, 32), elbow_l=(38, 46),
                  wrist_l=(46, 36), knee_r=(58, 98), ankle_r=(64, 126),
                  knee_l=(36, 96), ankle_l=(26, 126))


def camera(d, x, y, colour, w=13 * S):
    """A small camera glyph, for the multi-view part of the benchmark."""
    h = w * 0.62
    d.rectangle([x, y, x + w, y + h], outline=colour, width=max(2, int(1.6 * S)))
    d.polygon([(x + w, y + h * 0.3), (x + w + w * 0.42, y),
               (x + w + w * 0.42, y + h), (x + w, y + h * 0.7)],
              outline=colour, width=max(2, int(1.6 * S)))


def boxingvi(u=1.0):
    img, d = canvas()
    pad_top = 42 * S
    baseline = 170 * S          # leaves room for the annotation track below
    box_h = baseline - pad_top

    d.line([(20 * S, baseline), (W - 20 * S, baseline)],
           fill=GROUND, width=max(2, int(1.5 * S)))

    # The pair is centred on the canvas: the lead boxer's glove lands just short
    # of the other's guard, which is what makes it read as a punch rather than
    # two people standing apart.
    bw = 150 * S
    lead = morph(BOXER_WIND, BOXER_LEAD, stage(u, 0.06, 0.50))
    for pose, ox, colour in ((lead, 68 * S, INK),
                             (BOXER_GUARD, 162 * S, FADE)):
        pt = skeleton(d, pose, ox, pad_top, bw, box_h, colour)
        for hand in ("wrist_r", "wrist_l"):     # gloves
            wx, wy = pt(hand)
            gr = 5.5 / LOCAL_H * box_h
            d.ellipse([wx - gr, wy - gr, wx + gr, wy + gr], fill=colour)

    # multi-view cameras looking in on the pair
    camera(d, 22 * S, 72 * S, MUTED, w=20 * S)
    camera(d, 320 * S, 72 * S, MUTED, w=20 * S)

    # Annotation track: three labelled action segments, laid down one after the
    # other with the middle one landing as the punch does. This is a benchmark,
    # so what the loop shows is the labelling of a round, not just the round.
    ty = baseline + 14 * S
    th = 22 * S
    timeline(d, 20 * S, W - 20 * S, ty, th,
             ((0.02, 0.30, INK, stage(u, 0.10, 0.40)),
              (0.36, 0.58, FADE, stage(u, 0.40, 0.64)),
              (0.64, 0.98, INK, stage(u, 0.62, 0.92))),
             ticks=False)

    chrome(d, "BoxingVI", "multi-modal action benchmark", baseline,
           caption_y=ty + th + 12 * S)
    return img


# --------------------------------------------------------------------------- #
# 6. Cricket - bowler delivering to a batter, with a phase track
# --------------------------------------------------------------------------- #

BOWLER = dict(head=(46, 26), neck=(46, 40), pelvis=(48, 74),
              elbow_r=(56, 20), wrist_r=(62, 6), elbow_l=(34, 52),
              wrist_l=(24, 64), knee_r=(66, 96), ankle_r=(78, 126),
              knee_l=(32, 98), ankle_l=(22, 126))

# Hands high and behind, so the bat can be drawn as a clear backlift instead of
# a stroke that disappears into the legs.
BATTER = dict(head=(52, 26), neck=(52, 40), pelvis=(54, 74),
              elbow_r=(64, 48), wrist_r=(70, 42), elbow_l=(62, 54),
              wrist_l=(68, 48), knee_r=(44, 98), ankle_r=(38, 126),
              knee_l=(64, 98), ankle_l=(70, 126))


def stumps(d, x, baseline, h, colour):
    """Three stumps and two bails - the cue that says cricket."""
    lw = max(2, int(2.2 * S))
    gap = 6 * S
    for i in range(3):
        sx = x + i * gap
        d.line([(sx, baseline), (sx, baseline - h)], fill=colour, width=lw)
    for i in range(2):
        d.line([(x + i * gap, baseline - h), (x + (i + 1) * gap, baseline - h)],
               fill=colour, width=max(1, int(1.6 * S)))


def cricket(u=1.0):
    img, d = canvas()
    pad_top = 42 * S
    baseline = 170 * S
    box_h = baseline - pad_top
    bw = 150 * S

    d.line([(20 * S, baseline), (W - 20 * S, baseline)],
           fill=GROUND, width=max(2, int(1.5 * S)))

    bowl_pt = skeleton(d, BOWLER, 30 * S, pad_top, bw, box_h, INK)
    bat_pt = skeleton(d, BATTER, 206 * S, pad_top, bw, box_h, FADE)

    # ball in the bowler's raised hand, and its dotted path to the batter
    ball = bowl_pt("wrist_r")
    br = 5 * S
    d.ellipse([ball[0] - br, ball[1] - br, ball[0] + br, ball[1] + br], fill=INK)
    pitch_at = (bat_pt("ankle_r")[0] - 12 * S, baseline - 6 * S)

    # The delivery. The dotted path is laid down behind the ball rather than
    # being there from the start, so it reads as the trajectory this ball is
    # tracing and not as a line already drawn on the picture. The ball itself
    # fades back into the page as it reaches the pitch: the hand keeps its ball
    # and the path stays complete, which is the still.
    flight = stage(u, 0.10, 0.72)
    dotted_curve(d, ball, pitch_at, 20 * S, MUTED, 1.8 * S, upto=flight)
    if 0 < flight < 1:
        fx, fy = curve_at(ball, pitch_at, 20 * S, flight)
        d.ellipse([fx - br, fy - br, fx + br, fy + br],
                  fill=fade(INK, 1 - max(0.0, (flight - 0.78) / 0.22)))

    # bat: a thin handle out of the hands into a thicker blade, raised behind
    hands = bat_pt("wrist_r")
    toe = (hands[0] + 26 * S, hands[1] - 30 * S)
    mid = ((hands[0] + toe[0]) / 2, (hands[1] + toe[1]) / 2)
    d.line([hands, mid], fill=FADE, width=max(2, int(2.4 * S)))
    d.line([mid, toe], fill=FADE, width=max(4, int(6 * S)))

    stumps(d, 322 * S, baseline, 32 * S, MUTED)

    # run-up, delivery, and the stroke that follows it - the middle phase fills
    # while the ball is in the air
    ty, th = baseline + 14 * S, 22 * S
    timeline(d, 20 * S, W - 20 * S, ty, th,
             ((0.02, 0.24, FADE, stage(u, 0.00, 0.20)),
              (0.30, 0.62, INK, stage(u, 0.18, 0.66)),
              (0.68, 0.98, FADE, stage(u, 0.66, 0.94))),
             ticks=False)

    chrome(d, "Cricket", "gameplay phase transitions", baseline,
           caption_y=ty + th + 12 * S)
    return img


# --------------------------------------------------------------------------- #
# 7. Defect analysis - a reference image against a sample, flaw ringed
# --------------------------------------------------------------------------- #

def device(d, x, y, w, h, colour):
    """A stand-in for the device under inspection."""
    lw = max(2, int(2 * S))
    d.rounded_rectangle([x, y, x + w, y + h], radius=6 * S,
                        outline=colour, width=lw)
    for i in (0.32, 0.52):
        d.line([(x + w * 0.16, y + h * i), (x + w * 0.84, y + h * i)],
               fill=colour, width=max(1, int(1.6 * S)))
    r = w * 0.09
    cx, cy = x + w * 0.5, y + h * 0.76
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=colour, width=lw)


def defect_analysis(u=1.0):
    img, d = canvas()
    fy, fh = 60 * S, 130 * S
    fw = 130 * S
    left_x, right_x = 24 * S, 216 * S

    for x in (left_x, right_x):
        d.rounded_rectangle([x, fy, x + fw, fy + fh], radius=8 * S,
                            fill=(255, 255, 255), outline=GROUND,
                            width=max(2, int(1.6 * S)))
        device(d, x + fw * 0.22, fy + fh * 0.18, fw * 0.56, fh * 0.64, INK)

    # the sample carries a scratch, ringed in the one non-blue colour on the site
    sx, sy = right_x + fw * 0.60, fy + fh * 0.42

    # An inspection pass crossing the sample. The scratch is not drawn until the
    # sweep has reached it and the ring closes in behind it, so the loop shows
    # the flaw being found rather than presenting it as already known - which is
    # the only claim a paired-image detector makes.
    swept = stage(u, 0.04, 0.70)
    if 0 < swept < 1:
        line_x = right_x + fw * swept
        d.line([(line_x, fy + 3 * S), (line_x, fy + fh - 3 * S)],
               fill=lerp(GROUND, INK, 0.45), width=max(2, int(1.8 * S)))

    found = clamp((right_x + fw * swept - (sx - 10 * S)) / (14 * S))
    if found > 0:
        d.line([(sx - 9 * S, sy + 5 * S), (sx - 2 * S, sy - 4 * S),
                (sx + 4 * S, sy + 4 * S), (sx + 10 * S, sy - 3 * S)],
               fill=fade(DANGER, found), width=max(2, int(2 * S)), joint="curve")
    # The ring closes from wide onto the scratch. It starts a beat after the
    # scratch is visible: ring first and it reads as a target the sweep aimed
    # at, rather than as the mark the sweep turned up.
    ring = stage(u, 0.52, 0.86)
    if ring > 0:
        rr = 20 * S * (1 + 0.9 * (1 - ring))
        d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr],
                  outline=fade(DANGER, min(1.0, ring * 1.6)),
                  width=max(2, int(2 * S)))

    # divider between the pair
    mid = (left_x + fw + right_x) / 2
    dashed(d, (mid, fy), (mid, fy + fh), GROUND, max(1, int(1.4 * S)))
    d.text((mid - 9 * S, fy + fh * 0.45), "vs", font=font(13 * S), fill=MUTED)

    baseline = fy + fh + 16 * S
    d.line([(24 * S, baseline), (W - 24 * S, baseline)], fill=GROUND,
           width=max(2, int(1.5 * S)))
    chrome(d, "Defect Analysis", "paired-image defect detection", baseline)
    return img


# --------------------------------------------------------------------------- #
# 8. 3D motion retrieval - a query pose and its ranked matches
# --------------------------------------------------------------------------- #

QUERY_POSE = dict(head=(50, 22), neck=(50, 38), pelvis=(50, 74),
                  elbow_r=(66, 44), wrist_r=(78, 30), elbow_l=(34, 48),
                  wrist_l=(26, 64), knee_r=(64, 98), ankle_r=(70, 126),
                  knee_l=(36, 98), ankle_l=(30, 126))

# The bottom of the query's own swing: arms down and back, hips dropped. The
# query is a clip, not a posture, and the animation plays it - down and back up
# once per loop, which returns it to QUERY_POSE and so to the still.
QUERY_SWING = dict(head=(48, 26), neck=(48, 42), pelvis=(50, 78),
                   elbow_r=(62, 54), wrist_r=(70, 66), elbow_l=(36, 54),
                   wrist_l=(30, 68), knee_r=(62, 102), ankle_r=(70, 126),
                   knee_l=(38, 102), ankle_l=(30, 126))

# the retrieved neighbours: the same action, progressively looser matches
MATCH_POSES = [
    dict(head=(50, 24), neck=(50, 40), pelvis=(50, 74),
         elbow_r=(66, 46), wrist_r=(76, 32), elbow_l=(34, 50), wrist_l=(28, 66),
         knee_r=(62, 98), ankle_r=(68, 126), knee_l=(38, 98), ankle_l=(32, 126)),
    dict(head=(48, 26), neck=(48, 42), pelvis=(50, 76),
         elbow_r=(64, 50), wrist_r=(72, 36), elbow_l=(34, 54), wrist_l=(30, 70),
         knee_r=(60, 100), ankle_r=(66, 126), knee_l=(40, 100), ankle_l=(34, 126)),
    dict(head=(48, 28), neck=(48, 44), pelvis=(52, 76),
         elbow_r=(62, 56), wrist_r=(70, 44), elbow_l=(36, 56), wrist_l=(32, 72),
         knee_r=(58, 100), ankle_r=(64, 126), knee_l=(42, 100), ankle_l=(36, 126)),
]


def motion_retrieval(u=1.0):
    img, d = canvas()
    pad_top = 44 * S
    baseline = H - 30 * S
    box_h = baseline - pad_top

    d.line([(20 * S, baseline), (W - 20 * S, baseline)],
           fill=GROUND, width=max(2, int(1.5 * S)))

    # One swing of the query, down and back up. The matches are displaced by the
    # same joint deltas rather than being animated separately: they were
    # retrieved for performing this motion, so they had better perform it.
    swing = math.sin(math.pi * clamp(u))

    # query, at full size
    skeleton(d, morph(QUERY_POSE, QUERY_SWING, swing),
             16 * S, pad_top, 108 * S, box_h, INK)

    ax0 = 128 * S
    arrow(d, ax0, ax0 + 26 * S, pad_top + box_h * 0.5, MUTED)

    # Ranked matches, shorter and lighter the further down the ranking they are,
    # and returned in that order: the loop shows the ranking being filled in
    # from the top, which is what a retrieval result is.
    for i, pose in enumerate(MATCH_POSES):
        arrived = stage(u, 0.20 + 0.20 * i, 0.48 + 0.20 * i)
        if arrived <= 0:
            continue
        colour = lerp(INK, FADE, (i + 1) / (len(MATCH_POSES) + 1))
        scale = 1 - 0.06 * i
        bh = box_h * scale
        skeleton(d, offset_pose(pose, QUERY_POSE, QUERY_SWING, swing),
                 (184 + i * 66) * S, baseline - bh + (1 - arrived) * 12 * S,
                 96 * S, bh, fade(colour, arrived))

    chrome(d, "3D Motion Retrieval", "query and ranked motion matches", baseline)
    return img


# --------------------------------------------------------------------------- #
# 9. UMPIRE - deep clustering of embeddings into action segments
# --------------------------------------------------------------------------- #

def umpire(u=1.0):
    img, d = canvas()
    rng = random.Random(7)      # fixed seed: the scatter must be reproducible
    mid = lerp(FADE, INK, 0.5)

    # ph is bounded by the canvas: the panel, its rule and the caption all have
    # to fit inside 480px, and a taller panel pushes the caption off the bottom.
    px, py, pw, ph = 24 * S, 50 * S, 150 * S, 128 * S
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=8 * S,
                        fill=(255, 255, 255), outline=GROUND,
                        width=max(2, int(1.6 * S)))

    clusters = ((0.28, 0.30, INK), (0.70, 0.34, mid), (0.46, 0.74, FADE))
    r = 3.4 * S

    # Every embedding lands unlabelled - grey, drifting in from the middle of the
    # panel - and only then does the clustering resolve, one group at a time,
    # each group taking its colour as the stretch of timeline it explains fills
    # in beside it. Deep clustering is a two-step claim and this is the honest
    # order to make it in: the points exist before the labels do.
    landed = [stage(u, 0.00 + 0.010 * k, 0.30 + 0.010 * k) for k in range(9)]
    labelled = [stage(u, 0.42, 0.62), stage(u, 0.56, 0.76), stage(u, 0.70, 0.90)]
    for c, (cx, cy, colour) in enumerate(clusters):
        for k in range(9):
            x = px + (cx + rng.gauss(0, 0.075)) * pw
            y = py + (cy + rng.gauss(0, 0.075)) * ph
            here = landed[k]
            if here <= 0:
                continue
            x, y = mid_point((px + pw * 0.5, py + ph * 0.5), (x, y), here)
            # from the panel's own white, so a point does not appear against it
            # as a hard grey dot on frame one
            tone = lerp(lerp((255, 255, 255), MUTED, here), colour, labelled[c])
            d.ellipse([x - r, y - r, x + r, y + r], fill=tone)
    for k, (nx, ny) in enumerate(((0.10, 0.86), (0.88, 0.82), (0.14, 0.56))):
        # the DBSCAN noise: never claimed by a cluster, so it is the one thing on
        # the panel that stays hollow and grey the whole way through
        here = stage(u, 0.24 + 0.06 * k, 0.52 + 0.06 * k)
        if here <= 0:
            continue
        x, y = mid_point((px + pw * 0.5, py + ph * 0.5),
                         (px + nx * pw, py + ny * ph), here)
        d.ellipse([x - r, y - r, x + r, y + r],
                  outline=lerp((255, 255, 255), MUTED, here),
                  width=max(1, int(1.4 * S)))

    ay = py + ph * 0.5
    arrow(d, px + pw + 10 * S, px + pw + 36 * S, ay, MUTED)

    # each cluster becomes a labelled stretch of the timeline
    tx0 = px + pw + 52 * S
    timeline(d, tx0, W - 24 * S, ay - 13 * S, 26 * S,
             ((0.02, 0.30, INK, labelled[0]),
              (0.36, 0.62, mid, labelled[1]),
              (0.68, 0.98, FADE, labelled[2])))

    baseline = py + ph + 16 * S
    d.line([(24 * S, baseline), (W - 24 * S, baseline)], fill=GROUND,
           width=max(2, int(1.5 * S)))
    chrome(d, "UMPIRE", "deep clustering into action segments", baseline)
    return img


# --------------------------------------------------------------------------- #
# 10. Golf - three mesh keyframes over the eight-phase segmentation
# --------------------------------------------------------------------------- #

# Address, top of the backswing, finish. Face-on view, target to the right.
#
# Three frames, not four: these are bodies rather than sticks, and a fourth cell
# takes each one down to about 60px on the rendered thumbnail, where the mesh
# collapses into a blot. The three chosen are the three that stay distinct at
# that size - address and impact differ mostly in the hips and the trail heel,
# which is exactly the detail that disappears first.
#
# A golf grip is both hands on one shaft, so the wrists nearly coincide and the
# club comes out of the trail hand. The hands stay well outside the trunk: with
# a solid body, an arm drawn over the chest is simply swallowed by it.
GOLF_POSES = [
    # address - square and level, hands low and forward, club soled at the ball
    dict(head=(46, 20), neck=(46, 36), pelvis=(48, 72),
         elbow_r=(64, 54), wrist_r=(72, 74), elbow_l=(56, 56), wrist_l=(70, 72),
         knee_r=(58, 98), ankle_r=(60, 126), knee_l=(36, 98), ankle_l=(34, 126)),
    # top of the backswing - hands high above the trail shoulder, torso coiled
    dict(head=(46, 22), neck=(46, 38), pelvis=(50, 72),
         elbow_r=(68, 40), wrist_r=(78, 22), elbow_l=(58, 48), wrist_l=(76, 26),
         knee_r=(60, 98), ankle_r=(62, 126), knee_l=(36, 98), ankle_l=(34, 126)),
    # finish - turned through onto the lead leg, trail foot up on its toe. The
    # two arms fold into a V at the hands; drawn level they merge with the
    # shoulder line into one horizontal slab across the top of the body.
    dict(head=(52, 20), neck=(50, 36), pelvis=(48, 72),
         elbow_r=(34, 30), wrist_r=(20, 24), elbow_l=(42, 46), wrist_l=(24, 30),
         knee_r=(58, 96), ankle_r=(60, 120), knee_l=(42, 98), ankle_l=(38, 126)),
]

# Where the club head sits in each pose, in the same local box as the joints.
# Frame 0 puts it on the ball, out to the right and clear of the legs; 1 and 2
# swing it up past the shoulder, above the head rather than through it.
GOLF_SHAFT = [(88, 128), (44, 6), (58, 8)]

# On the ground at address and at the top, gone once the ball has been struck.
BALL_AT = (92, 127)

# Where the club head goes between the three authored positions. A straight line
# from the ball up to the top of the backswing runs through the golfer's own
# hips, so that leg bends out around his trail side.
#
# From the top to the finish it needs no help, and specifically must not be
# routed down through the ball: these three poses carry no impact frame, the
# hands go from high to high without ever coming down, and a club head put on
# the ball while the hands are up by the ear is a pole through the man. So the
# head stays above him and the body turns under it. The downswing is the one
# thing in this set the still cannot support, and inventing it looked worse than
# leaving it out.
GOLF_BACKSWING_ARC = (116, 46)


def golf_club_at(x):
    """The club head at fractional cell position `x`, in local coordinates."""
    if x <= 1:
        return bezier(GOLF_SHAFT[0], GOLF_BACKSWING_ARC, GOLF_SHAFT[1], x)
    return mid_point(GOLF_SHAFT[1], GOLF_SHAFT[2], x - 1)


def golf(u=1.0):
    img, d = canvas()
    pad_x, pad_top = 20 * S, 42 * S
    baseline = 170 * S
    cell = phase_grid(d, len(GOLF_POSES), pad_x, pad_top, baseline)
    box_h = baseline - pad_top

    for i, progress, alpha in relay(u, len(GOLF_POSES)):
        # The fade starts a third of the way along rather than at FADE itself: a
        # mesh body is mostly pale fill, so a figure outlined in FADE all but
        # disappears once the thumbnail is scaled down to 190px.
        t = i / (len(GOLF_POSES) - 1)
        colour = fade(lerp(FADE, INK, 0.35 + 0.65 * t), alpha)
        ox = pad_x + cell * i + cell * 0.08
        bw = cell * 0.84
        # where this cell is in the swing as a whole, for the club and the ball
        x = max(i - 1, 0) + progress if i else 0.0

        def local(lx, ly, ox=ox, bw=bw):
            return (ox + lx / LOCAL_W * bw, pad_top + ly / LOCAL_H * box_h)

        pt = mesh_figure(d, relay_pose(GOLF_POSES, i, progress),
                         ox, pad_top, bw, box_h, colour,
                         shadow_at=baseline, alpha=alpha)

        # shaft out of the hands, with the head as a short thick stroke square
        # to it - that reads as a club head whichever way the shaft points.
        hands, tip = pt("wrist_r"), local(*golf_club_at(x))
        d.line([hands, tip], fill=colour, width=max(2, int(2.2 * S)))
        vx, vy = tip[0] - hands[0], tip[1] - hands[1]
        n = math.hypot(vx, vy) or 1
        nx, ny = -vy / n, vx / n
        d.line([(tip[0] - nx * 4 * S, tip[1] - ny * 4 * S),
                (tip[0] + nx * 4 * S, tip[1] + ny * 4 * S)],
               fill=colour, width=max(4, int(5 * S)))

        # The ball goes early in the last transition, not halfway through it.
        # Impact falls between the top and the finish, and between is all a
        # three-keyframe strip can say about it: by the time the golfer is posed
        # at the finish the ball is long gone, so it leaves at the start of that
        # move rather than waiting for a downswing that is not drawn.
        br = 4 * S
        if x <= 1.10:                    # teed up, through address and the top
            bx, by = local(*BALL_AT)
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=colour)
        elif x < 1.62:                   # struck, climbing away and out of shot
            f = (x - 1.10) / 0.52
            bx, by = local(BALL_AT[0] + 34 * f, BALL_AT[1] - 58 * f)
            d.ellipse([bx - br, by - br, bx + br, by + br],
                      fill=fade(colour, 1 - f))

    # The eight canonical phases the detector splits the clip into, filling as
    # the swing runs through them - the whole point of the dashboard is that the
    # phases come out of the video, so they should not be there before it plays.
    ty, th, n = baseline + 16 * S, 24 * S, 8
    segments = [(i / n + 0.008, (i + 1) / n - 0.008, lerp(FADE, INK, i / (n - 1)),
                 stage(u, 0.06 + 0.105 * i, 0.20 + 0.105 * i)) for i in range(n)]
    timeline(d, pad_x, W - pad_x, ty, th, segments, ticks=False)

    chrome(d, "Golf Swing", "3D mesh, eight-phase segmentation", baseline,
           caption_y=ty + th + 12 * S)
    return img


# --------------------------------------------------------------------------- #
# 11. Tennis - a stroke at contact, and the strokes found in the rally
# --------------------------------------------------------------------------- #

# Forehand at contact: racket arm extended out in front, weight forward, stance
# wide. Both arms are thrown clear of the trunk - the body is a solid volume
# here, so anything drawn across the chest is occluded by it.
TENNIS_POSE = dict(head=(44, 22), neck=(44, 38), pelvis=(46, 74),
                   elbow_r=(64, 46), wrist_r=(80, 36), elbow_l=(28, 50),
                   wrist_l=(18, 62), knee_r=(62, 98), ankle_r=(70, 126),
                   knee_l=(32, 98), ankle_l=(24, 126))

# The takeback the contact frame comes out of: racket hand behind the body, the
# free arm up and pointing at the incoming ball, knees loaded. Both arms are kept
# out on the same side of the spine and swing forward without crossing it - a
# limb dragged over the chest is drawn before the trunk and simply vanishes into
# it, so a cross-body interpolation would make the arm disappear mid-swing.
TENNIS_WIND = dict(head=(46, 24), neck=(46, 40), pelvis=(48, 76),
                   elbow_r=(34, 50), wrist_r=(22, 46), elbow_l=(30, 44),
                   wrist_l=(24, 30), knee_r=(58, 100), ankle_r=(64, 126),
                   knee_l=(30, 100), ankle_l=(22, 126))

# Racket face angles matching those two poses, in the sense racket() takes: back
# over the shoulder, then out in front at contact.
TENNIS_SWING_DEG = (155, 22)


def racket(d, hand, angle_deg, reach, colour):
    """A grip out of the hand into a strung oval head.

    The strings are a grid, not a single cross: two lines through the middle of
    a circle read as a gunsight. Returns the far edge of the string bed, which
    is where the ball leaves.
    """
    hx, hy = hand
    dx, dy = math.cos(math.radians(angle_deg)), -math.sin(math.radians(angle_deg))
    d.line([hand, (hx + dx * reach * 0.44, hy + dy * reach * 0.44)],
           fill=colour, width=max(2, int(2.4 * S)))
    cx, cy = hx + dx * reach * 0.74, hy + dy * reach * 0.74
    rx, ry = reach * 0.30, reach * 0.24
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=colour,
              width=max(2, int(2.2 * S)))
    sw = max(1, int(1.2 * S))
    for frac in (-0.5, 0.0, 0.5):
        # chord half-lengths so the strings stop at the frame, not past it
        d.line([(cx + rx * frac, cy - ry * 0.86), (cx + rx * frac, cy + ry * 0.86)],
               fill=colour, width=sw)
        d.line([(cx - rx * 0.86, cy + ry * frac), (cx + rx * 0.86, cy + ry * frac)],
               fill=colour, width=sw)
    return (cx + dx * rx, cy + dy * ry)


def net(d, x, baseline, h, half_w, colour):
    """The net seen from the side: a wide, low mesh band under a white tape.

    Kept much wider than it is tall. Drawn anywhere near square it stops
    reading as a net and starts reading as a window or a bookshelf.
    """
    lw = max(2, int(2 * S))
    top = baseline - h
    d.line([(x - half_w, top), (x + half_w, top)], fill=colour, width=lw)
    for end in (-1, 1):
        d.line([(x + half_w * end, top), (x + half_w * end, baseline)],
               fill=colour, width=lw)
    mesh = max(1, int(1.3 * S))
    for i in range(1, 8):
        mx = x - half_w + 2 * half_w * i / 8
        d.line([(mx, top), (mx, baseline)], fill=colour, width=mesh)
    for i in range(1, 3):
        my = top + h * i / 3
        d.line([(x - half_w, my), (x + half_w, my)], fill=colour, width=mesh)


def tennis(u=1.0):
    img, d = canvas()
    pad_top = 42 * S
    baseline = 170 * S
    box_h = baseline - pad_top
    # 97 local units wide against 132 tall over the same box makes one unit of x
    # the same number of pixels as one unit of y, so the body is not stretched.
    bw = 97 * S

    d.line([(20 * S, baseline), (W - 20 * S, baseline)],
           fill=GROUND, width=max(2, int(1.5 * S)))

    # the mesh viewer's orbit ring, drawn as a ground-plane circle in
    # perspective: centred on the baseline, so its near arc dips below it
    # ry is held to 14 so the near arc clears the timeline track below, which is
    # drawn afterwards and would otherwise slice the ring in half
    orbit(d, (30 * S + bw * 0.46, baseline - 1 * S), bw * 0.54, 14 * S,
          lerp(GROUND, MUTED, 0.45), 2 * S)

    # one forehand: takeback to contact, the racket face turning with the arm
    swing = stage(u, 0.06, 0.52)
    pt = mesh_figure(d, morph(TENNIS_WIND, TENNIS_POSE, swing),
                     30 * S, pad_top, bw, box_h, INK, shadow_at=baseline)
    a0, a1 = TENNIS_SWING_DEG
    bed = racket(d, pt("wrist_r"), a0 + (a1 - a0) * swing, 42 * S, INK)

    net(d, 268 * S, baseline, 32 * S, 62 * S, MUTED)

    # the ball just off the strings, clearing the net on its way across. It sits
    # ahead of the bed rather than on it - drawn inside the frame it turns the
    # strung head into a bullseye.
    ball = (bed[0] + 11 * S, bed[1] - 4 * S)
    br = 4.5 * S
    # It is one ball for the whole loop, not two: it drops in from over the net
    # onto the strings, and the still is the instant it arrives. That is the only
    # way the incoming ball and the ball on the strings can be the same object,
    # which is what makes the frame read as contact rather than as a serve.
    ix, iy = curve_at((W - 30 * S, baseline - 104 * S), ball, 14 * S,
                      stage(u, 0.02, 0.52))
    d.ellipse([ix - br, iy - br, ix + br, iy + br], fill=INK)

    # and away, laying its path down behind it as it goes
    away = (W - 34 * S, baseline - 48 * S)
    flight = stage(u, 0.54, 0.92)
    dotted_curve(d, ball, away, 30 * S, MUTED, 1.8 * S, upto=flight)
    # It picks the ball up only once it has cleared the strings. Drawn from the
    # instant of departure it is a second dot a few pixels from the first, and
    # for those frames the one ball this thumbnail is careful to keep single
    # reads as two.
    if 0.16 < flight < 1:
        fx, fy = curve_at(ball, away, 30 * S, flight)
        d.ellipse([fx - br, fy - br, fx + br, fy + br],
                  fill=fade(INK, 1 - clamp((flight - 0.74) / 0.26)))

    # the strokes the classifier finds in the clip, the rest of it neutral
    ty, th = baseline + 16 * S, 24 * S
    mid = lerp(FADE, INK, 0.5)
    timeline(d, 20 * S, W - 20 * S, ty, th,
             ((0.04, 0.22, INK, stage(u, 0.10, 0.36)),
              (0.34, 0.52, mid, stage(u, 0.38, 0.62)),
              (0.66, 0.90, FADE, stage(u, 0.64, 0.90))),
             ticks=False)

    chrome(d, "Tennis Strokes", "orbitable 3D mesh, stroke phase metrics",
           baseline, caption_y=ty + th + 12 * S)
    return img


# --------------------------------------------------------------------------- #
# 12. Video ingestion - raw footage sorted into quality-filtered frames
#
# This one is a data-flow diagram rather than a motion figure: a reel of raw
# footage on the left, and on the right the frames it exports, split into the
# good ones the downstream models get and the poor ones held back. The three
# good frames carry the three colours of the timeline underneath, which is how
# the detected shot boundaries are shown without writing a word on the picture.
# --------------------------------------------------------------------------- #

# Three exported frames of the same passage of play, and the two frames rejected
# from it. All five are ordinary running / jumping poses: what matters here is
# the frame each one sits in, not the pose itself.
INGEST_GOOD = [
    dict(head=(48, 20), neck=(48, 36), pelvis=(50, 72),
         elbow_r=(66, 46), wrist_r=(78, 34), elbow_l=(32, 48), wrist_l=(22, 60),
         knee_r=(64, 96), ankle_r=(74, 124), knee_l=(34, 96), ankle_l=(24, 124)),
    dict(head=(50, 16), neck=(50, 32), pelvis=(50, 68),
         elbow_r=(64, 24), wrist_r=(72, 8), elbow_l=(34, 44), wrist_l=(26, 58),
         knee_r=(62, 94), ankle_r=(68, 122), knee_l=(36, 94), ankle_l=(30, 124)),
    dict(head=(46, 24), neck=(46, 40), pelvis=(48, 76),
         elbow_r=(64, 52), wrist_r=(76, 62), elbow_l=(30, 54), wrist_l=(18, 64),
         knee_r=(62, 100), ankle_r=(70, 126), knee_l=(32, 100), ankle_l=(22, 126)),
]

INGEST_POOR = [
    dict(head=(46, 22), neck=(46, 38), pelvis=(48, 74),
         elbow_r=(62, 50), wrist_r=(72, 40), elbow_l=(32, 50), wrist_l=(24, 62),
         knee_r=(60, 98), ankle_r=(68, 124), knee_l=(34, 98), ankle_l=(28, 126)),
    dict(head=(52, 18), neck=(52, 34), pelvis=(50, 70),
         elbow_r=(66, 34), wrist_r=(74, 20), elbow_l=(36, 46), wrist_l=(28, 60),
         knee_r=(62, 96), ankle_r=(70, 124), knee_l=(38, 96), ankle_l=(32, 124)),
]


def film_strip(d, x, y, w, h, cells, colour, lit=None):
    """A reel of footage: sprocket bands down both long edges, `cells` frames.

    `lit` is the frame the sampler is on, as a fraction across the reel, and it
    is allowed to run off either end - past the last frame nothing is lit, which
    is the state the still is in.
    """
    lw = max(2, int(1.6 * S))
    d.rounded_rectangle([x, y, x + w, y + h], radius=4 * S,
                        fill=(255, 255, 255), outline=GROUND, width=lw)

    band = h * 0.19
    holes = cells * 2
    hw, hh = w / holes * 0.46, band * 0.5
    for i in range(holes):
        cx = x + w * (i + 0.5) / holes
        for cy in (y + band * 0.5, y + h - band * 0.5):
            d.rounded_rectangle([cx - hw / 2, cy - hh / 2, cx + hw / 2, cy + hh / 2],
                                radius=1.5 * S, fill=GROUND)

    # The frames on the reel are left empty. At 190px a strip this size gives
    # each one about 6px of width, which is not enough for anything inside it to
    # be more than a smudge; drawn as plain outlines they at least read as film.
    fy0, fy1 = y + band + 3 * S, y + h - band - 3 * S
    fw = w / cells * 0.76
    for i in range(cells):
        fx = x + w * (i + 0.5) / cells
        on = 0.0 if lit is None else max(0.0, 1.0 - abs(lit - i))
        d.rectangle([fx - fw / 2, fy0, fx + fw / 2, fy1],
                    outline=lerp(colour, INK, on),
                    width=max(1, int(1.2 * S)) + (1 if on > 0.6 else 0))


def frame_card(d, x, y, w, h, pose, colour, poor=False):
    """One exported frame: a card with a figure in it.

    A poor frame is a grey card carrying a doubled, offset figure. Greying it
    alone reads as 'older'; the ghost is what reads as 'too blurred to use',
    which is the reason the pipeline holds it back.

    The corner radius and the inset are both capped against the card's own size
    rather than fixed: animated, the card is drawn on its way out of the reel at
    a fraction of its final size, and a 5px radius on a 12px card is not a
    rounded corner - it is an error.
    """
    # The border thins with the card, so a card in transit is a thin outline at
    # a small size rather than a thick one - the cap is at the full width, so a
    # finished card is drawn exactly as it always was.
    lw = max(2, int(1.8 * S * min(1.0, w / (44 * S))))
    radius = min(5 * S, w / 3, h / 3)
    if poor:
        d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                            fill=lerp(BG, GROUND, 0.55), outline=GROUND, width=lw)
    else:
        d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                            fill=(255, 255, 255), outline=colour, width=lw)

    inset = min(6 * S, h * 0.15)
    bh = h - 2 * inset
    bw = bh * LOCAL_W / LOCAL_H          # unstretched: one unit of x = one of y
    ox = x + (w - bw) / 2
    figure_lw = max(2, int(1.6 * S))
    # head_r is well above skeleton()'s default: at this size the default circle
    # comes out under 4px across and the figure looks decapitated.
    kw = dict(lw=figure_lw, head_r=9.5, joint_r=max(1, int(1.1 * S)))
    if poor:
        d.rounded_rectangle([x + lw, y + lw, x + w - lw, y + h - lw],
                            radius=min(4 * S, (w - 2 * lw) / 3, (h - 2 * lw) / 3),
                            fill=lerp(BG, GROUND, 0.55))
        # A short offset only. Pulled any further apart the two copies stop
        # overlapping and read as two players in the frame rather than as one
        # player smeared across it.
        ghost = lerp(lerp(BG, GROUND, 0.55), MUTED, 0.5)
        skeleton(d, pose, ox + 3.5 * S, y + inset, bw, bh, ghost, **kw)
        skeleton(d, pose, ox, y + inset, bw, bh, MUTED, **kw)
    else:
        skeleton(d, pose, ox, y + inset, bw, bh, colour, **kw)


def video_ingestion(u=1.0):
    img, d = canvas()
    baseline = 168 * S
    mid = lerp(FADE, INK, 0.5)
    # The palest of the three segment colours. Held off FADE itself: an outlined
    # card in FADE has all but disappeared by the time the thumbnail is down to
    # 190px, where the same colour as a filled timeline bar is still fine.
    pale = lerp(FADE, INK, 0.22)

    # the reel, with two more behind it: the input is a file, a folder of files
    # or a playlist, so a single strip would undersell it
    sx, sy, sw, sh = 22 * S, 86 * S, 108 * S, 54 * S
    for back in (2, 1):
        d.rounded_rectangle([sx + back * 4 * S, sy - back * 6 * S,
                             sx + sw + back * 4 * S, sy + sh - back * 6 * S],
                            radius=4 * S, fill=BG, outline=GROUND,
                            width=max(1, int(1.4 * S)))
    # the sampler running down the reel, one frame at a time. It starts before
    # the first frame and finishes past the last, so nothing is lit in the still.
    film_strip(d, sx, sy, sw, sh, 5, FADE, lit=-1 + 7 * clamp(u))

    # the split: one line out of the reel, then one branch into each row
    good_y, poor_y = 86 * S, 142 * S
    bx = 148 * S
    d.line([(sx + sw + 8 * S, (good_y + poor_y) / 2), (bx, (good_y + poor_y) / 2)],
           fill=MUTED, width=max(2, int(2 * S)))
    d.line([(bx, good_y), (bx, poor_y)], fill=MUTED, width=max(2, int(2 * S)))
    for y in (good_y, poor_y):
        arrow(d, bx, 176 * S, y, MUTED)

    # Each exported frame leaves the reel and grows into its slot. The order is
    # interleaved rather than one row and then the other, because that is what
    # the pipeline does: it decides per frame as it decodes, and the poor ones
    # are not swept up afterwards - they are set aside as they come.
    exit_at = (sx + sw + 6 * S, (good_y + poor_y) / 2)

    def card(slot, arrived, pose, colour, poor=False):
        if arrived <= 0:
            return
        x, y, w, h = slot
        # It leaves the reel at a bit over half size, not a fifth. Smaller than
        # this and the border is most of the card, so what travels down the
        # arrow is a dark speck rather than a frame - at 190px the difference
        # between a small card and a blot is about six pixels.
        scale = 0.55 + 0.45 * arrived
        cw, ch = w * scale, h * scale
        cx, cy = mid_point(exit_at, (x + w / 2, y + h / 2), arrived)
        frame_card(d, cx - cw / 2, cy - ch / 2, cw, ch, pose, colour, poor=poor)

    # kept frames, one per detected segment and coloured to match the timeline
    for i, pose in enumerate(INGEST_GOOD):
        card(((192 + i * 56) * S, good_y - 28 * S, 44 * S, 56 * S),
             stage(u, 0.06 + 0.24 * i, 0.34 + 0.24 * i), pose,
             (INK, mid, pale)[i])

    # rejected frames, on the row below and stopping short of the kept row's
    # width - the point is that fewer frames come out of this branch
    for i, pose in enumerate(INGEST_POOR):
        card(((192 + i * 56) * S, poor_y - 20 * S, 44 * S, 40 * S),
             stage(u, 0.20 + 0.36 * i, 0.48 + 0.36 * i), pose,
             GROUND, poor=True)

    d.line([(20 * S, baseline), (W - 20 * S, baseline)], fill=GROUND,
           width=max(2, int(1.5 * S)))

    # the shot boundaries found in the clip: three segments, in the colours the
    # kept frames were drawn in, with the cut between them left blank. Each one
    # closes only after the frame it belongs to has been filed.
    ty, th = baseline + 16 * S, 24 * S
    timeline(d, 20 * S, W - 20 * S, ty, th,
             ((0.02, 0.30, INK, stage(u, 0.30, 0.52)),
              (0.36, 0.62, mid, stage(u, 0.52, 0.72)),
              (0.70, 0.98, pale, stage(u, 0.72, 0.92))),
             ticks=False)

    chrome(d, "Video Ingestion", "frame sampling, quality filter, shot boundaries",
           baseline, caption_y=ty + th + 12 * S)
    return img


# --------------------------------------------------------------------------- #

THUMBNAILS = (
    (throwing4, "throwing4-phases"),
    (javelin, "javelin-phases"),
    (diving, "diving-phases"),
    (utal_gnn, "utal-gnn-graph"),
    (boxingvi, "boxingvi-actions"),
    (cricket, "cricket-phases"),
    (defect_analysis, "defect-pairs"),
    (motion_retrieval, "motion-retrieval"),
    (umpire, "umpire-clusters"),
    (golf, "golf-swing-phases"),
    (tennis, "tennis-strokes"),
    (video_ingestion, "video-ingestion"),
)


def main():
    print("writing thumbnails:")
    for draw, stem in THUMBNAILS:
        emit(draw, stem)


if __name__ == "__main__":
    main()
