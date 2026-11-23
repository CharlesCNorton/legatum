"""Prepare aligned projection and record provenance; external assets only."""
from pathlib import Path
from PIL import Image
import hashlib,json,os
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/barbarian-scout'
ref=Image.open('app/src/assets/units/barbarian-scout-256.png').convert('RGBA')
src=Image.open(A/'painting-source.png').convert('RGBA');box=src.getchannel('A').getbbox();s=src.crop(box)
# Use the committed token's alpha extent as the exact projection canvas reference.
target=ref.getchannel('A').point(lambda v:255 if v>24 else 0).getbbox();k=min((target[2]-target[0])/s.width,(target[3]-target[1])/s.height)
n=(round(s.width*k*4),round(s.height*k*4));im=Image.new('RGBA',(1024,1024));im.alpha_composite(s.resize(n,Image.Resampling.LANCZOS),(target[0]*4,target[1]*4));im.save(A/'painting-aligned.png')
(A/'sources.json').write_text(json.dumps({'painting':{'url':'https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/barbarian-scout-source.png','licence':'CC BY 4.0','sha256':hashlib.sha256((A/'painting-source.png').read_bytes()).hexdigest()},'painted-fur':{'tool':'OpenAI built-in image generation','version':'2026-11-22 round 1','licence':'Project CC BY 4.0','prompt':'Create one square seamless albedo texture for a premium hand-painted historical miniature wolf-pelt cloak. Entire canvas is tightly overlapping shaggy charcoal-brown and warm taupe fur tufts, tips picked out in ochre cream, deep dark crevices, individual fine hair brushstrokes, sophisticated oil-painted miniature craft. Soft even illumination, no cast shadows, no object silhouette, no people, no animals, no face, no text, no border. Use as the back and underside fur texture of a barbarian scout cloak. Opaque texture.','sha256':hashlib.sha256((A/'painted-fur.png').read_bytes()).hexdigest()}},indent=2))
print('projection extent',target)

p=A/'sources.json'
records=json.loads(p.read_text())
records['painted-linen']={'source':'Existing mounted-family generated fill, assets/horseman/fill-linen.png; prompt and generator provenance in assets/SOURCES.md','licence':'Project CC BY 4.0','sha256':hashlib.sha256((A/'painted-linen.png').read_bytes()).hexdigest()}
p.write_text(json.dumps(records,indent=2))
