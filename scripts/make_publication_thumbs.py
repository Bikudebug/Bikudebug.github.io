#!/usr/bin/env python3
"""Generate the thumbnails for every entry on /publications/.

The originals were sports GIFs, several of them enormous (diving_star.gif was
10.4 MB, BackFlop_diving.gif 4.9 MB) for a slot the page renders at 190x120.
Each is replaced by a small schematic of what the paper actually does, drawn in
one shared style so the list reads as a set.

Run from the repository root:
    python scripts/make_publication_thumbs.py
"""

import math
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
    d.line([(ax0, ay), (ax1, ay)], fill=MUTED, width=max(2, int(2 * S)))
    d.polygon([(ax1 + 7 * S, ay), (ax1, ay - 5 * S), (ax1, ay + 5 * S)], fill=MUTED)

    # --- right: a timeline with two localized action segments
    tx0, tx1 = ax1 + 16 * S, W - 20 * S
    ty = pad_top + box_h * 0.34
    th = 26 * S
    d.rounded_rectangle([tx0, ty, tx1, ty + th], radius=5 * S,
                        outline=GROUND, width=max(2, int(1.6 * S)))
    span = tx1 - tx0
    for start, end, colour in ((0.08, 0.36, FADE), (0.52, 0.90, INK)):
        d.rounded_rectangle([tx0 + span * start, ty + 3 * S,
                             tx0 + span * end, ty + th - 3 * S],
                            radius=3 * S, fill=colour)
    # dashed boundary markers dropping below the bar
    for frac in (0.08, 0.36, 0.52, 0.90):
        x = tx0 + span * frac
        dashed(d, (x, ty + th + 4 * S), (x, ty + th + 34 * S), GROUND,
               max(1, int(1.2 * S)), dash=4 * S, gap=4 * S)

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
    tx0, tx1 = 20 * S, W - 20 * S
    span = tx1 - tx0
    d.rounded_rectangle([tx0, ty, tx1, ty + th], radius=5 * S,
                        outline=GROUND, width=max(2, int(1.6 * S)))
    for start, end, colour in ((0.02, 0.30, INK), (0.36, 0.58, FADE),
                               (0.64, 0.98, INK)):
        d.rounded_rectangle([tx0 + span * start, ty + 3 * S,
                             tx0 + span * end, ty + th - 3 * S],
                            radius=3 * S, fill=colour)

    chrome(d, "BoxingVI", "multi-modal action benchmark", baseline,
           caption_y=ty + th + 12 * S)
    return img


# --------------------------------------------------------------------------- #

def main():
    print("writing publication thumbnails:")
    save(throwing4(), "throwing4-phases.png")
    save(javelin(), "javelin-phases.png")
    save(diving(), "diving-phases.png")
    save(utal_gnn(), "utal-gnn-graph.png")
    save(boxingvi(), "boxingvi-actions.png")


if __name__ == "__main__":
    main()
