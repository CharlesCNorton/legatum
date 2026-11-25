"""Rebuild the real-time unit from the preserved round-one Blender master.

Run via the gated Blender on PATH; see README. No camera-projected pigment.
"""
import sys, os, math, json, struct
from pathlib import Path
import bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dae import parse, geometry, bind, find, all, matrix

UNIT=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'oad/r2';WORK.mkdir(parents=True,exist_ok=True)
ART=ROOT/'oad/src/binaries/data/mods/public/art'
CREDIT='0 A.D. art by Wildfire Games, CC BY-SA 3.0; adapted for Legatum'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'oad/hoplite.blend'))
s=bpy.context.scene;s.render.fps=30
rig=bpy.data.objects['Athenian hoplite'];rig.name='Spearman'
body=bpy.data.objects['Native tunic body'];body.name='body'
for o in list(bpy.data.objects):
    if o.type not in {'ARMATURE','MESH'} or o.name.startswith('Review'):
        bpy.data.objects.remove(o,do_unlink=True)
rig.animation_data.action=None
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
rig.scale=(.39,)*3;rig.location=(0,0,0)
bpy.context.view_layer.update()
image=bpy.data.images.load(str(UNIT/'spearman-albedo.png'),check_existing=False)
materials=[]
for name in ['pigment','team']:
    m=bpy.data.materials.new(name);m.use_nodes=True
    shader=m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value=.85
    shader.inputs['Metallic'].default_value=0
    if name=='team':shader.inputs['Base Color'].default_value=(.3763,.0194,.0203,1)
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    m.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
    m.use_backface_culling=False
    materials.append(m)

def slots(ob):
    ob.data.materials.clear()
    for m in materials:ob.data.materials.append(m)
    if not ob.data.uv_layers:ob.data.uv_layers.new(name='Albedo')

def swatch(ob,poly,index,team=False):
    poly.material_index=int(team)
    uv=(((8 if team else index)+.5)/16, .875)
    for li in poly.loop_indices:ob.data.uv_layers.active.data[li].uv=uv

def paint(ob,index,team=False):
    slots(ob)
    for p in ob.data.polygons:swatch(ob,p,index,team)

def rigid(ob,bone):
    bpy.context.view_layer.update();world=ob.matrix_world.copy()
    ob.parent=rig;ob.parent_type='BONE';ob.parent_bone=bone
    ob.matrix_world=world
    ob['rigid_attachment']=bone

# Use the exact original socket transforms to attach the new helmet.
old=bpy.data.objects['Pilos helmet'];helmet_world=old.matrix_world.copy()
bpy.data.objects.remove(old,do_unlink=True)
def prop(path,name,transform=Matrix.Identity(4)):
    tree=parse(ART/path)
    node=next(n for n in all(tree,'.//c:visual_scene//c:node') if find(n,'c:instance_geometry') is not None)
    ob=geometry(tree,name,materials[0],transform @ matrix(node))
    ob.matrix_world=helmet_world;rigid(ob,'head')
    return ob,tree
helmet,tree=prop('meshes/props/helmet/hele_corinthian_a.dae','helmet')
crestmatrix=matrix(find(tree,'.//c:node[ @ name="prop-crest"]'))
crest,_=prop('meshes/props/helmet/props/hele_crest_a.dae','crest_base',crestmatrix)
hair,_=prop('meshes/props/helmet/props/hele_crest_hair_a.dae','crest',crestmatrix)
paint(helmet,0);paint(crest,6);paint(hair,2,True)
for p in helmet.data.polygons:
    centre=sum((helmet.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    if centre.y<-.12:
        for li in p.loop_indices:
            v=helmet.data.vertices[helmet.data.loops[li].vertex_index].co
            helmet.data.uv_layers.active.data[li].uv=((768+(v.x+.28)/.56*256)/1024,1-(255-(v.z+.15)/.85*256)/1024)

for name,bone in [('Greek head','head'),('Hoplite spear','weapon_R'),('Aspis front','shield_arm'),('Aspis back','shield_arm'),('Aspis handgrip','shield_arm')]:
    rigid(bpy.data.objects[name],bone)
bpy.data.objects['Hoplite spear'].name='spear'
bpy.data.objects['Aspis front'].name='aspis'
paint(bpy.data.objects['Greek head'],3)
paint(bpy.data.objects['Aspis back'],7)
paint(bpy.data.objects['Aspis handgrip'],4)
spear=bpy.data.objects['spear'];paint(spear,4)
for v in spear.data.vertices:v.co.z-=.28
for p in spear.data.polygons:
    z=sum(spear.data.vertices[i].co.z for i in p.vertices)/len(p.vertices)
    if z>1.65 or z< -3.8:swatch(spear,p,6)
shield=bpy.data.objects['aspis'];slots(shield)
for p in shield.data.polygons:
    centre=sum((shield.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    if math.hypot(centre.x+.105,centre.z)>.92:
        swatch(shield,p,2,True)
    else:
        for li in p.loop_indices:
            v=shield.data.vertices[shield.data.loops[li].vertex_index].co
            shield.data.uv_layers.active.data[li].uv=((512+(v.x+.105)*344)/1024,1-(640-v.z*344)/1024)
paint(body,1)
for p in body.data.polygons:
    c=sum((body.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    # Flat bronze cuirass/greaves, linen skirt, skin arms and leather sandal soles.
    colour=3
    if c.z<.18:colour=4
    elif c.z<1.12:colour=0
    elif c.z<2.25:colour=1
    elif abs(c.x)<.55 and c.z<3.4:colour=0
    if 2.13<c.z<2.28:colour=4
    swatch(body,p,colour)
cape_tree=parse(ART/'meshes/props/new/capes/cape_hd_hoplite.dae')
cape=geometry(cape_tree,'cloak',materials[0]);bind(cape,cape_tree,rig);paint(cape,2)
# Edge trim: actual faces belong to the team slot, so runtime tint remains cheap.
cape_minz=min(v.co.z for v in cape.data.vertices)
cape_maxx=max(abs(v.co.x) for v in cape.data.vertices)
for p in cape.data.polygons:
    c=sum((cape.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    if c.z<cape_minz+.18 or abs(c.x)>cape_maxx*.82:swatch(cape,p,6,True)
cape['team_region']='cloak trim';hair['team_region']='crest';shield['team_region']='shield rim'
# Join only deforming meshes. Every carried/worn prop stays a rigid node.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);cape.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
# Merge duplicate material slots after join while retaining the team assignment.
for p in body.data.polygons:p.material_index=p.material_index%2
while len(body.data.materials)>2:body.data.materials.pop(index=2)

keep=set()
for v in body.data.vertices:
    for g in v.groups:
        if g.weight>0:keep.add(body.vertex_groups[g.group].name)
keep.update(['weapon_R','shield_arm','head'])
for name in list(keep):
    b=rig.data.bones[name].parent
    while b:keep.add(b.name);b=b.parent
# All removed bones are unused leaf helpers or sockets replaced above.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for b in list(rig.data.edit_bones):
    if b.name not in keep:rig.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')
for g in list(body.vertex_groups):
    if g.name not in keep:body.vertex_groups.remove(g)
for b in rig.data.bones:b.use_deform=True
# glTF supports four influences; keep the strongest four and renormalize.
for v in body.data.vertices:
    groups=sorted([(g.group,g.weight) for g in v.groups if g.weight>0],key=lambda x:-x[1])
    total=sum(w for _,w in groups[:4])
    for i,w in groups:
        if (i,w) in groups[:4]:body.vertex_groups[i].add([v.index],w/total,'REPLACE')
        else:body.vertex_groups[i].remove([v.index])

sources={'idle':'idle_relax_01','walk':'walk_relax','attack':'attack_melee_05','hit':'procedural_hit','death':'death_b'}
cache={}
for name,source in sources.items():
    a=bpy.data.actions[source];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    start,end=a.frame_range;length=round(end-start)
    poses=[]
    for f in range(length+1):
        sample=start+f*(end-start)/length;s.frame_set(int(sample),subframe=sample%1)
        poses.append({p.name:p.matrix_basis.copy() for p in rig.pose.bones})
    # Close the last 20% with a smooth correction; retain native motion elsewhere.
    if name in {'idle','walk'}:
        blend=max(6,round(length*.2))
        for f in range(length-blend,length+1):
            t=min(1,(f-(length-blend))/(blend-1));t=t*t*(3-2*t)
            for bone in keep:
                # Extrapolate the outgoing tangent backward so both pose and
                # first derivative agree across the periodic boundary.
                target=poses[0][bone].lerp(poses[1][bone],f-length)
                poses[f][bone]=poses[f][bone].lerp(target,t)
    cache[name]=poses
rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)

meshes=[o for o in s.objects if o.type=='MESH']
def prop_floor(bone,objects,local_axis):
    # Rotate only the rigid socket, about the hand/forearm pivot. Binary search
    # the smallest correction toward a safe horizontal weapon / flat shield.
    p=rig.pose.bones[bone];original=p.matrix.copy()
    pivot=(rig.matrix_world @ original).translation
    points=[o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    if min(v.z for v in points)>=.002:return
    axis=(objects[0].matrix_world.to_3x3() @ Vector(local_axis)).normalized()
    if bone=='weapon_R':
        target=Vector((axis.x,axis.y,0)).normalized()
    else:
        # Aspis inner face points +local Y. Keep the convex face above ground.
        options=[Vector((0,0,-1)),Vector((0,0,1))]
        target=max(options,key=lambda t:min((pivot+axis.rotation_difference(t) @ (v-pivot)).z for v in points))
    correction=axis.rotation_difference(target)
    def minimum(t):
        q=Quaternion().slerp(correction,t)
        return min((pivot+q @ (v-pivot)).z for v in points)
    if minimum(1)<.002:
        return  # Leave an explicit diagnostic; never hide geometry at scale zero.
    lo=0;hi=1
    for _ in range(18):
        mid=(lo+hi)/2
        if minimum(mid)<.002:lo=mid
        else:hi=mid
    q=Quaternion().slerp(correction,hi)
    world=Matrix.Translation(pivot) @ q.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ rig.matrix_world @ original
    p.matrix=rig.matrix_world.inverted() @ world
    bpy.context.view_layer.update()
report={}
for name,poses in cache.items():
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
    low=[]
    for f,pose in enumerate(poses):
        s.frame_set(f+1)
        for p in rig.pose.bones:p.matrix_basis=pose[p.name];p.rotation_mode='QUATERNION'
        # Root remains fixed. Ground the actual feet/body, correcting native fall penetration.
        bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
        ev=body.evaluated_get(dep);me=ev.to_mesh()
        z=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
        if name=='death':
            z=min(z,min((o.matrix_world @ v.co).z for o in [helmet,crest,hair,bpy.data.objects['Greek head']] for v in o.data.vertices))
        hip=rig.pose.bones['hip'];world=hip.matrix.copy();world.translation.z-=z/rig.scale.z
        hip.matrix=world;bpy.context.view_layer.update()
        prop_floor('weapon_R',[spear],(0,0,1))
        prop_floor('shield_arm',[shield,bpy.data.objects['Aspis back'],bpy.data.objects['Aspis handgrip']],(0,1,0))
        if name=='death':
            bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
            floor=1e9
            for ob in meshes:
                ev=ob.evaluated_get(dep);me=ev.to_mesh()
                floor=min(floor,min((ev.matrix_world @ v.co).z for v in me.vertices));ev.to_mesh_clear()
            if floor<0:
                world=hip.matrix.copy();world.translation.z-=floor/rig.scale.z
                hip.matrix=world;bpy.context.view_layer.update()
        low.append(z)
        for p in rig.pose.bones:
            for field in ['location','rotation_quaternion','scale']:p.keyframe_insert(field,frame=f+1,group=p.name)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    report[name]={'frames':len(poses),'fps':30,'duration':(len(poses)-1)/30,'ground_correction_m':[min(low),max(low)]}
rig.animation_data.action=bpy.data.actions['idle'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];s.frame_set(1)
rig['credit']=CREDIT;rig['license']='CC-BY-SA-3.0';rig['forward']='+Z';rig['units']='metres'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'spearman.blend'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(UNIT/'spearman.glb'),export_format='GLB',use_selection=True,
    export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
    export_frame_range=False,export_extras=True,export_copyright=CREDIT,
    export_anim_slide_to_zero=True,export_optimize_animation_size=False)
# asset.extras is not emitted by Blender's exporter. Preserve all chunks while adding it.
p=UNIT/'spearman.glb';data=p.read_bytes();size,kind=struct.unpack_from('<II',data,12)
doc=json.loads(data[20:20+size]);doc['asset']['extras']={'credit':CREDIT,'license':'CC-BY-SA-3.0','license_url':'https://creativecommons.org/licenses/by-sa/3.0/','up_axis':'Y','forward':'+Z','units':'metres','fps':30}
# Derive each local prop matrix against the exported joint basis. The glTF
# exporter can change bone bases; assuming Blender's bone-tail convention here
# produces fixed prop offsets. Measure in both coordinate systems instead.
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB
exported=GLB(p)
idle=next(a for a in doc['animations'] if a['name']=='idle')
worlds=exported.worlds(idle,0)
parents={child:index for index,node in enumerate(doc['nodes']) for child in node.get('children',[])}
rig.animation_data.action=bpy.data.actions['idle'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
s.frame_set(1);bpy.context.view_layer.update()
axis=Matrix.Rotation(-math.pi/2,4,'X')
for index,node in enumerate(doc['nodes']):
    ob=bpy.data.objects.get(node.get('name',''))
    if ob and ob.type=='MESH' and ob.parent_type=='BONE':
        parent=worlds[parents[index]]
        parent=Matrix([[parent[c*4+r] for c in range(4)] for r in range(4)])
        converted=parent.inverted() @ axis @ ob.matrix_world @ axis.inverted()
        for key in ['translation','rotation','scale']:node.pop(key,None)
        node['matrix']=[converted[row][column] for column in range(4) for row in range(4)]
for material in doc['materials']:
    if material['name']=='team':material['pbrMetallicRoughness']['baseColorFactor']=[.3763,.0194,.0203,1]
# Skinned vertex transforms are joint-world * inverse-bind, independent of the
# mesh parent's transform. Detach its identity node to remove Khronos's warning.
for index,node in enumerate(doc['nodes']):
    if 'skin' in node:
        for parent in doc['nodes']:
            if index in parent.get('children',[]):parent['children'].remove(index)
        doc['scenes'][doc.get('scene',0)]['nodes'].append(index)
raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4)
rest=data[20+size:];p.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(raw)+len(rest))+struct.pack('<II',len(raw),kind)+raw+rest)
report.update(bones=len(keep),triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),glb_bytes=p.stat().st_size)
(WORK/'build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
