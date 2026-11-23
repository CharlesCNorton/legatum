"""A volumetric, skinned spearman. Run through build.sh; no relief geometry.

All poses are baked into a parented Blender armature. Two-bone analytic IK keeps
feet and grips attached; real closed meshes provide the previously hidden sides.
"""
import json
import math
import os
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

MASTER = Path.home() / 'LegatumRuns/anim-pilot/masters/spearman-3d'
MODE, ENGINE = sys.argv[sys.argv.index('--')+1:]
CLIPS = {'idle': (8,10,True), 'move': (8,12,True), 'attack': (10,14,False), 'hit': (4,12,False), 'death': (10,10,False)}
V = Vector
pi = math.pi
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = ENGINE
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
if ENGINE == 'CYCLES':
    scene.cycles.device = 'CPU'
    scene.cycles.samples = int(os.environ.get('SAMPLES', '12'))
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 3
scene.render.resolution_x = scene.render.resolution_y = 256
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Standard'
scene.world.color = (.28,.28,.28)


def material(name, tex=None, color=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new('ShaderNodeOutputMaterial')
    diffuse = n.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Roughness'].default_value = .85
    emit = n.new('ShaderNodeEmission')
    mix = n.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = .10
    l.new(diffuse.outputs[0], mix.inputs[1]); l.new(emit.outputs[0],mix.inputs[2]); l.new(mix.outputs[0],out.inputs[0])
    if tex:
        image = n.new('ShaderNodeTexImage')
        image.image = bpy.data.images.load(str(MASTER/'textures'/f'{tex}.png'))
        image.image.pack()
        if tex not in ('shield','cuirass','helmet','greave','cloth'):
            coord = n.new('ShaderNodeTexCoord')
            image.projection = 'BOX'
            image.projection_blend = .18
            l.new(coord.outputs['Generated'], image.inputs['Vector'])
        l.new(image.outputs['Color'],diffuse.inputs['Color']); l.new(image.outputs['Color'],emit.inputs['Color'])
        bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.16; bump.inputs['Distance'].default_value=.008
        l.new(image.outputs['Color'],bump.inputs['Height']); l.new(bump.outputs[0],diffuse.inputs['Normal'])
    else:
        diffuse.inputs['Color'].default_value = (*color,1)
        emit.inputs['Color'].default_value = (*color,1)
    return m

M = {k:material(k,k) for k in ('bronze','red','linen','skin','stone','wood','leather','shield','cuirass','helmet','greave','cloth')}
M['dark'] = material('Burnt umber seams',color=(.075,.042,.019))
M['gold'] = material('Drybrush ochre',color=(.66,.40,.14))
M['red_dark'] = material('Cloak fold shade',color=(.21,.025,.012))

# Rig in world coordinates: +Z up, -Y forward, spear at screen left.
rest = {}
def bone(name, a,b,parent=None): rest[name]=(V(a),V(b),parent)
bone('pelvis',(0,0,1.08),(0,0,1.30))
bone('torso',(0,0,1.22),(0,0,1.73),'pelvis')
bone('head',(0,0,1.73),(0,0,2.06),'torso')
for side,x in [('r',-.19),('l',.19)]:
    bone('thigh_'+side,(x,0,1.10),(x*1.28,-.025,.66),'pelvis')
    bone('shin_'+side,(x*1.28,-.025,.66),(x*1.65,0,.22),'thigh_'+side)
    bone('foot_'+side,(x*1.65,0,.22),(x*1.65,-.20,.17),'shin_'+side)
    sx=-.27 if side=='r' else .27
    elbow=(-.43,-.035,1.48) if side=='r' else (.43,-.04,1.43)
    hand=(-.50,-.24,1.55) if side=='r' else (.43,-.34,1.44)
    bone('upper_'+side,(sx,0,1.69),elbow,'torso')
    bone('fore_'+side,elbow,hand,'upper_'+side)
    bone('hand_'+side,hand,V(hand)+V((0,0,.10)),'fore_'+side)
bone('spear',(-.50,-.24,1.55),(-.50,-.24,2.05),'hand_r')
bone('shield',(.43,-.38,1.43),(.43,-.88,1.43),'hand_l')
bone('cloak',(0,.14,1.68),(0,.23,1.05),'torso')
arm = bpy.data.armatures.new('Spearman skeleton')
rig = bpy.data.objects.new('Spearman · volumetric rig',arm)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b,parent) in rest.items():
    eb=arm.edit_bones.new(name); eb.head=a; eb.tail=b
    if parent: eb.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
rig.select_set(False)


def skin(obj, bn):
    if bn:
        group=obj.vertex_groups.new(name=bn); group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
        mod=obj.modifiers.new('Skin to skeleton','ARMATURE'); mod.object=rig
    return obj


def finish(obj,name,mat,bn=None,smooth=True):
    obj.name=name; obj.data.materials.append(M[mat])
    if smooth:
        for p in obj.data.polygons:p.use_smooth=True
    # Vertices remain in world space so the armature is the only animated transform.
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True); bpy.ops.object.transform_apply(location=True,rotation=True,scale=True); obj.select_set(False)
    return skin(obj,bn)


def ell(name,loc,scale,mat,bn=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
    o=bpy.context.object;o.scale=scale
    return finish(o,name,mat,bn)


def rod(name,a,b,r,mat,bn=None,r2=None,verts=16):
    a,b=V(a),V(b)
    bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r if r2 is None else r2,depth=(b-a).length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y')
    return finish(o,name,mat,bn)


def mesh(name,verts,faces,mat,bn=None,uv=False):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);data.materials.append(M[mat])
    if uv:
        layer=data.uv_layers.new()
        for p in data.polygons:
            for i in p.loop_indices:
                co=data.vertices[data.loops[i].vertex_index].co
                layer.data[i].uv=((co.x-.43)/.90+.5,(co.z-1.43)/.90+.5)
    for p in data.polygons:p.use_smooth=True
    skin(o,bn);return o


def ringbody(name,rings,mat,bn,n=32,pleat=0):
    verts=[]
    for z,rx,ry in rings:
        for j in range(n):
            a=j*math.tau/n;p=1+pleat*math.cos(a*12)
            verts.append((rx*math.cos(a)*p,ry*math.sin(a)*p,z))
    faces=[tuple(range(n-1,-1,-1)),tuple(range((len(rings)-1)*n,len(rings)*n))]
    faces += [(k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for k in range(len(rings)-1) for j in range(n)]
    return mesh(name,verts,faces,mat,bn)

# Stone is a genuine beveled disc, not an image card; it never enters the rig.
base=rod('Cream limestone plinth',(0,0,.025),(0,0,.14),.665,'stone',r2=.65,verts=96)
bevel=base.modifiers.new('Soft worn stone edge','BEVEL');bevel.width=.025;bevel.segments=3
ringbody('Linen pleated skirt',[(.91,.31,.20),(1.06,.25,.17),(1.25,.19,.145)],'linen','pelvis',n=72,pleat=.06)
ringbody('Bronze cuirass',[(1.20,.19,.145),(1.30,.215,.15),(1.46,.25,.17),(1.62,.28,.17),(1.72,.22,.13)],'bronze','torso')
# Modelled breast and abdominal relief catches the light as the torso turns.
for x in (-.12,.12):
    ell('Hammered breastplate',(x,-.135,1.59),(.135,.065,.10),'bronze','torso')
for z in (1.34,1.41,1.48):
    for x in (-.07,.07):ell('Cuirass abdominal lobe',(x,-.148,z),(.075,.025,.04),'bronze','torso')
ringbody('Leather belt',[(1.22,.209,.166),(1.28,.21,.164)],'leather','pelvis')
ell('Belt clasp',(0,-.174,1.25),(.055,.02,.045),'gold','pelvis')
for j in range(12):
    a=math.tau*j/12
    x,y=.245*math.cos(a),.19*math.sin(a)
    o=rod('Leather pteruges',(x*.83,y*.85,1.25),(x,y,1.01),.031,'leather','pelvis',r2=.039,verts=6)
    ell('Pteruges rivet',(x*.93,y*.93,1.16),(.012,.012,.012),'gold','pelvis')
for side in ('r','l'):
    for part,r in [('thigh',.11),('shin',.075),('upper',.073),('fore',.058)]:
        a,b,_=rest[part+'_'+side]
        rod(part+' '+side,a,b,r,'skin',part+'_'+side,r2=r*.75)
        ell('Joint '+part+' '+side,a,(r,r,r),'skin',part+'_'+side)
    a,b,_=rest['shin_'+side]
    rod('Bronze greave '+side,a+V((0,-.01,-.025)),b+V((0,-.01,.07)),.083,'bronze','shin_'+side,r2=.055)
    ell('Knee guard '+side,a+V((0,-.045,0)),(.087,.057,.09),'bronze','shin_'+side)
    a,b,_=rest['foot_'+side]
    ell('Foot '+side,(a.x,-.075,.205),(.072,.15,.05),'skin','foot_'+side)
    ell('Sandal sole '+side,(a.x,-.075,.174),(.078,.16,.023),'leather','foot_'+side)
    for y in (-.14,-.075,0):rod('Sandal strap',(a.x-.067,y,.218),(a.x+.067,y,.218),.014,'leather','foot_'+side)
    a,b,_=rest['hand_'+side]
    ell('Closed grip '+side,a,(.066,.057,.073),'skin','hand_'+side)
    for z in (-.035,-.012,.012,.035):
        rod('Grip fingers '+side,a+V((-.04,-.045,z)),a+V((.04,-.045,z)),.011,'skin','hand_'+side)
    ell('Linen shoulder '+side,rest['upper_'+side][0],(.095,.10,.08),'linen','upper_'+side)
# Neck, dark face cavity, bronze helmet dome and separate cheek/nasal guards.
ell('Neck',(0,0,1.76),(.079,.075,.12),'skin','head')
ell('Face under helmet',(0,-.015,1.91),(.105,.095,.15),'skin','head')
ell('Helmet cap',(0,0,2.005),(.125,.12,.145),'bronze','head')
# Eye openings are spaces between surfaces, with a recessed dark face below.
ell('Eye shadow',(0,-.107,1.966),(.117,.02,.041),'dark','head')
for x in (-.082,.082):
    mesh('Corinthian cheek guard',[(x-.037,-.111,1.96),(x+.037,-.111,1.96),(x+.029,-.115,1.81),(x-.025,-.105,1.84),
                                  (x-.037,-.08,1.96),(x+.037,-.08,1.96),(x+.029,-.083,1.81),(x-.025,-.08,1.84)],
         [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'bronze','head')
    rod('Helmet brow',(x-.05,-.115,2.005),(x+.05,-.115,2.005),.02,'gold','head')
rod('Nasal guard',(0,-.14,2.01),(0,-.148,1.88),.022,'bronze','head',r2=.012,verts=6)
# Sagittal red horsehair crest, curved along the helmet instead of a flat billboard.
verts=[]
for j in range(25):
    a=-.9+j*2.35/24
    for x,r in [(-.036,.168),(.036,.168),(-.031,.265),(.031,.265)]:
        verts.append((x,math.sin(a)*r,2.01+math.cos(a)*r))
faces=[]
for j in range(24):
    k=j*4;faces += [(k,k+4,k+6,k+2),(k+1,k+3,k+7,k+5),(k+2,k+6,k+7,k+3),(k,k+1,k+5,k+4)]
faces += [(0,2,3,1),(96,97,99,98)]
mesh('Red horsehair crest',verts,faces,'red','head')
for j in range(25):
    a=-.9+j*2.35/24
    rod('Crest brush ridge',(0,math.sin(a)*.178,2.01+math.cos(a)*.178),(0,math.sin(a)*.262,2.01+math.cos(a)*.262),.005,'red_dark','head',verts=5)
# Cloth hangs behind the torso with a scalloped hem and a real thickness.
verts=[]
for k in range(9):
    t=k/8
    for j in range(17):
        u=j/16*2-1
        verts.append((u*(.23+.12*t),.15+.10*t+.04*math.cos(u*pi*4)*(t+.15),1.73-.89*t+.035*math.cos(u*pi*4)*t))
faces=[(k*17+j,k*17+j+1,(k+1)*17+j+1,(k+1)*17+j) for k in range(8) for j in range(16)]
cloak=mesh('Red wool cloak',verts,faces,'red','cloak');sol=cloak.modifiers.new('Wool thickness','SOLIDIFY');sol.thickness=.012
for z,rx,ry in [(1.72,.23,.155),(1.69,.22,.17)]:
    pts=[(rx*math.cos(a),ry*math.sin(a),z+.018*math.cos(a*3)) for a in [j*math.tau/32 for j in range(33)]]
    for a,b in zip(pts,pts[1:]):rod('Cloak collar folds',a,b,.025,'red','torso')
ell('Cloak clasp',(-.13,-.145,1.71),(.023,.015,.023),'gold','torso')
# Domed aspis with convex depth, continuous back, rim and raised sun boss.
verts=[(.43,-.49,1.43)]
for k in range(1,10):
    r=.44*k/9
    for j in range(64):
        a=j*math.tau/64
        verts.append((.43+r*math.cos(a),-.39-.10*math.sqrt(max(0,1-(r/.45)**2)),1.43+r*math.sin(a)))
faces=[(0,1+j,1+(j+1)%64) for j in range(64)]
for k in range(8):
    faces += [(1+k*64+j,1+k*64+(j+1)%64,1+(k+1)*64+(j+1)%64,1+(k+1)*64+j) for j in range(64)]
shield=mesh('Painted sunburst aspis',verts,faces,'shield','shield',uv=True)
sol=shield.modifiers.new('Aspis thickness','SOLIDIFY');sol.thickness=.035
for j in range(64):
    a,b=j*math.tau/64,(j+1)*math.tau/64
    rod('Rolled shield rim',(.43+.44*math.cos(a),-.412,1.43+.44*math.sin(a)),(.43+.44*math.cos(b),-.412,1.43+.44*math.sin(b)),.016,'gold','shield')
ell('Aspis sun boss',(.43,-.50,1.43),(.072,.037,.072),'bronze','shield')
# Full length spear is attached at the hand; leaf head has a modelled ridge.
rod('Ash spear shaft',(-.50,-.24,.20),(-.50,-.24,2.83),.013,'wood','spear')
rod('Bronze spear ferrule',(-.50,-.24,2.77),(-.50,-.24,2.85),.022,'bronze','spear')
mesh('Leaf spearhead',[(-.50,-.24,3.08),(-.55,-.24,2.87),(-.50,-.265,2.81),(-.45,-.24,2.87),(-.50,-.215,2.81)],
     [(0,1,2),(0,2,3),(0,3,4),(0,4,1),(1,4,3,2)],'bronze','spear')
rod('Spear butt spike',(-.50,-.24,.18),(-.50,-.24,.26),.004,'bronze','spear',r2=.02)

# Paint projected onto the rest mesh stays attached when the bone turns. The
# UVs are saved in the .blend; no screen-space texture changes during animation.
for ob in list(scene.objects):
    if ob.type!='MESH' or not ob.vertex_groups:continue
    bn=ob.vertex_groups[0].name
    tex=None
    if ob.name.startswith(('Bronze cuirass','Hammered breastplate','Cuirass abdominal')):
        tex='cuirass';xmin,xmax,zmin,zmax=-.28,.28,1.20,1.73
    elif ob.name.startswith(('Helmet cap','Corinthian cheek','Nasal guard')):
        tex='helmet';xmin,xmax,zmin,zmax=-.15,.15,1.81,2.16
    elif ob.name.startswith(('Bronze greave','Knee guard')):
        tex='greave';cx=rest[bn][0].x;xmin,xmax,zmin,zmax=cx-.10,cx+.10,.23,.70
    elif ob.name.startswith('Linen pleated skirt'):
        tex='cloth';xmin,xmax,zmin,zmax=-.32,.32,.91,1.25
    if tex:
        ob.data.materials.clear();ob.data.materials.append(M[tex])
        uv=ob.data.uv_layers.new()
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                co=ob.data.vertices[ob.data.loops[li].vertex_index].co
                uv.data[li].uv=(max(.01,min(.99,(co.x-xmin)/(xmax-xmin))),max(.01,min(.99,(co.z-zmin)/(zmax-zmin))))
    if bn=='spear':
        for v in ob.data.vertices:
            if v.co.z>1.55:v.co.z=1.55+(v.co.z-1.55)*.97

# The source aspis is oblique to the chest, not square to the viewer.
shield_pivot=rest['shield'][0]
shield_twist=Matrix.Rotation(.43,3,'Z')
for ob in list(scene.objects):
    if ob.type=='MESH' and ob.vertex_groups.get('shield'):
        for v in ob.data.vertices:v.co=shield_pivot+shield_twist @ ((v.co-shield_pivot)*.90)
# Preserve the source's tall adult proportions and base framing.
figure=bpy.data.objects.new('Figure proportions',None);scene.collection.objects.link(figure)
rig.parent=figure
for ob in list(scene.objects):
    if ob.type=='MESH' and len(ob.vertex_groups):ob.parent=figure
figure.scale.z=1.02;figure.location.z=-.14*.02

# Camera/light: matching the source base width and three-quarter view.
bpy.ops.object.camera_add(location=(-4,-8,5.0))
camera=bpy.context.object;target=V((0,0,1.42));camera.location=target+V((-4,-8,2.6))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=3.28;scene.camera=camera
for name,loc,power,size in [('Large softbox',(-3,-4,7),650,3),('Soft bounce',(4,-1,4),65,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(V((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()


def ik(a,b,l1,l2,bend):
    delta=b-a;d=min(delta.length,l1+l2-.001);unit=delta.normalized()
    along=(l1*l1-l2*l2+d*d)/(2*d)
    pole=V(bend);pole=(pole-unit*pole.dot(unit)).normalized()
    return a+unit*along+pole*math.sqrt(max(.0001,l1*l1-along*along))


def pose(clip,i,n):
    phase=i/n*math.tau
    shift=V((.025*math.sin(phase),0,-.015));lean=0;turn=.025*math.sin(phase)
    feet={s:rest['foot_'+s][0].copy() for s in ('r','l')}
    lunge=0;recoil=0;fall=0
    if clip=='idle': shift.z=-.015+.023*(1+math.sin(phase));lean=.018*math.sin(phase)
    if clip=='move':
        shift=V((.025*math.sin(phase),0,.025*(1+math.cos(phase*2))))
        turn=.10*math.sin(phase)
        for s,off in [('r',0),('l',pi)]:
            p=phase+off;feet[s].y=.20*math.cos(p);feet[s].z+=.13*max(0,math.sin(p))
    if clip=='attack':
        lunge=[0,-.08,-.10,.25,.8,1,1,.6,.2,0][i]
        shift=V((0,-.23*lunge,-.13*max(0,lunge)));lean=.27*lunge;turn=-.18*lunge
        feet['l'].y-=.29*max(0,lunge);feet['r'].y+=.13*max(0,lunge)
    if clip=='hit':
        recoil=[0,1,.55,0][i];shift=V((-.035*recoil,.10*recoil,-.055*recoil));lean=-.32*recoil;turn=.15*recoil
    if clip=='death':
        fall=[0,.06,.20,.4,.63,.82,.95,1,1,1][i]
        shift=V((-.15*fall,-.30*fall,-.68*fall));lean=-1.64*fall;turn=-.65*fall
        feet['r']+=V((-.08*fall,-.12*fall,0));feet['l']+=V((.04*fall,-.26*fall,0))
    center=V((0,0,1.12))+shift
    rot=Matrix.Rotation(lean,3,'X') @ Matrix.Rotation(turn,3,'Z')
    def body(p):return center+rot @ (V(p)-V((0,0,1.12)))
    targets={}
    targets['pelvis']=(center,center+rot @ V((0,0,.22)))
    targets['torso']=(body(rest['torso'][0]),body(rest['torso'][1]))
    head_start=body(rest['head'][0])
    head_end=body(rest['head'][1])+V((0,.08*recoil-.12*fall,-.025*recoil+.16*fall))
    targets['head']=(head_start,head_start+(head_end-head_start).normalized()*.33)
    for s in ('r','l'):
        hip=body(rest['thigh_'+s][0]);ankle=feet[s]
        knee=ik(hip,ankle,(rest['thigh_'+s][1]-rest['thigh_'+s][0]).length,(rest['shin_'+s][1]-rest['shin_'+s][0]).length,((-.8 if s=='r' else .8)*fall,-1+.7*fall,.1+1.4*fall))
        targets['thigh_'+s]=(hip,knee);targets['shin_'+s]=(knee,ankle)
        targets['foot_'+s]=(ankle,ankle+V((0,-.20,-.05)))
        shoulder=body(rest['upper_'+s][0]);hand=body(rest['hand_'+s][0])
        if s=='r':hand+=V((0,-.23*max(0,lunge),.01*lunge))
        else:hand+=V((-.12-.06*max(0,lunge),.08+.05*max(0,lunge),-.14))
        if clip=='move':hand+=V((0,.07*math.sin(phase+(pi if s=='l' else 0)),.025*math.sin(phase)))
        if clip=='death':
            settled=V((.34,-.12,.30)) if s=='l' else V((-.40,-.12,.23))
            hand=hand.lerp(settled,fall)
        reach=(rest['upper_'+s][1]-rest['upper_'+s][0]).length+(rest['fore_'+s][1]-rest['fore_'+s][0]).length-.002
        if (hand-shoulder).length>reach:hand=shoulder+(hand-shoulder).normalized()*reach
        elbow=ik(shoulder,hand,(rest['upper_'+s][1]-rest['upper_'+s][0]).length,(rest['fore_'+s][1]-rest['fore_'+s][0]).length,(-1 if s=='r' else 1,0,-.5+2*fall))
        targets['upper_'+s]=(shoulder,elbow);targets['fore_'+s]=(elbow,hand)
        targets['hand_'+s]=(hand,hand+rot @ V((0,0,.10)))
    hand=targets['hand_r'][0]
    spear_angle=1.45*max(0,lunge)-pi/2*math.sqrt(fall)
    if fall>0:
        # The shaft's lower 1.43 units must clear the stone as the hand lowers.
        spear_angle=min(spear_angle,-math.acos(max(0,min(1,(hand.z-.21)/1.43))))
    sr=Matrix.Rotation(.82*max(0,lunge),3,'Z') @ Matrix.Rotation(spear_angle,3,'X')
    targets['spear']=(hand,hand+sr @ V((0,0,.50)))
    hand=targets['hand_l'][0]
    targets['shield']=(hand+rot @ V((0,-.04,-.01)),hand+rot @ V((0,-.54,-.01)))
    targets['cloak']=(body(rest['cloak'][0]),body(rest['cloak'][1])+V((0,.06*math.sin(phase) if clip=='move' else 0,0)))
    for name in rest:
        a,b=targets[name]
        pb=rig.pose.bones[name]
        # Match each rest bone's roll: swing from its original world direction.
        direction=(b-a).normalized();original=(rest[name][1]-rest[name][0]).normalized()
        rotation=original.rotation_difference(direction).to_matrix().to_4x4()
        local_scale=Matrix.Diagonal((1,(b-a).length/(rest[name][1]-rest[name][0]).length,1,1))
        pb.matrix=Matrix.Translation(a) @ rotation @ Matrix.Translation(-rest[name][0]) @ arm.bones[name].matrix_local @ local_scale
        bpy.context.view_layer.update()
        pb.keyframe_insert('location');pb.keyframe_insert('rotation_quaternion');pb.keyframe_insert('scale')

# Default quaternion mode is set explicitly before baking all 40 poses.
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
frame=1
schedule=[]
for clip,(n,fps,loop) in CLIPS.items():
    scene.timeline_markers.new(clip,frame=frame)
    for i in range(n):
        scene.frame_set(frame);pose(clip,i,n);schedule.append((frame,clip,i));frame+=1
scene.frame_start=1;scene.frame_end=40
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'spearman-3d.blend'))
if MODE!='--model-only':
    for frame,clip,i in schedule:
        if MODE=='--preview' and (clip,i) not in [('idle',0),('idle',2),('move',2),('move',6),('attack',5),('hit',1),('death',4),('death',9)]:continue
        scene.frame_set(frame)
        folder=MASTER/('preview' if MODE=='--preview' else 'frames')/clip;folder.mkdir(parents=True,exist_ok=True)
        scene.render.filepath=str(folder/f'{i:02}.png')
        bpy.ops.render.render(write_still=True)
(MASTER/'render.json').write_text(json.dumps({'engine':ENGINE,'samples':scene.cycles.samples if ENGINE=='CYCLES' else None,'mode':MODE,'baked_frames':len(schedule),'rendered_frames':0 if MODE=='--model-only' else 8 if MODE=='--preview' else 40},indent=2)+'\n')
