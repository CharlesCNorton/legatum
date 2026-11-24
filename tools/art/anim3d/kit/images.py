"""Premultiplied-alpha sprite reduction; linear default, display opt-in."""
import numpy as np
from PIL import Image


def resize_rgba(image, size, space="linear"):
    assert space in {"linear", "display"}, space
    rgba = np.asarray(image.convert('RGBA'), dtype=np.float32)/255
    if image.size == size:
        return image.convert('RGBA').copy()
    rgb, alpha = rgba[..., :3], rgba[..., 3]
    linear = rgb if space == "display" else np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    def resize(channel):
        return np.asarray(Image.fromarray(channel.astype(np.float32)).resize(size, Image.Resampling.LANCZOS))
    a = np.clip(resize(alpha), 0, 1)
    premult = np.stack([resize(linear[..., i]*alpha) for i in range(3)], axis=-1)
    premult = np.minimum(np.maximum(premult, 0), a[..., None])
    colour = np.divide(premult, a[..., None], out=np.zeros_like(premult), where=a[..., None]>1e-7)
    srgb = colour if space == "display" else np.where(colour <= .0031308, colour*12.92, 1.055*colour**(1/2.4)-.055)
    return Image.fromarray(np.round(np.clip(np.dstack((srgb, a)), 0, 1)*255).astype(np.uint8))
