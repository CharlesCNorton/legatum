"""Full-depth tailoring in the painted rest pose, before capturing pigment UVs.

Executed in paint.py's namespace. Screen landmarks guide actual bind vertices;
no depth is removed and no painting alpha is used to cut the model silhouette.
"""
from mathutils import Matrix
import numpy as np
right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0))
up=sc.camera.matrix_world.to_quaternion() @ Vector((0,1,0))
scale=sc.camera.data.ortho_scale/256

def sculpt(obj, transform):
    states=[(m,m.show_viewport) for m in obj.modifiers if m.type!='ARMATURE']
    for m,_ in states:m.show_viewport=False
    bpy.context.view_layer.update()
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    worlds=[ev.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
    assert len(worlds)==len(obj.data.vertices),obj.name
    arm=next((m.object for m in obj.modifiers if m.type=='ARMATURE'),None)
    A=arm.matrix_world.inverted() @ obj.matrix_world if arm else None
    for v,w in zip(obj.data.vertices,worlds):
        q=world_to_camera_view(sc,sc.camera,w);x,y=q.x*256,(1-q.y)*256
        xx,yy=transform(x,y,v)
        delta=obj.matrix_world.to_3x3().inverted() @ ((right*(xx-x)-up*(yy-y))*scale)
        if arm:
            weighted=Matrix(((0.,0.,0.,0.),)*4);total=0
            for g in v.groups:
                name=obj.vertex_groups[g.group].name
                if name not in arm.pose.bones:continue
                p=arm.pose.bones[name];weighted+=(p.matrix @ p.bone.matrix_local.inverted())*g.weight;total+=g.weight
            if total:delta=(A.inverted() @ (weighted*(1/total)) @ A).to_3x3().inverted_safe() @ delta
        v.co+=delta
    obj.data.update()
    for m,state in states:m.show_viewport=state
    bpy.context.view_layer.update()

# Helmet shell, rolled edges, vents and nasal rib share one fitting transform.
for o in objects:
    if o.name.startswith(('GEO enclosed','GEO helmet','GEO dark ocular')):
        sculpt(o,lambda x,y,v:(124.8+(x-126.6)*.67,82+(y-87)*.85))

# Shorten the caparison as a continuous draped volume, with folded scalloped hems.
# The old cloth reached the hooves: projected horse legs then masqueraded as cloth.
for o in objects:
    if o.name.startswith(('GEO caparison','GEO chest')):
        def cloth(x,y,v):
            t=max(0,min(1,(y-143)/85))
            yy=y-27*t
            if x>138:
                yy+=max(0,15*(1-(y-120)/80))
                x=138+(x-138)*.94
            # Lift the open chest split to reveal the raised knee, without clipping.
            if x<95:yy-=10*t*max(0,(95-x)/24)
            return x,yy
        sculpt(o,cloth)

# Register four continuous legs by skin group, rather than painting fake legs
# onto the caparison. Original weights and source-action foot rotations remain.
horse=bpy.data.objects['Horse'];ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
qs=[world_to_camera_view(sc,sc.camera,ev.matrix_world @ v.co) for v in me.vertices]
screen=np.array([(q.x*256,(1-q.y)*256) for q in qs]);ev.to_mesh_clear()
profiles={
 'front.L':[(160,105,4),(180,106,3),(199,107,2.8),(214,103,3),(224,99,5)],
 'front.R':[(160,84,5),(178,78,4),(190,82,3),(203,86,3),(214,88,4)],
 'back.L':[(160,162,5),(181,165,3.7),(202,167,2.8),(214,163,3),(222,160,5)],
 'back.R':[(160,139,5),(180,141,3.3),(201,138,3),(213,134,3),(220,131,5)],
}
targets={}
for limb,profile in profiles.items():
    family,side=limb.split('.')
    names=([f'FrontUpperLeg.{side}',f'FrontLowerLeg.{side}',f'FF.{side}',f'IKFrontLeg.{side}'] if family=='front' else [f'BackUpperLeg.{side}',f'BackLowerLeg.{side}',f'FFB.{side}',f'IKBackLeg.{side}'])
    groups={horse.vertex_groups[n].index for n in names if n in horse.vertex_groups}
    ids=[v.index for v in horse.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.55 and screen[v.index,1]>156]
    assert ids,limb
    samples=screen[ids];oldbottom=max(samples[:,1]);bottom=profile[-1][0]
    for index in ids:
        x,y=screen[index];yy=156+(y-156)*(bottom-156)/(oldbottom-156)
        section=samples[abs(samples[:,1]-y)<3,0];center=(min(section)+max(section))/2;radius=max((max(section)-min(section))/2,.6)
        tx=np.interp(yy,[p[0] for p in profile],[p[1] for p in profile]);width=np.interp(yy,[p[0] for p in profile],[p[2] for p in profile])
        xx=tx+(x-center)*min(2.2,width/radius)
        blend=min(1,max(0,(y-156)/24));blend=blend*blend*(3-2*blend)
        targets[index]=(x+(xx-x)*blend,y+(yy-y)*blend)
sculpt(horse,lambda x,y,v:targets.get(v.index,(x,y)))
# Pull the hindquarter under its new shorter drape; keep the barrel fully rounded.
for o in objects:
    if o==horse or o.name.startswith(('Ivory woven','Blanket leather','Saddle raised')):
        def haunch(x,y,v):
            strength=math.exp(-((x-173)/18)**2-((y-126)/21)**2)
            return x-4*strength,y+15*strength
        sculpt(o,haunch)
# Fix mail/body correspondence at the supporting calf and raised glove.
for o in objects:
    if o.name.startswith(('Rider MPFB','GEO chainmail','GEO blue','GEO articulated')):
        def rider(x,y,v):
            t=math.exp(-((x-141)/12)**2-((y-180)/15)**2)
            return x-6*t,y-7*t
        sculpt(o,rider)
sc['round2_sculpt']='Continuous full-depth cloth, four weighted lower limbs, shared helmet details and haunch fitting'

# Fit the whole gauntlet around the existing physical lance grip. The previous
# MPFB curled fingers extended above the painted fist, exposing black mail.
for o in objects:
    if o.name.startswith(('Rider MPFB','GEO chainmail')):
        def glove(x,y,v):
            if 82<x<107 and 76<y<105:
                weight=max(0,min(1,(107-x)/5))*max(0,min(1,(105-y)/5))
                return x+(98+(x-97)*.55-x)*weight,y+(96+(y-94)*.52-y)*weight
            return x,y
        sculpt(o,glove)

from contacts import fit_rest_contacts
fit_rest_contacts()
