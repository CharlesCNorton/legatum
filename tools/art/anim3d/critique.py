#!/usr/bin/env python3
"""Compare a transparent 3D rest render with its painted unit and review clips.

Run with ~/LegatumRuns/anim-pilot/venv/bin/python (Pillow and numpy required).
Both images are sampled on the same 256 x 256 canvas; the camera and framing
must already match. Only the silhouette metric searches offsets (±3 pixels).
"""

import argparse
from collections import deque
import json
from pathlib import Path
import re
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFont


SIZE = 256
CREAM = (248, 244, 231, 255)
CLIPS = ("idle", "move", "attack", "hit", "death")
IOU_TARGET = 0.95
DELTA_E_TARGET = 6.0


def load_image(path):
    with Image.open(path) as source:
        return source.convert("RGBA").resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def painting_mask(image):
    """Use real alpha, or key corner-connected, near-corner RGB background."""
    pixels = np.asarray(image)
    alpha = pixels[:, :, 3]
    if np.any(alpha < 250):
        return alpha > 8, "alpha"

    rgb = pixels[:, :, :3].astype(np.int16)
    corners = (rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1])
    near = np.zeros((SIZE, SIZE), dtype=bool)
    for corner in corners:
        near |= np.max(np.abs(rgb - corner), axis=2) <= 16
    background = np.zeros_like(near)
    queue = deque((y, x) for y, x in ((0, 0), (0, SIZE - 1), (SIZE - 1, 0), (SIZE - 1, SIZE - 1)) if near[y, x])
    while queue:
        y, x = queue.popleft()
        if background[y, x] or not near[y, x]:
            continue
        background[y, x] = True
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < SIZE and 0 <= xx < SIZE and not background[yy, xx] and near[yy, xx]:
                queue.append((yy, xx))
    mask = ~background
    if not np.any(mask) or not np.any(background):
        raise ValueError("Could not separate painting from its background; supply an image with alpha")
    return mask, "corner background key"


def shift_array(array, dx, dy):
    """Translate without wraparound; positive offsets move right and down."""
    result = np.zeros_like(array)
    h, w = array.shape[:2]
    x0, x1 = max(0, dx), min(w, w + dx)
    y0, y1 = max(0, dy), min(h, h + dy)
    result[y0:y1, x0:x1] = array[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    return result


def best_iou(painting, render):
    best = (-1.0, 0, 0, None)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            moved = shift_array(render, dx, dy)
            union = np.count_nonzero(painting | moved)
            score = np.count_nonzero(painting & moved) / union if union else 1.0
            if score > best[0]:
                best = (score, dx, dy, moved)
    return best


def rgb_to_lab(rgb):
    """sRGB -> linear RGB -> XYZ (D65) -> CIE Lab, entirely in numpy."""
    rgb = np.asarray(rgb, dtype=np.float64) / 255.0
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = linear @ np.array([[0.4124564, 0.3575761, 0.1804375],
                             [0.2126729, 0.7151522, 0.0721750],
                             [0.0193339, 0.1191920, 0.9503041]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack((116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])), axis=-1)


def on_cream(image, mask):
    rgba = np.asarray(image).copy()
    rgba[:, :, 3] = np.where(mask, rgba[:, :, 3], 0)
    base = Image.new("RGBA", (SIZE, SIZE), CREAM)
    base.alpha_composite(Image.fromarray(rgba))
    return base.convert("RGB")


def make_contact_sheet(frames, path):
    tile, label = 160, 22
    width = max(len(paths) for paths in frames.values()) * tile
    sheet = Image.new("RGB", (width, len(CLIPS) * (tile + label)), CREAM[:3])
    draw = ImageDraw.Draw(sheet)
    for row, clip in enumerate(CLIPS):
        y = row * (tile + label)
        draw.text((4, y + 3), f"{clip} ({len(frames[clip])} frames)", fill=(40, 35, 30), font=ImageFont.load_default())
        for col, frame in enumerate(frames[clip]):
            with Image.open(frame) as source:
                thumb = source.convert("RGBA")
                thumb.thumbnail((tile, tile), Image.Resampling.LANCZOS)
            cell = Image.new("RGBA", (tile, tile), CREAM)
            cell.alpha_composite(thumb, ((tile - thumb.width) // 2, (tile - thumb.height) // 2))
            sheet.paste(cell.convert("RGB"), (col * tile, y + label))
    sheet.save(path)


def run(args):
    slug = args.slug
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("--slug must contain lowercase letters, digits and hyphens")
    if args.round < 0:
        raise ValueError("--round must be nonnegative")
    painting_path = args.painting or Path(f"app/src/assets/units/{slug}-source.png")
    if not painting_path.exists() and args.painting is None:
        painting_path = Path(f"app/src/assets/units/{slug}-256.png")
    if not painting_path.is_file():
        raise FileNotFoundError(painting_path)
    frames = {}
    for clip in CLIPS:
        folder = args.frames / clip
        paths = sorted((p for p in folder.glob("*.png") if p.stem.isdecimal()), key=lambda p: int(p.stem))
        if not paths:
            raise ValueError(f"Expected numbered PNG frames in {folder}")
        frames[clip] = paths
    if args.feet and not args.feet.is_file():
        raise FileNotFoundError(args.feet)

    painting = load_image(painting_path)
    with Image.open(args.rest) as source:
        if source.format != "PNG" or source.convert("RGBA").getchannel("A").getextrema()[0] == 255:
            raise ValueError("Rest render must be a transparent PNG")
    render = load_image(args.rest)
    paint_mask, mask_source = painting_mask(painting)
    render_mask = np.asarray(render)[:, :, 3] > 8
    iou, dx, dy, aligned_mask = best_iou(paint_mask, render_mask)
    overlap = paint_mask & aligned_mask
    if not np.any(overlap):
        raise ValueError("Painting and rest render have no overlapping figure pixels")

    paint_rgb = np.asarray(painting)[:, :, :3]
    render_rgb = shift_array(np.asarray(render)[:, :, :3], dx, dy)
    delta = np.linalg.norm(rgb_to_lab(paint_rgb) - rgb_to_lab(render_rgb), axis=2)
    mean_delta = float(np.mean(delta[overlap]))
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{slug}-round{args.round}"

    p_view, r_view = on_cream(painting, paint_mask), on_cream(render, render_mask)
    compare = Image.new("RGB", (SIZE * 2, SIZE), CREAM[:3])
    compare.paste(p_view, (0, 0))
    compare.paste(r_view, (SIZE, 0))
    compare.save(out / f"{stem}-side-by-side.png")
    Image.blend(p_view, r_view, 0.5).save(out / f"{stem}-crossfade.png")

    difference = np.full((SIZE, SIZE, 3), CREAM[:3], dtype=np.uint8)
    difference[overlap] = (48, 55, 50)
    difference[paint_mask & ~aligned_mask] = (0, 170, 210)
    difference[aligned_mask & ~paint_mask] = (220, 65, 150)
    Image.fromarray(difference).save(out / f"{stem}-silhouette-difference.png")
    heat = np.full((SIZE, SIZE, 3), CREAM[:3], dtype=np.uint8)
    intensity = np.clip(delta / 30, 0, 1)
    heat[overlap] = np.stack((255 * intensity, 210 * (1 - intensity), 40 * (1 - intensity)), axis=-1)[overlap].astype(np.uint8)
    Image.fromarray(heat).save(out / f"{stem}-deltae-heatmap.png")
    make_contact_sheet(frames, out / f"{stem}-contact-sheet.png")
    if args.feet:
        shutil.copyfile(args.feet, out / f"{stem}-feet-check.png")

    metrics = {
        "slug": slug, "round": args.round, "painting": str(painting_path), "rest": str(args.rest),
        "painting_mask_source": mask_source, "comparison_size_px": SIZE,
        "silhouette_iou": float(iou), "silhouette_target": IOU_TARGET,
        "silhouette_pass": bool(iou >= IOU_TARGET),
        "iou_search_px": 3, "best_render_offset_px": {"x": dx, "y": dy},
        "mean_delta_e_cie76": mean_delta, "delta_e_target": DELTA_E_TARGET,
        "colour_pass": bool(mean_delta <= DELTA_E_TARGET),
        "overlap_pixels": int(np.count_nonzero(overlap)),
        "frame_counts": {clip: len(frames[clip]) for clip in CLIPS},
    }
    (out / f"{stem}-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    with (out / f"{stem}-note.md").open("a") as note:
        note.write(f"\n### Automated critique: {stem}\n\n"
                   f"- Silhouette IoU: **{iou:.4f}** (target ≥ {IOU_TARGET:.2f}; {'PASS' if metrics['silhouette_pass'] else 'FAIL'}). "
                   f"Best of ±3 px offsets: render x={dx:+d}, y={dy:+d}.\n"
                   f"- Mean CIE76 ΔE: **{mean_delta:.2f}** (target ≤ {DELTA_E_TARGET:.0f}; {'PASS' if metrics['colour_pass'] else 'FAIL'}), "
                   f"over {metrics['overlap_pixels']} overlapping figure pixels after that offset.\n"
                   f"- Painting mask: {mask_source}; frames: "
                   + ", ".join(f"{clip} {len(frames[clip])}" for clip in CLIPS) + ".\n")
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--painting", type=Path, help="defaults to source master if present, otherwise 256 PNG")
    parser.add_argument("--rest", type=Path, required=True)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--feet", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), indent=2))
    except (FileNotFoundError, ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
