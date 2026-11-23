"""MPFB Medjay with a folded linen kilt, hide shield, feather and long spear."""
import sys, os, math, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from math import sin,cos,pi
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.30,muscle=.88,weight=.43,height=.55,proportions=.65);macro['race']={'african':.65,'caucasian':.30,'asian':.05}
body=HumanService.create_human(macro_detail_dict=macro);body.name='Medjay MPFB anatomical body'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();factor=1.80/(hi-lo);body.scale=(factor,factor,factor)
bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='Medjay MPFB game_engine';rig.location=(.025,.12,.105)
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='Medjay anatomical eyes'
skin=material('Painted ochre skin',(.36,.155,.060),fill='skin');linen=material('Woven ivory linen',(.77,.64,.44),rough=.87,fill='linen');hide=material('Oxhide shield backing',(.27,.105,.035),rough=.82,fill='hide');wood=material('Ash shaft',(.42,.22,.065),fill='wood');bronze=material('Bright bronze blade',(.65,.36,.095),metal=1,rough=.28);edge=material('Burnished edge',(.86,.56,.19),metal=1,rough=.22);dark=material('Dark hair and incisions',(.028,.014,.008),rough=.88);stone=material('Warm cream stone E9CFA0',(.98,.60,.30),rough=.86)
stone.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(.90,.55,.24,1);stone.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.28
body.data.materials.clear();body.data.materials.append(skin)
for p in body.data.polygons:p.use_smooth=True
sub=body.modifiers.new('Anatomical smoothing','SUBSURF');sub.levels=1;sub.render_levels=1
# Slightly open legs and planted bare feet. Targets are in rig-local coordinates.
limb(rig,'thigh_r','calf_r',(-.14,-.015,.09),(-.17,-.35,.55));limb(rig,'thigh_l','calf_l',(.14,.005,.09),(.17,-.35,.55))
limb(rig,'upperarm_r','lowerarm_r',(-.435,-.12,1.34),(-.33,-.05,1.11));limb(rig,'upperarm_l','lowerarm_l',(.34,-.21,1.18),(.39,-.04,1.17))
for side in ['r','l']:
 aim(rig,'hand_'+side,(-.02,-.01,.10))
 for digit in ['index','middle','ring','pinky']:
  for k in range(1,4):
   p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.10
# Turn head toward the shield side, matching the painting's profile.
p=rig.pose.bones['head'];p.rotation_mode='XYZ';p.rotation_euler.y=-.37;p.rotation_euler.z=-.32
bpy.context.view_layer.update()
# Cloth with sculpted longitudinal pleats and a separate overlapping front flap.
vs=[];fs=[];N=96;J=14
for j in range(J+1):
 t=j/J;z=1.16-.46*t;rx=.165+.060*t;ry=.118+.055*t
 for i in range(N):
  a=2*pi*i/N;pleat=(.003+.012*t)*cos(20*a)+.003*sin(39*a);vs.append((.025+(rx+pleat)*sin(a),.12-(ry+pleat)*cos(a),z+.012*cos(3*a)*t))
for j in range(J):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
kilt=mesh('Pleated linen kilt',vs,[tuple(reversed(f)) for f in fs],linen);solid(kilt,.006);sub=kilt.modifiers.new('Soft linen folds','SUBSURF');sub.levels=1;attach(kilt,rig,'pelvis')
vs=[];fs=[]
for j in range(15):
 t=j/14
 for i in range(15):
  u=i/14;x=-.10+u*.22+.035*t;y=-.026-.048*t-.008*cos(u*7*pi);z=1.135-.43*t+.035*t*u;vs.append((x,y,z))
for j in range(14):
 for i in range(14):a=j*15+i;fs.append((a,a+1,a+16,a+15))
flap=mesh('Overlapping pleated apron',vs,[tuple(reversed(f)) for f in fs],linen);solid(flap,.006);sub=flap.modifiers.new('Fold softness','SUBSURF');sub.levels=1;attach(flap,rig,'pelvis')
for j in range(3):
 pts=[(.025+(.17+.004*cos(a*14))*sin(a),.12-(.125+.004*cos(a*14))*cos(a),1.15+.012*j) for a in [2*pi*i/96 for i in range(97)]];attach(curve('Twisted linen waist cord',pts,.008,linen),rig,'pelvis')
for x in [-.015,.012]:attach(curve('Waist knot tail',[(x,-.022,1.17),(x-.03,-.04,1.12),(x-.025,-.05,1.03)],.009,linen),rig,'pelvis')
# Raise the entire linen ensemble to the reference waist/hem landmarks.
for o in bpy.context.scene.objects:
 if o.name.startswith(('Pleated linen','Overlapping pleated','Twisted linen','Waist knot')):
  world=o.matrix_world.copy();world.translation.z+=.04;o.matrix_world=world
# Hair cap fitted directly to anatomical scalp (real surface, not primitive head).
bpy.context.view_layer.update();hc=rig.matrix_world@rig.pose.bones['head'].head; headtop=1.905
# band follows the skull; feather is a curved thin solid with a raised quill.
for j in range(3):
 pts=[(.025+.088*sin(a),.12-.094*cos(a),1.832+j*.008+.014*cos(a)) for a in [2*pi*i/96 for i in range(97)]];attach(curve('Woven headband',pts,.008,linen),rig,'head')
pts=[(-.055,.14,1.855),(-.09,.15,1.94),(-.105,.16,2.01)]
attach(curve('Feather quill',pts,.003,bronze),rig,'head')
vs=[]
for i in range(17):
 t=i/16;cx=-.055-.050*t;cz=1.855+.155*t;w=.017*sin(pi*t)**.6
 vs.extend([(cx-w,.145,cz),(cx,.137,cz+.004),(cx+w,.145,cz)])
fs=[]
for i in range(16):
 a=i*3;fs.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
feather=solid(mesh('Ostrich feather vane',vs,fs,linen),.002);attach(feather,rig,'head')
for i in range(1,16):
 t=i/16;cx=-.055-.05*t;z=1.855+.155*t;w=.017*sin(pi*t)**.6
 for sign in [-1,1]:attach(curve('Feather barb',[(cx,.134,z),(cx+sign*w,.14,z-.009)],.0012,dark),rig,'head')
# The long spear is centered on the palm and attached to the hand.
grip=rig.matrix_world@rig.pose.bones['hand_r'].head+Vector((-.006,-.010,.035));direction=Vector((-.235,0,.972))
shaft=curve('Long ash spear',[(grip-direction*1.20),(grip+direction*.43)],.011,wood);attach(shaft,rig,'hand_r')
center=grip+direction*.43;side=Vector((.972,0,.235));depth=Vector((0,.010,0));tip=center+direction*.205
verts=[center-side*.034,center+side*.034,center-depth,center+depth,tip,center-direction*.055]
blade=mesh('Faceted bronze spearhead',[tuple(v) for v in verts],[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(0,5,2),(2,5,1),(1,5,3),(3,5,0)],bronze);bevel(blade,.0008);attach(blade,rig,'hand_r')
for t in [-.04,0,.03]:attach(curve('Spear socket binding',[center+direction*t,center+direction*(t+.015)],.015,edge),rig,'hand_r')
# Tall round-topped convex hide shield: a closed 3D shell with a rolled rim.
cx=.37;bottom=.755;shoulder=1.43;rad=.158
outline=[(cx-rad,bottom),(cx+rad,bottom),(cx+rad,shoulder)]
outline += [(cx+rad*cos(a),shoulder+rad*sin(a)) for a in [pi*i/40 for i in range(1,41)]]
outline += [(cx-rad,bottom)]
vs=[(cx,-.185,1.14)]+[(x,-.12-.025*(1-((x-cx)/rad)**2),z) for x,z in outline[:-1]]
fs=[(0,1+(i+1)%(len(vs)-1),1+i) for i in range(len(vs)-1)]
shield=mesh('Convex painted oxhide shield',vs,[tuple(reversed(f)) for f in fs],hide);solid(shield,.025);bevel(shield,.005);attach(shield,rig,'lowerarm_l')
attach(curve('Shield rolled leather rim',[(x,-.136,z) for x,z in outline],.008,wood),rig,'lowerarm_l')
for i,(x,z) in enumerate(outline[:-1]):
 if i%3==0:attach(curve('Shield hand stitching',[(x-.003,-.145,z-.003),(x+.003,-.145,z+.003)],.0016,linen),rig,'lowerarm_l')
shield_objects=[o for o in bpy.context.scene.objects if o.name.startswith(('Convex painted oxhide','Shield rolled','Shield hand'))]
shield_control=bpy.data.objects.new('Shield control',None);bpy.context.collection.objects.link(shield_control);shield_control.location=(cx,-.12,1.17);attach(shield_control,rig,'lowerarm_l')
for o in shield_objects:
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=shield_control;o.parent_type='OBJECT';o.matrix_world=world
# One hand-relative rigid spear control permits a physical release during death.
spear_objects=[o for o in bpy.context.scene.objects if o.name.startswith(('Long ash spear','Faceted bronze spearhead','Spear socket binding'))]
control=bpy.data.objects.new('Spear control',None);bpy.context.collection.objects.link(control);control.location=grip;attach(control,rig,'hand_r')
for o in spear_objects:
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=control;o.parent_type='OBJECT';o.matrix_world=world
# Stationary base: one low disc, never parented to the rig.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.495,depth=.085,location=(.025,.025,.0425));base=bpy.context.object;base.name='Stationary warm cream stone';base.data.materials.append(stone);bevel(base,.012)
for p in base.data.polygons:p.use_smooth=True
# Product shot; token camera has no DOF, so the full silhouette is sharp.
sc=bpy.context.scene;sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.43,.38,.30,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.10
bpy.ops.object.camera_add(location=(0,-8,3.30));sc.camera=bpy.context.object;sc.camera.name='Painting camera';target=Vector((-.018,0,.97));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.30;sc.camera.data.dof.use_dof=False
for name,loc,power,size,color in [('Warm upper left',(-3,-4,5),600,2,(1,.91,.76)),('Soft fill',(4,-3,3),130,3,(.9,.94,1)),('Cool rim',(2,3,4),180,2,(.72,.84,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
from coverage import covered_indices,apply_coverage
apply_coverage(body,covered_indices(body))
sc.render.fps=24;configure();rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});rig['neutral_location']=list(rig.location)
sc['source']='MPFB 2.0.18 CC0 anatomical body and weights; original Medjay equipment';sc['cream_target']='#E9CFA0'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'medjay-plain.blend'))
(M/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'bone_heads':{p.name:list(p.head) for p in rig.pose.bones if p.name in ['head','pelvis','foot_l','foot_r','hand_l','hand_r','spine_03']}},indent=2))
log('Built MPFB Medjay anatomy, folded linen, convex hide shield, bronze spear, feather, camera and cream disc; saved plain master.')
