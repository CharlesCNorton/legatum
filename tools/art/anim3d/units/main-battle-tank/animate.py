"""Authored mechanical animation on the actual 3D hierarchy. No image deformation.
Track speed is three eighths of a link pitch / output frame; wheel rotation uses the same distance.
"""
import bpy,os,math,json,sys,hashlib
from pathlib import Path
from math import pi,sin,cos
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runninggear import route
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/main-battle-tank';out=M/'clips';out.mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
for clip,(count,fps,loop) in CLIPS.items():
    if os.environ.get('ANIMATE_CLIP') and clip!=os.environ['ANIMATE_CLIP']:continue
    bpy.ops.wm.open_mainfile(filepath=str(M/'main-battle-tank.blend'))
    sc=bpy.context.scene
    routes={int(side):route(circles) for side,circles in json.loads(sc['track_circles']).items()}
    LENGTH=routes[-1][0]
    sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
    root=bpy.data.objects['Vehicle suspension root'];turret=bpy.data.objects['Turret traverse'];gun=bpy.data.objects['Gun recoil']
    bpy.context.view_layer.update()
    # Match the registered barrel muzzle, preserving local recoil/traverse motion.
    gun_effect_shift=Vector(sc['muzzle_local'])-Vector((2.14,0,0))
    wheels=[o for o in bpy.data.objects if 'wheel' in o];links=[o for o in bpy.data.objects if 'track_phase' in o];effects=[o for o in bpy.data.objects if 'effect' in o]
    if clip=='attack':
        # Lower optical density for the overlapping muzzle shells; the wreck
        # smoke keeps its heavier material. No volume grids or zero scales.
        haze=bpy.data.materials['Smoke • noise faded 3D shell'].copy()
        haze.name='Dispersing muzzle haze'
        for node in haze.node_tree.nodes:
            if node.type=='MATH' and node.operation=='MULTIPLY' and not node.inputs[1].is_linked:
                node.inputs[1].default_value=.12
        for effect in effects:
            if effect['effect']=='gun_smoke':
                effect.data.materials.clear();effect.data.materials.append(haze)
    movers=[root,turret,gun]+wheels+links+effects
    burns=[]
    if clip=='death':
        for mat in bpy.data.materials:
            if mat.name.startswith('Warm cream limestone'):continue
            if not any(term in mat.name for term in ['Olive drab','baked pigment','Dusty rubbed','painted projection']):continue
            n=mat.node_tree.nodes;l=mat.node_tree.links;shader=n.get('Principled BSDF')
            source=shader.inputs['Base Color'].links[0].from_socket
            noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3
            mask=n.new('ShaderNodeValToRGB');mask.color_ramp.elements[0].position=.25;mask.color_ramp.elements[0].color=(.80,.80,.80,1);mask.color_ramp.elements[1].position=.60
            l.new(noise.outputs['Fac'],mask.inputs[0])
            amount=n.new('ShaderNodeMath');amount.operation='MULTIPLY';l.new(mask.outputs[0],amount.inputs[0]);burns.append(amount)
            soot=n.new('ShaderNodeMixRGB');soot.inputs[2].default_value=(.013,.011,.008,1)
            l.new(source,soot.inputs[1]);l.new(amount.outputs[0],soot.inputs[0]);l.new(soot.outputs[0],shader.inputs['Base Color'])
            for node in n:
                if node.type=='EMISSION':l.new(soot.outputs[0],node.inputs['Color'])
    for i in range(count+1 if loop else count):
        # Final death pose is frozen, planted; same sample used twice by the renderer.
        j=min(i,8) if clip=='death' else i;t=j/(count-1);phase=2*pi*i/count
        root.location=(0,0,-.11);root.rotation_euler=(0,0,0);turret.rotation_euler=(0,0,math.radians(0));gun.rotation_euler=(0,math.radians(-10),0);gun.location=(.64,0,.28)
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
            root.location.z-=.008*settle;turret.rotation_euler[2]+=-.12*settle;gun.rotation_euler[1]=math.radians(-10)+.18*settle
        for o in wheels:
            # Small engine vibration does not turn wheels. Track pattern repeats at key 9; inspect the sampled wheel loop visually.
            o.rotation_euler[1]=-(i*3/8*routes[o['track_side']][0]/62/o.get('rolling_radius',.32 if 'Sprocket' in o.name else .28)) if clip=='move' else 0
        for o in links:
            offset=i*3/8/62 if clip=='move' else 0;x,z,a=routes[o['track_side']][1](o['track_phase']+offset)
            while a-o.rotation_euler[1]>pi:a-=2*pi
            while a-o.rotation_euler[1]<-pi:a+=2*pi
            o.location=(x,o['track_side']*.99,z);o.rotation_euler[1]=a
        for o in effects:
            o.scale=(1,)*3;o.hide_render=True;kind=o['effect'];k=o['index']
            if kind=='exhaust' and clip in ['idle','move']:
                o.hide_render=k>=5
                age=((i/count+k/9)%1);r=.025+.045*age
                o.location=(-1.72-.20*age,-.56+.05*sin(k+phase),1.04+.32*age);o.scale=(r*1.5,r,r*1.4)
            if kind=='flash' and clip=='attack' and j==4:
                o.hide_render=False
                o.location=(2.14,0,0);o.scale=(.5,.35,.35) if k<2 else (.4,.3,.32)
                o.rotation_euler=(k*.9,pi/2+.30*sin(k),.25*cos(k))
            if kind=='gun_smoke' and clip=='attack' and 4<=j<=8:
                o.hide_render=False
                age=(j-4)/5;r=.02+.04*age
                o.location=(2.12+.04*age,.06*sin(k*2)*age,.02*k*age+.10*age);o.scale=(r*1.3,r,r)
            if kind=='spark' and ((clip=='hit' and j in [1,2]) or (clip=='death' and j in [1,2,3])):
                o.hide_render=False
                age=j/3;a=k*2.399
                o.location=(.4+.28*age*cos(a),-.8-.23*age,1.45+.30*age*sin(a));o.scale=(.6+age,)*3;o.rotation_euler=Vector((cos(a),-.3,sin(a))).to_track_quat('Z','Y').to_euler()
            if kind=='wreck_smoke' and clip=='death' and j>=2:
                o.hide_render=False
                growth=min(1,(j-1)/4);age=(k/14+j*.055)%1;r=(.10+.12*age)*growth
                o.location=(-.65+.16*sin(k*1.7)+.20*age,.15*cos(k*2.4),1.54+.95*age);o.scale=(r*1.3,r,r*1.5)
            if kind in ('flash','gun_smoke'):
                o.location+=gun_effect_shift
        for amount in burns:
            amount.inputs[1].default_value=min(.75,max(0,(j-1)/7))
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
    sc['sample_frames']=json.dumps(samples);sc['clip']=clip;sc['loop']=loop;sc['source_sha256']=hashlib.sha256((M/'main-battle-tank.blend').read_bytes()).hexdigest()
    sc['track_distance_per_frame']=3/8*LENGTH/62 if clip=='move' else 0
    sc['track_distances_per_frame']=json.dumps({str(side):3/8*data[0]/62 if clip=='move' else 0 for side,data in routes.items()})
    sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{clip}.blend'))
    print('ANIMATED',clip,samples)
