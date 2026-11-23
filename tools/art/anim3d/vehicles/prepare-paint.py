"""Fit the full-resolution alpha master to the exact token camera field (no warping)."""
from pathlib import Path
import os,hashlib,json
from PIL import Image
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tank';source=M/'tank-source.png'
im=Image.open(source).convert('RGBA');fig=im.crop(im.getchannel('A').getbbox())
k=min(928/fig.width,928/fig.height);fig=fig.resize((round(fig.width*k),round(fig.height*k)),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(fig,((1024-fig.width)//2,(1024-fig.height)//2));out.save(M/'textures/painting-projection.png')
(M/'textures/painting-projection.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fit':'same alpha-bbox fit as unit-art.py: 232/256 field, 4x resolution','size':1024},indent=2))
