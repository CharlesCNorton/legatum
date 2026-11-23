"""Mechanical motion: +X travel, arc-length belt, angular speed = speed/radius."""
import bpy,os,sys,math,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runninggear import route
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/panzer';(M/'clips').mkdir(exist_ok=True)
clips={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
for clip,(count,fps) in clips.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/'panzer.blend'));sc=bpy.context.scene
    root=bpy.data.objects['Vehicle suspension root'];turret=bpy.data.objects['Turret traverse'];gun=bpy.data.objects['Gun recoil']
    turret_rest=turret.rotation_euler.copy();gun_rest=gun.location.copy();gun_rot=gun.rotation_euler.copy()
    length,point=route(json.loads(root['route_circles']))
    far_length,far_point=route(json.loads(root['route_circles_far']))
    wheels=[o for o in bpy.data.objects if 'wheel_radius' in o];links=[o for o in bpy.data.objects if 'track_phase' in o]
    effects=[o for o in bpy.data.objects if 'effect' in o]
    restloc={o.name:o.location.copy() for o in effects}
    # Soft irregular closed shells; edge falloff avoids the old stacked oval outlines.
    smoke=bpy.data.materials['Soot smoke'];n=smoke.node_tree.nodes;l=smoke.node_tree.links
    bsdf=n.get('Principled BSDF');output=n.get('Material Output')
    clear=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=4
    strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.50
    geom=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
    l.new(geom.outputs['Normal'],dot.inputs[0]);l.new(geom.outputs['Incoming'],dot.inputs[1])
    absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(dot.outputs['Value'],absolute.inputs[0])
    face=n.new('ShaderNodeMath');face.operation='POWER';face.inputs[1].default_value=2.5;l.new(absolute.outputs[0],face.inputs[0])
    breakup=n.new('ShaderNodeMath');breakup.operation='MULTIPLY';l.new(noise.outputs['Fac'],breakup.inputs[0]);l.new(face.outputs[0],breakup.inputs[1])
    l.new(breakup.outputs[0],strength.inputs[0]);l.new(strength.outputs[0],mix.inputs[0])
    l.new(clear.outputs[0],mix.inputs[1]);l.new(bsdf.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs['Surface'])
    burn=[]
    if clip=='death':
        for mat in bpy.data.materials:
            if 'painted projection' not in mat.name or 'limestone' in mat.name:continue
            n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
            color=bs.inputs['Base Color'].links[0].from_socket
            tint=n.new('ShaderNodeMixRGB');tint.name='Wreck soot';tint.blend_type='MULTIPLY';tint.inputs[2].default_value=(.28,.25,.22,1)
            l.new(color,tint.inputs[1]);l.new(tint.outputs[0],bs.inputs['Base Color'])
            for node in n:
                if node.type=='EMISSION':l.new(tint.outputs[0],node.inputs['Color'])
            burn.append(tint)
    for i in range(count+1):
        t=i/count;q=min(i,8)/8;wave=math.sin(math.tau*t)
        root.location=(0,0,0);root.rotation_euler=(0,0,0);turret.rotation_euler=turret_rest;gun.location=gun_rest;gun.rotation_euler=gun_rot
        if clip=='idle':
            root.rotation_euler[0]=.002*wave;turret.rotation_euler[2]+=.014*wave
        elif clip=='move':
            # Tank remains anchored as the game moves its token. Contact speed is -v.
            root.rotation_euler[1]=.004*math.sin(2*math.tau*t)
            distance=t*length*6/72
            for o in links:
                x,z,a=point(o['track_phase']+distance/length) if o['track_side']==-1 else far_point(o['track_phase']+distance/far_length);o.location=(x,o['track_y'],z);o.rotation_euler[1]=a
                o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
            for o in wheels:
                o.rotation_euler[1]=distance/o['wheel_radius'];o.keyframe_insert('rotation_euler',frame=i+1)
        elif clip=='attack':
            recoil=[0,0,.02,.19,.13,.065,.03,.01,0,0,0][i]
            gun.location.x-=recoil;root.rotation_euler[1]=recoil*.12
        elif clip=='hit':
            root.rotation_euler[0]=[0,-.045,.022,0,0][i];root.rotation_euler[1]=[0,.027,-.01,0,0][i]
            gun.location.x-=[0,.13,.04,0,0][i]
        else:
            settle=math.sin(min(q,1)*math.pi/2)
            root.rotation_euler[0]=-.045*settle;root.rotation_euler[1]=-.025*settle;root.location.z=-.015*settle
            turret.rotation_euler[2]+=.11*settle;gun.rotation_euler[1]+=.15*settle;gun.location.x-=.16*settle
        for tint in burn:
            tint.inputs[0].default_value=min(1,max(0,(q-.18)/.55));tint.inputs[0].keyframe_insert('default_value',frame=i+1)
        for o in [root,turret,gun]:
            o.keyframe_insert('location',frame=i+1);o.keyframe_insert('rotation_euler',frame=i+1)
        for o in effects:
            o.hide_render=True;o.location=restloc[o.name];o.scale=(1,1,1)
            if o['effect']=='flash':
                o.hide_render=not(clip=='attack' and i==3)
                o.location.x-=.13;o.scale=(.75,.85,.85)
            elif clip=='death' and i>=3:
                k=o['index'];o.hide_render=False;o.location=(-.62+.15*math.sin(k*2.4+q)-k*.018,.11*math.cos(k*2.2),1.83+k*.105+.13*q)
                o.scale=(1+k*.095,1+k*.08,1+k*.055)
            o.keyframe_insert('hide_render',frame=i+1);o.keyframe_insert('location',frame=i+1);o.keyframe_insert('scale',frame=i+1)
    for action in bpy.data.actions:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
    frames=list(range(1,count+1))
    if clip=='death':frames[-1]=frames[-2]
    sc['sample_frames']=json.dumps(frames);sc['clip']=clip;sc['source_sha256']=hashlib.sha256((M/'panzer.blend').read_bytes()).hexdigest()
    sc.frame_start=1;sc.frame_end=count+1;sc.render.fps=fps;sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
    print('CLIP_READY',clip,frames)
