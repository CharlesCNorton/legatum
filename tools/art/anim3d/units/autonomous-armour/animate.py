"""Five authored mechanical clips; no zero scales, volumes, handlers or external rig code."""
import bpy, sys, math, json, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import MASTER, CLIPS, log
from math import pi,sin,cos
R=.43;H=1.49;Z=.72;LENGTH=4*H+2*pi*R

def trackpoint(t):
    d=(t%1)*LENGTH
    if d<2*H:return(-H+d,Z+R,0)
    d-=2*H
    if d<pi*R:
        a=pi/2-d/R;return(H+R*cos(a),Z+R*sin(a),pi/2-a)
    d-=pi*R
    if d<2*H:return(H-d,Z-R,pi)
    d-=2*H;a=-pi/2-d/R;return(-H+R*cos(a),Z+R*sin(a),pi/2-a)

def curves(action):
    if hasattr(action,'fcurves'):return list(action.fcurves)
    return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]

(MASTER/'clips').mkdir(exist_ok=True)
for clip,(count,fps,loop) in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(MASTER/'finished.blend'));sc=bpy.context.scene
    root=bpy.data.objects['RIG-chassis'];turret=bpy.data.objects['RIG-turret'];gun=bpy.data.objects['RIG-gun'];sensor=bpy.data.objects['RIG-sensor']
    aerials=[bpy.data.objects[f'RIG-antenna-{i}'] for i in range(2)]
    wheels=[o for o in bpy.data.objects if 'wheel' in o];tracks=[o for o in bpy.data.objects if 'phase' in o]
    flash=bpy.data.objects['FX-flash'];scar=bpy.data.objects['FX-charred impact']
    controls=[root,turret,gun,sensor]+aerials+wheels+tracks
    rest={o.name:(o.location.copy(),o.rotation_euler.copy()) for o in controls}
    for f in range(1,count+2 if loop else count+1):
        t=(f-1)/count if loop else (f-1)/(count-1);p=2*pi*t
        for o in controls:o.location=rest[o.name][0];o.rotation_euler=rest[o.name][1]
        flash.hide_render=True;scar.hide_render=True
        if clip=='idle':
            turret.rotation_euler.z+=.025*sin(p);sensor.rotation_euler.z=.10*sin(p)
            for i,o in enumerate(aerials):o.rotation_euler.x=.012*sin(p+i*.7)
        elif clip=='move':
            # In-place travel: base and tread contact remain fixed; upper body vibrates.
            turret.location.z+=.012*sin(2*p);turret.rotation_euler.y=.008*sin(2*p)
            sensor.rotation_euler.z=.04*sin(p)
            for o in wheels:o.rotation_euler.y=-t*pi/3
            for o in tracks:
                x,z,a=trackpoint(o['phase']+2*t/64);o.location=(x,o['side']*1.04,z);o.rotation_euler.y=a
            for i,o in enumerate(aerials):o.rotation_euler.x=.04*sin(p+i*.8)
        elif clip=='attack':
            recoil=[0,0,0,.15,.10,.045,.015,0,0,0][f-1]
            aim=[0,.025,.04,.04,.035,.02,.01,0,0,0][f-1]
            turret.rotation_euler.z+=aim;gun.location.x-=recoil;gun.rotation_euler.y=-aim*.6
            turret.rotation_euler.y=-recoil*.09;flash.hide_render=f!=4
            for i,o in enumerate(aerials):o.rotation_euler.x=.055*sin((f-4)*1.7)*max(0,1-abs(f-4)/5)
        elif clip=='hit':
            impulse=[0,1,-.45,0][f-1]
            turret.rotation_euler.x=.075*impulse;turret.location.x-=.035*impulse;sensor.rotation_euler.y=.10*impulse
            for o in aerials:o.rotation_euler.x=.10*impulse
        else:
            q=min(1,max(0,(f-2)/6));q=q*q*(3-2*q)
            turret.rotation_euler.z+=.23*q;turret.rotation_euler.x=-.08*q;turret.location.z-=.075*q
            gun.rotation_euler.y=.28*q;sensor.rotation_euler.x=-.35*q
            for i,o in enumerate(aerials):o.rotation_euler.x=(.24+i*.10)*q
            scar.hide_render=f<3
        for o in controls:
            o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
        for o in [flash,scar]:o.keyframe_insert('hide_render',frame=f)
    # Mechanical trajectories are linear between authored samples; loops retain a closure key.
    for action in bpy.data.actions:
        for fc in curves(action):
            for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
    samples=list(range(1,count+1))
    if clip=='death':samples[-1]=samples[-2]
    sc['sample_frames']=json.dumps(samples);sc['clip']=clip;sc['loop']=loop
    sc['source_sha256']=hashlib.sha256((MASTER/'finished.blend').read_bytes()).hexdigest()
    sc.frame_start=1;sc.frame_end=count;sc.render.fps=fps;sc.frame_set(1)
    for o in controls:
        if o.animation_data and o.animation_data.action:o.animation_data.action.name=clip+' / '+o.name
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'clips'/f'{clip}.blend'))
    log(f'Authored {clip}: {count} output samples at {fps} fps; {len(controls)} mechanical controls; loop={loop}.')
