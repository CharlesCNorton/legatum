"""Pinned free CC0 KayKit 1.1 general reactions; assets remain outside Git."""
import hashlib
import io
import os
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

URL = 'https://media.githubusercontent.com/media/MightyBubble/Ludots-Assets/fab331eff1cb9c552c60399ea10186ef675cd460/animations/KayKit-Character-Animations-Free-1.1.zip'
SHA256 = '65882f31f905ad2e953819648a59287cdeab8f623908d5ef701971d3758be20f'
root = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
folder = root/'assets/kaykit-character-animations-1.1'
folder.mkdir(parents=True, exist_ok=True)
archive = folder/'Free-1.1.zip'
data = archive.read_bytes() if archive.exists() else urlopen(URL, timeout=60).read()
assert hashlib.sha256(data).hexdigest() == SHA256, 'KayKit archive changed'
if not archive.exists():
    archive.write_bytes(data)
with ZipFile(io.BytesIO(data)) as z:
    for relative in ['Animations/gltf/Rig_Medium/Rig_Medium_General.glb', 'License.txt']:
        content = z.read('KayKit_Character_Animations_1.1/'+relative)
        path = folder/Path(relative).name
        if path.exists():
            assert path.read_bytes() == content, f'Unexpected local reaction asset: {path}'
        else:
            path.write_bytes(content)
        print(path.name, hashlib.sha256(content).hexdigest())
