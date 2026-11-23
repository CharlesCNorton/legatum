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
construction_camera = camera.copy()
construction_camera.data = camera.data.copy()
# The visible lower rim of the reference disc fits a 227 x 42 px ellipse.
# Calibrate elevation from that round horizontal base, before fitting the kit.
# This keeps the base circular in world space instead of flattening its mesh.
target = Vector((0, 0, 1.14))
camera.location = (5.6, -10, 3.32)
camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
right = camera.rotation_euler.to_matrix() @ Vector((1, 0, 0))
up = camera.rotation_euler.to_matrix() @ Vector((0, 1, 0))
units = camera.data.ortho_scale / 256
records = []
# Preserve the already fitted armour/equipment landmarks while changing camera
# elevation. Running gear is solved below against its axles/contact circles;
# the round stone remains untouched so it determines the physical viewpoint.
for obj in bpy.data.objects:
    if obj.type != 'MESH' or 'effect' in obj or obj.name.startswith('Stationary'):
        continue
    if obj.parent and ('wheel' in obj.parent or 'track_phase' in obj.parent):
        continue
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        previous = world_to_camera_view(sc, construction_camera, world)
        current = world_to_camera_view(sc, camera, world)
        vertex.co = inverse @ (world + up * (previous.y-current.y)*camera.data.ortho_scale)
    obj.data.update()
bpy.data.objects.remove(construction_camera)


def fit(label, prefixes, center, scale=(1, 1), offset=(0, 0), target_bounds=None):
    objects = [o for o in bpy.data.objects
               if o.type == 'MESH' and o.name.startswith(prefixes)]
    assert objects, label
    if target_bounds:
        points = [world_to_camera_view(sc, camera, o.matrix_world @ v.co)
                  for o in objects for v in o.data.vertices]
        bounds = (min(p.x for p in points)*256, min(1-p.y for p in points)*256,
                  max(p.x for p in points)*256, max(1-p.y for p in points)*256)
        center = bounds[:2]
        scale = tuple((target_bounds[i+2]-target_bounds[i])/(bounds[i+2]-bounds[i])
                      for i in (0, 1))
        offset = tuple(target_bounds[i]-bounds[i] for i in (0, 1))
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
    (171.5, 56), target_bounds=(83,57,171.5,96))
fit('Low commander cupola', ('Closed commander', 'Cupola', 'Closed hatch seam', 'Hatch handle'),
    (126, 59), target_bounds=(100,49.5,128,62))
fit('Gun and mantlet', ('Rounded mantlet', 'Mantlet sleeve', 'Short 75', 'Worn muzzle', 'Dark muzzle'),
    (165, 85), target_bounds=(150,57,225.5,95))
fit('Mantlet casting width', ('Rounded mantlet',), (163, 79), (1.12, .90))
fit('Rear stowage', ('Rear stowage box', 'Stowage box lid', 'Stowage latch'),
    (64, 113), target_bounds=(24,86,99,115))
fit('Short jerricans', ('Rear deck jerrican', 'Jerrican'),
    (66, 91), target_bounds=(54,71.5,81,91))
# Place the real lamp housings at the painted fixtures, instead of relying on a
# second painted lamp on the glacis. Their old positions were 8/23 px too far left.
for suffix, dx, dy in (('',8,0),('.001',23,6)):
    for prefix in ('Headlamp housing','Headlamp dusty glass'):
        obj=bpy.data.objects[prefix+suffix];inverse=obj.matrix_world.inverted()
        delta=units*(right*dx-up*dy)
        for vertex in obj.data.vertices:
            vertex.co=inverse@(obj.matrix_world@vertex.co+delta)
        obj.data.update()
# The source has a slim muzzle; keep a genuine open bore and round barrel.
for name in ('Short 75 mm barrel','Worn muzzle rim','Dark muzzle bore'):
    obj=bpy.data.objects[name]
    center=sum((v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
    for vertex in obj.data.vertices:
        vertex.co.y=center.y+(vertex.co.y-center.y)*.72
        vertex.co.z=center.z+(vertex.co.z-center.z)*.72
    obj.data.update()
# Extend the bevelled rear armour shoulder under the newly registered stowage.
# The previous box relocation overhung its supporting hull.
hull = bpy.data.objects['Sloped upper hull']
inverse = hull.matrix_world.inverted()
for vertex in hull.data.vertices:
    influence = max(0, min(1, (-vertex.co.x - .95) / .40))
    vertex.co = inverse @ (hull.matrix_world @ vertex.co - right * units * 20 * influence)
hull.data.update()
records.append(dict(part='Rear shoulder support', extension_px=12, meshes=1))
# A restrained smoking wreck reads better than the old solid orange spikes.
for obj in list(bpy.data.objects):
    if obj.get('effect') == 'fire' or obj.name.startswith(('Wheel radial spoke','Wheel recessed aperture','Sprocket recess')):
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
            # Reduce the protruding shoe width, preserving pitch and real depth.
            for child in obj.children:
                child.location.y*=.85
                for vertex in child.data.vertices:vertex.co.y*=.85
                child.data.update()
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
