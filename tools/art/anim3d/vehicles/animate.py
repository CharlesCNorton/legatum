"""Authored mechanical animation on the actual 3D hierarchy. No image deformation.
Track speed is three eighths of a link pitch / output frame; wheel rotation uses the same distance.
"""
import bpy,os,math,json
from pathlib import Path
from math import pi,sin,cos
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tank';out=M/'clips';out.mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
HALF=1.39;RAD=.40;Z=.79;LENGTH=4*HALF+2*pi*RAD

def trackpoint(t):
    d=(t%1)*LENGTH
    if d<2*HALF:return(-HALF+d,Z+RAD,0)
    d-=2*HALF
    if d<pi*RAD:
        a=pi/2-d/RAD;return(HALF+RAD*cos(a),Z+RAD*sin(a),pi/2-a)
    d-=pi*RAD
    if d<2*HALF:return(HALF-d,Z-RAD,pi)
    d-=2*HALF;a=-pi/2-d/RAD;return(-HALF+RAD*cos(a),Z+RAD*sin(a),pi/2-a)

for clip,(count,fps,loop) in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/'tank.blend'))
    sc=bpy.context.scene;sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
    root=bpy.data.objects['Vehicle suspension root'];turret=bpy.data.objects['Turret traverse'];gun=bpy.data.objects['Gun recoil']
    bpy.context.view_layer.update()
    # Match the registered barrel muzzle, preserving local recoil/traverse motion.
    camera_basis=sc.camera.rotation_euler.to_matrix()
    gun_effect_shift=gun.matrix_world.inverted().to_3x3() @ (
        camera_basis @ Vector((-3,10,0)) * sc.camera.data.ortho_scale/256
    ) if sc.get('registered') else Vector((0,0,0))
    wheels=[o for o in bpy.data.objects if 'wheel' in o];links=[o for o in bpy.data.objects if 'track_phase' in o];effects=[o for o in bpy.data.objects if 'effect' in o]
    movers=[root,turret,gun]+wheels+links+effects
    burns=[]
    if clip=='death':
        for mat in bpy.data.materials:
            if mat.name.startswith('Warm cream limestone'):continue
            if not any(term in mat.name for term in ['Olive drab','baked pigment','Dusty rubbed','painted projection']):continue
            n=mat.node_tree.nodes;l=mat.node_tree.links;shader=n.get('Principled BSDF')
            source=shader.inputs['Base Color'].links[0].from_socket
            noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7
            mask=n.new('ShaderNodeValToRGB');mask.color_ramp.elements[0].position=.25;mask.color_ramp.elements[0].color=(.45,.45,.45,1);mask.color_ramp.elements[1].position=.60
            l.new(noise.outputs['Fac'],mask.inputs[0])
            amount=n.new('ShaderNodeMath');amount.operation='MULTIPLY';l.new(mask.outputs[0],amount.inputs[0]);burns.append(amount)
            soot=n.new('ShaderNodeMixRGB');soot.inputs[2].default_value=(.013,.011,.008,1)
            l.new(source,soot.inputs[1]);l.new(amount.outputs[0],soot.inputs[0]);l.new(soot.outputs[0],shader.inputs['Base Color'])
            for node in n:
                if node.type=='EMISSION':l.new(soot.outputs[0],node.inputs['Color'])
    for i in range(count+1 if loop else count):
        # Final death pose is frozen, planted; same sample used twice by the renderer.
        j=min(i,8) if clip=='death' else i;t=j/(count-1);phase=2*pi*i/count
        root.location=(0,0,-.11);root.rotation_euler=(0,0,0);turret.rotation_euler=(0,0,math.radians(15));gun.rotation_euler=(0,math.radians(-22),0);gun.location=(.55,0,.20)
        if clip=='idle':
            root.location.z+=.003*sin(phase*3);root.rotation_euler[0]=.002*sin(phase*2);turret.rotation_euler[2]+=.026*sin(phase)
        elif clip=='move':
            root.location.z+=.012+.012*sin(phase*2);root.rotation_euler[1]=.014*sin(phase);root.rotation_euler[0]=.008*cos(phase*2)
        elif clip=='attack':
            turret.rotation_euler[2]+=[0,-.025,-.06,-.08,-.08,-.07,-.04,-.015,0,0][j]
            recoil=[0,0,0,0,.18,.10,.045,.012,0,0][j]
            gun.location-=gun.rotation_euler.to_matrix() @ Vector((recoil,0,0))
            root.rotation_euler[1]=[0,0,0,0,-.018,.012,.006,0,0,0][j]
        elif clip=='hit':
            root.rotation_euler[0]=[0,.035,-.025,0][j];root.rotation_euler[1]=[0,-.02,.014,0][j];root.location.z+=[0,.018,.004,0][j]
        elif clip=='death':
            settle=min(1,j/6);root.rotation_euler[0]=.018*settle;root.rotation_euler[1]=.008*settle
            root.location.z-=.008*settle;turret.rotation_euler[2]+=-.12*settle;gun.rotation_euler[1]=math.radians(-22)+.18*settle
        for o in wheels:
            # Small engine vibration does not turn wheels. Track pattern repeats at key 9; inspect the sampled wheel loop visually.
            o.rotation_euler[1]=-(i*3/8*LENGTH/62/o.get('rolling_radius',.32 if 'Sprocket' in o.name else .28)) if clip=='move' else 0
        for o in links:
            offset=i*3/8/62 if clip=='move' else 0;x,z,a=trackpoint(o['track_phase']+offset)
            while a-o.rotation_euler[1]>pi:a-=2*pi
            while a-o.rotation_euler[1]<-pi:a+=2*pi
            o.location=(x,o['track_side']*.99,z);o.rotation_euler[1]=a
        for o in effects:
            o.scale=(1,)*3;o.hide_render=True;kind=o['effect'];k=o['index']
            if kind=='exhaust' and clip in ['idle','move']:
                o.hide_render=False
                age=((i/count+k/9)%1);r=.035+.075*age
                o.location=(-1.72-.20*age,-.56+.05*sin(k+phase),1.10+.75*age);o.scale=(r*1.5,r,r*1.4)
            if kind=='flash' and clip=='attack' and j==4:
                o.hide_render=False
                o.location=(1.36,0,0);o.scale=(1,.6,.8) if k<2 else (.6,.4,.7)
                o.rotation_euler=(k*.9,pi/2+.30*sin(k),.25*cos(k))
            if kind=='gun_smoke' and clip=='attack' and 4<=j<=8:
                o.hide_render=False
                age=(j-4)/5;r=.04+.11*age
                o.location=(1.38+.24*age+.018*k,.055*sin(k*2)*age,.03*k*age+.06*age);o.scale=(r*1.3,r,r)
            if kind=='spark' and ((clip=='hit' and j in [1,2]) or (clip=='death' and j in [1,2,3])):
                o.hide_render=False
                age=j/3;a=k*2.399
                o.location=(.4+.28*age*cos(a),-.8-.23*age,1.45+.30*age*sin(a));o.scale=(.6+age,)*3;o.rotation_euler=Vector((cos(a),-.3,sin(a))).to_track_quat('Z','Y').to_euler()
            if kind=='wreck_smoke' and clip=='death' and j>=2:
                o.hide_render=False
                growth=min(1,(j-1)/4);age=(k/14+j*.055)%1;r=(.10+.12*age)*growth
                o.location=(-.65+.16*sin(k*1.7)+.20*age,.15*cos(k*2.4),1.78+.95*age);o.scale=(r*1.3,r,r*1.5)
            if kind in ('flash','gun_smoke'):
                o.location+=gun_effect_shift
        for amount in burns:
            amount.inputs[1].default_value=min(.85,max(0,(j-1)/7))
            amount.inputs[1].keyframe_insert(data_path='default_value',frame=i+1)
        for o in effects:
            o.keyframe_insert(data_path='hide_render',frame=i+1)
        for o in movers:
            for prop in ['location','rotation_euler','scale']:o.keyframe_insert(data_path=prop,frame=i+1)
    # Blender 5 layered actions: mechanical travel is linear, visibility is stepped.
    for o in movers:
        action=o.animation_data.action
        curves=[fc for layer in action.layers for strip in layer.strips
                if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]
        for fc in curves:
            for key in fc.keyframe_points:
                key.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
    samples=list(range(1,count+1))
    if clip=='death':samples[-1]=samples[-2]
    sc['sample_frames']=json.dumps(samples);sc['clip']=clip;sc['loop']=loop
    sc['track_distance_per_frame']=3/8*LENGTH/62 if clip=='move' else 0
    sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{clip}.blend'))
    print('ANIMATED',clip,samples)
