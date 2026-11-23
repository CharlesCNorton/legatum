"""Register closed, full-depth mechanical meshes to measured painting landmarks.

These are vertex edits in the camera's horizontal/vertical axes, preserving depth,
not image warps or cards. Run once after build, before UV baking and projection.
"""
import json
import os
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runninggear import route

M = Path(os.environ['ANIM_ROOT']) / 'masters/tank'
bpy.ops.wm.open_mainfile(filepath=str(M / 'tank-built.blend'))
sc = bpy.context.scene
assert not sc.get('registered'), 'Rebuild before repeating geometry registration'
bpy.context.view_layer.update()
camera = sc.camera
right = camera.rotation_euler.to_matrix() @ Vector((1, 0, 0))
up = camera.rotation_euler.to_matrix() @ Vector((0, 1, 0))
units = camera.data.ortho_scale / 256
records = []


def fit(label, prefixes, center, scale=(1, 1), offset=(0, 0)):
    objects = [o for o in bpy.data.objects
               if o.type == 'MESH' and o.name.startswith(prefixes)]
    assert objects, label
    before, after = [], []
    for obj in objects:
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            p = world_to_camera_view(sc, camera, world)
            x, y = 256 * p.x, 256 * (1 - p.y)
            dx = (x - center[0]) * (scale[0] - 1) + offset[0]
            dy = (y - center[1]) * (scale[1] - 1) + offset[1]
            vertex.co = inverse @ (world + units * (right * dx - up * dy))
            before.append((x, y))
            after.append((x + dx, y + dy))
        obj.data.update()
    def bounds(points):
        return [round(v, 3) for v in (min(p[0] for p in points), min(p[1] for p in points),
                                      max(p[0] for p in points), max(p[1] for p in points))]
    records.append(dict(part=label, meshes=len(objects), before=bounds(before),
                        after=bounds(after), scale=scale, offset=offset))


fit('Cast turret and seam', ('Rounded cast turret', 'Turret casting seam', 'Turret lifting eye'),
    (171.5, 56), (1.14, .79), (0, 1))
fit('Low commander cupola', ('Closed commander', 'Cupola', 'Closed hatch seam', 'Hatch handle'),
    (126, 59), (.88, .80), (-12, -3))
fit('Gun and mantlet', ('Rounded mantlet', 'Mantlet sleeve', 'Short 75', 'Worn muzzle', 'Dark muzzle'),
    (165, 85), (1, 1), (-3, -10))
fit('Mantlet casting width', ('Rounded mantlet',), (163, 79), (1.12, .90))
fit('Rear stowage', ('Rear stowage box', 'Stowage box lid', 'Stowage latch'),
    (64, 113), (1, .80), (-12, 4))
fit('Short jerricans', ('Rear deck jerrican', 'Jerrican'),
    (66, 91), (1, .64), (0, 1))
# Extend the bevelled rear armour shoulder under the newly registered stowage.
# The previous box relocation overhung its supporting hull.
hull = bpy.data.objects['Sloped upper hull']
inverse = hull.matrix_world.inverted()
for vertex in hull.data.vertices:
    influence = max(0, min(1, (-vertex.co.x - .95) / .40))
    vertex.co = inverse @ (hull.matrix_world @ vertex.co - right * units * 12 * influence)
hull.data.update()
records.append(dict(part='Rear shoulder support', extension_px=12, meshes=1))
# A restrained smoking wreck reads better than the old solid orange spikes.
for obj in list(bpy.data.objects):
    if obj.get('effect') == 'fire' or obj.name.startswith(('Wheel radial spoke','Wheel recessed aperture')):
        bpy.data.objects.remove(obj, do_unlink=True)
smoke = bpy.data.materials['Smoke • noise faded 3D shell']
for node in smoke.node_tree.nodes:
    if node.type == 'BSDF_DIFFUSE':
        node.inputs['Color'].default_value = (.24,.22,.19,1)
    if node.type == 'MATH' and node.operation == 'MULTIPLY' and not node.inputs[1].is_linked:
        node.inputs[1].default_value = .14
# Register the rotating wheel faces to their own painted centres. Projecting a
# neighbouring bogie onto a miscentred wheel produces tearing when it turns.
wheel_targets = [(43,156), (64,159), (85,162), (107,166), (129,169), (149,172)]
for i, target in enumerate(wheel_targets):
    near = bpy.data.objects[f'Road wheel pivot -1 {i}']
    face = near.matrix_world @ Vector((0,-.16,0))
    p = world_to_camera_view(sc, camera, face)
    dx = (target[0] - p.x*256) * units / right.x
    dz = (-(target[1] - (1-p.y)*256)*units - up.x*dx) / up.z
    for side in (-1,1):
        wheel = bpy.data.objects[f'Road wheel pivot {side} {i}']
        wheel.location += Vector((dx,0,dz))
        wheel.scale = (.88,1,.88)
        wheel['rolling_radius'] = .28*.88
        wheel['track_side'] = side
    records.append(dict(part=f'Road wheel pair {i}', target_face_px=target,
                        radius_scale=.88))
for obj in bpy.data.objects:
    if obj.type=='MESH' and obj.name.startswith(('VVSS bogie','Bogie suspension','Vertical spring','Spring cover','Return roller')):
        i=min(range(3),key=lambda i:abs(obj.location.x-[-.83,.01,.85][i]))
        dx=[-8,-3,3][i]*units/right.x
        obj.location+=Vector((dx,0,-up.x*dx/up.z))

# Fit the whole running gear, preserving real depth and a planted lower run.
# Full source targets rather than moving a painted sprocket around a wrong axle.
routes={};endsets={}
for side in (-1,1):
    ends=[]
    targets=[(24,139),(174,154)] if side==-1 else [(82,125),(228,145)]
    for label,target,radius in zip(('-1.39','1.39'),targets,(.205,.260)):
        wheel=bpy.data.objects[f'Sprocket pivot {side} {label}']
        face=wheel.matrix_world @ Vector((0,side*.16,0))
        p=world_to_camera_view(sc,camera,face)
        dx=(target[0]-p.x*256)*units/right.x
        dz=(-(target[1]-(1-p.y)*256)*units-up.x*dx)/up.z
        wheel.location+=Vector((dx,0,dz));wheel.scale=(radius/.32,1,radius/.32)
        wheel['rolling_radius']=radius;wheel['track_side']=side
        ends.append((wheel.location.x,wheel.location.z,radius+.045))
        records.append(dict(part=f'End sprocket {side} {label}',target_face_px=target,radius=radius))
    circles=[ends[0],(-1.05,.64,.25),(1.10,.64,.25),ends[1]]
    routes[str(side)]=circles;endsets[side]=ends
sc['track_circles']=json.dumps(routes)
for side in (-1,1):
    length,trackpoint=route(routes[str(side)])
    if side==-1:sc['track_length']=length
    for obj in bpy.data.objects:
        if 'track_phase' in obj and obj['track_side']==side:
            x,z,a=trackpoint(obj['track_phase'])
            obj.location=(x,side*.99,z);obj.rotation_euler.y=a
# Full-depth fenders clear each independently registered suspension side.
for obj in bpy.data.objects:
    if obj.type!='MESH' or not obj.name.startswith(('Raised track fender','Fender folded edge','Front mudguard')):continue
    inverse=obj.matrix_world.inverted();root=bpy.data.objects['Vehicle suspension root']
    ends=endsets[-1 if obj.location.y<0 else 1]
    for vertex in obj.data.vertices:
        world=obj.matrix_world@vertex.co
        local=root.matrix_world.inverted()@world
        f=max(0,min(1,(local.x+1.8)/3.6))
        top=ends[0][1]+ends[0][2]+f*((ends[1][1]+ends[1][2])-(ends[0][1]+ends[0][2]))
        local.z+=top-1.19
        vertex.co=inverse@(root.matrix_world@local)
    obj.data.update()
# The transmission casting must meet the newly registered drive axle. Extend
# its real forward volume and adjoining glacis rather than leaving a hollow
# track loop beyond the short old nose.
for obj in bpy.data.objects:
    if obj.type!='MESH' or not obj.name.startswith(('Rounded transmission nose','Transmission casting seam','Sloped upper hull')):continue
    inverse=obj.matrix_world.inverted();root=bpy.data.objects['Vehicle suspension root']
    for vertex in obj.data.vertices:
        local=root.matrix_world.inverted()@(obj.matrix_world@vertex.co)
        weight=max(0,min(1,(local.x-.55)/.9))
        local.x+=.20*weight
        local.z+=.04*weight
        vertex.co=inverse@(root.matrix_world@local)
    obj.data.update()
# Broaden the sloped rear shoulder below the stowage, retaining its depth.
hull=bpy.data.objects['Sloped upper hull'];inverse=hull.matrix_world.inverted()
for vertex in hull.data.vertices:
    world=hull.matrix_world@vertex.co;p=world_to_camera_view(sc,camera,world)
    x,y=p.x*256,(1-p.y)*256
    w=max(0,min(1,(60-x)/25))*max(0,min(1,(y-95)/20))
    vertex.co=inverse@(world-right*units*8*w)
hull.data.update()
# Camera-only source pigment retains the painting's display colour. Physical
# lights remain responsible for shadows, bevel response and unseen surfaces.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for obj in bpy.data.objects:
    if obj.type=='LIGHT':obj.data.energy*=.55

for name in ('Flame amber mantle','Flame warm core'):
    bpy.data.materials[name].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value*=.35

sc['registered'] = True
bpy.ops.wm.save_as_mainfile(filepath=str(M / 'tank-plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(M / 'tank.blend'))
(M / 'registration.json').write_text(json.dumps(dict(
    method='Full-depth mesh registration in orthographic camera axes; depth unchanged',
    camera=list(camera.location), ortho_scale=camera.data.ortho_scale, parts=records), indent=2))
print('REGISTERED', len(records), 'part groups; closed 3D geometry retained')
