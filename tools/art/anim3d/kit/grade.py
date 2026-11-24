"""One rest-calibrated colour grade per unit, reused for every frame.

Fit a monotone per-channel histogram match between the rest render and the
painting, then apply that same lookup table to every clip frame. Never fit per
frame: colour pumps during motion. Keep the raw renders; the grade is bound to
the master and painting hashes so a stale grade cannot be applied silently.

Proven on Spearman rounds 3-10 at strength 0.80 (see SKILL.md step 6). Pure
Pillow; run with the pipeline venv, not inside Blender.
"""
import hashlib
import json
from pathlib import Path

from PIL import Image

STRENGTH = .80
OPAQUE = 240


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def histograms(image, opaque=OPAQUE):
    """RGB histograms over pixels whose alpha is above `opaque`."""
    image = image.convert('RGBA')
    mask = image.getchannel('A').point(lambda x: 255 if x > opaque else 0)
    return [image.getchannel(c).histogram(mask=mask) for c in 'RGB']


def cdf(hist):
    total = sum(hist)
    assert total, 'Empty opaque mask'
    result, acc = [], 0
    for count in hist:
        acc += count
        result.append(acc/total)
    return result


def fit(render, painting, strength=STRENGTH):
    """Three 256-entry lookup tables mapping `render` tones toward `painting`.

    Both images must show the same pose at the same size (the 256 px rest
    render against the 256 px painting). The mapping is monotone, so tonal
    order is preserved; `strength` blends it with identity.
    """
    assert 0 <= strength <= 1
    tables = []
    for src, target in zip(histograms(render), histograms(painting)):
        s, t = cdf(src), cdf(target)
        j, lut = 0, []
        for i, quantile in enumerate(s):
            while j < 255 and t[j] < quantile:
                j += 1
            lut.append(round(i*(1-strength)+j*strength))
        tables.append(lut)
    return tables


def apply(image, tables):
    """Grade RGB through the tables; alpha is returned untouched."""
    image = image.convert('RGBA')
    channels = [image.getchannel(c).point(table) for c, table in zip('RGB', tables)]
    return Image.merge('RGBA', (*channels, image.getchannel('A')))


def fit_file(rest_render, painting, master, out, size=256, strength=STRENGTH):
    """Fit from files and write the grade JSON with the hashes it depends on."""
    render = Image.open(rest_render).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
    source = Image.open(painting).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
    data = {'master_sha256': digest(master), 'reference_sha256': digest(painting),
            'calibration_render_sha256': digest(rest_render), 'strength': strength,
            'luts': fit(render, source, strength)}
    Path(out).write_text(json.dumps(data, indent=2))
    return data


def load(grade, master):
    """Read a grade and refuse it if the master changed since it was fitted."""
    data = json.loads(Path(grade).read_text())
    assert data['master_sha256'] == digest(master), 'Stale grade: rerender rest and refit'
    return data
