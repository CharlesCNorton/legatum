#!/usr/bin/env python3
"""Procedural Classical harbour VFX blockout. Blender 5.3; no render in --dry-run."""
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
from mathutils import Vector

FRAMES = 144
SIM_START = -23  # One second of wind/fire pre-roll, never delivered.
ROOT = Path(__file__).resolve().parents[4]
PAINTING = ROOT / 'app/src/assets/eras/classical-1920.jpg'
RNG = random.Random(27)
CLOTH = []
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


def paint(name, color):
    """Eevee diffuse -> RGB -> soft paint bands, retaining actual sun shadows."""
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    t = mat.node_tree
    t.nodes.clear()
    diffuse = node(t, 'ShaderNodeBsdfDiffuse', 'Sun and shadow illumination')
    diffuse.inputs['Color'].default_value = (0.8, .8, .8, 1)
    rgb = node(t, 'ShaderNodeShaderToRGB', 'Eevee light into pigment')
    ramp = node(t, 'ShaderNodeValToRGB', 'Soft paint bands')
    ramp.color_ramp.interpolation = 'EASE'
    stops = [(.12, .32), (.36, .68), (.55, .85), (.78, 1.2)]
    for i, (position, amount) in enumerate(stops):
        e = ramp.color_ramp.elements[i] if i < 2 else ramp.color_ramp.elements.new(position)
        e.position = position
        e.color = tuple(min(1, c*amount) for c in color[:3]) + (1,)
    emit = node(t, 'ShaderNodeEmission', 'Paint surface')
    out = node(t, 'ShaderNodeOutputMaterial', 'Output')
    for a, b in [(diffuse.outputs[0], rgb.inputs[0]), (rgb.outputs[0], ramp.inputs[0]),
                 (ramp.outputs[0], emit.inputs[0]), (emit.outputs[0], out.inputs['Surface'])]:
        t.links.new(a, b)
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
    # Explicit crop: ONLY sky and far mountains left of the painted acropolis.
    # Blender pixel rows are bottom-up. No painted boats, buildings or people survive.
    source = bpy.data.images.load(str(PAINTING))
    pixels = array('f', [0]) * (source.size[0]*source.size[1]*4)
    source.pixels.foreach_get(pixels)
    x0, x1, top, bottom = 460, 890, 15, 340
    w, h = x1-x0, bottom-top
    crop = array('f')
    for y in range(source.size[1]-bottom, source.size[1]-top):
        start = (y*source.size[0]+x0)*4
        crop.extend(pixels[start:start+w*4])
    image = bpy.data.images.new('Painting - sky and distant mountains ONLY', w, h)
    image.pixels.foreach_set(crop)
    image.pack()
    bpy.data.images.remove(source)
    mat = emission('Distant painted sky', (1, 1, 1, 1), .9)
    t = mat.node_tree
    tex = node(t, 'ShaderNodeTexImage', 'Upper-left skyline crop')
    tex.image = image
    t.links.new(tex.outputs['Color'], t.nodes['Distant painted sky'].inputs[0])
    aov = node(t, 'ShaderNodeOutputAOV', 'Backdrop light wrap matte')
    aov.aov_name = 'BackdropMask'
    aov.inputs['Value'].default_value = 1
    verts, faces = [], []
    for i in range(41):
        a = math.radians(-65+130*i/40)
        for z in (-5, 85):
            verts.append((130*math.sin(a), 130*math.cos(a), z))
    for i in range(40):
        faces.append((2*i, 2*i+1, 2*i+3, 2*i+2))
    ob = mesh('GEO-curved-sky-and-mountain-card', verts, faces, mat)
    uv = ob.data.uv_layers.new()
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            vi = ob.data.loops[li].vertex_index
            uv.data[li].uv = (vi//2/40, vi % 2)
    ob.pass_index = 1
    ob['source_crop_xy_top_origin'] = [x0, top, x1, bottom]
    return ob


def sea():
    ob = mesh('GEO-ocean', [(0, 0, 0)], [])
    ocean = ob.modifiers.new('Moving ocean and foam vertex layer', 'OCEAN')
    ocean.geometry_mode = 'GENERATE'
    ocean.resolution = 7
    ocean.viewport_resolution = 5
    ocean.spatial_size = 160
    ocean.wave_scale = .62
    ocean.choppiness = .65
    ocean.wind_velocity = 12
    ocean.wave_scale_min = .06
    ocean.use_normals = True
    ocean.use_foam = True
    ocean.foam_layer_name = 'foam'
    ocean.foam_coverage = .28
    ocean.random_seed = 19
    drive(ocean, 'time', None, '2 + frame / 24.0')
    mat = bpy.data.materials.new('Mineral blue water with white crest foam')
    mat.use_nodes = True
    t = mat.node_tree
    bsdf = t.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .22
    bsdf.inputs['IOR'].default_value = 1.333
    attr = node(t, 'ShaderNodeAttribute', 'Ocean foam vertex layer')
    attr.attribute_name = 'foam'
    ramp = node(t, 'ShaderNodeValToRGB', 'Blue water to ivory foam')
    ramp.color_ramp.elements[0].position = .05
    ramp.color_ramp.elements[0].color = BLUE
    ramp.color_ramp.elements[1].position = .55
    ramp.color_ramp.elements[1].color = (.86, .89, .82, 1)
    t.links.new(attr.outputs['Fac'], ramp.inputs[0])
    t.links.new(ramp.outputs[0], bsdf.inputs['Base Color'])
    rough = node(t, 'ShaderNodeMapRange', 'Rougher whitecaps')
    rough.inputs['To Min'].default_value = .22
    rough.inputs['To Max'].default_value = .8
    t.links.new(attr.outputs['Fac'], rough.inputs['Value'])
    t.links.new(rough.outputs[0], bsdf.inputs['Roughness'])
    ob.data.materials.append(mat)
    # Large sea extent, enough for the opening's low horizon.
    ob.location.y = 20
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
    drive(rig, 'location', 0, '-5 + .18*sin(frame*.04)')
    drive(rig, 'location', 1, '-5 + (frame-1)*.038')
    drive(rig, 'location', 2, '.35 + .16*sin(frame*.09)')
    drive(rig, 'rotation_euler', 0, '.025*sin(frame*.09+.5)')
    drive(rig, 'rotation_euler', 1, '.045*sin(frame*.08)')
    drive(rig, 'rotation_euler', 2, '-.12 + .025*sin(frame*.035)')
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
    cube('GEO-deck', (0,0,1.0), (2.1,7.8,.18), mats['ochre'], rig)
    for side in (-1,1):
        rod('GEO-gunwale', (side*1.28,-3.8,1.2), (side*1.28,3.8,1.2), .10, ivory, rig)
        for j in range(12):
            pivot = empty('RIG-oar', (side*1.25,-3.5+j*.62,.65), rig)
            drive(pivot,'rotation_euler',2,f'{side}*(.22+.42*sin(frame*.24))')
            drive(pivot,'rotation_euler',1,f'{side}*(.14+.20*cos(frame*.24))')
            rod('GEO-oar-shaft',(0,0,0),(side*2.5,0,-.15),.045,wood,pivot,8)
            cube('GEO-oar-blade',(side*2.65,0,-.15),(.70,.23,.065),ivory,pivot)
    rod('GEO-mast',(0,.3,1),(0,.3,6.8),.13,wood,rig)
    rod('GEO-yard',(-2.6,.3,6.4),(2.6,.3,6.4),.085,wood,rig)
    cloth('GEO-sail',4.9,3.8,(0,.38,6.35),ivory,cache,rig,pin_tacks=True)
    for side in (-1,1):
        rod('GEO-sail-tack-rope',(side*2.45,.38,2.55),(side*1.2,2,1.2),.025,wood,rig,6)
    rod('GEO-bow-ram',(0,4.7,.1),(0,6.5,.1),.16,mats['ochre'],rig)
    # A spatial foam wake, trailing the stern; analytic ribbons and flecks, not a fluid solve.
    wake_mat = emission('Wake foam',(.63,.76,.73,1),.85)
    for side in (-1,1):
        vs, fs = [], []
        for j in range(30):
            d=j/29
            for edge in (-1,1):
                vs.append((side*(.8+d*2.6)+edge*(.12+.22*d),-5-d*10,.03))
        for j in range(29):
            fs.append((2*j,2*j+1,2*j+3,2*j+2))
        wake=mesh('GEO-foamy-wake-ribbon',vs,fs,wake_mat)
        wake.parent=rig
        wave=wake.modifiers.new('Wake undulation','WAVE')
        wave.use_x=False
        wave.use_y=True
        wave.height=.10
        wave.width=1.2
        wave.speed=.14
        wave.narrowness=2
    for j in range(34):
        side=RNG.choice((-1,1)); d=RNG.uniform(0,9)
        fleck=sphere('GEO-wake-bubbles',(side*(.8+d*.25),-5-d,-.15),(.12,.35,.045),wake_mat,rig)
        drive(fleck,'location',2,f'-.15+.10*sin(frame*.24+{j})')
    return rig


def architecture(m):
    cube('GEO-quay', (0,15,.1), (43,7,2.4),m['stone'])
    cube('GEO-quay-coping',(0,11.6,1.3),(43,.4,.3),m['ivory'])
    for x in range(-20,22,3):
        cube('GEO-pier-joint',(x,11.36,.35),(.08,.07,1.9),m['wood'])
    sphere('GEO-headland',(5,32,1),(19,18,9),m['stone'])
    for j in range(25):
        x,y=RNG.uniform(-12,23),RNG.uniform(19,43)
        sphere('GEO-limestone-rock',(x,y,RNG.uniform(.4,3)),
               (RNG.uniform(1,3),RNG.uniform(1,3),RNG.uniform(2,5)),m['stone'])
    for j in range(12):
        cube('GEO-acropolis-stair',(4,18+j*.64,1.4+j*.59),(7,1.0,.6),m['ivory'])
    for j in range(3):
        cube('GEO-temple-stylobate',(5,32,8.1+j*.35),(14-j*.6,18-j*.6,.4),m['ivory'])
    for x in (-.7,10.7):
        for y in (24.8,27.7,30.6,33.5,36.4,39.3):
            rod('GEO-doric-column',(x,y,9),(x,y,14.5),.40,m['ivory'],vertices=12)
            cube('GEO-doric-capital',(x,y,14.5),(1.05,1.05,.3),m['ivory'])
    for y in (24.8,39.3):
        for x in (1.6,3.9,6.2,8.5):
            rod('GEO-front-column',(x,y,9),(x,y,14.5),.40,m['ivory'],vertices=12)
            cube('GEO-front-capital',(x,y,14.5),(1.05,1.05,.3),m['ivory'])
    cube('GEO-cella',(5,32,11.4),(6.5,10,4.8),m['ochre'])
    cube('GEO-entablature',(5,32,14.9),(13.5,17,.65),m['ivory'])
    roof=mesh('GEO-terracotta-pediment', [(-2,23.3,15.2),(12,23.3,15.2),(5,23.3,18),
             (-2,40.7,15.2),(12,40.7,15.2),(5,40.7,18)],
             [(0,1,2),(5,4,3),(0,3,4,1),(0,2,5,3),(1,4,5,2)],m['terra'])
    for x in (-16,-10,17,22):
        y=22+RNG.uniform(-2,4)
        cube('GEO-harbour-house',(x,y,2.6),(3.5,4,4),m['ivory'])
        cube('GEO-house-roof',(x,y,4.8),(4,4.5,.4),m['terra'])
        for offset in (-.8,.8):
            cube('GEO-house-window',(x+offset,y-2.02,3.1),(.5,.08,.9),m['wood'])
    for j in range(18):
        x,y=RNG.choice((-1,1))*RNG.uniform(10,18)+4,RNG.uniform(22,39)
        rod('GEO-cypress-trunk',(x,y,3),(x,y,7),.16,m['wood'])
        sphere('GEO-cypress',(x,y,7.2),(.8,.85,3.2),m['sage'])


def fire(m, cache):
    cube('GEO-beacon-plinth',(-12,15,2.0),(2,2,1.6),m['stone'])
    rod('GEO-beacon-bowl',(-12,15,2.8),(-12,15,3.3),1.05,m['ochre'])
    for i in range(5):
        rod('GEO-burning-log',(-12.6,14.65+i*.16,3.25),(-11.4,15.35-i*.16,3.5),.12,m['wood'])
    flow=sphere('GEO-fire-smoke-emitter',(-12,15,3.65),(.65,.65,.55))
    mod=flow.modifiers.new('Fire and smoke source','FLUID')
    mod.fluid_type='FLOW'
    fs=mod.flow_settings
    fs.flow_type='BOTH'
    fs.flow_behavior='INFLOW'
    fs.surface_distance=1.5
    fs.fuel_amount=1.4
    fs.density=.8
    fs.use_initial_velocity=True
    fs.velocity_coord=(.2,0,1.1)
    # Transparent surface, while the closed emitter remains present in the solver.
    transparent=bpy.data.materials.new('Invisible fluid emitter surface')
    transparent.use_nodes=True
    t=transparent.node_tree
    t.nodes.clear()
    tr=node(t,'ShaderNodeBsdfTransparent','Transparent')
    out=node(t,'ShaderNodeOutputMaterial','Output')
    t.links.new(tr.outputs[0],out.inputs['Surface'])
    flow.data.materials.append(transparent)
    domain=cube('GEO-Mantaflow-fire-smoke-domain',(-11.3,15,8.1),(6,6,11))
    mod=domain.modifiers.new('48 voxel real billowing gas','FLUID')
    mod.fluid_type='DOMAIN'
    ds=mod.domain_settings
    ds.domain_type='GAS'
    ds.resolution_max=48
    ds.cache_frame_start,ds.cache_frame_end=SIM_START,FRAMES
    ds.cache_type='ALL'
    ds.cache_data_format='UNI'
    ds.cache_directory=str(cache/'fluid')
    ds.use_noise=False
    ds.use_adaptive_domain=False
    ds.vorticity=.7
    ds.flame_vorticity=1.1
    ds.burning_rate=.7
    ds.flame_smoke=.8
    ds.use_dissolve_smoke=True
    ds.dissolve_speed=50
    ds.timesteps_max=2
    ds.effector_weights.wind=.15
    vol=bpy.data.materials.new('Real density and flame grids')
    vol.use_nodes=True
    t=vol.node_tree
    t.nodes.clear()
    p=node(t,'ShaderNodeVolumePrincipled','Mantaflow density and blackbody')
    setv(p,'Color',(.23,.21,.18,1))
    setv(p,'Density',2.0)
    setv(p,'Density Attribute','density')
    setv(p,'Blackbody Intensity',1.5)
    setv(p,'Temperature',1100)
    setv(p,'Temperature Attribute','temperature')
    attr=node(t,'ShaderNodeAttribute','Flame grid')
    attr.attribute_name='flame'
    power=node(t,'ShaderNodeMath','Flame emission strength')
    power.operation='MULTIPLY'
    power.inputs[1].default_value=5
    t.links.new(attr.outputs['Fac'],power.inputs[0])
    t.links.new(power.outputs[0],inp(p,'Emission Strength'))
    setv(p,'Emission Color',(1,.22,.025,1))
    out=node(t,'ShaderNodeOutputMaterial','Volume only output')
    t.links.new(p.outputs['Volume'],out.inputs['Volume'])
    domain.data.materials.append(vol)
    lamp=bpy.data.lights.new('LGT-fire-flicker','POINT')
    lamp.color=(1,.25,.035)
    lamp.energy=650
    lamp.shadow_soft_size=1.1
    lob=bpy.data.objects.new(lamp.name,lamp)
    bpy.context.collection.objects.link(lob)
    lob.location=(-12,15,4)
    drive(lamp,'energy',None,'650+160*sin(frame*.7)+90*sin(frame*1.73)')
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
    pts=[(RNG.uniform(-19,15),RNG.uniform(12.6,16.7),1.36) for _ in range(42)]
    host=mesh('GEO-42-instanced-quay-walkers',pts,[])
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
    world=bpy.data.worlds.new('Mineral blue sky fill'); scene.world=world
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.28,.39,.52,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.55
    sun=bpy.data.lights.new('LGT-warm-upper-left-sun','SUN'); sun.energy=2.6
    sun.color=(1,.84,.61); sun.angle=.12
    ob=bpy.data.objects.new(sun.name,sun); scene.collection.objects.link(ob)
    ob.rotation_euler=(math.radians(28),math.radians(-30),math.radians(-35))
    sphere('GEO-sun-disc',(-28,94,38),(3,1,3),emission('Sun glow',(1,.75,.42,1),6))
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
    camera_data=bpy.data.cameras.new('CAM-water-to-acropolis'); camera_data.lens=26
    camera_data.clip_end=400
    cam=bpy.data.objects.new(camera_data.name,camera_data); scene.collection.objects.link(cam)
    scene.camera=cam
    # Explicit per-frame cubic paths: substantial translation, zero velocity at end.
    # First movement passes ship to its right; last 18 frames ease into destination.
    points=[Vector(p) for p in [(-13,-22,1.7),(-7,-17,2.0),(14,-3,13),(5,9,13.5)]]
    for frame in range(SIM_START,FRAMES+1):
        t=max(0,(frame-1)/(FRAMES-1))
        s=t*t*(3-2*t)
        cam.location=(1-s)**3*points[0]+3*(1-s)**2*s*points[1]+3*(1-s)*s*s*points[2]+s**3*points[3]
        target=Vector((-3,6,4.0)).lerp(Vector((5,31,12.8)),s)
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
    scene.world.mist_settings.start=22; scene.world.mist_settings.depth=100
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
    mist=mathn('Gentle depth haze','MULTIPLY',rl.outputs['Mist'],.30)
    beauty=mix('Blue parchment distance haze','MIX',rl.outputs['Image'],(.55,.63,.68,1),mist)
    # Shader AOV matte isolates the bright card, blurs its colour across silhouettes,
    # then removes the card itself: a real foreground-edge light wrap.
    mask=rl.outputs['BackdropMask']
    isolated=mix('Isolate bright backdrop','MULTIPLY',rl.outputs['Image'],mask,1.0)
    blur=node(ng,'CompositorNodeBlur','Backdrop wrap radius'); setv(blur,'Size',(12,12))
    link(isolated,blur.inputs['Image'])
    foreground=mathn('Foreground mask','SUBTRACT',1,mask)
    wrap=mix('Wrap restricted to foreground','MULTIPLY',blur.outputs[0],foreground,1.0)
    beauty=mix('Light wrap edge add','ADD',beauty,wrap,.18)
    glare=node(ng,'CompositorNodeGlare','Fire and sun bloom'); setv(glare,'Type','Fog Glow')
    setv(glare,'Quality','Low'); setv(glare,'Threshold',1.25); setv(glare,'Strength',.7)
    setv(glare,'Size',.35); link(beauty,glare.inputs['Image'])
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
    setv(grade,'Lift',(.98,1.0,1.015,1)); setv(grade,'Gamma',(1.025,1.0,.97,1))
    setv(grade,'Gain',(1.045,1.02,.96,1)); link(beauty,grade.inputs['Image'])
    kuw=node(ng,'CompositorNodeKuwahara','Anisotropic brush unification')
    setv(kuw,'Type','Anisotropic'); setv(kuw,'Size',2)
    setv(kuw,'Uniformity',2); link(grade.outputs[0],kuw.inputs['Image'])
    beauty=mix('Retain detail under paint pass','MIX',grade.outputs[0],kuw.outputs[0],.45)
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
    scene.eevee.taa_render_samples=12
    scene.eevee.use_raytracing=True
    scene.eevee.ray_tracing_method='SCREEN'
    scene.eevee.volumetric_samples=24
    scene.eevee.volumetric_shadow_samples=8
    scene.view_settings.view_transform='AgX'
    mats={key:paint(key,col) for key,col in {
        'ivory':IVORY,'ochre':OCHRE,'terra':TERRA,'blue':BLUE,'sage':SAGE,
        'wood':(.12,.055,.021,1),'stone':(.42,.36,.25,1),'skin':(.49,.29,.15,1)}.items()}
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
    return hashlib.sha256(Path(__file__).read_bytes()+PAINTING.read_bytes()+bpy.app.version_string.encode()).hexdigest()


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
    print('BAKE: Mantaflow 48 voxels, -23..144, six workers',flush=True)
    result=bpy.ops.fluid.bake_all()
    if 'FINISHED' not in result or not domain.modifiers[0].domain_settings.has_cache_baked_data:
        raise RuntimeError(f'Mantaflow bake failed: {result}; no completion marker written')
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
    fluid=list((cache/'fluid'/'data').glob('*'))
    for f in range(SIM_START,FRAMES+1):
        suffix=f'_{"-" if f<0 else ""}{abs(f):04d}.uni'
        if not any(p.is_file() and p.stat().st_size>0 and p.name.endswith(suffix) for p in fluid):
            raise RuntimeError(f'Missing Mantaflow cache frame {f}')
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
                'resolution':[960,540],'frames':144,'samples':12,'threads':6,
                'cloth':[ob.name for ob in CLOTH],'fluid_resolution':48,
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
    for frame in range(first,last+1):
        scene.frame_set(frame)
        scene.render.filepath=str(args.out/f'frame_{frame:04d}.png')
        print(f'RENDER {frame}/{FRAMES}',flush=True)
        bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    main()
