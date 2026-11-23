"""Register the articulated mount before freezing pigment, preserving camera depth.

Source actions remain immutable. Store the fitted/native local rest transforms so
animate.py transports source motion into this rest pose instead of stretching a
fixed camera-space leg sculpture through an unrelated skeleton.
"""
sc.frame_set(sc['rest_frame']);bpy.context.view_layer.update()
source_rest={p.name:p.matrix_basis.copy() for p in hrig.pose.bones}
original={p.name:p.matrix.copy() for p in hrig.pose.bones}
rider_world=rig.matrix_world.copy()
view_rotation=sc.camera.matrix_world.to_quaternion()
right=view_rotation @ Vector((1,0,0));up=view_rotation @ Vector((0,1,0))
def pixel_target(x,y,w):
 q=world_to_camera_view(sc,sc.camera,w)
 return w+sc.camera.data.ortho_scale*(right*(x/256-q.x)+up*(1-y/256-q.y))
# Anatomical joint landmarks, in the token's exact 256px camera. Hidden-side
# joints have a small offset, keeping four separate full-depth limbs.
landmarks={
 'Back':(92,140),'Torso':(115,143),'Torso2':(142,145),'Torso3':(174,141),
 'Neck1':(184,129),'Neck2':(192,118),'Neck3':(205,109),'Head':(208,127),
 'FrontShoulder.R':(179,148),'FrontUpperLeg.R':(185,150),'FrontLowerLeg.R':(211,177),
 'IKFrontLeg.R':(233,193),'FF.R':(240,197),
 'FrontShoulder.L':(176,143),'FrontUpperLeg.L':(181,145),'FrontLowerLeg.L':(204,166),
 'IKFrontLeg.L':(221,185),'FF.L':(229,189),
 'BackShoulder.R':(89,143),'BackLeg.R':(87,145),'BackUpperLeg.R':(76,166),'BackLowerLeg.R':(60,178),
 'IKBackLeg.R':(44,191),'FFB.R':(40,198),
 'BackShoulder.L':(95,142),'BackLeg.L':(95,145),'BackUpperLeg.L':(83,163),'BackLowerLeg.L':(59,169),
 'IKBackLeg.L':(47,178),'FFB.L':(39,183),
 'Tail1':(88,132),'Tail2':(77,130),'Tail3':(66,133),'Tail4':(53,137),'Tail5':(40,140),'Tail6':(29,143),'Tail7':(19,146)}
endpoints={'Back':'Torso','Torso':'Torso2','Torso2':'Torso3','Torso3':'Neck1','Neck1':'Neck2','Neck2':'Neck3','Neck3':'Head',
 'FrontShoulder.R':'FrontUpperLeg.R','FrontUpperLeg.R':'FrontLowerLeg.R','FrontLowerLeg.R':'IKFrontLeg.R',
 'FrontShoulder.L':'FrontUpperLeg.L','FrontUpperLeg.L':'FrontLowerLeg.L','FrontLowerLeg.L':'IKFrontLeg.L',
 'BackShoulder.R':'BackLeg.R','BackLeg.R':'BackUpperLeg.R','BackUpperLeg.R':'BackLowerLeg.R','BackLowerLeg.R':'IKBackLeg.R',
 'BackShoulder.L':'BackLeg.L','BackLeg.L':'BackUpperLeg.L','BackUpperLeg.L':'BackLowerLeg.L','BackLowerLeg.L':'IKBackLeg.L',
 **{f'Tail{i}':f'Tail{i+1}' for i in range(1,7)}}
inv=hrig.matrix_world.inverted()
targets={n:inv @ pixel_target(x,y,hrig.matrix_world @ original[n].translation) for n,(x,y) in landmarks.items()}
# Work parent-first. Matrix assignment derives a local pose relative to the
# already-fitted parent. No tiny scale and no independent foot-axis patch.
for p in hrig.pose.bones:
 if p.name not in targets:continue
 mat=original[p.name].copy();a=mat.translation.copy();b=targets[p.name]
 if p.name in endpoints:
  child=endpoints[p.name];v=original[child].translation-a;w=targets[child]-b
  mat=v.rotation_difference(w).to_matrix().to_4x4() @ mat
 mat.translation=b;p.matrix=mat;bpy.context.view_layer.update()
rig.matrix_world=rider_world;bpy.context.view_layer.update()
fitted={p.name:p.matrix_basis.copy() for p in hrig.pose.bones}
sc['horse_source_rest']=json.dumps({n:[list(r) for r in m] for n,m in source_rest.items()})
sc['horse_fitted_rest']=json.dumps({n:[list(r) for r in m] for n,m in fitted.items()})
# A dedicated keyed rest prevents frame_set during preview from reloading the
# unregistered source gallop; original actions remain available to animation.
hrig.animation_data.action=None
for p in hrig.pose.bones:
 p.matrix_basis=fitted[p.name];p.rotation_mode='QUATERNION'
 for prop in ('location','rotation_quaternion','scale'):p.keyframe_insert(prop,frame=sc['rest_frame'])
hrig.animation_data.action.name='Keshig registered rest'
sc['registered_pose_method']='Anatomical joint fit with retained camera depth and native local motion deltas'
