"""Fetch only the pinned, free CC0 Standard glTF; never execute asset code."""
import hashlib
import os
from pathlib import Path
from urllib.request import urlopen

root = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
folder = root/'assets/quaternius-ual'
folder.mkdir(parents=True, exist_ok=True)
base = 'https://raw.githubusercontent.com/J-Ponzo/gltf-universal-animation-library/e24c23cf2a1323488a3faa226ea7ea21f644b73e/'
files = {
    'glTF/AnimationLibrary_Godot_Standard.gltf': '0ff075c7ad6855c5c2c37a171592ee8f0d6ab2f58259e2be77a9b63dd8027765',
    'glTF/AnimationLibrary_Godot_Standard.bin': '6e65377d81558333c4093dbb144a48fd19019343d82b1a3a7992a98ec0e0543c',
    'LICENSE': 'a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499',
}
for relative, expected in files.items():
    destination = folder/Path(relative).name
    if destination.exists():
        data = destination.read_bytes()
    else:
        with urlopen(base+relative, timeout=60) as response:
            data = response.read()
    assert hashlib.sha256(data).hexdigest() == expected, f'Unexpected source bytes: {relative}'
    if not destination.exists(): destination.write_bytes(data)
    print('MOTION_SOURCE_OK', destination.name)
