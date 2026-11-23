"""Render saved rest, build clip keys, then serially render each stage under one gate."""
import sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from render import render,CLIPS
from animate import animate
render('c')
for clip in CLIPS:
 animate(clip)
 render('e-'+clip)
