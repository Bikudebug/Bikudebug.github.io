#!/usr/bin/env python3
"""Generate the thumbnail for the Throwing4 publication entry.

The previous thumbnail was a 12.5 MB AI-generated cartoon, which does not
belong on a publication list. This draws a plain schematic instead: four pose
skeletons stepping through a throwing motion, split by phase dividers, which
is what the paper is actually about (phase-aligned, pose-based analysis).

Run from the repository root:
    python scripts/make_throwing4_thumb.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "images" / "throwing4-phases.png"

# 2x the 190x120 slot the publication list renders, for high-DPI screens
W, H = 760, 480
SCALE = 2

BG = (246, 248, 250)          # matches --global-code-background-color
INK = (9, 105, 218)           # matches --global-link-color
INK_FADE = (140, 178, 226)
GROUND = (190, 200, 210)
LABEL = (31, 35, 40)

# Joints are given in a local 100 x 150 box, y increasing downwards.
POSES = [
    # wind-up: coiled, implement held back at the shoulder
    dict(head=(50, 18), neck=(50, 32), pelvis=(50, 68),
         elbow_r=(62, 44), wrist_r=(71, 35),
         elbow_l=(38, 46), wrist_l=(30, 56),
         knee_r=(62, 95), ankle_r=(67, 125),
         knee_l=(36, 92), ankle_l=(29, 124)),
    # drive: rotating through the circle
    dict(head=(52, 15), neck=(52, 29), pelvis=(50, 65),
         elbow_r=(66, 38), wrist_r=(78, 30),
         elbow_l=(38, 40), wrist_l=(27, 34),
         knee_r=(64, 90), ankle_r=(74, 121),
         knee_l=(34, 94), ankle_l=(24, 123)),
    # release: throwing arm fully extended
    dict(head=(50, 17), neck=(50, 30), pelvis=(52, 67),
         elbow_r=(66, 22), wrist_r=(81, 10),
         elbow_l=(34, 38), wrist_l=(23, 28),
         knee_r=(62, 92), ankle_r=(69, 124),
         knee_l=(38, 94), ankle_l=(30, 124)),
    # follow-through: reverse, arm swung across
    dict(head=(48, 19), neck=(48, 32), pelvis=(52, 69),
         elbow_r=(34, 35), wrist_r=(22, 27),
         elbow_l=(60, 41), wrist_l=(70, 49),
         knee_r=(66, 93), ankle_r=(77, 121),
         knee_l=(40, 96), ankle_l=(30, 124)),
]

BONES = [
    ("neck", "pelvis"),
    ("neck", "elbow_r"), ("elbow_r", "wrist_r"),
    ("neck", "elbow_l"), ("elbow_l", "wrist_l"),
    ("pelvis", "knee_r"), ("knee_r", "ankle_r"),
    ("pelvis", "knee_l"), ("knee_l", "ankle_l"),
]

# the implement is in hand for the first three phases, gone after release
HOLDS_IMPLEMENT = [True, True, True, False]


def load_font(size):
    for name in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


# Local box height used for the y mapping. The lowest ankle sits at y=125, so
# mapping over 132 (not 150) lands the feet just on the ground line instead of
# leaving the figures floating above it.
LOCAL_H = 132


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def draw_pose(d, pose, ox, oy, box_w, box_h, colour, holds):
    """Map a pose from its local box onto the canvas and stroke it."""
    def pt(joint):
        x, y = pose[joint]
        return (ox + x / 100 * box_w, oy + y / LOCAL_H * box_h)

    lw = max(2, int(3 * SCALE))
    for a, b in BONES:
        d.line([pt(a), pt(b)], fill=colour, width=lw, joint="curve")

    hx, hy = pt("head")
    r = 7 / 100 * box_w
    d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=colour, width=lw)

    for joint in ("elbow_r", "wrist_r", "elbow_l", "wrist_l",
                  "knee_r", "ankle_r", "knee_l", "ankle_l", "pelvis"):
        jx, jy = pt(joint)
        jr = max(2, int(2.2 * SCALE))
        d.ellipse([jx - jr, jy - jr, jx + jr, jy + jr], fill=colour)

    if holds:
        wx, wy = pt("wrist_r")
        sr = 5 / 100 * box_w
        d.ellipse([wx - sr, wy - sr, wx + sr, wy + sr], fill=colour)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    pad_x, pad_top = int(20 * SCALE), int(38 * SCALE)
    baseline = H - int(30 * SCALE)
    usable = W - 2 * pad_x
    cell = usable / len(POSES)
    box_h = baseline - pad_top

    # ground line
    d.line([(pad_x, baseline), (W - pad_x, baseline)], fill=GROUND,
           width=max(2, int(1.5 * SCALE)))

    # dashed phase dividers
    for i in range(1, len(POSES)):
        x = pad_x + cell * i
        y = pad_top - int(6 * SCALE)
        while y < baseline:
            d.line([(x, y), (x, min(y + 6 * SCALE, baseline))],
                   fill=GROUND, width=max(1, int(1.2 * SCALE)))
            y += 12 * SCALE

    # the four phases, darkening left to right so the sequence reads as time
    for i, pose in enumerate(POSES):
        colour = lerp(INK_FADE, INK, i / (len(POSES) - 1))
        draw_pose(d, pose, pad_x + cell * i + cell * 0.08, pad_top,
                  cell * 0.84, box_h, colour, HOLDS_IMPLEMENT[i])

    title = load_font(int(19 * SCALE))
    d.text((pad_x, int(12 * SCALE)), "Throwing4", font=title, fill=LABEL)

    sub = load_font(int(12 * SCALE))
    d.text((pad_x, baseline + int(9 * SCALE)),
           "phase-aligned throwing sequence", font=sub, fill=(120, 130, 140))

    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB, {W}x{H})")


if __name__ == "__main__":
    main()
