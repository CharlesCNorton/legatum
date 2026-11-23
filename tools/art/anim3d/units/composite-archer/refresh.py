"""Regenerate just one clip after a motion correction, preserving the rest LUT."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from animate import animate
from render import render
for clip in os.environ['CLIP'].split(','):
 animate(clip);render('e-'+clip)
