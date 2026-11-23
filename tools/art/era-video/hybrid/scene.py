#!/usr/bin/env python3
"""Hybrid Classical v5. Python --prepare; Blender 5.3 builds/bakes/renders under lead's lock."""
import os
for _name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS'):
    os.environ[_name] = '6'

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'build_scene.py'
FRAMES, FPS, SIM_START = 144, 24, -47
CAMERA_Z, HEIGHT, WIDTH, RELIEF = 800.0, 200.0, 200 * 16 / 9, 8.0
DOLLY, DRIFT = .16, (12.0, 11.0)
INPUTS = ('painting.png', 'background.png', 'depth-smooth16.png', 'relief.npz',
          'mask-water.png', 'mask-sky.png', 'mask-cloth.png')
# Source-pixel coordinates, at 1920x1080. Keep the original painted ships.
SHIP_START, SHIP_END, SHIP_Y = 825., 400., 550.
SHIP_SCALE, SHIP_Z = 3.65, 32.
FLUID_RESOLUTION, FLUID_SIZE = 72, (24, 52, 16)
FLUID_GRAVITY = (0., -9.81, 0.)  # +Y is picture-up; Z is camera depth.
BANNERS = (
    ((1658, 445, 1710, 539), [(1664,450),(1687,464),(1700,460),(1702,529),(1666,535)]),
    ((1655, 539, 1710, 634), [(1662,548),(1701,542),(1703,619),(1695,626),
                             (1686,621),(1676,628),(1664,619)]),
)
bpy = Vector = base = None  # Imported only by the Blender path, never by preparation.


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smooth(t):
    t = np.clip(t, 0., 1.)
    return t * t * t * (10 + t * (-15 + t * 6))


def timing(frame):
    """Physical dolly; constant cruise with 0.75s ease-in/out, no lens zoom."""
    seconds = np.clip((frame - 1) / FPS, 0, (FRAMES - 1) / FPS)
    duration, ramp = (FRAMES - 1) / FPS, .75
    def integral(q):
        return 2.5*q**4 - 3*q**5 + q**6
    if seconds < ramp:
        distance = ramp * integral(seconds / ramp)
    elif seconds <= duration - ramp:
        distance = seconds - ramp / 2
    else:
        q = (seconds - duration + ramp) / ramp
        distance = duration - 1.5*ramp + ramp*(q - integral(q))
    return float(distance / (duration - ramp)), float(seconds)


def ship_pixel(frame):
    t = np.clip((frame - 1) / (FRAMES - 1), 0, 1)
    return SHIP_START + (SHIP_END - SHIP_START) * t, SHIP_Y


def water_contact_pixel(frame, z=4.):
    """Intersect the current eye-to-ship ray with the shallow painted harbour.

    The ship stands in front of the relief; reusing its original UV would detach
    its wake and reflection during the dolly. No change to the camera itself.
    """
    px, py = ship_pixel(frame)
    ship_xy = np.array(((px/1920-.5)*WIDTH, (.5-py/1080)*HEIGHT))*(CAMERA_Z-SHIP_Z)/CAMERA_Z
    progress, _ = timing(frame)
    camera_xy = np.array(DRIFT)*progress
    camera_z = CAMERA_Z*(1-DOLLY*progress)
    water_xy = camera_xy+(ship_xy-camera_xy)*(camera_z-z)/(camera_z-SHIP_Z)
    uv = water_xy*CAMERA_Z/(CAMERA_Z-z)/np.array((WIDTH, HEIGHT))+.5
    return float(uv[0]*1920), float((1-uv[1])*1080)


def prepare(args):
    """Reproducible Pillow/OpenCV prep; no Blender import, model or network call."""
    from PIL import Image
    import cv2
    cv2.setNumThreads(6)
    plates = args.masters / 'plates'
    plates.mkdir(parents=True, exist_ok=True)
    for name in INPUTS:
        shutil.copy2(args.source / name, plates / name)
    rgb = np.asarray(Image.open(plates / 'painting.png').convert('RGB'))
    if rgb.shape != (1080, 1920, 3):
        raise ValueError('Authored placements require the 1920x1080 Classical painting')
    cloth = np.asarray(Image.open(plates / 'mask-cloth.png'), dtype=np.float32) / 255
    # Two foreground blue banners need moving silhouettes, not just UV shimmer.
    # Lift their actual painted pixels onto cloth meshes; repair only the hidden
    # wall underneath. Original painting.png and all source plates stay intact.
    banner_masks = []
    repair = np.zeros((1080, 1920), np.uint8)
    for _, polygon in BANNERS:
        cut = np.zeros_like(repair)
        cv2.fillPoly(cut, [np.array(polygon)], 255)
        banner_masks.append(cut)
        repair = np.maximum(repair, cut)
    repair = cv2.dilate(repair, np.ones((5,5), np.uint8))
    cloth[repair > 0] = 0
    clean = cv2.inpaint(rgb, repair, 5, cv2.INPAINT_TELEA)
    Image.fromarray(clean).save(plates / 'painting-cloth-clean.png')
    # Keep existing sails/banners. Add the right awning interior, pinning the roof,
    # fringe, poles and outer silhouette rather than dragging architecture with it.
    awning = np.zeros((1080, 1920), np.uint8)
    cv2.fillPoly(awning, [np.array([(1757, 535), (1840, 507), (1919, 479),
                                  (1919, 544), (1840, 556), (1774, 558)])], 1)
    distance = cv2.distanceTransform(awning, cv2.DIST_L2, 5)
    cloth = np.maximum(cloth, smooth((distance - 2) / 12))
    Image.fromarray(np.uint8(cloth * 255)).save(plates / 'mask-cloth.png')
    with np.load(args.source / 'relief.npz') as data:
        depth = data['depth'].copy()
    np.savez_compressed(plates / 'relief.npz', depth=depth,
                       cloth=cv2.resize(cloth, (depth.shape[1], depth.shape[0]),
                                        interpolation=cv2.INTER_AREA))
    # Foreground shoreline/columns hide the galley; the distant lighthouse and
    # hills must NOT hide its sail. This is a visibility matte, not a new plate.
    visible = np.full((1080, 1920), 255, np.uint8)
    shore = [(0, 495), (263, 495), (263, 523), (296, 536), (349, 540),
             (359, 577), (452, 596), (499, 592), (509, 567), (539, 589),
             (596, 574), (665, 574), (704, 580), (749, 576), (776, 548),
             (802, 546), (817, 570), (846, 548), (874, 548), (874, 522),
             (921, 514), (921, 480), (1920, 480), (1920, 1080), (0, 1080)]
    cv2.fillPoly(visible, [np.array(shore)], 0)
    visible[:, :255] = 0  # left foreground colonnade
    visible = cv2.GaussianBlur(visible, (5, 5), .8)
    Image.fromarray(visible).save(plates / 'mask-ship-visible.png')
    textures = args.masters / 'textures'
    textures.mkdir(exist_ok=True)
    for index, ((box, _), mask) in enumerate(zip(BANNERS, banner_masks)):
        # A half-pixel antialiased edge keeps the cutout's painted silhouette.
        rgba = np.dstack((rgb, cv2.GaussianBlur(mask, (3,3), .45)))
        Image.fromarray(rgba).crop(box).save(textures / f'banner-{index}.png')
    crops = {'sail': (609, 461, 656, 510), 'wood': (620, 545, 675, 553)}
    for name, box in crops.items():
        Image.fromarray(rgb).crop(box).save(textures / f'{name}.png')
    y, x = np.mgrid[:540, :960]
    rng = np.random.default_rng(44)
    tooth = np.clip(1 + .012*np.sin(x*2.3)*np.sin(y*2.6)
                    + rng.normal(0, .003, x.shape), .975, 1)
    Image.fromarray(np.uint8(tooth*255)).save(textures / 'canvas.png')
    files = {str(p.relative_to(args.masters)): digest(p)
             for folder in (plates, textures) for p in sorted(folder.iterdir()) if p.is_file()}
    manifest = {'source': str(args.source), 'source_hashes':
                {name: digest(args.source / name) for name in INPUTS},
                'recipe': digest(__file__), 'files': files, 'crops': crops,
                'provenance': 'Existing Legatum Classical painting; LICENSE-ART (CC BY 4.0).',
                'painted_ships': 'Retained; hero galley crosses in front, behind near shore matte.'}
    (args.masters / 'prepared.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Prepared {len(files)} files in {args.masters}; no Blender invoked.')


def node(tree, kind, name):
    result = tree.nodes.new(kind)
    result.name = result.label = name
    return result


def socket(n, name):
    return next(s for s in n.inputs if s.name == name and s.enabled)


def setv(n, name, value):
    # Blender 5.x nodes can expose a float and a colour socket with the same name; pick the one matching the value.
    vector = isinstance(value, (tuple, list))
    for s in n.inputs:
        if s.name == name and s.enabled and hasattr(s, 'default_value'):
            if vector == hasattr(s.default_value, '__len__') and not isinstance(s.default_value, str):
                s.default_value = value
                return
    socket(n, name).default_value = value


def connect(tree, value, target):
    if isinstance(value, (float, int, tuple)):
        target.default_value = value
    else:
        tree.links.new(value, target)


def mathn(tree, operation, a, b=0):
    n = node(tree, 'ShaderNodeMath', operation)
    n.operation = operation
    connect(tree, a, n.inputs[0]); connect(tree, b, n.inputs[1])
    return n.outputs[0]


def image_node(tree, path, uv=None, data=False):
    n = node(tree, 'ShaderNodeTexImage', Path(path).name)
    n.image = bpy.data.images.load(str(path), check_existing=True)
    n.image.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    n.extension = 'EXTEND'
    if uv is not None:
        tree.links.new(uv, n.inputs['Vector'])
    return n


def material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat, mat.node_tree


def aov(tree, value=1):
    output = node(tree, 'ShaderNodeOutputAOV', 'CG-only finishing matte')
    output.aov_name = 'CGMask'
    connect(tree, value, output.inputs['Value'])


def finish_surface(mat, shader, alpha=None):
    tree = mat.node_tree
    out = node(tree, 'ShaderNodeOutputMaterial', 'Surface')
    if alpha is not None:
        mat.surface_render_method = 'DITHERED'
        transparent = node(tree, 'ShaderNodeBsdfTransparent', 'Feather to original painting')
        mix = node(tree, 'ShaderNodeMixShader', 'Masked surface')
        connect(tree, alpha, mix.inputs[0])
        tree.links.new(transparent.outputs[0], mix.inputs[1])
        tree.links.new(shader, mix.inputs[2])
        shader = mix.outputs[0]
    tree.links.new(shader, out.inputs['Surface'])


def plate_material(masters, background=False):
    """Hook for build_scene.relief: crisp, unlit paint, edge-aware repair reveal."""
    mat, tree = material('Crisp repaired plate' if background else 'Crisp source painting')
    uv = node(tree, 'ShaderNodeTexCoord', 'Rest projection').outputs['UV']
    tex = image_node(tree, masters / ('background.png' if background else 'painting-cloth-clean.png'), uv)
    emission = node(tree, 'ShaderNodeEmission', 'Preserve original pigments')
    tree.links.new(tex.outputs['Color'], emission.inputs['Color'])
    alpha = None
    if not background:
        cloth = image_node(tree, masters / 'mask-cloth.png', uv, True).outputs['Color']
        xyz = node(tree, 'ShaderNodeSeparateXYZ', 'Cloth rest coordinates')
        tree.links.new(uv, xyz.inputs[0])
        phase = mathn(tree, 'SUBTRACT', mathn(tree, 'ADD',
                      mathn(tree, 'MULTIPLY', xyz.outputs['X'], 145),
                      mathn(tree, 'MULTIPLY', xyz.outputs['Y'], 65)),
                      mathn(tree, 'MULTIPLY', clock_node(tree), 3.6))
        fold = mathn(tree, 'MULTIPLY', mathn(tree, 'SINE', phase),
                     mathn(tree, 'MULTIPLY', cloth, .24))
        tree.links.new(mathn(tree, 'ADD', 1, fold), emission.inputs['Strength'])
        attr = node(tree, 'ShaderNodeAttribute', 'Stretch opacity')
        attr.attribute_name = 'stretch_opacity'
        amount = node(tree, 'ShaderNodeValue', 'Camera-dependent edge reveal')
        for frame in range(1, FRAMES + 1):
            amount.outputs[0].default_value = timing(frame)[0]
            amount.outputs[0].keyframe_insert('default_value', frame=frame)
        alpha = mathn(tree, 'SUBTRACT', 1, mathn(tree, 'MULTIPLY',
                      mathn(tree, 'SUBTRACT', 1, attr.outputs['Fac']), amount.outputs[0]))
    aov(tree, 0)
    finish_surface(mat, emission.outputs[0], alpha)
    return mat


def clock_node(tree):
    n = node(tree, 'ShaderNodeValue', 'Seconds')
    for frame in range(1, FRAMES + 1):
        n.outputs[0].default_value = (frame - 1) / FPS
        n.outputs[0].keyframe_insert('default_value', frame=frame)
    return n.outputs[0]


def projected(px, py, z):
    return Vector(((px / 1920 - .5) * WIDTH * (CAMERA_Z-z)/CAMERA_Z,
                   (.5 - py / 1080) * HEIGHT * (CAMERA_Z-z)/CAMERA_Z, z))


def sample_depth(depth, px, py):
    # Bilinear sampling avoids tiny steps in the boat's forward travel.
    x, y = px / 1920 * (depth.shape[1]-1), py / 1080 * (depth.shape[0]-1)
    ix, iy = int(x), int(y)
    dx, dy = x-ix, y-iy
    return float((depth[iy, ix]*(1-dx)+depth[iy, ix+1]*dx)*(1-dy)
                 +(depth[iy+1, ix]*(1-dx)+depth[iy+1, ix+1]*dx)*dy) * RELIEF


def water(args, relief):
    """A real tessellated sheet, fitted to the reconstructed harbour, with moving normals.

    The original water remains underneath only as a feather-edge fallback. Rest UVs,
    not the moving camera's coordinates, keep both albedo and the shore attached.
    """
    coords = np.empty((len(relief.data.vertices), 3), np.float32)
    relief.data.vertices.foreach_get('co', coords.ravel())
    old_z = coords[:, 2].copy()
    coords[:, 2] += .10
    coords[:, :2] *= ((CAMERA_Z-coords[:, 2])/(CAMERA_Z-old_z))[:, None]
    # Crop geometry to the mask's authored bounding box; do not duplicate the
    # entire painting mesh or its shape keys for a small patch of harbour.
    with np.load(args.masters/'plates/relief.npz') as data:
        rows,cols=data['depth'].shape
    u,v=np.meshgrid(np.linspace(0,1,cols),np.linspace(1,0,rows))
    uv_array=np.stack((u,v),axis=-1).reshape(-1,2)
    kept=(u>=245/1920)&(u<=845/1920)&(v>=1-610/1080)&(v<=1-340/1080)
    ids=np.flatnonzero(kept.ravel())
    remap=np.full(rows*cols,-1,np.int32); remap[ids]=np.arange(len(ids))
    a=(np.arange(rows-1)[:,None]*cols+np.arange(cols-1)).ravel()
    faces=np.concatenate((np.stack((a,a+cols,a+1),axis=1),
                          np.stack((a+1,a+cols,a+cols+1),axis=1)))
    faces=remap[faces]; faces=faces[np.all(faces>=0,axis=1)]
    mat, tree = material('Harbour pigment with moving ripple normals and glints')
    uv = node(tree, 'ShaderNodeTexCoord', 'Paint projection').outputs['UV']
    color = image_node(tree, args.masters/'plates/painting.png', uv).outputs['Color']
    mask = image_node(tree, args.masters/'plates/mask-water.png', uv, True).outputs['Color']
    time_socket = clock_node(tree)
    sep = node(tree, 'ShaderNodeSeparateXYZ', 'Source pixel coordinates')
    tree.links.new(uv, sep.inputs[0])
    u, v = sep.outputs['X'], sep.outputs['Y']
    # Moving ship centre drives thin interrupted Kelvin-like ripples and contact tone.
    centre = node(tree, 'ShaderNodeValue', 'Sailing ship U')
    waterline = node(tree, 'ShaderNodeValue', 'Projected ship waterline V')
    for frame in range(1, FRAMES+1):
        px, py = water_contact_pixel(frame)
        centre.outputs[0].default_value = px/1920
        waterline.outputs[0].default_value = 1-py/1080
        waterline.outputs[0].keyframe_insert('default_value', frame=frame)
        centre.outputs[0].keyframe_insert('default_value', frame=frame)
    dx = mathn(tree, 'SUBTRACT', u, centre.outputs[0])
    signed_dy = mathn(tree, 'SUBTRACT', waterline.outputs[0], v)
    dy = mathn(tree, 'ABSOLUTE', signed_dy)
    arm = mathn(tree, 'ABSOLUTE', mathn(tree, 'SUBTRACT', dy, mathn(tree, 'MULTIPLY', dx, .20)))
    ridge = mathn(tree, 'MAXIMUM', 0, mathn(tree, 'SUBTRACT', 1, mathn(tree, 'MULTIPLY', arm, 500)))
    trail = mathn(tree, 'MULTIPLY', mathn(tree, 'GREATER_THAN', dx, .065),
                  mathn(tree, 'LESS_THAN', dx, .21))
    decay = mathn(tree, 'MAXIMUM', 0, mathn(tree, 'SUBTRACT', 1, mathn(tree, 'MULTIPLY', dx, 4)))
    noise = node(tree, 'ShaderNodeTexNoise', 'Advected capillary ripples')
    noise.noise_dimensions = '4D'
    setv(noise, 'Scale', 90.); setv(noise, 'Detail', 2.)
    stretch = node(tree, 'ShaderNodeVectorMath', 'Long horizontal wavelets')
    stretch.operation = 'MULTIPLY'
    tree.links.new(uv, stretch.inputs[0]); stretch.inputs[1].default_value = (1, 3, 1)
    tree.links.new(stretch.outputs[0], noise.inputs['Vector'])
    tree.links.new(mathn(tree, 'MULTIPLY', time_socket, .85), noise.inputs['W'])
    wake = mathn(tree, 'MULTIPLY', mathn(tree, 'MULTIPLY', ridge, trail),
                 mathn(tree, 'MULTIPLY', decay, noise.outputs['Fac']))
    bump = node(tree, 'ShaderNodeBump', 'Real time-varying surface normal')
    setv(bump, 'Strength', .52); setv(bump, 'Distance', .20)
    tree.links.new(mathn(tree, 'ADD', noise.outputs['Fac'], wake), bump.inputs['Height'])
    # Emission anchors albedo to the original linear pigment. Gloss adds a restrained
    # moving reflection only; a large diffuse contribution would double-light the art.
    emission = node(tree, 'ShaderNodeEmission', 'Painting water albedo')
    # A deliberately broken painted reflection, anchored to the moving mast.
    # A camera-facing relief sheet cannot produce a useful planar SSR reflection.
    # Mirror the linen silhouette below the waterline, with horizontal ripple gaps.
    jitter = mathn(tree, 'MULTIPLY', mathn(tree, 'SUBTRACT', noise.outputs['Fac'], .5), .009)
    reflection_x = mathn(tree, 'ABSOLUTE', mathn(tree, 'ADD', dx, jitter))
    sail_width = mathn(tree, 'SUBTRACT', .047, mathn(tree, 'MULTIPLY', signed_dy, .3))
    reflection = mathn(tree, 'MULTIPLY', mathn(tree, 'LESS_THAN', reflection_x, sail_width),
                       mathn(tree, 'MULTIPLY', mathn(tree, 'GREATER_THAN', signed_dy, .006),
                             mathn(tree, 'LESS_THAN', signed_dy, .052)))
    ripple_phase = mathn(tree, 'ADD', mathn(tree, 'ADD', mathn(tree, 'MULTIPLY', v, 900),
                        mathn(tree, 'MULTIPLY', noise.outputs['Fac'], 3)),
                        mathn(tree, 'MULTIPLY', time_socket, -5))
    ripple = mathn(tree, 'SINE', ripple_phase)
    reflection = mathn(tree, 'MULTIPLY', reflection,
                       mathn(tree, 'MULTIPLY', mathn(tree, 'GREATER_THAN', ripple, -.15), .36))
    reflected = node(tree, 'ShaderNodeMixRGB', 'Broken ochre linen reflection')
    tree.links.new(reflection, reflected.inputs[0]); tree.links.new(color, reflected.inputs[1])
    reflected.inputs[2].default_value = (.40, .34, .23, 1)
    foam = node(tree, 'ShaderNodeMixRGB', 'Interrupted ivory foam wake')
    tree.links.new(mathn(tree, 'MULTIPLY', wake, 1.3), foam.inputs[0])
    tree.links.new(reflected.outputs[0], foam.inputs[1])
    foam.inputs[2].default_value=(.65,.66,.53,1)
    tree.links.new(foam.outputs[0], emission.inputs['Color'])
    # Broad, moving bands are visible at 960 wide; high-frequency normals alone
    # mostly disappear in antialiasing. Modulate only water, never the painting.
    moving = mathn(tree, 'MULTIPLY', ripple, .13)
    sparkle = mathn(tree, 'MULTIPLY', mathn(tree, 'GREATER_THAN', noise.outputs['Fac'], .64),
                    mathn(tree, 'MULTIPLY', mathn(tree, 'MAXIMUM', ripple, 0), .65))
    ellipse=mathn(tree,'ADD',mathn(tree,'POWER',mathn(tree,'MULTIPLY',dx,13),2),
                  mathn(tree,'POWER',mathn(tree,'MULTIPLY',dy,145),2))
    contact=mathn(tree,'MULTIPLY',mathn(tree,'EXPONENT',mathn(tree,'MULTIPLY',ellipse,-2)),.25)
    luminance=mathn(tree,'ADD',mathn(tree,'SUBTRACT',1,contact),mathn(tree,'MULTIPLY',wake,1.8))
    tree.links.new(mathn(tree, 'ADD', luminance, mathn(tree, 'ADD', moving, sparkle)),
                   emission.inputs['Strength'])
    gloss = node(tree, 'ShaderNodeBsdfGlossy', 'Warm moving sun glints')
    gloss.inputs['Color'].default_value = (.16, .17, .15, 1)
    gloss.inputs['Roughness'].default_value = .22
    tree.links.new(bump.outputs['Normal'], gloss.inputs['Normal'])
    add = node(tree, 'ShaderNodeAddShader', 'Pigment plus glints')
    tree.links.new(emission.outputs[0], add.inputs[0]); tree.links.new(gloss.outputs[0], add.inputs[1])
    aov(tree, mask)
    finish_surface(mat, add.outputs[0], mask)
    ob=base.mesh_object('GEO-depth-fitted-harbour-water',coords[ids].tolist(),
                        faces.tolist(),uv_array[ids],mat)
    for poly in ob.data.polygons:
        poly.use_smooth=True
    return ob


def ship_visibility(args, tree):
    # Ray-project onto the relief at its mean foreground depth. This tracks the
    # shoreline during the push, unlike an unchanging front-projection mask.
    pos = node(tree, 'ShaderNodeNewGeometry', 'World position for shoreline occlusion')
    xyz = node(tree, 'ShaderNodeSeparateXYZ', 'World axes')
    tree.links.new(pos.outputs['Position'], xyz.inputs[0])
    camera = [node(tree, 'ShaderNodeValue', 'Camera '+axis) for axis in 'XYZ']
    for frame in range(1, FRAMES+1):
        progress, _ = timing(frame)
        for n, value in zip(camera, (DRIFT[0]*progress, DRIFT[1]*progress,
                                    CAMERA_Z*(1-DOLLY*progress))):
            n.outputs[0].default_value=value
            n.outputs[0].keyframe_insert('default_value', frame=frame)
    plane_z = 4.
    ratio = mathn(tree, 'DIVIDE', mathn(tree, 'SUBTRACT', camera[2].outputs[0], plane_z),
                  mathn(tree, 'SUBTRACT', camera[2].outputs[0], xyz.outputs['Z']))
    uv = node(tree, 'ShaderNodeCombineXYZ', 'Foreground painting projection')
    for axis, extent, eye in zip('XY', (WIDTH, HEIGHT), camera):
        hit = mathn(tree, 'ADD', eye.outputs[0], mathn(tree, 'MULTIPLY', ratio,
                    mathn(tree, 'SUBTRACT', xyz.outputs[axis], eye.outputs[0])))
        value = mathn(tree, 'ADD', .5,
                      mathn(tree, 'MULTIPLY', hit, CAMERA_Z/(extent*(CAMERA_Z-plane_z))))
        tree.links.new(value, uv.inputs[axis])
    return image_node(tree, args.masters/'plates/mask-ship-visible.png',
                      uv.outputs[0], True).outputs['Color']


def painted_cg(args, name, crop):
    mat, tree = material(name)
    uv = node(tree, 'ShaderNodeTexCoord', 'Rest texture UV').outputs['UV']
    color = image_node(tree, args.masters/'textures'/f'{crop}.png', uv).outputs['Color']
    p = node(tree, 'ShaderNodeBsdfPrincipled', 'Warm daylight on painted pigment')
    tree.links.new(color, p.inputs['Base Color'])
    tree.links.new(color, p.inputs['Emission Color'])
    setv(p, 'Emission Strength', .32); setv(p, 'Roughness', .83)
    setv(p, 'Specular IOR Level', .18)
    alpha = ship_visibility(args, tree)
    aov(tree, alpha); finish_surface(mat, p.outputs[0], alpha)
    return mat


def mesh(name, verts, faces, mat, uv=None, parent=None):
    if uv is None:
        # Stable planar paint coordinates on small timber parts; no Generated swim.
        a = np.asarray(verts)
        axes = np.argsort(np.ptp(a, axis=0))[-2:]
        xy = a[:, axes]
        uv = (xy-xy.min(axis=0))/np.maximum(np.ptp(xy, axis=0), 1e-6)
    ob = base.mesh_object(name, verts, faces, uv, mat)
    ob.parent = parent
    return ob


def empty(name):
    ob = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(ob)
    return ob


def rod(name, a, b, radius, mat, parent):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=radius, radius2=radius*.85,
                                  depth=(b-a).length, location=(a+b)/2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    ob.data.materials.append(mat)
    ob.parent = parent
    return ob


def ship(args, depth):
    wood = painted_cg(args, 'Ship timber sampled from painted hull', 'wood')
    canvas = painted_cg(args, 'Sail sampled from painted linen', 'sail')
    root = empty('GEO-sailing-galley')
    root.scale = (SHIP_SCALE,) * 3
    hull_root = empty('GEO-galley-leftward-heading')
    hull_root.parent = root
    hull_root.rotation_euler.z = math.pi
    # Local X bow/stern, local Y beam, local Z up. A slim rounded hull with a real keel.
    verts, uv, faces = [], [], []
    sections, rings = 28, 12
    for i in range(sections+1):
        t = i/sections
        beam = .08 + 1.08*math.sin(math.pi*t)**.65
        sheer = .30 + .58*abs(2*t-1)**3
        for j in range(rings+1):
            angle = math.pi*j/rings
            verts.append(((t-.5)*14, -beam*math.cos(angle), sheer-1.25*math.sin(angle)))
            uv.append((t, j/rings))
    for i in range(sections):
        for j in range(rings):
            k = i*(rings+1)+j
            faces.append((k,k+1,k+rings+2,k+rings+1))
    hull = mesh('GEO-rounded-planked-hull', verts, faces, wood, uv, hull_root)
    solid = hull.modifiers.new('Real hull thickness', 'SOLIDIFY'); solid.thickness = .10
    for poly in hull.data.polygons:
        poly.use_smooth = True
    mesh('GEO-deck', [(-5,-.85,.18),(5,-.85,.18),(6,0,.30),(5,.85,.18),
                     (-5,.85,.18),(-6,0,.30)], [(0,1,2,3,4,5)], wood, parent=hull_root)
    rod('GEO-mast', (0,0,.20), (0,0,8.0), .10, wood, hull_root)
    rod('GEO-yard', (-4.4,0,7.3), (4.4,0,7.3), .08, wood, hull_root)
    rod('GEO-bow-stay', (6,0,.7), (0,0,7.8), .022, wood, hull_root)
    rod('GEO-stern-stay', (-6,0,.7), (0,0,7.8), .022, wood, hull_root)
    verts, uv, faces = [], [], []
    nx, ny = 24, 16
    for j in range(ny+1):
        v = j/ny
        for i in range(nx+1):
            u = i/nx
            verts.append(((u-.5)*(8.3-.9*v), .75*math.sin(math.pi*u)*math.sin(math.pi*v), 7.25-5.1*v))
            uv.append((u,1-v))
    for j in range(ny):
        for i in range(nx):
            a = j*(nx+1)+i
            faces.append((a,a+1,a+nx+2,a+nx+1))
    sail = mesh('GEO-billowing-linen-sail', verts, faces, canvas, uv, hull_root)
    sail.shape_key_add(name='Basis')
    for mode in range(2):
        key = sail.shape_key_add(name=f'Wind fold {mode+1}'); key.slider_min = -1
        for index, point in enumerate(key.data):
            u, v = uv[index][0], 1-uv[index][1]
            pin = math.sin(math.pi*u) * v
            point.co.y += pin * 1.05 * math.sin(u*math.pi*(mode+2)+v*4)
            point.co.z += pin * .36 * math.sin(u*5+mode)
        for frame in range(1, FRAMES+1):
            key.value = math.sin((frame-1)/FPS*(1.9+mode*.7)+mode*1.4)
            key.keyframe_insert('value', frame=frame)
    solid = sail.modifiers.new('Linen thickness', 'SOLIDIFY'); solid.thickness = .025
    # Independent round shafts and solid narrow blades. Each pivot sweeps and lifts.
    for side in (-1,1):
        for index in range(9):
            pivot = empty(f'GEO-oar-pivot-{side}-{index}')
            pivot.parent = hull_root; pivot.location = (-4.2+index*.95, side*.95, .18)
            rod('GEO-round-oar-shaft', (0,0,0), (0,side*2.5,-.20), .045, wood, pivot)
            blade = mesh('GEO-solid-oar-blade', [(-.11,side*1.95,-.20),(.11,side*1.95,-.20),
                        (.17,side*2.85,-.24),(-.17,side*2.85,-.24)], [(0,1,2,3)], wood, parent=pivot)
            thick = blade.modifiers.new('Solid blade thickness', 'SOLIDIFY'); thick.thickness = .07
            bevel = blade.modifiers.new('Soft blade edge', 'BEVEL'); bevel.width=.025; bevel.segments=2
            for frame in range(1,FRAMES+1):
                phase=(frame-1)/FPS*3.4+index*.045
                pivot.rotation_euler=(side*.15*math.cos(phase),0,side*.36*math.sin(phase))
                pivot.keyframe_insert('rotation_euler',frame=frame)
    ship_splashes(args, hull_root)
    for frame in range(1, FRAMES+1):
        px, py = ship_pixel(frame)
        z = SHIP_Z
        root.location = projected(px, py, z)
        root.rotation_euler = (math.radians(-68)+.008*math.sin(frame*.13),
                               .012*math.sin(frame*.10), .018)
        root.keyframe_insert('location',frame=frame)
        root.keyframe_insert('rotation_euler',frame=frame)
    return root


def ship_splashes(args, parent):
    """Small reusable brush-shaped meshes; no expensive liquid/particle solve."""
    mat, tree = material('Warm ivory bow spray and rowing foam')
    e = node(tree, 'ShaderNodeEmission', 'Sunlit foam pigment')
    setv(e, 'Color', (.70, .69, .56, 1)); setv(e, 'Strength', 1.15)
    alpha = ship_visibility(args, tree)
    aov(tree, alpha); finish_surface(mat, e.outputs[0], alpha)
    # Each oar enters on the same phase as its shaft; short fans lift and fall.
    for side in (-1, 1):
        for index in range(9):
            fan = mesh(f'GEO-oar-splash-{side}-{index}',
                       [(-.45,0,0),(.40,0,0),(.23,side*.22,.32),
                        (0,side*.08,.13),(-.20,side*.16,.24)],
                       [(0,1,2,3,4)], mat, parent=parent)
            for frame in range(1, FRAMES+1):
                phase = (frame-1)/FPS*3.4+index*.045
                pulse = max(0., -math.cos(phase)) ** 3
                fan.location = (-4.2+index*.95-.9*math.sin(phase), side*3.65, -.18)
                fan.scale = (max(.025, pulse),)*3
                fan.keyframe_insert('location', frame=frame)
                fan.keyframe_insert('scale', frame=frame)
    # Droplets peel aft from the bow, not stationary glowing dots. Staggered
    # ballistic arcs form two continuous low fans with a lively broken silhouette.
    rng = np.random.default_rng(52)
    for index in range(36):
        side = (-1, 1)[index % 2]
        spread = float(rng.uniform(.4, 1.2))
        droplet = mesh(f'GEO-bow-spray-{index}',
                       [(-.08,0,0),(.09,0,0),(0,0,.18)], [(0,1,2)], mat, parent=parent)
        for frame in range(1, FRAMES+1):
            age = ((frame-1)/FPS*1.8+index/36) % 1
            droplet.location = (6.7-age*2.5, side*(.3+age*spread),
                                -.12+1.7*age*(1-age))
            size = max(.025, math.sin(math.pi*age))
            droplet.scale = (size,)*3
            droplet.keyframe_insert('location', frame=frame)
            droplet.keyframe_insert('scale', frame=frame)


def cloth_motion(relief):
    # Keep v4's verified geometric displacement. Faster travelling highlight/shadow
    # folds in plate_material make the blue banners and awning visibly breathe
    # without pulling masonry or exceeding the inherited strain/fold checks.
    keys = relief.data.shape_keys.key_blocks
    for mode, key in enumerate(list(keys)[1:]):
        for point, original in zip(key.data, keys[0].data):
            point.co = original.co + (point.co-original.co)*100
        for frame in range(1, FRAMES+1):
            key.value = .90*math.sin((frame-1)/FPS*2.8+mode*1.7)
            key.keyframe_insert('value', frame=frame)
    return [key.name for key in list(keys)[1:]]


def banners(args, depth):
    """Painted cloth cutouts, pinned at the top with freely waving lower edges."""
    for index, (bounds, _) in enumerate(BANNERS):
        x0,y0,x1,y1=bounds
        mat,tree=material(f'Original blue banner pigment {index}')
        uv_socket=node(tree,'ShaderNodeTexCoord','Cloth UV').outputs['UV']
        tex=image_node(tree,args.masters/f'textures/banner-{index}.png',uv_socket)
        e=node(tree,'ShaderNodeEmission','Preserved blue and gold paint')
        tree.links.new(tex.outputs['Color'],e.inputs['Color'])
        aov(tree,tex.outputs['Alpha']); finish_surface(mat,e.outputs[0],tex.outputs['Alpha'])
        verts,uv,faces=[],[],[]
        nx,ny=12,24
        for j in range(ny+1):
            for i in range(nx+1):
                u,v=i/nx,j/ny
                px,py=x0+(x1-x0)*u,y0+(y1-y0)*v
                verts.append(tuple(projected(px,py,sample_depth(depth,px,py)+1.2)))
                uv.append((u,1-v))
        for j in range(ny):
            for i in range(nx):
                a=j*(nx+1)+i; faces.append((a,a+1,a+nx+2,a+nx+1))
        ob=mesh(f'GEO-free-edge-blue-banner-{index}',verts,faces,mat,uv)
        ob.shape_key_add(name='Basis')
        for mode in range(2):
            key=ob.shape_key_add(name=f'Top-pinned wind {mode}'); key.slider_min=-1
            for k,point in enumerate(key.data):
                u,v=uv[k][0],1-uv[k][1]
                pin=v**1.3
                phase=v*4+u*2+mode*1.8
                point.co.x+=pin*(.72 if mode==0 else .30)*math.sin(phase)
                point.co.y+=pin*.12*math.sin(phase+1)
                point.co.z+=pin*.30*math.cos(phase)
            for frame in range(1,FRAMES+1):
                key.value=math.sin((frame-1)/FPS*(3.1+mode*.8)+index+mode*1.6)
                key.keyframe_insert('value',frame=frame)
        for frame in range(1,FRAMES+1):
            e.inputs['Strength'].default_value=1+.13*math.sin((frame-1)/FPS*3.1+index)
            e.inputs['Strength'].keyframe_insert('default_value',frame=frame)


def gulls():
    mat, tree = material('Warm charcoal gull strokes')
    e = node(tree, 'ShaderNodeEmission', 'Distant umber')
    setv(e, 'Color', (.085,.077,.060,1))
    aov(tree); finish_surface(mat,e.outputs[0])
    wing = mesh('GEO-gull-wing-prototype', [(0,0,0),(.5,.22,0),
                (1.3,.06,.03),(.80,-.10,0),(.35,-.06,0)], [(0,1,2,3,4)], mat)
    wing.hide_render = True
    # Source coordinates and world-space sizes, ~11-24px projected wingspans.
    # The seventh gull crosses near the camera at z=160; others cross sky/harbour.
    paths = [(520,130,1180,205,18,1.65), (660,220,1300,155,24,1.8),
             (1260,270,610,210,30,1.65), (410,365,1030,320,22,1.8),
             (1030,390,520,350,35,1.65), (780,115,1480,180,26,2.0),
             (1450,300,480,245,160,2.2)]
    for index, (x0,y0,x1,y1,z,size) in enumerate(paths):
        root=empty(f'GEO-gull-{index}')
        mesh(f'GEO-gull-body-{index}', [(-.12,0,0),(0,.33,0),(.12,0,0),
             (.06,-.33,0),(-.06,-.33,0)], [(0,1,2,3,4)], mat, parent=root)
        for side in (-1,1):
            ob=bpy.data.objects.new(f'GEO-gull-wing-{index}-{side}',wing.data)
            bpy.context.collection.objects.link(ob); ob.parent=root
            ob.scale.x=side
            for frame in range(1,FRAMES+1):
                seconds=(frame-1)/FPS
                # Flap in short bursts, then hold wings open in a readable glide.
                burst=smooth((math.sin(seconds*1.7+index)-.05)*3)
                flap=burst*math.sin(seconds*10.5+index*1.7)
                ob.rotation_euler[1]=side*.70*flap
                ob.rotation_euler[2]=side*(.10+.48*flap)
                ob.keyframe_insert('rotation_euler',frame=frame)
        for frame in range(1,FRAMES+1):
            t=(frame-1)/(FRAMES-1)
            root.location=projected(x0+(x1-x0)*t,y0+(y1-y0)*t+12*math.sin(t*5+index),z)
            root.scale=(size,)*3
            root.rotation_euler.z=.12*math.sin(t*6+index)
            root.keyframe_insert('location',frame=frame)
            root.keyframe_insert('rotation_euler',frame=frame)


def active(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active=ob


def box(name, location, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    ob=bpy.context.object; ob.name=name; ob.scale=size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def fire(args, depth):
    source=projected(390,676,17.0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=source)
    flow=bpy.context.object; flow.name='GEO-brazier-fire-emitter'
    flow.scale=(1.8,1.2,1.6)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=flow.modifiers.new('Real fire and smoke inflow','FLUID'); mod.fluid_type='FLOW'
    fs=mod.flow_settings
    fs.flow_type='BOTH'; fs.flow_behavior='INFLOW'; fs.surface_distance=1.5
    fs.fuel_amount=1.6; fs.temperature=2.0; fs.density=2.2
    fs.use_initial_velocity=True; fs.velocity_coord=(1.2,6.0,0)
    transparent, tree=material('Invisible closed fluid emitter')
    tr=node(tree,'ShaderNodeBsdfTransparent','Emitter surface hidden')
    finish_surface(transparent,tr.outputs[0]); flow.data.materials.append(transparent)
    domain=box('GEO-brazier-Mantaflow-domain',source+Vector((5,23,0)),FLUID_SIZE)
    mod=domain.modifiers.new('72 voxel billowing smoke plus 2x noise','FLUID'); mod.fluid_type='DOMAIN'
    ds=mod.domain_settings; ds.domain_type='GAS'; ds.resolution_max=FLUID_RESOLUTION
    ds.cache_frame_start=SIM_START; ds.cache_frame_end=FRAMES
    ds.cache_type='ALL'; ds.cache_directory=str(args.masters/'cache/fluid')
    ds.cache_data_format='UNI'; ds.cache_noise_format='UNI'
    ds.gravity=FLUID_GRAVITY  # Keep the fallback consistent with scene gravity.
    ds.use_noise=True; ds.noise_scale=2; ds.noise_strength=.5
    # Confinement reinforces existing curl each step. The old 2.5/2.0 settings
    # drove cached velocities above 1500 and flushed the noise plume through
    # open boundaries. Use gentle curl; fuel pulses and wavelets supply detail.
    ds.use_adaptive_domain=False; ds.vorticity=.15; ds.flame_vorticity=.1
    ds.alpha=2.0; ds.beta=3.0; ds.burning_rate=.85; ds.flame_smoke=2.2
    ds.use_dissolve_smoke=True; ds.dissolve_speed=110
    ds.cfl_condition=2.; ds.timesteps_min=1; ds.timesteps_max=6
    # Animate inflow quantities, never domain or emitter transforms. Pulsing
    # density/fuel injects separated billows before the first delivery frame.
    for frame in range(SIM_START, FRAMES+1):
        fs.fuel_amount=1.55+.35*math.sin(frame*.43)+.16*math.sin(frame*1.13)
        fs.density=2.1+.55*math.sin(frame*.17)
        fs.velocity_coord=(1.2+.65*math.sin(frame*.09),6+.9*math.sin(frame*.21),0)
        for prop in ('fuel_amount','density','velocity_coord'):
            fs.keyframe_insert(prop,frame=frame)
    # The set is in camera-projection coordinates: +Y is picture-up. Scene gravity
    # below makes buoyancy rise +Y. Open every side; fade before the +Y boundary.
    for face in ('front','back','left','right','top','bottom'):
        setattr(ds,f'use_collision_border_{face}',False)
    mat,tree=material('Daylit smoke density and blackbody flame grids')
    p=node(tree,'ShaderNodeVolumePrincipled','Smoke is non-emissive except actual flame')
    setv(p,'Color',(.43,.40,.33,1)); setv(p,'Color Attribute','')
    setv(p,'Density Attribute',''); setv(p,'Anisotropy',.18)
    coord=node(tree,'ShaderNodeTexCoord','Local domain position')
    xyz=node(tree,'ShaderNodeSeparateXYZ','Fade before plume ceiling')
    tree.links.new(coord.outputs['Generated'],xyz.inputs[0])
    ceiling=node(tree,'ShaderNodeMapRange','No rectangular smoke cutoff'); ceiling.clamp=True
    setv(ceiling,'From Min',.72); setv(ceiling,'From Max',.98)
    setv(ceiling,'To Min',1.8); setv(ceiling,'To Max',0)
    tree.links.new(xyz.outputs['Y'],ceiling.inputs['Value'])
    density=node(tree,'ShaderNodeAttribute','Smoke density grid'); density.attribute_name='density'
    tree.links.new(mathn(tree,'MULTIPLY',density.outputs['Fac'],ceiling.outputs[0]),
                   socket(p,'Density'))
    flame=node(tree,'ShaderNodeAttribute','Flame grid'); flame.attribute_name='flame'
    heat=node(tree,'ShaderNodeAttribute','Heat grid'); heat.attribute_name='temperature'
    temp=node(tree,'ShaderNodeMapRange','Heat to kelvin'); temp.clamp=True
    setv(temp,'From Min',0); setv(temp,'From Max',1)
    setv(temp,'To Min',1250); setv(temp,'To Max',2050)
    tree.links.new(heat.outputs['Fac'],temp.inputs['Value'])
    bb=node(tree,'ShaderNodeBlackbody','Warm blackbody fire')
    tree.links.new(temp.outputs[0],bb.inputs[0]); tree.links.new(bb.outputs[0],socket(p,'Emission Color'))
    setv(p,'Blackbody Intensity',0)
    power=mathn(tree,'MULTIPLY',mathn(tree,'POWER',flame.outputs['Fac'],1.2),14)
    tree.links.new(power,socket(p,'Emission Strength'))
    out=node(tree,'ShaderNodeOutputMaterial','Volume only')
    tree.links.new(p.outputs['Volume'],out.inputs['Volume']); domain.data.materials.append(mat)
    light=bpy.data.lights.new('LGT-brazier-warmth','POINT')
    light.color=(1,.39,.075); light.shadow_soft_size=1.3
    ob=bpy.data.objects.new(light.name,light); bpy.context.collection.objects.link(ob)
    ob.location=source+Vector((0,1,2))
    for frame in range(1,FRAMES+1):
        light.energy=1800+320*math.sin(frame*.6)+180*math.sin(frame*1.27)
        light.keyframe_insert('energy',frame=frame)
    for ob in (domain,flow):
        assert min(ob.dimensions)>1 and all(abs(s-1)<1e-6 for s in ob.scale)
        assert ob.parent is None and all(abs(r)<1e-6 for r in ob.rotation_euler), \
            'Fluid local Y must remain world/picture up'
        if ob.animation_data and ob.animation_data.action:
            for layer in ob.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        assert all(fc.data_path not in ('scale','location','rotation_euler')
                                   for fc in bag.fcurves), 'Never animate fluid transforms'
    return domain


def lighting_camera(scene):
    scene.world=bpy.data.worlds.new('Cool Mediterranean fill')
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value=(.48,.58,.70,1); bg.inputs['Strength'].default_value=.35
    sun=bpy.data.lights.new('LGT-warm-upper-left-sun','SUN')
    sun.energy=1.5; sun.color=(1,.83,.62); sun.angle=math.radians(9)
    ob=bpy.data.objects.new(sun.name,sun); bpy.context.collection.objects.link(ob)
    ob.rotation_euler=Vector((.6,-.8,-1.4)).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.cameras.new('CAM-harbour-push')
    camera.type='PERSP'; camera.sensor_fit='HORIZONTAL'; camera.sensor_width=36
    camera.lens=36*CAMERA_Z/WIDTH*1.015
    camera.clip_start=.1; camera.clip_end=2000; camera.dof.use_dof=False
    ob=bpy.data.objects.new(camera.name,camera); bpy.context.collection.objects.link(ob)
    scene.camera=ob
    for frame in range(1,FRAMES+1):
        p,_=timing(frame)
        ob.location=(DRIFT[0]*p,DRIFT[1]*p,CAMERA_Z*(1-DOLLY*p))
        ob.keyframe_insert('location',frame=frame)


def compositor(scene,args):
    tree=bpy.data.node_groups.new('Hybrid CG-only pigment finish','CompositorNodeTree')
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    scene.compositing_node_group=tree; scene.render.use_compositing=True
    layer=scene.view_layers[0]
    mask=layer.aovs.add(); mask.name='CGMask'; mask.type='VALUE'; layer.update_render_passes()
    rl=node(tree,'CompositorNodeRLayers','Beauty and surface CG mask'); rl.scene=scene
    def mix(name,kind,a,b,amount):
        n=node(tree,'ShaderNodeMix',name); n.data_type='RGBA'; n.blend_type=kind
        connect(tree,a,socket(n,'A')); connect(tree,b,socket(n,'B'))
        connect(tree,amount,socket(n,'Factor'))
        return next(s for s in n.outputs if s.enabled)
    original=rl.outputs['Image']
    grade=node(tree,'CompositorNodeColorBalance','Warm CG pigments only')
    setv(grade,'Lift',(1,1,1,1)); setv(grade,'Gamma',(1.015,1,.985,1))
    setv(grade,'Gain',(1.015,1,.985,1)); tree.links.new(original,grade.inputs['Image'])
    kuw=node(tree,'CompositorNodeKuwahara','Small CG brush unification')
    setv(kuw,'Type','Anisotropic'); setv(kuw,'Size',2); setv(kuw,'Uniformity',2)
    tree.links.new(grade.outputs[0],kuw.inputs['Image'])
    cg=mix('Only 25 percent filtering','MIX',grade.outputs[0],kuw.outputs[0],.25)
    canvas=node(tree,'CompositorNodeImage','Fixed canvas tooth')
    canvas.image=bpy.data.images.load(str(args.masters/'textures/canvas.png'),check_existing=True)
    canvas.image.colorspace_settings.name='Non-Color'
    cg=mix('Subtle CG canvas grain','MULTIPLY',cg,canvas.outputs['Image'],.30)
    beauty=mix('Keep original painting crisp','MIX',original,cg,rl.outputs['CGMask'])
    # Volumes are intentionally outside the surface AOV: they are naturally soft,
    # never flattened into opaque Kuwahara patches. HDR fire and sun glints bloom.
    glare=node(tree,'CompositorNodeGlare','Restrained fire and sun-glint glare')
    setv(glare,'Type','Fog Glow'); setv(glare,'Quality','High')
    setv(glare,'Threshold',1.2); setv(glare,'Strength',.24); setv(glare,'Size',.18)
    tree.links.new(beauty,glare.inputs['Image'])
    out=node(tree,'NodeGroupOutput','Finished image')
    tree.links.new(glare.outputs['Image'],out.inputs['Image'])


def validate_vfx(scene):
    """Lead-side measurement in the actual built scene, before any fluid bake."""
    from bpy_extras.object_utils import world_to_camera_view
    hull=bpy.data.objects['GEO-rounded-planked-hull']
    root=bpy.data.objects['GEO-sailing-galley']
    samples=[]
    for frame in (1,72,144):
        scene.frame_set(frame); bpy.context.view_layer.update()
        points=[world_to_camera_view(scene,scene.camera,hull.matrix_world @ Vector(p))
                for p in hull.bound_box]
        centre=world_to_camera_view(scene,scene.camera,root.matrix_world.translation)
        samples.append({'frame':frame,'hull_width_px':(max(p.x for p in points)-min(p.x for p in points))*960,
                        'centre_px':[centre.x*960,(1-centre.y)*540]})
    travel=samples[0]['centre_px'][0]-samples[-1]['centre_px'][0]
    assert 144 <= samples[-1]['hull_width_px'] <= 192, samples
    assert 240 <= travel <= 384, samples
    return {'hero_ship_projection':samples,'hero_ship_travel_px':travel,'gulls':7,
            'blue_banner_cutouts':2}


def build(args):
    global base
    bpy.ops.wm.read_factory_settings(use_empty=True)
    spec=importlib.util.spec_from_file_location('hybrid_relief_base',BASE)
    base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
    for key,value in {'FRAMES':FRAMES,'SETTLE':FRAMES,'CAMERA_Z':CAMERA_Z,
                      'HEIGHT':HEIGHT,'WIDTH':WIDTH,'RELIEF':RELIEF,
                      'DOLLY':DOLLY,'DRIFT':DRIFT,'timing':timing,
                      'material':plate_material}.items():
        setattr(base,key,value)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.threads_mode='FIXED'; scene.render.threads=6
    scene.render.resolution_x=960; scene.render.resolution_y=540; scene.render.resolution_percentage=100
    scene.render.fps=FPS; scene.render.fps_base=1
    scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.color_depth='8'; scene.render.image_settings.compression=15
    scene.render.use_sequencer=False; scene.render.compositor_device='CPU'
    scene.eevee.taa_render_samples=32; scene.eevee.use_raytracing=True
    scene.eevee.ray_tracing_method='SCREEN'; scene.eevee.use_volumetric_shadows=True
    scene.eevee.volumetric_samples=96; scene.eevee.volumetric_shadow_samples=16
    # Concentrate froxels around the shallow set over the whole camera move;
    # sampling 0..900 would undersample a ten-unit-thick smoke domain at distance 800.
    scene.eevee.use_volume_custom_range=True
    scene.eevee.volumetric_start=620; scene.eevee.volumetric_end=830
    scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
    scene.view_settings.exposure=0; scene.view_settings.gamma=1
    scene.use_gravity=True; scene.gravity=FLUID_GRAVITY
    scene.frame_start=1; scene.frame_end=FRAMES
    stats=base.relief(args.masters/'plates')
    relief=bpy.data.objects['Continuous painted relief']
    stats['cloth_modes']=cloth_motion(relief)
    water(args,relief)
    with np.load(args.masters/'plates/relief.npz') as data:
        depth=data['depth'].copy()
    ship(args,depth); banners(args,depth); gulls(); domain=fire(args,depth)
    lighting_camera(scene); compositor(scene,args)
    # Original builder hardcodes its old sample frame 145. The last key extrapolates
    # constantly, so this also checks our 144 endpoint with the same geometry.
    stats.update(base.validate_deformation(scene))
    stats.update(validate_vfx(scene))
    scene.frame_set(1); bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    stats.update({'resolution':[960,540],'frames':FRAMES,'fps':FPS,'threads':6,
                  'camera_dolly':DOLLY,'camera_drift':DRIFT,'relief':RELIEF,
                  'simulation_frames':[SIM_START,FRAMES],'fluid_resolution':FLUID_RESOLUTION,
                  'fluid_noise_scale':2,'fluid_dimensions':list(domain.dimensions),
                  'fluid_setup':validate_fluid_axes(scene,domain),
                  'status':'built; not baked or rendered'})
    return scene,domain,stats


def signature(args):
    manifest=json.loads((args.masters/'prepared.json').read_text())
    if manifest['recipe']!=digest(__file__):
        raise RuntimeError('Scene recipe changed: rerun Python --prepare first')
    for path,expected in manifest['files'].items():
        if digest(args.masters/path)!=expected:
            raise RuntimeError(f'Prepared asset changed: {path}; rerun --prepare')
    return hashlib.sha256((digest(__file__)+digest(BASE)+json.dumps(manifest,sort_keys=True)
                           +bpy.app.version_string).encode()).hexdigest()


def cache_valid(args,stamp):
    cache=args.masters/'cache'
    try:
        info=json.loads((cache/'complete.json').read_text())
        return (info['signature']==stamp and bool(info['files']) and
                'baked.blend' in info['files'] and
                all((cache/p).is_file() and (cache/p).stat().st_size==size
                    for p,size in info['files'].items()))
    except (OSError,ValueError,KeyError):
        return False


def validate_fluid_axes(scene,domain):
    """The grid, shader ceiling fade, inflow and buoyancy must share picture-up."""
    ds=domain.modifiers[0].domain_settings
    if not scene.use_gravity or not np.allclose(scene.gravity,FLUID_GRAVITY):
        raise RuntimeError('Hybrid smoke requires scene gravity along -Y (picture down)')
    if not np.allclose(np.asarray(domain.matrix_world)[:3,:3],np.eye(3)):
        raise RuntimeError('Smoke height readback requires an unrotated, unit-scale domain')
    if not np.allclose(domain.dimensions,FLUID_SIZE):
        raise RuntimeError('Smoke domain dimensions differ from the authored grid bounds')
    return {'scene_gravity':list(scene.gravity),'domain_gravity':list(ds.gravity),
            'height_axis':'world Y / grid Y / picture up',
            'vorticity':ds.vorticity,'flame_vorticity':ds.flame_vorticity,
            'noise_strength':ds.noise_strength,'timesteps_max':ds.timesteps_max,
            'preroll_frames':1-SIM_START}


def smoke_spans(density,resolution,size):
    """Occupied centre-to-centre spans in XYZ; Mantaflow X runs fastest."""
    grid=np.asarray(density,dtype=np.float32).reshape(tuple(resolution[::-1]))
    if not np.all(np.isfinite(grid)):
        raise RuntimeError('Non-finite smoke density; inspect simulation stability')
    spans=[]
    for axis in range(3):
        occupied=np.flatnonzero(np.max(grid,axis=tuple(a for a in range(3)
                                                     if a!=2-axis))>.04)
        spans.append(float((occupied[-1]-occupied[0])*size[axis]/resolution[axis])
                     if occupied.size else 0.)
    return spans


def verify_smoke(scene):
    samples=[]
    for frame in (1,48,96,144):
        scene.frame_set(frame)
        dg=bpy.context.evaluated_depsgraph_get(); dg.update()
        domain=bpy.data.objects['GEO-brazier-Mantaflow-domain'].evaluated_get(dg)
        validate_fluid_axes(scene,domain)
        ds=domain.modifiers[0].domain_settings
        density=np.asarray(ds.density_grid[:],dtype=np.float32)
        maximum=float(density.max()) if density.size else 0.
        if maximum<=0:
            raise RuntimeError(f'Empty smoke cache at delivery frame {frame}')
        # RNA returns the noise grid when noise is enabled (not the base grid).
        resolution=np.asarray(ds.domain_resolution,dtype=int)
        if density.size != int(np.prod(resolution)):
            resolution *= ds.noise_scale
        if density.size != int(np.prod(resolution)):
            raise RuntimeError(f'Unexpected density-grid dimensions: {resolution}, {density.size}')
        spans=smoke_spans(density,resolution,domain.dimensions)
        height=spans[1]  # Y is anti-gravity, not Blender's default world Z.
        if height < (8 if frame==1 else 12):
            raise RuntimeError(f'Smoke is only {height:.1f} units tall at frame {frame}; '
                               f'XYZ spans={spans}; inspect cached velocity and vorticity')
        samples.append({'frame':frame,'maximum_density':maximum,
                        'plume_height_units':height,'plume_spans_xyz':spans,
                        'density_grid_resolution':resolution.tolist()})
    scene.frame_set(1)
    return samples


def bake(args,scene,domain,stamp,report):
    cache=args.masters/'cache'; cache.mkdir(exist_ok=True)
    marker=cache/'complete.json'; marker.unlink(missing_ok=True)
    # Only remove this task-owned invalid fluid cache, never source plates or renders.
    if (cache/'fluid').exists():
        shutil.rmtree(cache/'fluid')
    (cache/'fluid').mkdir()
    scene.frame_start=SIM_START; scene.frame_set(SIM_START)
    bpy.ops.wm.save_as_mainfile(filepath=str(cache/'baked.blend'))
    active(domain)
    started=time.monotonic()
    validate_fluid_axes(scene,domain)
    print(f'BAKE: {FLUID_RESOLUTION} voxels + 2x noise, {SIM_START}..{FRAMES}, '
          'six threads, at most six substeps; target <480 seconds',flush=True)
    result=bpy.ops.fluid.bake_all()
    ds=domain.modifiers[0].domain_settings
    if 'FINISHED' not in result or not ds.has_cache_baked_data or not ds.has_cache_baked_noise:
        raise RuntimeError(f'Incomplete fluid bake: {result}')
    for kind in ('data','noise'):
        paths=list((cache/'fluid'/kind).glob('*.uni'))
        for frame in range(SIM_START,FRAMES+1):
            suffix=f'_{"-" if frame<0 else ""}{abs(frame):04d}.uni'
            if not any(p.name.endswith(suffix) and p.stat().st_size>0 for p in paths):
                raise RuntimeError(f'Missing {kind} cache frame {frame}')
    scene.frame_start=1; scene.frame_set(1)
    report['smoke_readback']=verify_smoke(scene)
    bpy.ops.wm.save_as_mainfile(filepath=str(cache/'baked.blend'))
    files={str(p.relative_to(cache)):p.stat().st_size for p in cache.rglob('*.uni')}
    files['baked.blend']=(cache/'baked.blend').stat().st_size
    elapsed=time.monotonic()-started
    marker.write_text(json.dumps({'signature':stamp,'files':files,'seconds':elapsed},indent=2)+'\n')
    report.update(status='baked; not rendered',bake_seconds=round(elapsed,2),
                  bake_target_met=elapsed<=480)
    (args.masters/'scene-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'BAKE COMPLETE: {elapsed:.1f}s; eight-minute target met: {elapsed<=480}',flush=True)


def parse_args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--masters',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,help='Existing classical plates; default: masters sibling/classical')
    p.add_argument('--frames',default='1-144',help='Inclusive global frames, e.g. 1-1 or 72-96')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--prepare',action='store_true',help='Python-only asset preparation; no bpy required')
    mode.add_argument('--dry-run',action='store_true',help='Build/validate/save only, no bake/render')
    mode.add_argument('--bake-only',action='store_true',help='Build and bake or reuse valid cache; no render')
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    args=p.parse_args(argv)
    try:
        args.first,args.last=map(int,args.frames.split('-'))
        if not 1<=args.first<=args.last<=FRAMES:
            raise ValueError
    except ValueError:
        p.error('--frames must be an inclusive range within 1-144')
    args.masters=args.masters.resolve(); args.out=args.out.resolve()
    args.source=(args.source or args.masters.parent/'classical').resolve()
    if args.masters==args.source or args.source in args.masters.parents:
        p.error('Hybrid masters must be separate from the original classical plates')
    return args


def main():
    global bpy,Vector
    args=parse_args()
    args.masters.mkdir(parents=True,exist_ok=True)
    if args.prepare:
        prepare(args); return
    import bpy as blender
    from mathutils import Vector as vector
    bpy,Vector=blender,vector
    if bpy.app.version<(5,3,0):
        raise RuntimeError('This pilot uses the installed Blender 5.3 compositor API')
    stamp=signature(args)
    if not args.dry_run and cache_valid(args,stamp):
        bpy.ops.wm.open_mainfile(filepath=str(args.masters/'cache/baked.blend'))
        scene=bpy.context.scene
        report=json.loads((args.masters/'scene-report.json').read_text())
        report['smoke_readback']=verify_smoke(scene)
        print('CACHE: loaded verified baked scene',flush=True)
    else:
        scene,domain,report=build(args)
        report['source_signature']=stamp; report['blender']=bpy.app.version_string
        bpy.ops.wm.save_as_mainfile(filepath=str(args.masters/'scene.blend'))
        (args.masters/'scene-report.json').write_text(json.dumps(report,indent=2)+'\n')
        if args.dry_run:
            print('DRY RUN: saved scene.blend; no bake or render',flush=True); return
        bake(args,scene,domain,stamp,report)
    if args.bake_only:
        return
    if scene.camera is None:
        raise RuntimeError('No hybrid camera; refusing to render')
    scene.render.threads_mode='FIXED'; scene.render.threads=6
    args.out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    for frame in range(args.first,args.last+1):
        scene.frame_set(frame)
        scene.render.filepath=str(args.out/f'frame_{frame:04d}.png')
        print(f'RENDER {frame}/{FRAMES}',flush=True)
        bpy.ops.render.render(write_still=True)
    report.update(status='rendered requested range; visual review still required',
                  rendered_range=[args.first,args.last],render_seconds=round(time.monotonic()-started,2))
    (args.masters/'scene-report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
