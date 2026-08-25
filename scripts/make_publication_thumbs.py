#!/usr/bin/env python3
"""Generate the thumbnails used on /publications/ and /projects/.

The publication originals were sports GIFs, several of them enormous
(diving_star.gif was 10.4 MB, BackFlop_diving.gif 4.9 MB) for a slot the page
renders at 190x120. Each is a small schematic of what the work actually does,
drawn in one shared style so both lists read as a set. Projects that are the
same work as a paper reuse that paper's thumbnail.

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


def dotted_curve(d, p0, p1, lift, colour, width, dots=22):
    """A dotted quadratic arc from p0 to p1, `lift` pixels above the chord."""
    cx = (p0[0] + p1[0]) / 2
    cy = (p0[1] + p1[1]) / 2 - lift
    r = max(1, int(width))
    for i in range(dots + 1):
        t = i / dots
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t ** 2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t ** 2 * p1[1]
        if i % 2 == 0:
            d.ellipse([x - r, y - r, x + r, y + r], fill=colour)


def arrow(d, x0, x1, y, colour):
    d.line([(x0, y), (x1, y)], fill=colour, width=max(2, int(2 * S)))
    d.polygon([(x1 + 7 * S, y), (x1, y - 5 * S), (x1, y + 5 * S)], fill=colour)


def timeline(d, x0, x1, y, h, segments, ticks=True):
    """An outlined track with filled segments given as (start, end, colour)."""
    d.rounded_rectangle([x0, y, x1, y + h], radius=5 * S,
                        outline=GROUND, width=max(2, int(1.6 * S)))
    span = x1 - x0
    for start, end, colour in segments:
        d.rounded_rectangle([x0 + span * start, y + 3 * S,
                             x0 + span * end, y + h - 3 * S],
                            radius=3 * S, fill=colour)
    if ticks:
        for start, end, _ in segments:
            for frac in (start, end):
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


def sequence(title, caption, poses, extras=None, water=False):
    """The shared left-to-right phase layout used by the motion thumbnails."""
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

    for i, pose in enumerate(poses):
        colour = lerp(FADE, INK, i / max(1, len(poses) - 1))
        ox = pad_x + cell * i + cell * 0.08
        bw = cell * 0.84
        pt = skeleton(d, pose, ox, pad_top, bw, box_h, colour)
        if extras:
            extras(d, i, pt, colour, ox, bw, pad_top, box_h)

    chrome(d, title, caption, baseline)
    return img


def save(img, name):
    path = IMAGES / name
    img.save(path, optimize=True)
    print(f"  {name:28s} {path.stat().st_size / 1024:6.1f} KB")


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
                facing=1, shadow_at=None):
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
        d.ellipse([ax - sx, shadow_at - sy, ax + sx, shadow_at + sy],
                  fill=lerp(BG, GROUND, 0.75))

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


def throwing4():
    def shot(d, i, pt, colour, ox, bw, oy, bh):
        if i < 3:  # implement in hand until release
            wx, wy = pt("wrist_r")
            r = 5 / LOCAL_W * bw
            d.ellipse([wx - r, wy - r, wx + r, wy + r], fill=colour)

    return sequence("Throwing4", "phase-aligned throwing sequence",
                    THROW_POSES, extras=shot)


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


def javelin():
    def spear(d, i, pt, colour, ox, bw, oy, bh):
        lw = max(2, int(2.2 * S))
        bounds = (ox - bw * 0.06, ox + bw * 1.02)
        if JAVELIN_SPEAR[i] is None:
            # released: draw it in flight above the athlete
            implement(d, (ox + bw * 0.55, oy + bh * 0.015), 16,
                      bw * 0.34, bw * 0.34, colour, lw, bounds)
        else:
            angle, back, fwd = JAVELIN_SPEAR[i]
            implement(d, pt("wrist_r"), angle, bw * back, bw * fwd,
                      colour, lw, bounds)

    return sequence("Javelin", "biomechanical phase segmentation",
                    JAVELIN_POSES, extras=spear)


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


def diving():
    def splash(d, i, pt, colour, ox, bw, oy, bh):
        if i != len(DIVE_POSES) - 1:
            return
        x = ox + bw * 0.50
        y = oy + bh                      # the water line
        lw = max(2, int(1.8 * S))
        for side in (-1, 1):
            d.line([(x + side * 5 * S, y), (x + side * 12 * S, y - 9 * S)],
                   fill=colour, width=lw)

    return sequence("Diving", "unsupervised temporal segmentation",
                    DIVE_POSES, extras=splash, water=True)


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


def utal_gnn():
    img, d = canvas()
    pad_top = 40 * S
    baseline = H - 30 * S
    box_h = baseline - pad_top

    # --- left: the spatio-temporal graph over a skeleton
    ox, bw = 18 * S, 120 * S
    pt = skeleton(d, GNN_POSE, ox, pad_top, bw, box_h, INK)
    for a, b in GRAPH_EDGES:
        d.line([pt(a), pt(b)], fill=FADE, width=max(1, int(1.4 * S)))
    for joint in JOINTS:  # not the head - a dot inside the circle reads as an eye
        jx, jy = pt(joint)
        r = max(2, int(2.6 * S))
        d.ellipse([jx - r, jy - r, jx + r, jy + r], fill=INK)

    # --- arrow across to the timeline
    ax0, ax1 = ox + bw + 8 * S, ox + bw + 34 * S
    ay = pad_top + box_h * 0.5
    arrow(d, ax0, ax1, ay, MUTED)

    # --- right: a timeline with two localized action segments
    timeline(d, ax1 + 16 * S, W - 20 * S, pad_top + box_h * 0.34, 26 * S,
             ((0.08, 0.36, FADE), (0.52, 0.90, INK)))

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


def camera(d, x, y, colour, w=13 * S):
    """A small camera glyph, for the multi-view part of the benchmark."""
    h = w * 0.62
    d.rectangle([x, y, x + w, y + h], outline=colour, width=max(2, int(1.6 * S)))
    d.polygon([(x + w, y + h * 0.3), (x + w + w * 0.42, y),
               (x + w + w * 0.42, y + h), (x + w, y + h * 0.7)],
              outline=colour, width=max(2, int(1.6 * S)))


def boxingvi():
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
    for pose, ox, colour in ((BOXER_LEAD, 68 * S, INK),
                             (BOXER_GUARD, 162 * S, FADE)):
        pt = skeleton(d, pose, ox, pad_top, bw, box_h, colour)
        for hand in ("wrist_r", "wrist_l"):     # gloves
            wx, wy = pt(hand)
            gr = 5.5 / LOCAL_H * box_h
            d.ellipse([wx - gr, wy - gr, wx + gr, wy + gr], fill=colour)

    # multi-view cameras looking in on the pair
    camera(d, 22 * S, 72 * S, MUTED, w=20 * S)
    camera(d, 320 * S, 72 * S, MUTED, w=20 * S)

    # annotation track: three labelled action segments
    ty = baseline + 14 * S
    th = 22 * S
    timeline(d, 20 * S, W - 20 * S, ty, th,
             ((0.02, 0.30, INK), (0.36, 0.58, FADE), (0.64, 0.98, INK)),
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


def cricket():
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
    dotted_curve(d, ball, pitch_at, 20 * S, MUTED, 1.8 * S)

    # bat: a thin handle out of the hands into a thicker blade, raised behind
    hands = bat_pt("wrist_r")
    toe = (hands[0] + 26 * S, hands[1] - 30 * S)
    mid = ((hands[0] + toe[0]) / 2, (hands[1] + toe[1]) / 2)
    d.line([hands, mid], fill=FADE, width=max(2, int(2.4 * S)))
    d.line([mid, toe], fill=FADE, width=max(4, int(6 * S)))

    stumps(d, 322 * S, baseline, 32 * S, MUTED)

    ty, th = baseline + 14 * S, 22 * S
    timeline(d, 20 * S, W - 20 * S, ty, th,
             ((0.02, 0.24, FADE), (0.30, 0.62, INK), (0.68, 0.98, FADE)),
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


def defect_analysis():
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
    d.line([(sx - 9 * S, sy + 5 * S), (sx - 2 * S, sy - 4 * S),
            (sx + 4 * S, sy + 4 * S), (sx + 10 * S, sy - 3 * S)],
           fill=DANGER, width=max(2, int(2 * S)), joint="curve")
    rr = 20 * S
    d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], outline=DANGER,
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


def motion_retrieval():
    img, d = canvas()
    pad_top = 44 * S
    baseline = H - 30 * S
    box_h = baseline - pad_top

    d.line([(20 * S, baseline), (W - 20 * S, baseline)],
           fill=GROUND, width=max(2, int(1.5 * S)))

    # query, at full size
    skeleton(d, QUERY_POSE, 16 * S, pad_top, 108 * S, box_h, INK)

    ax0 = 128 * S
    arrow(d, ax0, ax0 + 26 * S, pad_top + box_h * 0.5, MUTED)

    # ranked matches, shorter and lighter the further down the ranking they are
    for i, pose in enumerate(MATCH_POSES):
        colour = lerp(INK, FADE, (i + 1) / (len(MATCH_POSES) + 1))
        scale = 1 - 0.06 * i
        bh = box_h * scale
        skeleton(d, pose, (184 + i * 66) * S, baseline - bh, 96 * S, bh, colour)

    chrome(d, "3D Motion Retrieval", "query and ranked motion matches", baseline)
    return img


# --------------------------------------------------------------------------- #
# 9. UMPIRE - deep clustering of embeddings into action segments
# --------------------------------------------------------------------------- #

def umpire():
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
    for cx, cy, colour in clusters:
        for _ in range(9):
            x = px + (cx + rng.gauss(0, 0.075)) * pw
            y = py + (cy + rng.gauss(0, 0.075)) * ph
            d.ellipse([x - r, y - r, x + r, y + r], fill=colour)
    for nx, ny in ((0.10, 0.86), (0.88, 0.82), (0.14, 0.56)):  # DBSCAN noise
        x, y = px + nx * pw, py + ny * ph
        d.ellipse([x - r, y - r, x + r, y + r], outline=MUTED,
                  width=max(1, int(1.4 * S)))

    ay = py + ph * 0.5
    arrow(d, px + pw + 10 * S, px + pw + 36 * S, ay, MUTED)

    # each cluster becomes a labelled stretch of the timeline
    tx0 = px + pw + 52 * S
    timeline(d, tx0, W - 24 * S, ay - 13 * S, 26 * S,
             ((0.02, 0.30, INK), (0.36, 0.62, mid), (0.68, 0.98, FADE)))

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


def golf():
    img, d = canvas()
    pad_x, pad_top = 20 * S, 42 * S
    baseline = 170 * S
    cell = phase_grid(d, len(GOLF_POSES), pad_x, pad_top, baseline)
    box_h = baseline - pad_top

    for i, pose in enumerate(GOLF_POSES):
        # The fade starts a third of the way along rather than at FADE itself: a
        # mesh body is mostly pale fill, so a figure outlined in FADE all but
        # disappears once the thumbnail is scaled down to 190px.
        t = i / (len(GOLF_POSES) - 1)
        colour = lerp(FADE, INK, 0.35 + 0.65 * t)
        ox = pad_x + cell * i + cell * 0.08
        bw = cell * 0.84

        def local(lx, ly, ox=ox, bw=bw):
            return (ox + lx / LOCAL_W * bw, pad_top + ly / LOCAL_H * box_h)

        pt = mesh_figure(d, pose, ox, pad_top, bw, box_h, colour,
                         shadow_at=baseline)

        # shaft out of the hands, with the head as a short thick stroke square
        # to it - that reads as a club head whichever way the shaft points.
        hands, tip = pt("wrist_r"), local(*GOLF_SHAFT[i])
        d.line([hands, tip], fill=colour, width=max(2, int(2.2 * S)))
        vx, vy = tip[0] - hands[0], tip[1] - hands[1]
        n = math.hypot(vx, vy) or 1
        nx, ny = -vy / n, vx / n
        d.line([(tip[0] - nx * 4 * S, tip[1] - ny * 4 * S),
                (tip[0] + nx * 4 * S, tip[1] + ny * 4 * S)],
               fill=colour, width=max(4, int(5 * S)))

        if i < 2:
            bx, by = local(*BALL_AT)
            br = 4 * S
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=colour)

    # the eight canonical phases the detector splits the clip into
    ty, th, n = baseline + 16 * S, 24 * S, 8
    segments = [(i / n + 0.008, (i + 1) / n - 0.008, lerp(FADE, INK, i / (n - 1)))
                for i in range(n)]
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


def tennis():
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

    pt = mesh_figure(d, TENNIS_POSE, 30 * S, pad_top, bw, box_h, INK,
                     shadow_at=baseline)
    bed = racket(d, pt("wrist_r"), 22, 42 * S, INK)

    net(d, 268 * S, baseline, 32 * S, 62 * S, MUTED)

    # the ball just off the strings, clearing the net on its way across. It sits
    # ahead of the bed rather than on it - drawn inside the frame it turns the
    # strung head into a bullseye.
    ball = (bed[0] + 11 * S, bed[1] - 4 * S)
    br = 4.5 * S
    d.ellipse([ball[0] - br, ball[1] - br, ball[0] + br, ball[1] + br], fill=INK)
    dotted_curve(d, ball, (W - 34 * S, baseline - 48 * S), 30 * S, MUTED, 1.8 * S)

    # the strokes the classifier finds in the clip, the rest of it neutral
    ty, th = baseline + 16 * S, 24 * S
    mid = lerp(FADE, INK, 0.5)
    timeline(d, 20 * S, W - 20 * S, ty, th,
             ((0.04, 0.22, INK), (0.34, 0.52, mid), (0.66, 0.90, FADE)),
             ticks=False)

    chrome(d, "Tennis Strokes", "orbitable 3D mesh, stroke phase metrics",
           baseline, caption_y=ty + th + 12 * S)
    return img


# --------------------------------------------------------------------------- #

def main():
    print("writing thumbnails:")
    save(throwing4(), "throwing4-phases.png")
    save(javelin(), "javelin-phases.png")
    save(diving(), "diving-phases.png")
    save(utal_gnn(), "utal-gnn-graph.png")
    save(boxingvi(), "boxingvi-actions.png")
    save(cricket(), "cricket-phases.png")
    save(defect_analysis(), "defect-pairs.png")
    save(motion_retrieval(), "motion-retrieval.png")
    save(umpire(), "umpire-clusters.png")
    save(golf(), "golf-swing-phases.png")
    save(tennis(), "tennis-strokes.png")


if __name__ == "__main__":
    main()
