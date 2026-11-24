"""Linear-light, premultiplied-alpha sprite downsampling."""
import numpy as np
from PIL import Image


def resize_rgba(image, size, space='linear'):
    """Lanczos reduction with premultiplied alpha.

    space='linear' averages light (physically right for compositing; the
    Spearman delivery through round 10). space='display' averages encoded sRGB
    values, which is how the game's painted tokens were reduced from their
    masters: a render reduced this way can match the painting, while the same
    pixels reduced in linear light sit about 3 CIE76 away (look lane,
    2026-11-24). Use one space for a unit's delivery and for every image it is
    compared with.
    """
    assert space in ('linear', 'display')
    if image.size == size:
        return image.convert('RGBA').copy()
    if space == 'display':
        # Pillow premultiplies RGBA internally when resampling.
        return image.convert('RGBA').resize(size, Image.Resampling.LANCZOS)
    rgba = np.asarray(image.convert('RGBA'), dtype=np.float32)/255
    rgb, alpha = rgba[..., :3], rgba[..., 3]
    linear = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    def resize(channel):
        return np.asarray(Image.fromarray(channel.astype(np.float32)).resize(size, Image.Resampling.LANCZOS))
    a = np.clip(resize(alpha), 0, 1)
    premult = np.stack([resize(linear[..., i]*alpha) for i in range(3)], axis=-1)
    premult = np.minimum(np.maximum(premult, 0), a[..., None])
    colour = np.divide(premult, a[..., None], out=np.zeros_like(premult), where=a[..., None]>1e-7)
    srgb = np.where(colour <= .0031308, colour*12.92, 1.055*colour**(1/2.4)-.055)
    return Image.fromarray(np.round(np.clip(np.dstack((srgb, a)), 0, 1)*255).astype(np.uint8))
