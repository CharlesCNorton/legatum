"""Host rerender of saved masters; preserves rig, geometry and projected materials."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from render import render,CLIPS
render('c')
for clip in CLIPS:render('e-'+clip)
exec(compile((Path(__file__).parent/'audit.py').read_text(),'audit.py','exec'))
