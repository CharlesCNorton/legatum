"""Fit one alpha-masked painting grade at rest; reuse it for every animation frame."""
import hashlib
import json
from PIL import Image, ImageEnhance, ImageStat


def stats(im):
    mask = im.getchannel('A').point(lambda a: 255 if a > 192 else 0)
    rgb = im.convert('RGB')
    values = ImageStat.Stat(rgb, mask)
    return {'mean': values.mean, 'luma_std': ImageStat.Stat(rgb.convert('L'), mask).stddev[0],
            'saturation': ImageStat.Stat(rgb.convert('HSV').getchannel('S'), mask).mean[0]}


def fit(im, source):
    actual, target = stats(im), stats(source)
    gain = [max(.90, min(1.18, b / max(1, a))) for a, b in zip(actual['mean'], target['mean'])]
    calibration = {'channel_gain': gain, 'contrast': 1., 'saturation': 1.,
                   'pivot': sum(actual['mean']) / 3, 'source': target, 'rest_before': actual}
    # Fit in application order: gains alter both contrast and saturation.
    balanced = stats(grade(im, calibration))
    calibration['contrast'] = max(.90, min(1.25, target['luma_std'] / max(1, balanced['luma_std'])))
    contrasted = stats(grade(im, calibration))
    calibration['saturation'] = max(.80, min(1.25, target['saturation'] / max(1, contrasted['saturation'])))
    return calibration



def grade(im, calibration):
    # Unlike ImageEnhance.Contrast on an RGBA canvas, the pivot excludes transparent black.
    contrast, pivot = calibration['contrast'], calibration['pivot']
    channels = [c.point(lambda v, g=g: round(max(0, min(255, (v * g - pivot) * contrast + pivot))))
                for c, g in zip(im.convert('RGB').split(), calibration['channel_gain'])]
    rgb = ImageEnhance.Color(Image.merge('RGB', channels)).enhance(calibration['saturation'])
    rgb.putalpha(im.getchannel('A'))
    return rgb


def apply(folder, source):
    raw = folder / 'ungraded'; raw.mkdir(exist_ok=True)
    calibration_path = folder.parent / 'grade-calibration.json'
    signature = hashlib.sha256((folder / 'render.json').read_bytes()).hexdigest()
    previous_path = folder / 'grade.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    repeated = previous.get('render_signature') == signature
    files = sorted(folder.glob('*.png'))
    for path in files:
        if not repeated or not (raw / path.name).exists():
            Image.open(path).convert('RGBA').save(raw / path.name)
    if folder.name == 'c':
        calibration = fit(Image.open(raw / files[0].name).convert('RGBA'), source)
        calibration_path.write_text(json.dumps(calibration, indent=2) + '\n')
    else:
        calibration = json.loads(calibration_path.read_text())
    report = {'render_signature': signature, 'calibration': calibration, 'frames': {}}
    for path in files:
        result = grade(Image.open(raw / path.name).convert('RGBA'), calibration)
        result.save(path)
        report['frames'][path.name] = stats(result)
    previous_path.write_text(json.dumps(report, indent=2) + '\n')
