"""Finish actual surfaces before freezing source UVs; repeat from unpainted input."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view

bpy.ops.wm.open_mainfile(filepath=str(M/'unpainted.blend'))
sc=bpy.context.scene
rig=bpy.data.objects['RIG-eagle-warrior']
body=bpy.data.objects['GEO-MPFB-anatomy']
# Armature-deformed clothing also needs object parenting to follow root travel.
# Without it the underlayer remained behind during the source death fall.
garment=bpy.data.objects['GEO-Feather garment underlayer']
world=garment.matrix_world.copy();garment.parent=rig;garment.matrix_parent_inverse=rig.matrix_world.inverted();garment.matrix_world=world

# Preserve the morphable checkpoint. Freeze its current mixed macro shape only
# on this working copy, keeping every original vertex group and the live rig.
bpy.context.view_layer.objects.active=body
if body.data.shape_keys:
    mixed=body.shape_key_add(name='Frozen macro shape',from_mix=True)
    points=[v.co.copy() for v in mixed.data]
    body.shape_key_clear()
    for v,p in zip(body.data.vertices,points):v.co=p

# Calibrate ankle/foot axes before any retarget: the old source pose aimed the
# foot bone nearly downward in world Z to mimic a screen-space toe position.
# That pitched MPFB anatomy through otherwise horizontal sandal soles.
# Preserve actual kit world matrices while fitting anatomically horizontal feet.
sandals={ob.name:ob.matrix_world.copy() for ob in sc.objects if ob.name.startswith('GEO-Sandal')}
for side,delta in [('r',(-.035,-.15,-.015)),('l',(.10,-.13,-.015))]:
    head=rig.pose.bones['foot_'+side].head.copy()
    bone_line(rig,'foot_'+side,head,head+Vector(delta))
for name,world in sandals.items():
    if name.endswith(' l') or 'binding l' in name:world.translation.x-=.039
    bpy.data.objects[name].matrix_world=world
bpy.context.view_layer.update()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['foot_reference']='horizontal ankle-to-toe calibration before retarget; sole world transforms preserved'

# Fit the whole hand's actual anatomy, including fingers, through inverse skin.
# Source knuckles form a compact fist around the bound grip, not an open fan.
for v in body.data.vertices:
    groups={body.vertex_groups[g.group].name:g.weight for g in v.groups}
    hand_weight=sum(w for n,w in groups.items() if n=='hand_r' or n.endswith('_r') and n.startswith(('index_','middle_','ring_','pinky_','thumb_')))
    if hand_weight<.01:continue
    transforms=[(w,rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()) for n,w in groups.items() if n in rig.pose.bones]
    total=sum(w for w,_ in transforms)
    deform=Matrix([[sum(w*m[r][c] for w,m in transforms)/total for c in range(4)] for r in range(4)])
    world=body.matrix_world@deform@v.co
    p=world_to_camera_view(sc,sc.camera,world);x=p.x*256;y=(1-p.y)*256
    # Compress the forward finger fan and seat it over the painted grip.
    target_x=60+(x-57)*.63;target_y=70+(y-69)*.65
    delta=P(target_x,target_y,world.y)-P(x,y,world.y)
    v.co=deform.inverted()@body.matrix_world.inverted()@(world+delta*min(1,hand_weight))

from footfit import fit_foot_undersides
fit_foot_undersides()

# Replace the old screen-space binding arcs with real straps over the fitted
# foot arch. Their three offsets follow the sole length; no floating anklets.
for side in ['l','r']:
    old=[ob for ob in list(sc.objects) if ob.name.startswith('GEO-Sandal binding '+side)]
    mat=old[0].data.materials[0]
    for ob in old:bpy.data.objects.remove(ob,do_unlink=True)
    sole=bpy.data.objects['GEO-Sandal sole '+side].matrix_world.translation
    for offset in [-.063,0,.060]:
        pts=[]
        for j in range(17):
            t=j/16;pts.append(sole+Vector((.076*(2*t-1),offset,.021+.050*sin(pi*t))))
        ob=curve('Sandal binding '+side,pts,.0045,mat)
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
        attach(bpy.context.object,rig,'foot_'+side)


# Finish the hanging primary feathers as longer tapered vanes, retaining their
# actual depth and curved cross-section. Only the lower half is extended.
for ob in sc.objects:
    if ob.type != 'MESH' or not ob.name.startswith('GEO-Weapon wing primary'):continue
    world=ob.matrix_world.copy();inverse=world.inverted()
    pts=[world@v.co for v in ob.data.vertices]
    pixels=[world_to_camera_view(sc,sc.camera,p) for p in pts]
    xs=[p.x*256 for p in pixels];ys=[(1-p.y)*256 for p in pixels]
    cx=sum(xs)/len(xs);y0=min(ys);span=max(ys)-y0
    # Calibrated hanging tips from the painting; shape the full curved vane.
    # A blanket extension added an unwanted curtain below the outer wrist.
    outline=[(64,94),(66,105),(68,103),(70,114),(72,111),(74,125),(76,122),(78,119),(80,115),(82,115),(84,120),(86,116),(88,111),(90,111),(92,113),(94,110),(96,105),(98,105),(100,109),(102,106),(104,105),(106,104),(110,103)]
    tip=sum(xs[-3:])/3
    j=next((i for i in range(len(outline)-1) if outline[i][0]<=tip<=outline[i+1][0]),len(outline)-2)
    a,b=outline[j],outline[j+1];t=max(0,min(1,(tip-a[0])/(b[0]-a[0])))
    extension=(a[1]+t*(b[1]-a[1]))-max(ys)
    for v,p,x,y in zip(ob.data.vertices,pts,xs,ys):
        t=max(0,min(1,(y-y0)/max(span,.001)))
        xx=cx+(x-cx)*(.90-.22*t)
        yy=y+extension*t*t
        v.co=inverse@(p+P(xx,yy,p.y)-P(x,y,p.y))

# Same horizontal circular disc; keep the contact top at .20m.
base=bpy.data.objects['GEO-cream-stone-base']
for v in base.data.vertices:
    v.co.x*=.955;v.co.y*=.955
    v.co.z=.05+(v.co.z-.05)*1.28
base.location.y=.10
for mod in base.modifiers:
    if mod.type=='BEVEL':mod.width=.018;mod.segments=5
for mat in base.data.materials:
    n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    color=tuple(linear(c/255) for c in ((235,190,131) if 'rim' in mat.name else (255,225,176)))+(1,)
    bs.inputs['Base Color'].default_value=color
    bs.inputs['Emission Strength'].default_value=0
    for node in n:
        if node.type=='BUMP':node.inputs['Distance'].default_value=.0007;node.inputs['Strength'].default_value=.12
    pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera stone pigment'
    pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0
    pigment.inputs['Emission Color'].default_value=color; pigment.inputs['Emission Strength'].default_value=1
    ray=n.new('ShaderNodeLightPath');amount=n.new('ShaderNodeMath');amount.operation='MULTIPLY';amount.inputs[1].default_value=.85 if 'rim' in mat.name else .90
    l.new(ray.outputs['Is Camera Ray'],amount.inputs[0]);mix=n.new('ShaderNodeMixShader');l.new(amount.outputs[0],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    coord=n.new('ShaderNodeTexCoord');grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=210;grain.inputs['Detail'].default_value=2
    l.new(coord.outputs['Object'],grain.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=tuple(c*.88 for c in color[:3])+(1,);ramp.color_ramp.elements[1].color=color
    l.new(grain.outputs['Fac'],ramp.inputs[0])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.16
    shaded=n.new('ShaderNodeMixRGB');shaded.blend_type='MULTIPLY';shaded.inputs[0].default_value=.38
    l.new(ramp.outputs['Color'],shaded.inputs[1]);l.new(ao.outputs['Color'],shaded.inputs[2]);l.new(shaded.outputs[0],pigment.inputs['Emission Color'])

# High broad key: soften contact shadows without a painted shadow on the disc.
key=bpy.data.objects['LGT-warm-key'];key.location=(-3,-4,7);key.data.energy=1150;key.data.size=4;key.data.color=(1,.97,.91);aim(key,(0,0,1))
bpy.data.objects['LGT-soft-fill'].data.energy=230

# Apply finish on the true surface, while retaining armature deformation. Static
# kit already has bone parenting. No screen-facing or silhouette-cut geometry.
finished={}
for o in list(sc.objects):
    if o.type!='MESH':continue
    bpy.context.view_layer.objects.active=o
    disabled=[]
    for mod in o.modifiers:
        if mod.type=='ARMATURE':disabled.append((mod,mod.show_viewport));mod.show_viewport=False
    for mod in list(o.modifiers):
        if mod.type in {'SOLIDIFY','BEVEL','SUBSURF'}:
            if mod.type=='SUBSURF' and mod.levels==0:o.modifiers.remove(mod)
            else:bpy.ops.object.modifier_apply(modifier=mod.name)
    for mod,state in disabled:mod.show_viewport=state
    finished[o.name]=len(o.data.vertices)
bpy.context.view_layer.update()
sc['finished_surfaces']=json.dumps(finished)
sc['refinement_round']=2
sc['driver_round']=2
save('surface.blend')
# Clay uses the same completed geometry; keep a clean material checkpoint above.
clay=material('Round two clay',(.50,.44,.32))
for o in sc.objects:
    if o.type=='MESH' and o!=base:o.data.materials.clear();o.data.materials.append(clay)
save('plain.blend')
log('- Finished actual solid/beveled surfaces before projection, compacted the weighted weapon fist, and calibrated the physical circular stone and broad product key; retained original MPFB weights and generated feather fill.')
print('REFINE_OK',len(finished),flush=True)
