"""Shared lossless-alpha token reduction for packing and independent reconstruction."""
from PIL import Image


def token(image):
    # Pillow RGBa is premultiplied; bicubic avoids Lanczos perimeter ringing.
    return image.convert('RGBa').resize((160, 160), Image.Resampling.BICUBIC).convert('RGBA')
