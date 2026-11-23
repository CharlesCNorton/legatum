#!/usr/bin/env python3
"""Painted Classical harbour cinematic. Blender 5.3; no render in --dry-run."""
import argparse
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import time

# Also cap Mantaflow/OpenMP, independently of the render thread setting.
os.environ['OMP_NUM_THREADS'] = '6'
import bpy
from mathutils import Euler, Matrix, Vector

FRAMES = 144
SIM_START = -71  # Three seconds let a tall smoke column establish before delivery.
ROOT = Path(__file__).resolve().parents[4]
PAINTING = ROOT / 'app/src/assets/eras/classical-1920.jpg'
RNG = random.Random(27)
CLOTH = []
TEXTURES = None
GAS_RESOLUTION = 80
IVORY = (0.76, 0.65, 0.45, 1)
OCHRE = (0.43, 0.27, 0.10, 1)
TERRA = (0.39, 0.12, 0.055, 1)
BLUE = (0.055, 0.16, 0.24, 1)
SAGE = (0.15, 0.21, 0.12, 1)


def node(tree, kind, name):
    n = tree.nodes.new(kind)
    n.label = n.name = name
    return n


def inp(n, name):
    return next(s for s in n.inputs if s.name == name and s.enabled)


def setv(n, name, value):
    candidates = [s for s in n.inputs if s.name == name and s.enabled]
    if isinstance(value, tuple):
        candidates = [s for s in candidates if hasattr(s.default_value, '__len__')
                      and len(s.default_value) == len(value)]
    candidates[0].default_value = value


def mesh(name, verts, faces, mat=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    if mat:
        data.materials.append(mat)
        if 'paint_family' in mat:
            stroke_uv(data)
    return ob


def active(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def cube(name, loc, size, mat=None, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        ob.data.materials.append(mat)
        if 'paint_family' in mat:
            stroke_uv(ob.data)
    ob.parent = parent
    return ob


def sphere(name, loc, size, mat=None, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        ob.data.materials.append(mat)
        if 'paint_family' in mat:
            stroke_uv(ob.data)
    ob.parent = parent
    return ob


def rod(name, a, b, radius, mat, parent=None, vertices=10):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                  radius2=radius * .88, depth=(b-a).length,
                                  location=(a+b)/2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    ob.data.materials.append(mat)
    if 'paint_family' in mat:
        stroke_uv(ob.data)
    ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.parent = parent
    return ob


def drive(ob, path, index, expression):
    fc = ob.driver_add(path, index) if index is not None else ob.driver_add(path)
    fc.driver.expression = expression


def stroke_uv(data):
    """Rest-space planar UVs in metres, with consistent tangent handedness.

    No Generated coordinates: those stretch with dimensions/deformation. A sail's
    UVs stay attached to its cloth and a ship's brushwork follows its hull.
    """
    uv = data.uv_layers.active or data.uv_layers.new(name='Pigment rest space')
    for poly in data.polygons:
        axis = max(range(3), key=lambda i: abs(poly.normal[i]))
        sign = 1 if poly.normal[axis] >= 0 else -1
        for li in poly.loop_indices:
            x, y, z = data.vertices[data.loops[li].vertex_index].co
            uv.data[li].uv = ((y, sign*z) if axis == 0 else
                              (z, sign*x) if axis == 1 else (x, sign*y))


def texture_image(filename, data=False):
    image = bpy.data.images.load(str(TEXTURES / filename), check_existing=True)
    image.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    if not image.packed_file:
        image.pack()
    return image


def paint(name, color, family='marble', tile_metres=3.6, tint=None):
    """Albedo, tangent normals and roughness extracted from the era painting."""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    mat['paint_family'] = family
    t = mat.node_tree
    bsdf = t.nodes.get('Principled BSDF')
    bsdf.inputs['IOR'].default_value = 1.46
    bsdf.inputs['Metallic'].default_value = 0
    bsdf.inputs['Specular IOR Level'].default_value = .24
    coord = node(t, 'ShaderNodeTexCoord', 'Rest-space painted strokes')
    mapping = node(t, 'ShaderNodeVectorMath', 'Brush size in world metres')
    mapping.operation = 'SCALE'
    mapping.inputs['Scale'].default_value = 1 / tile_metres
    t.links.new(coord.outputs['UV'], mapping.inputs[0])
    maps = {}
    for suffix in ('albedo', 'normal', 'roughness'):
        tex = node(t, 'ShaderNodeTexImage', f'Painting {family} {suffix}')
        tex.image = texture_image(f'{family}-{suffix}.png', suffix != 'albedo')
        tex.extension = 'REPEAT'
        tex.interpolation = 'Linear'
        t.links.new(mapping.outputs[0], tex.inputs['Vector'])
        maps[suffix] = tex
    albedo = maps['albedo'].outputs['Color']
    if tint is not None:
        mix = node(t, 'ShaderNodeMixRGB', 'Pigment glaze over sampled brushwork')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1
        mix.inputs[2].default_value = tint
        t.links.new(albedo, mix.inputs[1])
        albedo = mix.outputs[0]
    t.links.new(albedo, bsdf.inputs['Base Color'])
    t.links.new(maps['roughness'].outputs['Color'], bsdf.inputs['Roughness'])
    normal = node(t, 'ShaderNodeNormalMap', 'Luminance-derived bristle relief')
    normal.space = 'TANGENT'
    normal.inputs['Strength'].default_value = .65
    t.links.new(maps['normal'].outputs['Color'], normal.inputs['Color'])
    t.links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    if family in ('cloth', 'blue_cloth'):
        bsdf.inputs['Sheen Weight'].default_value = .18
    return mat


def emission(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    t = mat.node_tree
    t.nodes.clear()
    e = node(t, 'ShaderNodeEmission', name)
    e.inputs[0].default_value = color
    e.inputs[1].default_value = strength
    out = node(t, 'ShaderNodeOutputMaterial', 'Output')
    t.links.new(e.outputs[0], out.inputs['Surface'])
    return mat


def backdrop():
    """Painted sky and two alpha-cut mountain plates with aerial perspective."""
    def card(name, radius, low, high, material, offset=0):
        verts, faces = [], []
        for i in range(97):
            angle = math.radians(-100 + 200*i/96)
            for z in (low, high):
                verts.append((radius*math.sin(angle), radius*math.cos(angle), z))
        for i in range(96):
            faces.append((2*i, 2*i+1, 2*i+3, 2*i+2))
        ob = mesh(name, verts, faces, material)
        uv = ob.data.uv_layers.new()
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                vi = ob.data.loops[li].vertex_index
                uv.data[li].uv = (vi//2/96 + offset, vi % 2)
        return ob

    sky = emission('Distant painted sky', (1, 1, 1, 1), .9)
    t = sky.node_tree
    tex = node(t, 'ShaderNodeTexImage', 'Painting sky crop')
    tex.image = texture_image('sky.png')
    tex.extension = 'EXTEND'
    t.links.new(tex.outputs['Color'], t.nodes['Distant painted sky'].inputs[0])
    aov = node(t, 'ShaderNodeOutputAOV', 'Backdrop light wrap matte')
    aov.aov_name = 'BackdropMask'
    aov.inputs['Value'].default_value = 1
    ob = card('GEO-curved-painted-sky', 200, -35, 155, sky)
    for layer, (radius, low, high, haze, shift) in enumerate(
            ((150, -12, 38, .42, 0), (122, -15, 25, .16, .22))):
        mat = emission(f'Painted aerial mountain {layer}', (1, 1, 1, 1), .82)
        mat.surface_render_method = 'DITHERED'
        t = mat.node_tree
        tex = node(t, 'ShaderNodeTexImage', 'Actual mountain brushwork and skyline')
        tex.image = texture_image('mountains.png')
        tex.extension = 'REPEAT'
        tint = node(t, 'ShaderNodeMixRGB', 'Distance blue-grey pigment veil')
        tint.inputs[0].default_value = haze
        tint.inputs[2].default_value = (.36, .47, .59, 1)
        t.links.new(tex.outputs['Color'], tint.inputs[1])
        e = t.nodes[f'Painted aerial mountain {layer}']
        t.links.new(tint.outputs[0], e.inputs[0])
        tr = node(t, 'ShaderNodeBsdfTransparent', 'Soft painted skyline edge')
        mix = node(t, 'ShaderNodeMixShader', 'Mountain silhouette alpha')
        t.links.new(tex.outputs['Alpha'], mix.inputs[0])
        t.links.new(tr.outputs[0], mix.inputs[1])
        t.links.new(e.outputs[0], mix.inputs[2])
        t.links.new(mix.outputs[0], t.nodes['Output'].inputs['Surface'])
        card(f'GEO-painted-mountain-layer-{layer}', radius, low, high, mat, shift)
    return ob


def sea():
    ob = mesh('GEO-ocean', [(0, 0, 0)], [])
    ocean = ob.modifiers.new('Moving ocean and foam vertex layer', 'OCEAN')
    ocean.geometry_mode = 'GENERATE'
    ocean.resolution = 8
    ocean.viewport_resolution = 6
    ocean.spatial_size = 220
    ocean.wave_scale = .38
    ocean.choppiness = .85
    ocean.wind_velocity = 9
    ocean.wave_scale_min = .04
    ocean.use_normals = True
    ocean.use_foam = True
    ocean.foam_layer_name = 'foam'
    ocean.foam_coverage = -.35
    ocean.random_seed = 19
    drive(ocean, 'time', None, '2 + frame / 24.0')
    mat = bpy.data.materials.new('Mineral blue water with sparse crest foam')
    mat.use_nodes = True
    t = mat.node_tree
    bsdf = t.nodes.get('Principled BSDF')
    bsdf.inputs['IOR'].default_value = 1.333  # dielectric Fresnel, not metallic paint
    bsdf.inputs['Metallic'].default_value = 0
    coord=node(t,'ShaderNodeTexCoord','Water coordinates')
    mapping=node(t,'ShaderNodeVectorMath','Wind-stretched water brush marks')
    mapping.operation='MULTIPLY'; mapping.inputs[1].default_value=(.7,3.5,1)
    t.links.new(coord.outputs['Object'],mapping.inputs[0])
    noise=node(t,'ShaderNodeTexNoise','Small wind ripples')
    noise.inputs['Scale'].default_value=3.2; noise.inputs['Detail'].default_value=2
    t.links.new(mapping.outputs[0],noise.inputs['Vector'])
    water=node(t,'ShaderNodeValToRGB','Deep mineral blue and teal')
    water.color_ramp.elements[0].color=(.008,.055,.10,1)
    water.color_ramp.elements[1].color=(.025,.20,.23,1)
    t.links.new(noise.outputs['Fac'],water.inputs[0])
    attr=node(t,'ShaderNodeAttribute','Ocean foam vertex layer'); attr.attribute_name='foam'
    crest=node(t,'ShaderNodeMapRange','Only high foam crests survive')
    crest.clamp=True; crest.inputs['From Min'].default_value=.72
    crest.inputs['From Max'].default_value=.96
    t.links.new(attr.outputs['Fac'],crest.inputs['Value'])
    broken=node(t,'ShaderNodeMath','Broken crest flecks'); broken.operation='MULTIPLY'
    t.links.new(crest.outputs[0],broken.inputs[0]); t.links.new(noise.outputs['Fac'],broken.inputs[1])
    mix=node(t,'ShaderNodeMixRGB','Crest-only ivory foam')
    t.links.new(broken.outputs[0],mix.inputs[0]); t.links.new(water.outputs[0],mix.inputs[1])
    mix.inputs[2].default_value=(.65,.79,.74,1)
    t.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
    rough=node(t,'ShaderNodeMapRange','Fresnel glints and rough whitecaps')
    rough.inputs['To Min'].default_value=.16; rough.inputs['To Max'].default_value=.68
    t.links.new(broken.outputs[0],rough.inputs['Value']); t.links.new(rough.outputs[0],bsdf.inputs['Roughness'])
    bump=node(t,'ShaderNodeBump','Sun-catching ripple normals')
    bump.inputs['Strength'].default_value=.27; bump.inputs['Distance'].default_value=.065
    t.links.new(noise.outputs['Fac'],bump.inputs['Height']); t.links.new(bump.outputs[0],bsdf.inputs['Normal'])
    ob.data.materials.append(mat)
    ob.location.y=20
    return ob


def cloth(name, width, height, loc, mat, cache, parent=None, pin_tacks=False):
    nx, nz = 18, 12
    verts = [(width*(i/nx-.5), .24*math.sin(math.pi*i/nx)*math.sin(math.pi*j/nz),
              -height*j/nz) for j in range(nz+1) for i in range(nx+1)]
    faces = [(j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i)
             for j in range(nz) for i in range(nx)]
    ob = mesh(name, verts, faces, mat)
    ob.location = loc
    ob.parent = parent
    group = ob.vertex_groups.new(name='Pinned upper edge')
    group.add(list(range(nx+1)), 1, 'REPLACE')
    if pin_tacks:
        group.add([nz*(nx+1),(nz+1)*(nx+1)-1],1,'REPLACE')
    mod = ob.modifiers.new('Baked wind cloth', 'CLOTH')
    st = mod.settings
    st.quality = 4
    st.mass = .18
    st.air_damping = 2
    st.tension_stiffness = 18
    st.compression_stiffness = 18
    st.shear_stiffness = 12
    st.bending_stiffness = .25
    st.vertex_group_mass = group.name
    st.pin_stiffness = 1
    st.effector_weights.gravity = .6
    mod.collision_settings.use_self_collision = False
    pc = mod.point_cache
    pc.frame_start, pc.frame_end = SIM_START, FRAMES
    pc.name = name.replace('GEO-', '')
    # Small cloth caches are packed into cache/baked.blend. This is more robust
    # than Blender 5.3's named .bphys cache lookup after background reloads.
    pc.use_disk_cache = False
    thick = ob.modifiers.new('Real cloth thickness', 'SOLIDIFY')
    thick.thickness = .018
    CLOTH.append(ob)
    return ob


def ship(mats, cache):
    wood, ivory, blue = mats['wood'], mats['ivory'], mats['blue']
    rig = empty('RIG-trireme')
    rig.scale=(1.35,1.35,1.35)
    drive(rig, 'location', 0, '-6 + (frame-1)*.025')
    drive(rig, 'location', 1, '-5 + (frame-1)*.045')
    drive(rig, 'location', 2, '.35 + .16*sin(frame*.09)')
    drive(rig, 'rotation_euler', 0, '.025*sin(frame*.09+.5)')
    drive(rig, 'rotation_euler', 1, '.045*sin(frame*.08)')
    drive(rig, 'rotation_euler', 2, '-.62 + .025*sin(frame*.035)')
    verts, faces = [], []
    for y, width, lift in [(-5.4,.13,.55),(-4,1.05,0),(-2,1.38,0),(2,1.38,0),(4,1.0,.1),(5.7,.06,.9)]:
        verts += [(-width,y,1.0+lift),(-width*.65,y,-.15+lift),(0,y,-.45+lift),
                  (width*.65,y,-.15+lift),(width,y,1.0+lift)]
    for j in range(5):
        for i in range(4):
            a=j*5+i
            faces.append((a,a+1,a+6,a+5))
        faces.append((j*5, j*5+5, j*5+9, j*5+4))
    faces += [(0,4,3,2,1),(25,26,27,28,29)]
    hull = mesh('GEO-trireme-carved-hull', verts, [face[::-1] for face in faces], wood)
    hull.parent = rig
    bevel=hull.modifiers.new('Rounded carved hull edges','BEVEL'); bevel.width=.16; bevel.segments=3
    for poly in hull.data.polygons: poly.use_smooth=True
    for side in (-1,1):
        for z in (.2,.48,.76):
            curve=bpy.data.curves.new('Hull strake','CURVE'); curve.dimensions='3D'
            curve.bevel_depth=.028; curve.bevel_resolution=2
            spline=curve.splines.new('POLY'); spline.points.add(5)
            for point,(y,w,lift) in zip(spline.points,[(-5.4,.13,.55),(-4,1.05,0),(-2,1.38,0),(2,1.38,0),(4,1,.1),(5.7,.06,.9)]):
                point.co=(side*w*.94,y,z+lift,1)
            strake=bpy.data.objects.new('GEO-hull-strake',curve); bpy.context.collection.objects.link(strake)
            curve.materials.append(mats['ochre']); strake.parent=rig
    cube('GEO-deck', (0,0,1.0), (2.1,7.8,.18), mats['ochre'], rig)
    for side in (-1,1):
        rod('GEO-gunwale', (side*1.28,-3.8,1.2), (side*1.28,3.8,1.2), .10, ivory, rig)
        for j in range(12):
            pivot = empty('RIG-oar', (side*1.25,-3.5+j*.62,.65), rig)
            drive(pivot,'rotation_euler',2,f'{side}*(.22+.42*sin(frame*.24))')
            drive(pivot,'rotation_euler',1,f'{side}*(.14+.20*cos(frame*.24))')
            shaft=rod('GEO-oar-shaft',(0,0,0),(side*2.55,0,-.15),.070,wood,pivot,12)
            for poly in shaft.data.polygons: poly.use_smooth=True
            # A solid tapered paddle with a shoulder and rounded tip, not a white strip.
            outline=[(2.28,-.075),(2.52,-.19),(3.15,-.22),(3.35,-.12),
                     (3.35,.12),(3.15,.22),(2.52,.19),(2.28,.075)]
            vs=[(side*x,y,-.15+z) for z in (-.055,.055) for x,y in outline]
            fs=[tuple(reversed(range(8))),tuple(range(8,16))]
            fs += [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
            if side<0: fs=[face[::-1] for face in fs]
            blade=mesh('GEO-solid-timber-oar-blade',vs,fs,wood); blade.parent=pivot
            bevel=blade.modifiers.new('Soft paddle edges','BEVEL'); bevel.width=.035; bevel.segments=2
    rod('GEO-mast',(0,.3,1),(0,.3,6.8),.13,wood,rig)
    rod('GEO-yard',(-2.6,.3,6.4),(2.6,.3,6.4),.085,wood,rig)
    cloth('GEO-sail',4.9,2.5,(0,.38,6.35),mats['cloth'],cache,rig,pin_tacks=True)
    for side in (-1,1):
        rod('GEO-sail-tack-rope',(side*2.45,.38,3.85),(side*1.2,2,1.2),.025,wood,rig,6)
    rod('GEO-bow-ram',(0,4.7,.1),(0,6.5,.1),.16,mats['ochre'],rig)
    foam_particles()
    return rig


def ship_transform(frame):
    """The v2 ship drivers, sampled at particle birth, including pitch and roll."""
    pos = Vector((-6+(frame-1)*.025, -5+(frame-1)*.045, .35+.16*math.sin(frame*.09)))
    rot = Euler((.025*math.sin(frame*.09+.5), .045*math.sin(frame*.08),
                 -.62+.025*math.sin(frame*.035)), 'XYZ').to_matrix().to_4x4()
    return Matrix.Translation(pos) @ rot @ Matrix.Diagonal((1.35,1.35,1.35,1))


def foam_particles():
    """Deterministic birth/advection/lifetime particles, packed as shape keys.

    Actual 3D foam instances are emitted in world space from the moving stern
    and immersed oar blades. They drift after emission instead of following the
    hull. No ribbon mesh, frame handler, external add-on or extra fluid bake.
    """
    rng = random.Random(431)  # Never perturb the town/figure layout RNG.
    particles = []
    for birth in range(-95, FRAMES+1, 2):
        matrix = ship_transform(birth)
        for side in (-1,1):
            for _ in range(7):
                local = Vector((side*rng.uniform(.2,1.05),rng.uniform(-5.7,-4.9),-.1))
                pos = matrix @ local
                drift = matrix.to_3x3() @ Vector((side*rng.uniform(.10,.32),-.08,0))
                particles.append((birth,rng.uniform(65,100),pos,drift,rng.uniform(.065,.17)))
            # Position and immersion come from the same rotation as the modeled oar.
            rotation = Euler((0,side*(.14+.20*math.cos(birth*.24)),
                              side*(.22+.42*math.sin(birth*.24))), 'XYZ').to_matrix()
            for j in range(12):
                tip = Vector((side*1.25,-3.5+j*.62,.65)) + rotation @ Vector((side*3.12,0,-.15))
                pos = matrix @ tip
                if pos.z > .22:  # Recovery stroke makes no new surface foam.
                    continue
                for _ in range(3):
                    jitter = Vector((rng.uniform(-.14,.14),rng.uniform(-.16,.16),0))
                    drift = matrix.to_3x3() @ Vector((side*rng.uniform(.14,.36),-.12,0))
                    particles.append((birth,rng.uniform(24,48),pos+jitter,drift,rng.uniform(.045,.12)))
    host = mesh('FX-world-space-foam-particles', [(0,0,0)]*len(particles), [])
    host['method'] = 'Seeded surface particles: birth at stern/oars, drift, expansion, lifetime'
    host['particle_count'] = len(particles)
    host['simulation'] = 'Analytic advection, not a fluid or dynamic-paint solve'
    for name, column in (('birth',0),('lifetime',1),('radius',4)):
        attribute = host.data.attributes.new(name, 'FLOAT', 'POINT')
        attribute.data.foreach_set('value', [p[column] for p in particles])
    # Absolute shape keys interpolate the baked particle buffer, surviving .blend reload.
    host.shape_key_add(name='Frame 001')
    keys = host.data.shape_keys
    keys.use_relative = False
    for frame in range(1,FRAMES+1):
        key = keys.key_blocks[0] if frame == 1 else host.shape_key_add(name=f'Frame {frame:03d}')
        key.interpolation = 'KEY_LINEAR'
        values = array('f')
        for birth,life,pos,drift,radius in particles:
            age = max(0,min(life,frame-birth))/24
            x = pos.x + drift.x*age + .075*math.sin(age*2.2+birth)
            y = pos.y + drift.y*age + .075*math.cos(age*1.7+birth)
            values.extend((x,y,1.0))  # Project vertically onto the actual Ocean below.
        key.data.foreach_set('co',values)
    active(host)
    bpy.ops.object.shape_key_retime()
    step = keys.key_blocks[1].frame - keys.key_blocks[0].frame
    start = keys.key_blocks[0].frame
    if step <= 0:
        raise RuntimeError('Absolute foam shape keys must have increasing sample times')
    drive(keys,'eval_time',None,f'{start}+max(0,min(143,frame-1))*{step}')
    wrap = host.modifiers.new('Particles ride the actual Ocean surface','SHRINKWRAP')
    wrap.target = bpy.data.objects['GEO-ocean']
    wrap.wrap_method = 'PROJECT'; wrap.use_project_z = True
    wrap.use_negative_direction = True; wrap.use_positive_direction = True
    wrap.offset = .025
    ng = bpy.data.node_groups.new('Surface foam particle instancing','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    mod = host.modifiers.new('Foam particle instances','NODES'); mod.node_group=ng
    ni=node(ng,'NodeGroupInput','Advected particles'); no=node(ng,'NodeGroupOutput','Foam')
    tm=node(ng,'GeometryNodeInputSceneTime','Particle clock')
    def attr(name):
        n=node(ng,'GeometryNodeInputNamedAttribute',name); n.data_type='FLOAT'
        n.inputs['Name'].default_value=name
        return n.outputs['Attribute']
    def mathn(op,a,b):
        n=node(ng,'ShaderNodeMath',op); n.operation=op
        for value,sock in zip((a,b),n.inputs):
            if isinstance(value,(int,float)): sock.default_value=value
            else: ng.links.new(value,sock)
        return n.outputs[0]
    age=mathn('SUBTRACT',tm.outputs['Frame'],attr('birth'))
    fraction=mathn('MINIMUM',mathn('MAXIMUM',mathn('DIVIDE',age,attr('lifetime')),0),1)
    envelope=mathn('MAXIMUM',mathn('SINE',mathn('MULTIPLY',fraction,math.pi),0),0)
    radius=mathn('MULTIPLY',attr('radius'),envelope)
    shape=node(ng,'ShaderNodeCombineXYZ','Flat irregular foam globules')
    ng.links.new(mathn('MULTIPLY',radius,1.4),shape.inputs['X'])
    ng.links.new(radius,shape.inputs['Y'])
    ng.links.new(mathn('MULTIPLY',radius,.20),shape.inputs['Z'])
    ico=node(ng,'GeometryNodeMeshIcoSphere','Shared foam particle')
    ico.inputs['Radius'].default_value=1; ico.inputs['Subdivisions'].default_value=1
    mat=bpy.data.materials.new('Warm broken foam pigment'); mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(.42,.58,.54,1)
    bsdf.inputs['Roughness'].default_value=.78
    material=node(ng,'GeometryNodeSetMaterial','Foam pigment')
    material.inputs['Material'].default_value=mat
    ng.links.new(ico.outputs['Mesh'],material.inputs['Geometry'])
    inst=node(ng,'GeometryNodeInstanceOnPoints','Lifetime foam particles')
    alive=mathn('MULTIPLY',mathn('GREATER_THAN',fraction,0),mathn('LESS_THAN',fraction,1))
    ng.links.new(alive,inst.inputs['Selection'])
    ng.links.new(ni.outputs['Geometry'],inst.inputs['Points'])
    ng.links.new(material.outputs['Geometry'],inst.inputs['Instance'])
    ng.links.new(shape.outputs[0],inst.inputs['Scale'])
    ng.links.new(inst.outputs[0],no.inputs['Geometry'])


def architecture(m):
    cube('GEO-quay', (0,15,.1), (110,7,2.4),m['stone'])
    cube('GEO-quay-coping',(0,11.6,1.3),(110,.4,.3),m['ivory'])
    for x in range(-53,55,3):
        cube('GEO-pier-joint',(x,11.36,.35),(.08,.07,1.9),m['wood'])
    cube('GEO-coastal-town-ground',(0,103,.35),(200,170,2.1),m['stone'])
    # Layered irregular outcrop, with a genuinely flat acropolis platform.
    verts,faces=[],[]
    sectors=64
    for ring,(rx,ry,z) in enumerate(((22,19,-.5),(19,17,1.8),(16,14,4.1),(13.5,12.5,6.4),(12,11.5,8.0))):
        for i in range(sectors):
            theta=2*math.pi*i/sectors
            broken=1+.07*math.sin(5*theta+.4)+.04*math.sin(13*theta+ring*.7)
            verts.append((5+rx*math.cos(theta)*broken,34+ry*math.sin(theta)*broken,
                          z+(RNG.uniform(-.65,.65) if ring not in (0,4) else 0)))
    for ring in range(4):
        for i in range(sectors):
            a=ring*sectors+i; b=ring*sectors+(i+1)%sectors
            faces.extend(((a,b,b+sectors),(a,b+sectors,a+sectors)))
    faces.append(tuple(range(4*sectors,5*sectors)))
    cliff=mesh('GEO-stratified-limestone-outcrop',verts,faces,m['rock'])
    for poly in cliff.data.polygons: poly.use_smooth=True
    for j in range(95):
        theta=RNG.uniform(0,math.tau); r=RNG.uniform(.78,1)
        x,y=5+18*r*math.cos(theta),34+16*r*math.sin(theta)
        rock=sphere('GEO-weathered-limestone-buttress',(x,y,RNG.uniform(1.3,4)),
                    (RNG.uniform(.6,1.8),RNG.uniform(.7,2),RNG.uniform(1.2,3.7)),m['rock'])
        rock.rotation_euler=(RNG.uniform(-.3,.3),RNG.uniform(-.3,.3),RNG.random())
        texture=bpy.data.textures.get('Weathered limestone') or bpy.data.textures.new('Weathered limestone','CLOUDS')
        texture.noise_scale=.7
        displace=rock.modifiers.new('Eroded rock faces','DISPLACE'); displace.texture=texture; displace.strength=.3
        for poly in rock.data.polygons: poly.use_smooth=True
    # Mortared courses, not a solid featureless box; joints remain narrow.
    for course in range(4):
        z=5.3+course*.76
        for j in range(12):
            x=-5.8+j*1.95+(course%2)*.45
            cube('GEO-acropolis-front-ashlar',(x,22.7,z),(1.91,1.4,.73),m['ivory'])
        for side in (-1,1):
            for j in range(11):
                cube('GEO-acropolis-side-ashlar',(5+side*12,23.7+j*1.85,z),
                     (1.4,1.81,.73),m['ivory'])
    cube('GEO-acropolis-terrace',(5,33.4,8.03),(25.5,23.4,.35),m['ivory'])
    for x in (-7,17):
        cube('GEO-retaining-wall-cap',(x,33.4,8.4),(1.7,23.8,.35),m['ivory'])
    for j in range(24):
        cube('GEO-acropolis-stair',(4,15.2+j*.34,1.4+j*.29),(5,.58,.31),m['ivory'])
    for j in range(3):
        cube('GEO-temple-stylobate',(5,32,8.1+j*.35),(14-j*.6,18-j*.6,.4),m['ivory'])
    for x in (-.7,10.7):
        for y in (24.8,27.7,30.6,33.5,36.4,39.3):
            rod('GEO-doric-column',(x,y,9),(x,y,14.5),.40,m['ivory'],vertices=24)
            cube('GEO-doric-capital',(x,y,14.5),(1.05,1.05,.3),m['ivory'])
    for y in (24.8,39.3):
        for x in (1.6,3.9,6.2,8.5):
            rod('GEO-front-column',(x,y,9),(x,y,14.5),.40,m['ivory'],vertices=24)
            cube('GEO-front-capital',(x,y,14.5),(1.05,1.05,.3),m['ivory'])
    cube('GEO-cella',(5,32,11.4),(6.5,10,4.8),m['ochre'])
    cube('GEO-entablature',(5,32,14.9),(13.5,17,.65),m['ivory'])
    roof=mesh('GEO-terracotta-pediment', [(-2,23.3,15.2),(12,23.3,15.2),(5,23.3,18),
             (-2,40.7,15.2),(12,40.7,15.2),(5,40.7,18)],
             [(0,1,2),(5,4,3),(0,3,4,1),(0,2,5,3),(1,4,5,2)],m['terra'])
    # Roof structure, triglyph rhythm, capitals and tympanum give scale at 540p.
    for y in (23.18,40.82):
        mesh('GEO-limestone-tympanum',[(-1.8,y,15.22),(11.8,y,15.22),(5,y,17.7)],[(0,1,2)],m['ivory'])
        rod('GEO-pediment-raking-cornice',(-2,y,15.25),(5,y,17.95),.14,m['ivory'])
        rod('GEO-pediment-raking-cornice',(5,y,17.95),(12,y,15.25),.14,m['ivory'])
        for j in range(19):
            cube('GEO-frieze-triglyph',(-1.4+j*.71,y,14.95),(.17,.16,.48),m['ochre'])
        for j in range(9):
            x=1+j
            z=15.45
            h=max(.2,1.5-abs(x-5)*.28)
            sphere('GEO-pediment-relief',(x,y-.08,z+h*.4),(.19,.13,h*.45),m['ivory'])
    for j in range(28):
        y=23.45+j*.63
        for side in (-1,1):
            rod('GEO-roof-tile-ridge',(5,y,18.03),(5+side*7,y,15.27),.047,m['terra'],vertices=6)
    for ob in list(bpy.context.scene.objects):
        if 'column' in ob.name:
            for poly in ob.data.polygons: poly.use_smooth=True
            x,y,_=ob.location
            rod('GEO-doric-echinus',(x,y,14.23),(x,y,14.48),.54,m['ivory'],vertices=24)
    # Cluster houses along both flanks and the waterfront, leaving the stair open.
    for j in range(64):
        side=-1 if j%2 else 1
        # Staggered neighbourhoods continue beyond the wide, not an isolated plinth.
        x=5+side*(16+(j//2)%8*4.5+RNG.uniform(-.4,.4))
        y=22+(j//16)*7+RNG.uniform(-.6,.6)
        ground=1.2 if y<25 else 2.0
        w,d,h=RNG.uniform(2.2,3.6),RNG.uniform(2.5,4),RNG.uniform(2.2,4)
        cube('GEO-harbour-house',(x,y,ground+h/2),(w,d,h),m['ivory'])
        mesh('GEO-house-pitched-roof',[(x-w*.56,y-d*.56,ground+h),(x+w*.56,y-d*.56,ground+h),
             (x,y-d*.56,ground+h+.9),(x-w*.56,y+d*.56,ground+h),
             (x+w*.56,y+d*.56,ground+h),(x,y+d*.56,ground+h+.9)],
             [(0,1,2),(5,4,3),(0,2,5,3),(1,4,5,2)],m['terra'])
        for offset in (-.6,.6):
            cube('GEO-house-window',(x+offset,y-d/2-.025,ground+h*.65),(.4,.08,.65),m['wood'])
        cube('GEO-house-door',(x,y-d/2-.03,ground+.65),(.65,.09,1.3),m['wood'])
    # Harbour stoa: deep shadowed arcade against warm columns.
    cube('GEO-stoa-back',(-15,23,3.5),(14,.6,4.2),m['ochre'])
    cube('GEO-stoa-roof',(-15,21.1,5.8),(15,4.8,.45),m['terra'])
    for j in range(12):
        rod('GEO-stoa-column',(-21.5+j*1.18,19.2,1.4),(-21.5+j*1.18,19.2,5.55),.19,m['ivory'],vertices=20)
    for x in (-38,-28,28,38,48):
        y=18.8
        rod('GEO-olive-trunk',(x,y,1.4),(x+.3,y,4),.19,m['wood'],vertices=16)
        for j in range(5):
            crown=sphere('GEO-olive-crown',(x+RNG.uniform(-1,1),y+RNG.uniform(-.7,.7),4+RNG.uniform(0,.7)),
                         (1.3,1.0,.85),m['sage'])
            for poly in crown.data.polygons: poly.use_smooth=True
        for j in range(3):
            cube('GEO-quayside-cargo',(x+j*.75,y-2.2,1.8),(.65,.65,.8),m['wood'])
    for j in range(18):
        x,y=RNG.choice((-1,1))*RNG.uniform(10,18)+4,RNG.uniform(22,39)
        rod('GEO-cypress-trunk',(x,y,3),(x,y,7),.16,m['wood'])
        tree=sphere('GEO-cypress',(x,y,7.2),(.8,.85,3.2),m['sage'])
        for poly in tree.data.polygons: poly.use_smooth=True
        tex=bpy.data.textures.get('Cypress foliage') or bpy.data.textures.new('Cypress foliage','CLOUDS')
        tex.noise_scale=.35
        dis=tree.modifiers.new('Uneven foliage silhouette','DISPLACE'); dis.texture=tex; dis.strength=.35


def fire(m, cache):
    cube('GEO-beacon-plinth',(-12,15,2.0),(2,2,1.6),m['stone'])
    rod('GEO-beacon-bowl',(-12,15,2.8),(-12,15,3.3),1.05,m['ochre'])
    for i in range(5):
        rod('GEO-burning-log',(-12.6,14.65+i*.16,3.25),(-11.4,15.35-i*.16,3.5),.12,m['wood'])
    flow=sphere('GEO-fire-smoke-emitter',(-12,15,3.85),(1.2,1.05,.75))
    mod=flow.modifiers.new('Fire and smoke source','FLUID')
    mod.fluid_type='FLOW'
    fs=mod.flow_settings
    fs.flow_type='BOTH'
    fs.flow_behavior='INFLOW'
    fs.surface_distance=1.5
    fs.fuel_amount=1.4
    fs.temperature=3.0
    fs.density=1.0  # RNA maximum; larger source/longer emission supplies more smoke.
    fs.use_initial_velocity=True
    fs.velocity_coord=(.30,.08,4.0)
    # Transparent surface, while the closed emitter remains present in the solver.
    transparent=bpy.data.materials.new('Invisible fluid emitter surface')
    transparent.use_nodes=True
    t=transparent.node_tree
    t.nodes.clear()
    tr=node(t,'ShaderNodeBsdfTransparent','Transparent')
    out=node(t,'ShaderNodeOutputMaterial','Output')
    t.links.new(tr.outputs[0],out.inputs['Surface'])
    flow.data.materials.append(transparent)
    domain=cube('GEO-Mantaflow-fire-smoke-domain',(-9,16,18),(14,12,34))
    mod=domain.modifiers.new('80 voxel gas plus 2x billow detail','FLUID')
    mod.fluid_type='DOMAIN'
    ds=mod.domain_settings
    ds.domain_type='GAS'
    ds.resolution_max=GAS_RESOLUTION
    ds.cache_frame_start,ds.cache_frame_end=SIM_START,FRAMES
    ds.cache_type='ALL'
    ds.cache_data_format='UNI'
    ds.cache_noise_format='UNI'
    ds.cache_directory=str(cache/'fluid')
    ds.use_noise=True
    ds.noise_scale=2
    ds.noise_strength=.75
    ds.noise_pos_scale=2.0
    ds.use_adaptive_domain=False
    ds.use_collision_border_top=False
    ds.vorticity=2.1
    ds.alpha=2.0
    ds.beta=2.2
    ds.flame_vorticity=2.2
    ds.burning_rate=.85
    ds.flame_smoke=2.6
    ds.use_dissolve_smoke=True
    ds.dissolve_speed=150
    ds.timesteps_max=3
    ds.effector_weights.wind=.025
    vol=bpy.data.materials.new('Real density and flame grids')
    vol.use_nodes=True
    t=vol.node_tree
    t.nodes.clear()
    p=node(t,'ShaderNodeVolumePrincipled','Lit smoke with blackbody flame emission')
    setv(p,'Color',(.34,.31,.27,1))
    setv(p,'Color Attribute','')  # Do not multiply by the solver's dark smoke colour.
    setv(p,'Anisotropy',.28)
    setv(p,'Density',1.35)  # Allow key/fill into the billows instead of a black blob.
    setv(p,'Density Attribute','density')
    geometry=node(t,'ShaderNodeNewGeometry','Smoke height in world space')
    xyz=node(t,'ShaderNodeSeparateXYZ','Upper plume height')
    t.links.new(geometry.outputs['Position'],xyz.inputs[0])
    top=node(t,'ShaderNodeMapRange','Dissipate before the open domain ceiling')
    top.clamp=True
    top.inputs['From Min'].default_value=28; top.inputs['From Max'].default_value=34
    top.inputs['To Min'].default_value=1.35; top.inputs['To Max'].default_value=0
    t.links.new(xyz.outputs['Z'],top.inputs['Value'])
    t.links.new(top.outputs[0],inp(p,'Density'))
    setv(p,'Blackbody Intensity',0)  # Explicit blackbody node below, gated by flame.
    flame=node(t,'ShaderNodeAttribute','Mantaflow flame grid'); flame.attribute_name='flame'
    heat=node(t,'ShaderNodeAttribute','Mantaflow temperature grid'); heat.attribute_name='temperature'
    kelvin=node(t,'ShaderNodeMapRange','Simulation heat to flame kelvin')
    kelvin.clamp=True
    kelvin.inputs['From Min'].default_value=0; kelvin.inputs['From Max'].default_value=1
    kelvin.inputs['To Min'].default_value=1050; kelvin.inputs['To Max'].default_value=1850
    t.links.new(heat.outputs['Fac'],kelvin.inputs['Value'])
    blackbody=node(t,'ShaderNodeBlackbody','Real blackbody flame colour')
    t.links.new(kelvin.outputs[0],blackbody.inputs['Temperature'])
    t.links.new(blackbody.outputs['Color'],inp(p,'Emission Color'))
    core=node(t,'ShaderNodeMath','Flame-grid emission only'); core.operation='POWER'
    core.inputs[1].default_value=1.6
    t.links.new(flame.outputs['Fac'],core.inputs[0])
    power=node(t,'ShaderNodeMath','Restrained flame radiance'); power.operation='MULTIPLY'
    power.inputs[1].default_value=8
    t.links.new(core.outputs[0],power.inputs[0])
    t.links.new(power.outputs[0],inp(p,'Emission Strength'))
    out=node(t,'ShaderNodeOutputMaterial','Volume only output')
    t.links.new(p.outputs['Volume'],out.inputs['Volume'])
    domain.data.materials.append(vol)
    lamp=bpy.data.lights.new('LGT-fire-flicker','POINT')
    lamp.color=(1,.25,.035)
    lamp.energy=650
    lamp.shadow_soft_size=.7
    lob=bpy.data.objects.new(lamp.name,lamp)
    bpy.context.collection.objects.link(lob)
    lob.location=(-12,15,4)
    drive(lamp,'energy',None,'650+160*sin(frame*.7)+80*sin(frame*1.73)')
    under=bpy.data.lights.new('LGT-warm-smoke-underside','AREA')
    under.energy=650; under.color=(1,.40,.12); under.shape='DISK'; under.size=3
    uob=bpy.data.objects.new(under.name,under); bpy.context.collection.objects.link(uob)
    uob.location=(-12,13,3.7)
    uob.rotation_euler=(Vector((-11,15,8))-uob.location).to_track_quat('-Z','Y').to_euler()
    rim=bpy.data.lights.new('LGT-smoke-daylight-volume-rim','AREA')
    rim.energy=4200; rim.color=(.74,.83,1); rim.shape='DISK'; rim.size=9
    rim.diffuse_factor=0; rim.specular_factor=0; rim.volume_factor=1
    rob=bpy.data.objects.new(rim.name,rim); bpy.context.collection.objects.link(rob)
    rob.location=(-17,23,19)
    rob.rotation_euler=(Vector((-10,15,12))-rob.location).to_track_quat('-Z','Y').to_euler()
    return domain


def move_to_collection(ob, col):
    for old in list(ob.users_collection):
        old.objects.unlink(ob)
    col.objects.link(ob)


def crowds(m):
    # Unlinked collection is an instance library, never a second visible crowd.
    library=bpy.data.collections.new('LIB-four-walking-tunic-figures')
    for variant,color in enumerate(('ivory','blue','terra','sage')):
        parts=[]
        parts.append(rod('tunic',(0,0,.55),(0,0,1.25),.25,m[color]))
        parts.append(sphere('head',(0,0,1.5),(.12,.12,.16),m['skin']))
        for side in (-1,1):
            parts.append(rod('leg',(side*.105,0,.05),(side*.105,0,.65),.065,m['skin']))
            parts.append(rod('arm',(side*.27,0,.72),(side*.23,0,1.23),.055,m['skin']))
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts: p.select_set(True)
        bpy.context.view_layer.objects.active=parts[0]
        bpy.ops.object.join()
        ob=bpy.context.object
        ob.name=f'LIB-walker-{color}'
        # Put mesh origin at ground for meaningful pose coordinates.
        bpy.context.scene.cursor.location=(0,0,0)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        ob.shape_key_add(name='Rest')
        stride=ob.shape_key_add(name='Stride')
        for v in stride.data:
            if v.co.z < .65:
                v.co.y += (.65-v.co.z)*(.5 if v.co.x>0 else -.5)
            elif abs(v.co.x)>.20 and v.co.z<1.24:
                v.co.y += (1.24-v.co.z)*(-.7 if v.co.x>0 else .7)
        stride.slider_min=-1
        drive(stride,'value',None,f'sin(frame*.32+{variant*1.7})')
        move_to_collection(ob,library)
    pts=[(RNG.uniform(-42,44),RNG.uniform(12.6,16.7),1.36) for _ in range(84)]
    host=mesh('GEO-84-instanced-quay-walkers',pts,[])
    ng=bpy.data.node_groups.new('Walking crowd instances','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    mod=host.modifiers.new('Actual geometry nodes instancing','NODES'); mod.node_group=ng
    ni=node(ng,'NodeGroupInput','Quay points'); no=node(ng,'NodeGroupOutput','Crowd')
    tm=node(ng,'GeometryNodeInputSceneTime','Walk clock')
    idx=node(ng,'GeometryNodeInputIndex','Walker phase')
    def mathn(op,a,b):
        n=node(ng,'ShaderNodeMath',op); n.operation=op
        for v,s in zip((a,b),n.inputs):
            if isinstance(v,(int,float)): s.default_value=v
            else: ng.links.new(v,s)
        return n.outputs[0]
    phase=mathn('ADD',mathn('MULTIPLY',tm.outputs['Seconds'],7.68),idx.outputs[0])
    bob=mathn('MULTIPLY',mathn('SINE',phase,0),.035)
    combine=node(ng,'ShaderNodeCombineXYZ','Walk along quay and bob')
    ng.links.new(mathn('MULTIPLY',tm.outputs['Seconds'],.42),combine.inputs['X'])
    ng.links.new(bob,combine.inputs['Z'])
    pos=node(ng,'GeometryNodeSetPosition','Moving points')
    ng.links.new(ni.outputs['Geometry'],pos.inputs['Geometry'])
    ng.links.new(combine.outputs[0],pos.inputs['Offset'])
    ci=node(ng,'GeometryNodeCollectionInfo','Four tunic and stride variants')
    ci.inputs['Collection'].default_value=library
    ci.inputs['Separate Children'].default_value=True
    inst=node(ng,'GeometryNodeInstanceOnPoints','Instanced walkers')
    inst.inputs['Pick Instance'].default_value=True
    inst.inputs['Rotation'].default_value=(0,0,-math.pi/2)
    ng.links.new(idx.outputs[0],inst.inputs['Instance Index'])
    ng.links.new(pos.outputs[0],inst.inputs['Points'])
    ng.links.new(ci.outputs['Instances'],inst.inputs['Instance'])
    ng.links.new(inst.outputs[0],no.inputs['Geometry'])


def gulls(m):
    for phase in range(3):
        lib=bpy.data.collections.new(f'LIB-gull-phase-{phase}')
        body=sphere('GEO-gull-body',(0,0,0),(.11,.28,.09),m['ivory'])
        move_to_collection(body,lib)
        for side in (-1,1):
            wing=mesh('GEO-gull-flapping-wing',[(0,0,0),(side*.65,.08,.05),(side*.9,.25,.02),(side*.3,-.17,0)],[(0,1,2,3)],m['ivory'])
            drive(wing,'rotation_euler',1,f'{side}*(.30+.65*sin(frame*.37+{phase*2.1}))')
            move_to_collection(wing,lib)
        for i in range(3):
            bird=empty('RIG-instanced-circling-gull')
            bird.instance_type='COLLECTION'; bird.instance_collection=lib
            phi=(phase*3+i)*.69; r=6+i*1.2
            drive(bird,'location',0,f'2+{r}*cos(frame*.018+{phi})')
            drive(bird,'location',1,f'22+{r}*sin(frame*.018+{phi})')
            drive(bird,'location',2,f'{10+phase*.9}+.4*sin(frame*.04+{phi})')
            drive(bird,'rotation_euler',2,f'frame*.018+{phi}')


def lights_camera(scene,m):
    world=bpy.data.worlds.new('Cool daylight environment'); scene.world=world
    world.use_nodes=True
    wt=world.node_tree
    sky=node(wt,'ShaderNodeTexSky','Physical sky for water Fresnel reflections')
    sky.sky_type='MULTIPLE_SCATTERING'; sky.sun_disc=False
    sky.sun_elevation=math.radians(30); sky.sun_rotation=math.radians(218)
    sky.air_density=1.1; sky.aerosol_density=.6
    wt.links.new(sky.outputs[0],wt.nodes['Background'].inputs[0])
    wt.nodes['Background'].inputs[1].default_value=.22
    sun=bpy.data.lights.new('LGT-warm-upper-left-sun','SUN'); sun.energy=3.2
    sun.color=(1,.83,.60); sun.angle=math.radians(2.0)
    ob=bpy.data.objects.new(sun.name,sun); scene.collection.objects.link(ob)
    ob.location=(-45,-35,33)
    ob.rotation_euler=(Vector((0,0,0))-ob.location).to_track_quat('-Z','Y').to_euler()
    # A specular-only reflection accent puts the sun path into the water without
    # introducing a second set of architectural shadows.
    glint=bpy.data.lights.new('LGT-water-sun-glints','SUN')
    glint.energy=1.4; glint.color=(1,.86,.62); glint.angle=math.radians(.6)
    glint.diffuse_factor=0; glint.volume_factor=0
    gob=bpy.data.objects.new(glint.name,glint); scene.collection.objects.link(gob)
    gob.location=(-25,70,32)
    gob.rotation_euler=(-gob.location).to_track_quat('-Z','Y').to_euler()
    # The reference has an offscreen sun. No opaque white sphere in the sky.
    fill=bpy.data.lights.new('LGT-large-cool-sky-fill','AREA')
    fill.energy=6000; fill.color=(.50,.69,1); fill.shape='DISK'; fill.size=45
    fob=bpy.data.objects.new(fill.name,fill); scene.collection.objects.link(fob)
    fob.location=(15,0,30)
    fob.rotation_euler=(Vector((0,22,5))-fob.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.effector_add(type='WIND',location=(-10,-10,5))
    wind=bpy.context.object; wind.name='FX-wind-for-sail-banners-smoke'
    wind.rotation_euler=(math.radians(-82),math.radians(12),0)
    wind.field.strength=65; wind.field.noise=1.4; wind.field.seed=27
    drive(wind.field,'strength',None,'65+40*sin(frame*.11)+15*sin(frame*.37)')
    drive(wind,'rotation_euler',2,'.28*sin(frame*.10)')
    bpy.ops.object.effector_add(type='TURBULENCE',location=(-12,15,6))
    turbulence=bpy.context.object; turbulence.name='FX-beacon-turbulence'
    turbulence.field.strength=1.2; turbulence.field.size=1.5
    turbulence.field.seed=19
    turbulence.field.use_max_distance=True; turbulence.field.distance_max=7
    camera_data=bpy.data.cameras.new('CAM-water-to-acropolis'); camera_data.lens=32
    camera_data.clip_end=500; camera_data.show_composition_thirds=True
    cam=bpy.data.objects.new(camera_data.name,camera_data); scene.collection.objects.link(cam)
    scene.camera=cam
    # Continuous Hermite path: follow broadside for 2.5s, then rise above the mast
    # while pulling out to a wide. The last 18 frames decelerate, not zoom in.
    keys=[(1,(-24,-25,4.8),(-1,14,4.8)),
          (55,(-23,-25,6.0),(0,17,4.0)),
          (88,(-24,-28,13.5),(1,20,2.0)),
          (126,(-28,-36,22.5),(2,22,3.0)),
          (144,(-28.5,-37,23),(2,22,3.0))]
    def hermite(frame,index):
        for j in range(len(keys)-1):
            if frame<=keys[j+1][0]: break
        f0,f1=keys[j][0],keys[j+1][0]; dt=f1-f0
        u=max(0,min(1,(frame-f0)/dt))
        p0,p1=Vector(keys[j][index]),Vector(keys[j+1][index])
        m0=Vector((0,0,0)) if j==0 else (p1-Vector(keys[j-1][index]))/(f1-keys[j-1][0])
        m1=Vector((0,0,0)) if j==len(keys)-2 else (Vector(keys[j+2][index])-p0)/(keys[j+2][0]-f0)
        return (2*u**3-3*u*u+1)*p0+(u**3-2*u*u+u)*dt*m0+(-2*u**3+3*u*u)*p1+(u**3-u*u)*dt*m1
    for frame in range(SIM_START,FRAMES+1):
        crane=max(0,min(1,(frame-35)/65))
        camera_data.lens=32-5*crane*crane*(3-2*crane)
        camera_data.keyframe_insert('lens',frame=frame)
        cam.location=hermite(frame,1)
        target=hermite(frame,2)
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.keyframe_insert('location',frame=frame)
        cam.keyframe_insert('rotation_euler',frame=frame)
    return cam


def procedural_mask(name,width,height,fn):
    image=bpy.data.images.new(name,width,height)
    values=array('f')
    for y in range(height):
        for x in range(width):
            v=fn(x/width,y/height)
            values.extend((v,v,v,1))
    image.pixels.foreach_set(values); image.pack()
    return image


def compositor(scene):
    # Blender 5.3 compositor uses a node group and shared shader math/mix nodes.
    ng=bpy.data.node_groups.new('Harbour AE style finishing','CompositorNodeTree')
    ng.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    scene.compositing_node_group=ng
    scene.render.use_compositing=True
    layer=scene.view_layers[0]; layer.use_pass_mist=True
    aov=layer.aovs.add(); aov.name='BackdropMask'; aov.type='VALUE'
    layer.update_render_passes()
    scene.world.mist_settings.start=38; scene.world.mist_settings.depth=130
    scene.world.mist_settings.falloff='QUADRATIC'
    rl=node(ng,'CompositorNodeRLayers','Beauty, mist and backdrop ID'); rl.scene=scene
    def link(a,b): ng.links.new(a,b)
    def mix(name,kind,a,b,factor):
        n=node(ng,'ShaderNodeMix',name); n.data_type='RGBA'; n.blend_type=kind
        for value,sock in [(a,inp(n,'A')),(b,inp(n,'B')),(factor,inp(n,'Factor'))]:
            if isinstance(value,(float,int,tuple)): sock.default_value=value
            else: link(value,sock)
        return next(s for s in n.outputs if s.enabled)
    def mathn(name,op,a,b):
        n=node(ng,'ShaderNodeMath',name); n.operation=op
        for value,sock in zip((a,b),n.inputs):
            if isinstance(value,(float,int)): sock.default_value=value
            else: link(value,sock)
        return n.outputs[0]
    mask=rl.outputs['BackdropMask']
    foreground=mathn('Foreground mask','SUBTRACT',1,mask)
    mist=mathn('Gentle depth haze','MULTIPLY',rl.outputs['Mist'],.24)
    mist=mathn('Keep painted sky colour','MULTIPLY',mist,foreground)
    beauty=mix('Blue parchment distance haze','MIX',rl.outputs['Image'],(.38,.51,.64,1),mist)
    # Shader AOV matte isolates the bright card, blurs its colour across silhouettes,
    # then removes the card itself: a real foreground-edge light wrap.
    isolated=mix('Isolate bright backdrop','MULTIPLY',rl.outputs['Image'],mask,1.0)
    blur=node(ng,'CompositorNodeBlur','Backdrop wrap radius'); setv(blur,'Size',(12,12))
    link(isolated,blur.inputs['Image'])
    wrap=mix('Wrap restricted to foreground','MULTIPLY',blur.outputs[0],foreground,1.0)
    beauty=mix('Light wrap edge add','ADD',beauty,wrap,.055)
    glare=node(ng,'CompositorNodeGlare','Fire and sun bloom'); setv(glare,'Type','Fog Glow')
    setv(glare,'Quality','High'); setv(glare,'Threshold',2.2); setv(glare,'Strength',.30)
    setv(glare,'Size',.25); link(beauty,glare.inputs['Image'])
    # Packed procedural dirt and vignette: no external image dependencies.
    specks=[(RNG.random(),RNG.random(),RNG.uniform(.002,.012),RNG.uniform(.15,.7)) for _ in range(65)]
    def dirt(x,y):
        return min(1,.04+sum(a*max(0,1-((x-sx)**2+(y-sy)**2)/(r*r))**2 for sx,sy,r,a in specks))
    dn=node(ng,'CompositorNodeImage','Procedural lens speckles')
    dn.image=procedural_mask('Procedural lens dirt',960,540,dirt)
    glow_socket=glare.outputs.get('Glare')
    if glow_socket is None:
        raise RuntimeError('Blender compositor must expose the glare-only output')
    dirty=mix('Lens dirt multiplied with glare only','MULTIPLY',glow_socket,dn.outputs['Image'],1.0)
    beauty=mix('Subtle dirty lens halo','ADD',glare.outputs['Image'],dirty,.16)
    grade=node(ng,'CompositorNodeColorBalance','Ivory ochre mineral-blue grade')
    setv(grade,'Lift',(.985,.995,1.01,1)); setv(grade,'Gamma',(1.035,1.0,.96,1))
    setv(grade,'Gain',(1.07,1.025,.94,1)); link(beauty,grade.inputs['Image'])
    kuw=node(ng,'CompositorNodeKuwahara','Anisotropic brush unification')
    setv(kuw,'Type','Anisotropic'); setv(kuw,'Size',6)
    setv(kuw,'Uniformity',3); link(grade.outputs[0],kuw.inputs['Image'])
    beauty=mix('Retain detail under paint pass','MIX',grade.outputs[0],kuw.outputs[0],.90)
    canvas=node(ng,'CompositorNodeImage','Canvas weave at delivery resolution')
    canvas.image=texture_image('canvas.png',data=True)
    beauty=mix('Canvas tooth multiply after oil pass','MULTIPLY',beauty,canvas.outputs['Image'],.70)
    vignette=node(ng,'CompositorNodeImage','Soft elliptical vignette')
    vignette.image=procedural_mask('Procedural vignette',960,540,
        lambda x,y: 1-.22*min(1,((x-.5)/.7)**2+((y-.5)/.7)**2))
    beauty=mix('Vignette multiply','MULTIPLY',beauty,vignette.outputs[0],1.0)
    output=node(ng,'NodeGroupOutput','Finished image'); link(beauty,output.inputs['Image'])
    for i,n in enumerate(ng.nodes): n.location=((i%7)*220,-(i//7)*220)


def build(args):
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.threads_mode='FIXED'; scene.render.threads=6
    scene.render.resolution_x,scene.render.resolution_y=960,540
    scene.render.resolution_percentage=100; scene.render.fps=24
    scene.frame_start,scene.frame_end=1,FRAMES
    scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.color_depth='8'; scene.render.image_settings.compression=15
    scene.render.filepath=str(args.out/'frame_')
    scene.render.use_file_extension=True
    scene.eevee.taa_render_samples=32
    scene.eevee.use_fast_gi=True
    scene.eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY'
    scene.eevee.fast_gi_distance=3
    scene.eevee.shadow_ray_count=3
    scene.eevee.use_volumetric_shadows=True
    scene.eevee.use_raytracing=True
    scene.eevee.ray_tracing_method='SCREEN'
    scene.eevee.volumetric_samples=64
    scene.eevee.volumetric_shadow_samples=16
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.35
    scene.render.compositor_device='CPU'
    mats = {
        'ivory': paint('ivory', IVORY, 'marble', 3.8),
        'ochre': paint('ochre', OCHRE, 'quay', 3.4, (.82,.64,.39,1)),
        'terra': paint('terra', TERRA, 'terracotta', 4.8),
        'blue': paint('blue', BLUE, 'blue_cloth', 1.5),
        'sage': paint('sage', SAGE, 'foliage', 2.6),
        'wood': paint('wood', (.12,.055,.021,1), 'timber', 3.2),
        'stone': paint('stone', (.42,.36,.25,1), 'quay', 4.2),
        'rock': paint('rock', (.42,.36,.25,1), 'rock', 5.5),
        'cloth': paint('cloth', IVORY, 'cloth', 3.8),
        'skin': paint('skin', (.49,.29,.15,1), 'cloth', 1.8, (.78,.55,.36,1)),
    }
    backdrop(); sea(); architecture(mats); ship(mats,args.masters/'cache')
    for x in (-18,15):
        rod('GEO-banner-pole',(x,12.5,1.4),(x,12.5,6.3),.075,mats['wood'])
        rod('GEO-banner-crossbar',(x-.65,12.5,6.1),(x+.65,12.5,6.1),.05,mats['wood'])
        cloth(f'GEO-banner-{x}',1.2,2.4,(x,12.5,6),mats['blue'],args.masters/'cache')
    domain=fire(mats,args.masters/'cache')
    crowds(mats); gulls(mats); lights_camera(scene,mats); compositor(scene)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    # Reject dangerous volumes before evaluation/baking. Never animate their scale.
    for ob in scene.objects:
        if any(mod.type=='FLUID' for mod in ob.modifiers):
            assert min(ob.dimensions)>.1, (ob.name,tuple(ob.dimensions))
            assert all(abs(s-1)<1e-6 for s in ob.scale), ob.name
            assert ob.animation_data is None, ob.name
    return scene,domain


def signature():
    return hashlib.sha256(Path(__file__).read_bytes()+PAINTING.read_bytes()+
                          (TEXTURES/'manifest.json').read_bytes()+
                          bpy.app.version_string.encode()).hexdigest()


def verify_textures():
    """Refuse missing/stale crops instead of silently falling back to toon paint."""
    manifest=TEXTURES/'manifest.json'
    if not manifest.is_file():
        raise RuntimeError(f'Prepare paint_textures.py --out {TEXTURES} before running Blender')
    info=json.loads(manifest.read_text())
    prep=Path(__file__).with_name('paint_textures.py')
    if (info['source_sha256']!=hashlib.sha256(PAINTING.read_bytes()).hexdigest() or
            info['generator_sha256']!=hashlib.sha256(prep.read_bytes()).hexdigest()):
        raise RuntimeError('Painting or texture recipe changed; rerun paint_textures.py')
    for name,expected in info['files'].items():
        path=TEXTURES/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise RuntimeError(f'Missing/changed painting texture: {path}; rerun prep')


def verify_cached_motion(scene, masters):
    """Read evaluated state, not just bake flags; never invoke the renderer."""
    names=('GEO-sail','GEO-banner--18','GEO-banner-15')
    samples=[]
    cloth_positions={name:[] for name in names}
    for frame in (1,48,96,144):
        scene.frame_set(frame)
        dg=bpy.context.evaluated_depsgraph_get()
        dg.update()
        for name in names:
            ob=bpy.data.objects[name].evaluated_get(dg)
            # Local-space bottom centre: excludes the parent ship's motion.
            cloth_positions[name].append(tuple(ob.data.vertices[237].co))
        domain=bpy.data.objects['GEO-Mantaflow-fire-smoke-domain'].evaluated_get(dg)
        density=domain.modifiers[0].domain_settings.density_grid
        maximum=max(density,default=0)
        if maximum<=0:
            raise RuntimeError(f'Empty smoke cache at frame {frame}')
        ocean=bpy.data.objects['GEO-ocean'].evaluated_get(dg)
        if 'foam' not in ocean.data.attributes:
            raise RuntimeError('Ocean foam attribute missing')
        samples.append({'frame':frame,'max_smoke_density':maximum,
                        'camera':list(scene.camera.location)})
    for name,points in cloth_positions.items():
        movement=max((Vector(p)-Vector(points[0])).length for p in points[1:])
        if movement<.02:
            raise RuntimeError(f'Cloth cache did not deform after readback: {name}')
    result={'samples':samples,'cloth_local_bottom_vertices':cloth_positions,
            'verified':'Nonzero smoke, Ocean foam, and cached cloth deformation; no render'}
    (masters/'cache-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    scene.frame_set(1)


def cache_valid(args):
    marker=args.masters/'cache'/'complete.json'
    if not marker.exists(): return False
    try:
        info=json.loads(marker.read_text())
        return (info['signature']==signature() and
                all((args.masters/'cache'/p).is_file() and
                    (args.masters/'cache'/p).stat().st_size==size for p,size in info['files'].items()) and
                bool(info['files']) and (args.masters/'cache'/'baked.blend').is_file())
    except (ValueError,KeyError,OSError): return False


def bake(args, scene, domain):
    cache=args.masters/'cache'; cache.mkdir(parents=True,exist_ok=True)
    marker=cache/'complete.json'; marker.unlink(missing_ok=True)
    started=time.monotonic()
    scene.frame_start=SIM_START
    scene.frame_set(SIM_START)
    # Packed cloth point caches and external Mantaflow grids both live under cache/.
    bpy.ops.wm.save_as_mainfile(filepath=str(cache/'baked.blend'))
    active(domain)
    print(f'BAKE: Mantaflow {GAS_RESOLUTION} voxels + 2x noise, {SIM_START}..144, six workers',flush=True)
    result=bpy.ops.fluid.bake_all()
    if 'FINISHED' not in result or not domain.modifiers[0].domain_settings.has_cache_baked_data:
        raise RuntimeError(f'Mantaflow bake failed: {result}; no completion marker written')
    if not domain.modifiers[0].domain_settings.has_cache_baked_noise:
        raise RuntimeError('Mantaflow noise bake missing; no completion marker written')
    for ob in CLOTH:
        active(ob)
        pc=ob.modifiers['Baked wind cloth'].point_cache
        pc.use_disk_cache=False
        print(f'BAKE: cloth {ob.name}',flush=True)
        scene.frame_set(SIM_START)
        with bpy.context.temp_override(scene=scene,object=ob,active_object=ob,point_cache=pc):
            result=bpy.ops.ptcache.bake(bake=True)
        if 'FINISHED' not in result or not pc.is_baked:
            raise RuntimeError(f'Cloth bake failed: {ob.name}: {result}')
    scene.frame_start=1; scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(cache/'baked.blend'))
    verify_cached_motion(scene,args.masters)
    files={str(p.relative_to(cache)):p.stat().st_size for p in cache.rglob('*')
           if p.is_file() and p.suffix in ('.uni','.vdb')}
    files['baked.blend']=(cache/'baked.blend').stat().st_size
    # Ensure actual frame coverage, not just Blender's bake flag.
    for kind in ('data','noise'):
        fluid=list((cache/'fluid'/kind).glob('*'))
        for f in range(SIM_START,FRAMES+1):
            suffix=f'_{"-" if f<0 else ""}{abs(f):04d}.uni'
            if not any(p.is_file() and p.stat().st_size>0 and p.name.endswith(suffix) for p in fluid):
                raise RuntimeError(f'Missing Mantaflow {kind} cache frame {f}')
    marker.write_text(json.dumps({'signature':signature(),'files':files,
                                 'seconds':round(time.monotonic()-started,2)},indent=2)+'\n')
    # scene.blend remains the reproducible pre-bake scene.
    report_path=args.masters/'scene-report.json'
    report=json.loads(report_path.read_text())
    report['status']='baked, not rendered'
    report['baked_scene']=str(cache/'baked.blend')
    report['bake_seconds']=round(time.monotonic()-started,2)
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(f'BAKE COMPLETE: {time.monotonic()-started:.1f}s',flush=True)


def main():
    global TEXTURES
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--masters',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--frames',default='1-144',help='Inclusive delivery frames, e.g. 1-12')
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--dry-run',action='store_true')
    modes.add_argument('--bake-only',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    try:
        first,last=map(int,args.frames.split('-'))
        if not 1<=first<=last<=FRAMES: raise ValueError
    except ValueError: parser.error('--frames must be an inclusive range within 1-144')
    args.masters=args.masters.resolve(); args.out=args.out.resolve()
    args.masters.mkdir(parents=True,exist_ok=True)
    TEXTURES=args.masters/'textures'
    verify_textures()
    if bpy.app.version < (5,3,0):
        raise RuntimeError('This pilot uses the Blender 5.3 compositor API; use the installed 5.3 build.')
    if not args.dry_run and cache_valid(args):
        print('CACHE: verified existing simulation files; loading baked scene',flush=True)
        bpy.ops.wm.open_mainfile(filepath=str(args.masters/'cache'/'baked.blend'))
        scene=bpy.context.scene
        verify_cached_motion(scene,args.masters)
    else:
        scene,domain=build(args)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.masters/'scene.blend'))
        report={'blender':bpy.app.version_string,'objects':len(scene.objects),
                'resolution':[960,540],'frames':144,'samples':32,'threads':6,
                'cloth':[ob.name for ob in CLOTH],'fluid_resolution':GAS_RESOLUTION,'fluid_noise_scale':2,
                'texture_manifest':str(TEXTURES/'manifest.json'),
                'foam_particles':bpy.data.objects['FX-world-space-foam-particles']['particle_count'],
                'fluid_dimensions':list(domain.dimensions),'simulation_frames':[SIM_START,FRAMES],
                'status':'built, not baked or rendered','source_signature':signature()}
        (args.masters/'scene-report.json').write_text(json.dumps(report,indent=2)+'\n')
        if args.dry_run:
            print('DRY RUN COMPLETE: scene.blend saved; no bake or render.',flush=True)
            return
        bake(args,scene,domain)
    if args.bake_only:
        print('BAKE ONLY COMPLETE: no render.',flush=True)
        return
    # The lead invokes this path outside the sandbox under the external render lock.
    args.out.mkdir(parents=True,exist_ok=True)
    scene.render.threads_mode='FIXED'; scene.render.threads=6
    if scene.camera is None:
        raise RuntimeError('Missing v2 harbour camera; refusing to render')
    for frame in range(first,last+1):
        scene.frame_set(frame)
        scene.render.filepath=str(args.out/f'frame_{frame:04d}.png')
        print(f'RENDER {frame}/{FRAMES}',flush=True)
        bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    main()
