"""Mechanical object rig: closed track circuits, recoil and a held disabled wreck."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/landship';(M/'clips').mkdir(exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def curves(action):
    if hasattr(action,'fcurves'):return list(action.fcurves)
    return [fc for layer in action.layers for strip in layer.strips if hasattr(strip,'channelbags') for bag in strip.channelbags for fc in bag.fcurves]
for clip,(count,fps,loop) in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/'landship.blend'));sc=bpy.context.scene;sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
    root=bpy.data.objects['RIG-chassis'];gun=bpy.data.objects['RIG-sponson_recoil'];hatch=bpy.data.objects['RIG-roof_hatch'];hatch_rest=hatch.location.copy();gun_rest=gun.location.copy();gun_axis=Vector(sc['barrel_axis'])
    smoke_rest={o.name:o.location.copy() for o in sc.objects if o.get('effect')}
    soot=[]
    if clip=='death':
        for mat in bpy.data.materials:
            if '_projected' not in mat.name or 'cream' in mat.name:continue
            n=mat.node_tree.nodes;l=mat.node_tree.links
            for emission in [x for x in n if x.type=='EMISSION']:
                old=emission.inputs['Color'].links[0].from_socket if emission.inputs['Color'].is_linked else None
                if old:
                    mix=n.new('ShaderNodeMixRGB');mix.name='Death soot';mix.blend_type='MULTIPLY';mix.inputs[2].default_value=(.20,.18,.15,1);l.new(old,mix.inputs[1]);l.new(mix.outputs[0],emission.inputs['Color']);soot.append(mix)
    shoes=[o for o in sc.objects if 'track_distance' in o];effects=[o for o in sc.objects if o.get('effect')];route=[Vector(p) for p in json.loads(sc['route'])];lens=[0.]
    for a,b in zip(route,route[1:]+route[:1]):lens.append(lens[-1]+(b-a).length)
    L=lens[-1];pitch=L/64
    def at(d,y):
        d%=L
        for i in range(len(route)):
            if d<=lens[i+1]:
                a,b=route[i],route[(i+1)%len(route)];p=a.lerp(b,(d-lens[i])/(lens[i+1]-lens[i]));p.y=y;return p,-math.atan2(b.z-a.z,b.x-a.x)
    for f in range(1,count+2 if loop else count+1):
        t=(f-1)/count;phase=t*math.tau;u=min((f-1)/8,1)
        root.location=(0,0,0);root.rotation_euler=(0,0,0);gun.location=gun_rest;gun.rotation_euler=(0,0,0);hatch.location=hatch_rest;hatch.rotation_euler=(0,0,0)
        if clip=='idle':root.location.z=.007*math.sin(phase);root.rotation_euler.x=.002*math.sin(phase)
        if clip=='move':
            root.location.z=.008*(1-math.cos(phase*2))
            for o in shoes:
                # Route is clockwise: bottom shoes move backward for +X travel.
                p,ang=at(o['track_distance']+pitch*4*t,o['track_y']);o.location=p;o.rotation_euler.y=ang;o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
        if clip=='attack':
            recoil=[0,0,.018,.23,.16,.08,.035,.01,0,0][f-1];gun.location=gun_rest-gun_axis*recoil;root.rotation_euler.x=-.025*(recoil/.23)
        if clip=='hit':root.rotation_euler.x=[0,-.03,.018,0][f-1];root.rotation_euler.z=[0,.018,-.008,0][f-1]
        if clip=='death':
            # A disabled vehicle stays grounded; sag upper cab/hatch, open and smoke.
            hatch.location.z=hatch_rest.z+.04*min(u*3,1);hatch.rotation_euler.y=1.15*min(u*2,1)
            gun.rotation_euler.x=.065*min(u*2,1);root.rotation_euler.z=.012*math.sin(u*math.pi*4)*(1-u)
        # Keep the lowest physical track point on or above the stone under recoil/hit.
        bpy.context.view_layer.update()
        contact=min((o.matrix_world@Vector(v)).z for o in shoes for v in o.bound_box)
        root.location.z+=max(0,.205-contact)
        for o in (root,gun,hatch):
            o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_euler',frame=f)
        for mix in soot:
            mix.inputs[0].default_value=.70*u;mix.inputs[0].keyframe_insert('default_value',frame=f)
        for o in effects:
            o.location=smoke_rest[o.name]
            if clip=='death' and 'smoke' in o.name:o.location.z+=.24*u;o.location.x+=.12*u
            o.keyframe_insert('location',frame=f)
            o.hide_render=not ((clip=='attack' and 'flash' in o.name and f==4) or (clip=='death' and 'smoke' in o.name and f>=4))
            o.keyframe_insert('hide_render',frame=f)
    for o in sc.objects:
        if o.animation_data and o.animation_data.action:
            o.animation_data.action.name=f'{clip}/{o.name}'
            for fc in curves(o.animation_data.action):
                for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'LINEAR'
    sc.frame_set(1);sc['source_sha256']=hashlib.sha256((M/'landship.blend').read_bytes()).hexdigest();sc['clip']=clip;sc['loop']=loop
    bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
print('FIVE CLIPS SAVED')
