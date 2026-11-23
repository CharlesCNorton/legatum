"""Serial unit stages; each invocation uses the PATH Blender gate exactly once."""
import os,sys,runpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
stage=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'c'
if stage=='build':
    runpy.run_path(str(HERE/'scene.py'),run_name='__main__')
    from render import render
    render('b')
elif stage=='materials':runpy.run_path(str(HERE/'materials.py'),run_name='__main__')
elif stage=='animate':runpy.run_path(str(HERE/'animate.py'),run_name='__main__')
elif stage=='death-final':
    from render import render
    render('e-death')
    runpy.run_path(str(HERE/'audit.py'),run_name='__main__')
elif stage=='check-death':
    os.environ['CLIP']='death'
    runpy.run_path(str(HERE/'animate.py'),run_name='__main__')
    from render import render
    render('death-check')
elif stage.startswith('motion-'):
    clip=stage[len('motion-'):];assert clip in ['idle','move','attack','hit','death']
    os.environ['CLIP']=clip
    runpy.run_path(str(HERE/'animate.py'),run_name='__main__')
    from render import render
    if clip=='attack':render('d')
    render('e-'+clip)
elif stage=='motion':
    runpy.run_path(str(HERE/'animate.py'),run_name='__main__')
    from render import render
    render('d')
    for clip in ['idle','move','attack','hit','death']:render('e-'+clip)
    runpy.run_path(str(HERE/'audit.py'),run_name='__main__')
elif stage=='g':runpy.run_path(str(HERE/'feet.py'),run_name='__main__')
elif stage=='audit':runpy.run_path(str(HERE/'audit.py'),run_name='__main__')
elif stage=='rest':
    runpy.run_path(str(HERE/'scene.py'),run_name='__main__')
    from render import render
    render('b')
    runpy.run_path(str(HERE/'materials.py'),run_name='__main__')
    render('c');render('c-details')
elif stage in ('round','rebuild'):
    if stage=='rebuild':
        runpy.run_path(str(HERE/'scene.py'),run_name='__main__')
        from render import render
        render('b')
    runpy.run_path(str(HERE/'materials.py'),run_name='__main__')
    from render import render
    render('c');render('c-details')
    runpy.run_path(str(HERE/'animate.py'),run_name='__main__')
    render('d')
    for clip in ['idle','move','attack','hit','death']:render('e-'+clip)
    runpy.run_path(str(HERE/'audit.py'),run_name='__main__')
elif stage=='finish-motion':
    os.environ['CLIP']='attack'
    runpy.run_path(str(HERE/'animate.py'),run_name='__main__')
    runpy.run_path(str(HERE/'audit.py'),run_name='__main__')
    from render import render
    render('d')
    for clip in ['attack','hit','death']:render('e-'+clip)
    render('b')
elif stage=='cloth-fix-final':
    for clip in ['move','death']:
        os.environ['CLIP']=clip
        runpy.run_path(str(HERE/'animate.py'),run_name='__main__')
    os.environ.pop('CLIP',None)
    runpy.run_path(str(HERE/'cloth_mask.py'),run_name='__main__')
    from render import render
    render('c');render('c-details');render('d')
    for clip in ['idle','move','attack','hit','death']:render('e-'+clip)
    render('b')
    runpy.run_path(str(HERE/'audit.py'),run_name='__main__')
elif stage=='final':
    from render import render
    render('c');render('c-details');render('d')
    for clip in ['idle','move','attack','hit','death']:render('e-'+clip)
    runpy.run_path(str(HERE/'audit.py'),run_name='__main__')
else:
    from render import render
    render(stage)
