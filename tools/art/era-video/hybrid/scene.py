#!/usr/bin/env python3
"""Hybrid Classical v10. Python --prepare; Blender 5.3 builds/renders under lead's lock."""
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
FRAMES, FPS = 144, 24
PREVIEW_SIZE, FULL_SIZE = (960, 540), (1920, 1080)
CAMERA_Z, HEIGHT, WIDTH, RELIEF = 800.0, 200.0, 200 * 16 / 9, 8.0
DOLLY, DRIFT = .16, (12.0, 11.0)
INPUTS = ('painting.png', 'background.png', 'depth-smooth16.png', 'relief.npz',
          'mask-water.png', 'mask-sky.png', 'mask-cloth.png')
# Source-pixel coordinates, at 1920x1080. Keep the original painted ships.
SHIP_START, SHIP_END, SHIP_Y = 528., 517., 550.
SHIP_Z = 8.  # Visibility lift only; size/contact come from the sampled water depth.
SHIP_RATIO = 1.10
# Hull widths, not sail/mast bounding boxes. The two small ships bound the lane's
# depth. The larger merchant galley is logged separately: different vessel sizes
# coexist at the same y, so one universal width-vs-y curve would be misleading.
SHIP_REFERENCES = (
    ('west-square-sail', (345., 501.), 44.),
    ('near-square-sail', (412., 568.), 56.),
)
PAINTED_GALLEY = ((645., 552.), 145.)
# Conservative source-pixel boxes: hull, mast, sails and oars, including docked
# boats and tiny horizon sails. Inspected on the original painting at 2x.
PAINTED_SHIPS = {
    'horizon-square-sail': (320, 368, 354, 394),
    'distant-lateen-west': (361, 395, 376, 413),
    'distant-lateen-east': (588, 393, 609, 411),
    'small-lateen-by-lighthouse': (362, 419, 381, 438),
    'west-harbour-boats': (282, 450, 325, 484),
    'west-square-sail': (315, 442, 372, 512),
    'near-square-sail': (378, 498, 450, 580),
    'central-small-sail': (490, 462, 544, 504),
    'central-docked-boat': (551, 476, 585, 501),
    'painted-galley': (566, 413, 727, 567),
    'east-docked-masts': (716, 451, 795, 520),
    'east-harbour-boats': (723, 496, 866, 543),
}
HARBOUR_OBSTACLES = {
    'lighthouse-mole': (374, 384, 487, 484),
    'central-quay': (434, 442, 572, 480),
    'near-shore-west': (255, 548, 377, 610),
    'near-shore-lane': (450, 592, 558, 632),
}
# Clip the lower keel; position the root from this exact immersed contact.
SHIP_WATERLINE = -.22
FIRE_Z = 24.
FLAME_LAYERS, SPARK_POOL = 6, 60
BEACON_PIXEL = (680, 350)
BEACON_WIDTH, BEACON_HEIGHT = 9., 25.
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


def ship_placement(depth, frame):
    """Calibrated relief depth -> hull size; immersed contact -> camera-ray lift.

    Relief depth is an artistic disparity, not metres. Calibrate its size curve
    with measured neighbouring hulls instead of treating it as a metric Z map.
    """
    pixel = ship_pixel(frame)
    z = sample_depth(depth, *pixel)
    refs = sorted((sample_depth(depth, *p), width) for _, p, width in SHIP_REFERENCES)
    expected = float(np.interp(z, [r[0] for r in refs], [r[1] for r in refs]))
    hull_width = SHIP_RATIO * expected
    scale = hull_width * WIDTH / 1920 * (CAMERA_Z-SHIP_Z) / CAMERA_Z / 14
    progress, _ = timing(frame)
    eye = np.array((DRIFT[0]*progress,DRIFT[1]*progress,CAMERA_Z*(1-DOLLY*progress)))
    water = project_array(pixel, z+.10)
    contact = eye+(water-eye)*(eye[2]-SHIP_Z)/(eye[2]-water[2])
    offset = rotation_matrix(frame) @ np.array((0., 0., SHIP_WATERLINE*scale))
    return contact-offset, scale, expected, water


def ship_rotation(frame):
    return (math.radians(-68)+.008*math.sin(frame*.13),
            .012*math.sin(frame*.10), .018)


def fire_flicker(frame):
    return 1+.24*math.sin(frame*.61)+.15*math.sin(frame*1.37)+.08*math.sin(frame*2.17)


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
    # Material maps retain the painting's own bristles, with UV-locked folds,
    # sail-panel seams and hull strakes. These are CG textures, never plate edits.
    yy, xx = np.mgrid[:256, :512]
    u, v = xx/511, 1-yy/255
    for name, tint in (('sail', (1.20, 1.28, 1.32)), ('wood', (.72, .56, .37))):
        patch = np.asarray(Image.open(textures/f'{name}.png').resize((512,256),
                           Image.Resampling.LANCZOS), dtype=np.float32)/255
        lum = patch @ np.array((.2126,.7152,.0722))
        bristle = lum-cv2.GaussianBlur(lum,(0,0),3)
        if name == 'sail':
            fold = .96+.13*np.cos(u*31+v*2)+.055*np.cos(u*67-v*4)
            seam = np.exp(-(np.sin(u*math.pi*6)/.095)**2)
            hem = np.exp(-((v-.04)/.018)**2)+np.exp(-((v-.96)/.018)**2)
            shading = fold-.17*seam-.10*hem
        else:
            # UV V runs around the hull: the keel is V=.5, both gunwales V=0/1.
            wet = np.sin(math.pi*v)**4
            seams = np.exp(-(np.sin(v*math.pi*8)/.12)**2)
            shading = 1.12-.48*wet-.17*seams+.10*np.cos(u*5)
        albedo = patch*np.array(tint)*shading[...,None]+bristle[...,None]*.65
        Image.fromarray(np.uint8(np.clip(albedo,0,1)*255)).save(textures/f'{name}.png')
    # Surface-specific spill: faces, robes, bowl and pedestal, not a screen glow.
    spill = np.zeros((1080,1920),np.float32)
    for polygon, strength in (([(204,629),(249,638),(284,705),(267,764),(204,719)],.9),
                              ([(273,701),(322,717),(373,798),(362,883),(305,849)],1.),
                              ([(106,678),(160,674),(201,721),(232,806),(207,847),
                                (144,802),(83,777)],.45),
                              ([(347,672),(430,672),(432,802),(350,802)],.85)):
        patch = np.zeros_like(spill)
        cv2.fillPoly(patch,[np.array(polygon)],strength)
        spill = np.maximum(spill,cv2.GaussianBlur(patch,(0,0),10))
    Image.fromarray(np.uint8(spill*255)).save(textures/'fire-spill.png')
    y, x = np.mgrid[:PREVIEW_SIZE[1], :PREVIEW_SIZE[0]]
    rng = np.random.default_rng(44)
    tooth = np.clip(1 + .012*np.sin(x*2.3)*np.sin(y*2.6)
                    + rng.normal(0, .003, x.shape), .975, 1)
    canvas = Image.fromarray(np.uint8(tooth*255))
    canvas.save(textures / 'canvas.png')
    # The same tooth at twice the pixel density, not a different grain pattern.
    canvas.resize(FULL_SIZE, Image.Resampling.BILINEAR).save(textures / 'canvas-full.png')
    prepare_fire_textures(textures)
    clearance = offline_ship_clearance(depth)
    contact = verify_water_contact(depth, np.asarray(Image.open(plates/'mask-water.png')))
    (args.masters/'scene-report.json').write_text(json.dumps({
        'status': 'prepared; Blender build and visual review pending',
        'bake_required': False, 'ship_clearance': clearance,
        'hero_ship_projection': ship_scale_report(depth),
        'water_contact': contact,
        'flame_cards': FLAME_LAYERS, 'brazier_spark_pool': SPARK_POOL,
        'spark_alive_range': spark_alive_range(),
        'beacon_source_pixel': BEACON_PIXEL,
        'beacon_projection': beacon_report(depth),
        'spark_streak_px_960': [2.8, 4.0],
        'spark_width_px_960': [1.0, 1.35]}, indent=2)+'\n')
    files = {str(p.relative_to(args.masters)): digest(p)
             for folder in (plates, textures) for p in sorted(folder.iterdir()) if p.is_file()}
    manifest = {'source': str(args.source), 'source_hashes':
                {name: digest(args.source / name) for name in INPUTS},
                'recipe': digest(__file__), 'files': files, 'crops': crops,
                'provenance': 'Existing Legatum Classical painting; LICENSE-ART (CC BY 4.0).',
                'painted_ships': PAINTED_SHIPS,
                'procedural_fx': 'Seeded OpenCV pigment strokes; no downloaded textures.'}
    (args.masters / 'prepared.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Prepared {len(files)} files in {args.masters}; no Blender invoked.')


def prepare_fire_textures(textures):
    """Seeded pigment strokes, pointed silhouettes and translucent distant billows."""
    import cv2
    from PIL import Image
    rng=np.random.default_rng(903)
    h,w=384,160
    yy,xx=np.mgrid[:h,:w]; u=xx/(w-1); v=1-yy/(h-1)
    for index in range(FLAME_LAYERS):
        # Curved tapered tongue, with a pinched neck and a wandering fine tip.
        centre=.5+.16*np.sin(v*5+index*1.4)*v+.06*np.sin(v*12+index)*v*v
        half=.34*(1-v)**.78*(.78+.22*np.sin(v*8+index))
        edge=np.clip((half-np.abs(u-centre))*w/1.8,0,1)
        alpha=edge*smooth(v/.045)*(1-smooth((v-.94)/.06))
        distance=np.abs(u-centre)/np.maximum(half,.001)
        core=(1-smooth((distance-.06)/.65))*(1-smooth((v-.18)/.66))
        deep=np.array((.64,.19,.035)); ochre=np.array((.94,.48,.095))
        ivory=np.array((1.,.88,.59))
        pigment=deep+(ochre-deep)*(1-distance.clip(0,1))[...,None]
        pigment=pigment*(1-core[...,None])+ivory*core[...,None]
        # Long bristle marks follow the curl, with broken ochre overpainting.
        bristle=.05*np.sin((u-centre)*190+v*8)+.026*np.sin((u-centre)*470-v*13)
        pigment+=bristle[...,None]
        for _ in range(22):
            t=float(rng.uniform(.08,.84)); off=float(rng.uniform(-.18,.18))
            pts=[]
            for q in np.linspace(t,min(.95,t+float(rng.uniform(.06,.18))),9):
                c=.5+.16*math.sin(q*5+index*1.4)*q+.06*math.sin(q*12+index)*q*q
                pts.append((int((c+off*(1-q))*w),int((1-q)*h)))
            stroke=np.zeros((h,w),np.uint8)
            cv2.polylines(stroke,[np.array(pts)],False,255,int(rng.integers(1,4)),cv2.LINE_AA)
            pigment+=stroke[...,None]/255*float(rng.uniform(-.09,.08))
        rgba=np.dstack((np.clip(pigment,0,1),alpha))
        Image.fromarray(np.uint8(rgba*255),'RGBA').save(textures/f'flame-{index}.png')
    h,w=512,256
    yy,xx=np.mgrid[:h,:w]; u=xx/(w-1); v=1-yy/(h-1)
    body=np.zeros_like(u); light=np.zeros_like(u)
    for i in range(17):
        t=.04+i*.049
        x=.40+.23*t+.065*math.sin(t*16)
        rx=.045+.105*t; ry=.045+.025*t
        lobe=np.exp(-2*((u-x)/rx)**2-2*((v-t)/ry)**2)
        body+=lobe*(.25+.15*math.sin(i*2)**2)
        light+=lobe*(u-x)/rx
    edge=smooth(u/.12)*smooth((1-u)/.12)*smooth(v/.04)*(1-smooth((v-.70)/.27))
    alpha=np.clip(body,0,.66)*edge
    # Cool grey-ochre is already mixed towards distant sky haze, not charcoal.
    rgb=np.empty((h,w,3)); rgb[:]=(.87,.86,.80)
    rgb+=np.clip(light,-.3,.3)[...,None]*.17
    rgb+=(.015*np.sin(u*110+v*27)*np.sin(v*85))[...,None]
    Image.fromarray(np.uint8(np.dstack((np.clip(rgb,0,1),alpha))*255),'RGBA').save(textures/'beacon-plume.png')


def rotation_matrix(frame):
    x,y,z=ship_rotation(frame)
    rx=np.array(((1,0,0),(0,math.cos(x),-math.sin(x)),(0,math.sin(x),math.cos(x))))
    ry=np.array(((math.cos(y),0,math.sin(y)),(0,1,0),(-math.sin(y),0,math.cos(y))))
    rz=np.array(((math.cos(z),-math.sin(z),0),(math.sin(z),math.cos(z),0),(0,0,1)))
    return rz @ ry @ rx


def project_array(pixels, depth):
    pixels=np.asarray(pixels,dtype=float)
    z=np.broadcast_to(depth,pixels.shape[:-1])
    return np.stack(((pixels[...,0]/1920-.5)*WIDTH*(CAMERA_Z-z)/CAMERA_Z,
                     (.5-pixels[...,1]/1080)*HEIGHT*(CAMERA_Z-z)/CAMERA_Z,z),axis=-1)


def screen_array(points, frame, width=960):
    """Matches the unchanged zero-rotation perspective camera, including 1.015 crop."""
    t,_=timing(frame); points=np.asarray(points)
    eye=np.array((DRIFT[0]*t,DRIFT[1]*t,CAMERA_Z*(1-DOLLY*t)))
    focal=width*CAMERA_Z/WIDTH*1.015
    xy=(points[...,:2]-eye[:2])*focal/(eye[2]-points[...,2,None])
    return np.stack((width/2+xy[...,0],width*9/32-xy[...,1]),axis=-1)


def bounds2(points):
    p=np.asarray(points)
    return [float(p[:,0].min()),float(p[:,1].min()),float(p[:,0].max()),float(p[:,1].max())]


def box_clearance(a,b):
    dx=max(a[0]-b[2],b[0]-a[2]); dy=max(a[1]-b[3],b[1]-a[3])
    return math.hypot(max(dx,0),max(dy,0)) if max(dx,dy)>0 else max(dx,dy)


def painted_ship_points(depth):
    result={}
    for name,(x0,y0,x1,y1) in {**PAINTED_SHIPS, **HARBOUR_OBSTACLES}.items():
        # Grid-sample each box, not just its centre: relief parallax varies.
        points=[(x,y) for y in np.linspace(y0,y1,9) for x in np.linspace(x0,x1,9)]
        result[name]=project_array(points,[sample_depth(depth,x,y) for x,y in points])
    return result


def ship_scale_report(depth):
    rows=[]
    hull=np.array([(x,y,z) for x in (-7,7) for y in (-1.16,1.16) for z in (-.95,.88)])
    for frame in range(1,FRAMES+1):
        root,scale,expected,water=ship_placement(depth,frame)
        hull_screen=screen_array((hull*scale) @ rotation_matrix(frame).T+root,frame,1920)
        width=float(np.ptp(hull_screen[:,0]))
        x,y=ship_pixel(frame); z=sample_depth(depth,x,y)
        def painted_width(pixel,span):
            px,py=pixel
            return float(np.ptp(screen_array(project_array(
                [(px-span/2,py),(px+span/2,py)],sample_depth(depth,px,py)),frame,1920)[:,0]))
        reference=painted_width((x,y),expected)
        ratio=width/reference
        if not .9 <= ratio <= 1.2:
            raise RuntimeError(f'Ship depth/scale mismatch at {frame}: {ratio}')
        contact=root+rotation_matrix(frame) @ np.array((0,0,SHIP_WATERLINE*scale))
        error=float(np.linalg.norm(screen_array([contact,water],frame,1920)[0]
                                   -screen_array([contact,water],frame,1920)[1]))
        assert error<.01,error
        rows.append({'frame':frame,'source_waterline_pixel':[x,y],
                     'sampled_relief_depth':z,'world_scale':scale,
                     'waterline_px_1080':screen_array([water],frame,1920)[0].tolist(),
                     'hull_width_px_1080':width,'depth_matched_painted_width_px_1080':reference,
                     'relative_ship_scale':ratio,
                     'near_painted_sailboat_width_px_1080':painted_width(*SHIP_REFERENCES[1][1:]),
                     'ratio_to_near_painted_sailboat':width/painted_width(*SHIP_REFERENCES[1][1:]),
                     'large_painted_galley_width_px_1080':painted_width(*PAINTED_GALLEY),
                     'water_contact_error_px_1080':error})
    return {'method':'small painted hull widths interpolated by sampled relief depth',
            'references':SHIP_REFERENCES,'target_ratio':SHIP_RATIO,
            'ratio_range':[min(r['relative_ship_scale'] for r in rows),max(r['relative_ship_scale'] for r in rows)],
            'samples':[rows[f-1] for f in (1,72,144)],'per_frame':rows}


def beacon_depth(depth):
    # A tall card spans more relief than its base. Keep its entire soft silhouette
    # just ahead of that distant headland, never buried inside the mountains.
    x,y=BEACON_PIXEL
    return max(sample_depth(depth,px,py) for px in np.linspace(x-40,x+60,12)
               for py in np.linspace(y-155,y,20))+.7


def beacon_report(depth):
    anchor=project_array(BEACON_PIXEL,beacon_depth(depth))
    rows=[]
    for frame in (1,72,144):
        # Prepared texture spans 82.8% of its card above effective alpha .08.
        points=screen_array([anchor,anchor+np.array((0,BEACON_HEIGHT*.828,0))],frame)
        rows.append({'frame':frame,'plume_height_px_960':float(abs(points[1,1]-points[0,1]))})
    return {'method':'82.8 percent texture alpha envelope at opacity > .08; visual read pending render','samples':rows}


def verify_water_contact(depth, water_mask):
    """Reject a clear-of-ships route if the waterline actually runs over land."""
    contact_min,reflection_min=255,255
    for frame in range(1,FRAMES+1):
        x,y=ship_pixel(frame)
        _,_,expected,_=ship_placement(depth,frame)
        # Include 4 percent extra for yaw/beam and a 5px-deep contact strip.
        half=expected*SHIP_RATIO*.52
        strip=water_mask[round(y)-2:round(y)+3,round(x-half):round(x+half)+1]
        contact_min=min(contact_min,int(strip.min()))
        reflection_min=min(reflection_min,int(water_mask[round(y):round(y)+15,round(x)].min()))
    if min(contact_min,reflection_min)<230:
        raise RuntimeError(f'Ship contact/reflection leaves water: {contact_min}, {reflection_min}')
    return {'frames_checked':FRAMES,'minimum_water_mask_at_hull':contact_min/255,
            'minimum_water_mask_at_reflection_centre':reflection_min/255,
            'local_keel_z':-.95,'local_immersion_cutoff_z':SHIP_WATERLINE,
            'maximum_projection_error_px_1080':max(r['water_contact_error_px_1080']
                for r in ship_scale_report(depth)['per_frame'])}


def offline_ship_clearance(depth):
    # Conservative bounds include rigging, the full oar sweep, sail deformation,
    # solidify thickness and bow. Live validation additionally checks actual meshes.
    local=np.array([(x,y,z) for x in (-7.7,7.7) for y in (-4.6,4.6) for z in (-1.1,8.4)])
    painted=painted_ship_points(depth)
    rows=[]
    for frame in range(1,FRAMES+1):
        root,scale,_,_=ship_placement(depth,frame)
        world=(local*scale) @ rotation_matrix(frame).T+root
        box=bounds2(screen_array(world,frame))
        checks=[(box_clearance(box,bounds2(screen_array(points,frame))),name)
                for name,points in painted.items()]
        distance,name=min(checks)
        rows.append({'frame':frame,'clearance_px_960':round(distance,3),
                     'nearest_painted_ship':name,'hero_bounds_px_960':box})
    worst=min(rows,key=lambda row:row['clearance_px_960'])
    if worst['clearance_px_960']<3:
        raise RuntimeError(f'Unsafe middle-harbour galley path: {worst}')
    return {'method':'conservative full-ship box vs 12 painted ships, lighthouse mole, quay and near shore; relief and camera projection',
            'frames_checked':FRAMES,'minimum_clearance_px_960':worst['clearance_px_960'],
            'minimum_clearance_px_1080':2*worst['clearance_px_960'],
            'worst_frame':worst['frame'],'nearest_painted_ship':worst['nearest_painted_ship'],
            'per_frame':rows}


def spark_state(index,frame):
    age=((frame-1)/FPS+index/SPARK_POOL*1.9)%1.9
    t=min(age/1.6,1.)
    fade=float(smooth(t/.06)*(1-smooth((t-.84)/.16))) if age<1.6 else 0.
    return age,t,fade


def spark_alive_range():
    counts=[sum(spark_state(i,f)[2]>.25 for i in range(SPARK_POOL)) for f in range(1,FRAMES+1)]
    return [min(counts),max(counts)]


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
        spill = image_node(tree, masters.parent/'textures/fire-spill.png', uv, True)
        pulse = node(tree, 'ShaderNodeValue', 'Brazier flicker on painted scholars')
        for frame in range(1, FRAMES+1):
            pulse.outputs[0].default_value = .24*fire_flicker(frame)
            pulse.outputs[0].keyframe_insert('default_value', frame=frame)
        warm = node(tree, 'ShaderNodeMixRGB', 'Local amber reflected firelight')
        warm.blend_type = 'ADD'
        tree.links.new(mathn(tree,'MULTIPLY',spill.outputs['Color'],pulse.outputs[0]),warm.inputs[0])
        tree.links.new(tex.outputs['Color'],warm.inputs[1])
        warm.inputs[2].default_value = (.34,.105,.018,1)
        tree.links.new(warm.outputs[0],emission.inputs['Color'])
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
        depth=data['depth'].copy()
        rows,cols=data['depth'].shape
    u,v=np.meshgrid(np.linspace(0,1,cols),np.linspace(1,0,rows))
    uv_array=np.stack((u,v),axis=-1).reshape(-1,2)
    kept=(u>=245/1920)&(u<=1040/1920)&(v>=1-610/1080)&(v<=1-340/1080)
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
    effect_scale = node(tree, 'ShaderNodeValue', 'Depth-scaled wake and reflection')
    for frame in range(1, FRAMES+1):
        px, py = ship_pixel(frame)
        _,_,expected,_=ship_placement(depth,frame)
        effect_scale.outputs[0].default_value=3.65/(expected*SHIP_RATIO*WIDTH/1920/14)
        effect_scale.outputs[0].keyframe_insert('default_value',frame=frame)
        centre.outputs[0].default_value = px/1920
        waterline.outputs[0].default_value = 1-py/1080
        waterline.outputs[0].keyframe_insert('default_value', frame=frame)
        centre.outputs[0].keyframe_insert('default_value', frame=frame)
    dx = mathn(tree, 'SUBTRACT', u, centre.outputs[0])
    signed_dy = mathn(tree, 'SUBTRACT', waterline.outputs[0], v)
    # Wake, contact and reflected sail shrink with the hull, not the camera.
    dx = mathn(tree,'MULTIPLY',dx,effect_scale.outputs[0])
    signed_dy = mathn(tree,'MULTIPLY',signed_dy,effect_scale.outputs[0])
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
    setv(bump, 'Strength', .72); setv(bump, 'Distance', .28)
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
                       mathn(tree, 'MULTIPLY', mathn(tree, 'GREATER_THAN', signed_dy, .0005),
                             mathn(tree, 'LESS_THAN', signed_dy, .052)))
    ripple_phase = mathn(tree, 'ADD', mathn(tree, 'ADD', mathn(tree, 'MULTIPLY', v, 900),
                        mathn(tree, 'MULTIPLY', noise.outputs['Fac'], 3)),
                        mathn(tree, 'MULTIPLY', time_socket, -5))
    ripple = mathn(tree, 'SINE', ripple_phase)
    reflection = mathn(tree, 'MULTIPLY', reflection,
                       mathn(tree, 'MULTIPLY', mathn(tree, 'GREATER_THAN', ripple, -.35), .58))
    reflected = node(tree, 'ShaderNodeMixRGB', 'Broken ochre linen reflection')
    tree.links.new(reflection, reflected.inputs[0]); tree.links.new(color, reflected.inputs[1])
    reflected.inputs[2].default_value = (.53, .40, .23, 1)
    foam = node(tree, 'ShaderNodeMixRGB', 'Interrupted ivory foam wake')
    tree.links.new(mathn(tree, 'MULTIPLY', wake, 1.9), foam.inputs[0])
    tree.links.new(reflected.outputs[0], foam.inputs[1])
    foam.inputs[2].default_value=(.65,.66,.53,1)
    tree.links.new(foam.outputs[0], emission.inputs['Color'])
    # Broad, moving bands are visible at 960 wide; high-frequency normals alone
    # mostly disappear in antialiasing. Modulate only water, never the painting.
    moving = mathn(tree, 'MULTIPLY', ripple, .21)
    # Soft thresholds keep bright horizontal crests readable without binary popping.
    crest = node(tree, 'ShaderNodeMapRange', 'Rolling sunlit ripple crests'); crest.clamp=True
    setv(crest, 'From Min', .55); setv(crest, 'From Max', .82)
    tree.links.new(ripple, crest.inputs['Value'])
    breakup = node(tree, 'ShaderNodeMapRange', 'Sparse glint breakup'); breakup.clamp=True
    setv(breakup, 'From Min', .54); setv(breakup, 'From Max', .73)
    tree.links.new(noise.outputs['Fac'], breakup.inputs['Value'])
    sparkle = mathn(tree, 'MULTIPLY', crest.outputs[0], breakup.outputs[0])
    glints = node(tree, 'ShaderNodeMixRGB', 'Ivory light on painted wave crests')
    glints.blend_type = 'ADD'
    tree.links.new(mathn(tree, 'MULTIPLY', sparkle, .48), glints.inputs[0])
    tree.links.new(foam.outputs[0], glints.inputs[1])
    glints.inputs[2].default_value = (.62, .59, .43, 1)
    tree.links.new(glints.outputs[0], emission.inputs['Color'])
    sparkle = mathn(tree, 'MULTIPLY', sparkle, .90)
    ellipse=mathn(tree,'ADD',mathn(tree,'POWER',mathn(tree,'MULTIPLY',dx,13),2),
                  mathn(tree,'POWER',mathn(tree,'MULTIPLY',dy,145),2))
    contact=mathn(tree,'MULTIPLY',mathn(tree,'EXPONENT',mathn(tree,'MULTIPLY',ellipse,-2)),.62)
    luminance=mathn(tree,'ADD',mathn(tree,'SUBTRACT',1,contact),mathn(tree,'MULTIPLY',wake,1.8))
    tree.links.new(mathn(tree, 'ADD', luminance, mathn(tree, 'ADD', moving, sparkle)),
                   emission.inputs['Strength'])
    gloss = node(tree, 'ShaderNodeBsdfGlossy', 'Warm moving sun glints')
    setv(gloss, 'Color', (.23, .24, .21, 1))
    setv(gloss, 'Roughness', .19)
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


def painted_cg(args, name, crop, tint=None):
    mat, tree = material(name)
    uv = node(tree, 'ShaderNodeTexCoord', 'Rest texture UV').outputs['UV']
    color = image_node(tree, args.masters/'textures'/f'{crop}.png', uv).outputs['Color']
    if tint is not None:
        pigment = node(tree, 'ShaderNodeMixRGB', 'Ochre or umber painted detail')
        pigment.blend_type = 'MULTIPLY'; pigment.inputs[0].default_value = 1
        tree.links.new(color,pigment.inputs[1]); pigment.inputs[2].default_value = tint
        color = pigment.outputs[0]
    p = node(tree, 'ShaderNodeBsdfPrincipled', 'Warm daylight on painted pigment')
    tree.links.new(color, p.inputs['Base Color'])
    tree.links.new(color, p.inputs['Emission Color'])
    setv(p, 'Emission Strength', .12); setv(p, 'Roughness', .93)
    setv(p, 'Specular IOR Level', .08)
    bump = node(tree, 'ShaderNodeBump', 'Paint bristles follow the material UV')
    setv(bump,'Strength',.19); setv(bump,'Distance',.035)
    tree.links.new(color,bump.inputs['Height']); tree.links.new(bump.outputs[0],p.inputs['Normal'])
    pigment = node(tree, 'ShaderNodeEmission', 'Preserved painted contrast')
    tree.links.new(color,pigment.inputs['Color'])
    blend = node(tree, 'ShaderNodeMixShader', 'Paint with restrained daylight modelling')
    blend.inputs[0].default_value = .68
    tree.links.new(p.outputs[0],blend.inputs[1]); tree.links.new(pigment.outputs[0],blend.inputs[2])
    alpha = ship_visibility(args, tree)
    local=node(tree,'ShaderNodeTexCoord','Ship local water plane')
    local.object=bpy.data.objects['GEO-sailing-galley']
    xyz=node(tree,'ShaderNodeSeparateXYZ','Keel immersion')
    tree.links.new(local.outputs['Object'],xyz.inputs[0])
    wet=node(tree,'ShaderNodeMapRange','Water occludes the submerged keel'); wet.clamp=True
    setv(wet,'From Min',SHIP_WATERLINE-.06); setv(wet,'From Max',SHIP_WATERLINE+.02)
    tree.links.new(xyz.outputs['Z'],wet.inputs['Value'])
    alpha=mathn(tree,'MULTIPLY',alpha,wet.outputs[0])
    aov(tree, alpha); finish_surface(mat, blend.outputs[0], alpha)
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
    root = empty('GEO-sailing-galley')
    wood = painted_cg(args, 'Ship timber sampled from painted hull', 'wood')
    canvas = painted_cg(args, 'Sail sampled from painted linen', 'sail')
    ochre = painted_cg(args, 'Painted ochre gunwale', 'sail', (.56,.36,.14,1))
    dark = painted_cg(args, 'Tarred umber waterline and eye', 'wood', (.27,.30,.32,1))
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
    # Both sides get a raised gunwale and a dark wet strake: the near side is
    # visible after the heading rotation, and no flat plank silhouette remains.
    for side in (-1,1):
        for band, angle, radius, mat in (('gunwale',.04,.095,ochre),
                                         ('wet-strake',.88,.065,dark)):
            points=[]
            for i in range(sections+1):
                t=i/sections; beam=.08+1.08*math.sin(math.pi*t)**.65
                sheer=.30+.58*abs(2*t-1)**3
                if band=='wet-strake':
                    angle=math.asin((sheer-SHIP_WATERLINE-.055)/1.25)
                points.append(((t-.5)*14,side*(beam*math.cos(angle)+.035),
                               sheer-1.25*math.sin(angle)))
            for a,b in zip(points,points[1:]):
                rod(f'GEO-{band}-{side}',a,b,radius,mat,hull_root)
        # Almond eye follows the tapered bow; inset pupil stays on the exterior.
        for name, span, rise, mat, offset in (('eye',.53,.19,ochre,.04),
                                             ('pupil',.14,.13,dark,.06)):
            verts=[]
            for dx,dz in ((-span,0),(0,rise),(span,0),(0,-rise)):
                x=5.65+dx; t=x/14+.5
                beam=.08+1.08*math.sin(math.pi*t)**.65
                verts.append((x,side*(beam+offset),.16+dz))
            mesh(f'GEO-prow-{name}-{side}',verts,[(0,1,2,3)],mat,parent=hull_root)
    rod('GEO-raised-prow',(6.5,0,.55),(7.25,0,1.55),.14,ochre,hull_root)
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
        location,scale,_,_=ship_placement(depth,frame)
        root.location = location
        root.scale = (scale,)*3
        root.rotation_euler = ship_rotation(frame)
        root.keyframe_insert('location',frame=frame)
        root.keyframe_insert('scale',frame=frame)
        root.keyframe_insert('rotation_euler',frame=frame)
    return root


def ship_splashes(args, parent):
    """Stroke-synchronous foam decals and pooled ballistic spray particles."""
    mat, tree = material('Warm ivory bow spray and rowing foam')
    e = node(tree, 'ShaderNodeEmission', 'Sunlit foam pigment')
    setv(e, 'Color', (.82, .81, .68, 1)); setv(e, 'Strength', 1.25)
    alpha = ship_visibility(args, tree)
    aov(tree, alpha); finish_surface(mat, e.outputs[0], alpha)
    # Project the actual rotated blade tip onto the water. The existing shaft
    # sweep is unchanged; cos(phase)<0 is its downstroke, deepest at phase=pi.
    def tip(side, index, phase):
        rx, rz = side*.15*math.cos(phase), side*.36*math.sin(phase)
        reach = math.cos(rx)*side*2.85 + math.sin(rx)*.24
        return (-4.2+index*.95-math.sin(rz)*reach,
                side*.95+math.cos(rz)*reach, SHIP_WATERLINE+.04)

    for side in (-1, 1):
        for index in range(9):
            fan = mesh(f'GEO-oar-splash-{side}-{index}',
                       [(-.55,0,0),(.50,0,0),(.31,side*.22,.62),
                        (0,side*.08,.20),(-.25,side*.16,.48)],
                       [(0,1,2,3,4)], mat, parent=parent)
            # Broken low rings spread along the surface after each entry.
            verts, faces = [], []
            for segment in range(12):
                if segment in (2, 6, 9):
                    continue
                start = len(verts)
                for angle, radius in ((segment*.524,.52),((segment+1)*.524,.52),
                                      ((segment+1)*.524,.34),(segment*.524,.34)):
                    verts.append((math.cos(angle)*radius, math.sin(angle)*radius*.55, 0))
                faces.append(tuple(range(start,start+4)))
            foam = mesh(f'GEO-oar-whitewater-{side}-{index}', verts, faces, mat, parent=parent)
            for frame in range(1, FRAMES+1):
                phase = (frame-1)/FPS*3.4+index*.045
                pulse = max(0., -math.cos(phase)) ** 2
                fan.location = tip(side,index,phase)
                fan.scale = (pulse,)*3
                fan.keyframe_insert('location', frame=frame)
                fan.keyframe_insert('scale', frame=frame)
                foam.location = fan.location
                foam.scale = (pulse*1.6, pulse*1.4, 1)
                foam.keyframe_insert('location', frame=frame)
                foam.keyframe_insert('scale', frame=frame)
            for particle in range(4):
                drop = mesh(f'GEO-oar-droplet-{side}-{index}-{particle}',
                            [(-.13,0,0),(.13,0,0),(0,0,.29)], [(0,1,2)], mat, parent=parent)
                for frame in range(1,FRAMES+1):
                    phase = (frame-1)/FPS*3.4+index*.045
                    age = ((phase-2.05-particle*.12) % math.tau)/3.4
                    life = .48
                    age_visible = min(age,life)
                    origin = np.array(tip(side,index,2.05+particle*.12))
                    drop.location = origin + np.array(((particle-1.5)*age_visible,
                        side*age_visible*.8, 4.2*age_visible*(1-age_visible/life)))
                    size = float(smooth(age/.06)*(1-smooth((age-.25)/.23))) if age<life else 0.
                    drop.scale = (size,)*3
                    drop.keyframe_insert('location',frame=frame)
                    drop.keyframe_insert('scale',frame=frame)
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
                                SHIP_WATERLINE+.04+1.7*age*(1-age))
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
                point.co.x+=pin*(1.55 if mode==0 else .68)*math.sin(phase)
                point.co.y+=pin*.26*math.sin(phase+1)
                point.co.z+=pin*.65*math.cos(phase)
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
    # Five distant strokes, plus two closer 28-44px open-wing passes.
    paths = [(520,130,1180,205,18,1.65), (660,220,1300,155,24,1.8),
             (1260,270,610,210,30,1.65), (410,365,1030,320,22,1.8),
             (1030,390,520,350,35,1.65), (780,115,1480,180,180,3.1),
             (1450,300,480,245,210,3.5)]
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


def fire_sparks(source):
    """Seeded particle pool: staggered births, buoyant curl, cooling and death.

    Keyed meshes avoid a second simulation cache and legacy particle API changes.
    All ages are absolute, so stills and out-of-order frame renders agree.
    """
    rng = np.random.default_rng(81)
    for index in range(SPARK_POOL):
        mat, tree = material(f'Cooling ember {index:02d}')
        glow = node(tree, 'ShaderNodeEmission', 'Hot ember radiance')
        alpha = node(tree, 'ShaderNodeValue', 'Particle lifetime fade')
        aov(tree,0)
        finish_surface(mat, glow.outputs[0], alpha.outputs[0])
        # Dimensions are compensated per frame to remain 2-4px long at 960.
        radius = .5
        spark = mesh(f'GEO-brazier-spark-{index:02d}',
                     [(-radius,-.28,0),(0,-radius,0),(radius,.28,0),(0,radius,0)],
                     [(0,1,2,3)], mat)
        length_px = float(rng.uniform(2.8,4.0))
        width_px = float(rng.uniform(1.0,1.35))
        # Emerge at the taller flame tips: v9 spent most of the bright lifetime
        # hidden inside the flames, then faded to subpixel orange in the sky.
        origin = np.array((rng.uniform(-3,3),rng.uniform(18,23),rng.uniform(2.5,4)))
        rise, drift = float(rng.uniform(6,10)), float(rng.uniform(1.3,3.5))
        curl = float(rng.uniform(.3,.9))
        for frame in range(1,FRAMES+1):
            age,t,fade=spark_state(index,frame)
            spark.location = np.array(source)+origin+np.array((
                drift*age+curl*(math.sin(age*6+index)-math.sin(index)),
                rise*age-2*age*age, .4*math.sin(age*4+index)))
            progress,_=timing(frame)
            units_per_px=(CAMERA_Z*(1-DOLLY*progress)-spark.location.z)/(960*CAMERA_Z/WIDTH*1.015)
            streak=length_px*units_per_px
            spark.scale = (width_px*units_per_px,streak,1)
            spark.rotation_euler.z=-.12-.10*math.sin(age*4+index)
            spark.keyframe_insert('rotation_euler',frame=frame)
            spark.keyframe_insert('location',frame=frame)
            spark.keyframe_insert('scale',frame=frame)
            setv(glow,'Color',(1., .35*(1-t)+.42, .25*(1-t)+.12, 1))
            setv(glow,'Strength',(5.5+.6*fire_flicker(frame))*(1-.20*t))
            socket(glow,'Color').keyframe_insert('default_value',frame=frame)
            socket(glow,'Strength').keyframe_insert('default_value',frame=frame)
            alpha.outputs[0].default_value=fade
            alpha.outputs[0].keyframe_insert('default_value',frame=frame)


def painted_fx_card(args, name, texture, width, height, source, strength=1., opacity=1.):
    """A pigment surface plus a small additive radiance, never an opaque rectangle."""
    mat, tree = material(name)
    uv = node(tree, 'ShaderNodeTexCoord', 'Painted card coordinates').outputs['UV']
    separate = node(tree, 'ShaderNodeSeparateXYZ', 'Pinned base UV')
    tree.links.new(uv, separate.inputs[0])
    noise = node(tree, 'ShaderNodeTexNoise', 'Slow travelling tongue distortion')
    noise.noise_dimensions = '4D'
    setv(noise, 'Scale', 3.2); setv(noise, 'Detail', 2.)
    tree.links.new(uv, noise.inputs['Vector'])
    tree.links.new(mathn(tree, 'MULTIPLY', clock_node(tree), 1.7), noise.inputs['W'])
    shift = mathn(tree, 'MULTIPLY', mathn(tree, 'SUBTRACT', noise.outputs['Fac'], .5),
                  mathn(tree, 'MULTIPLY', separate.outputs['Y'], .12))
    coords = node(tree, 'ShaderNodeCombineXYZ', 'Curl UV above fixed coals')
    tree.links.new(mathn(tree, 'ADD', separate.outputs['X'], shift), coords.inputs['X'])
    tree.links.new(separate.outputs['Y'], coords.inputs['Y'])
    tex = image_node(tree, args.masters/'textures'/texture, coords.outputs[0])
    tex.extension = 'CLIP'
    alpha = mathn(tree, 'MULTIPLY', tex.outputs['Alpha'], opacity)
    pigment = node(tree, 'ShaderNodeEmission', 'Painted ochre and ivory radiance')
    tree.links.new(tex.outputs['Color'], pigment.inputs['Color'])
    setv(pigment, 'Strength', strength)
    # Keep these authored strokes out of Kuwahara, which joined v8's tongues
    # into a soft blob. The compositor adds a restrained halo above HDR cores.
    aov(tree, 0)
    finish_surface(mat, pigment.outputs[0], alpha)
    if strength > 1.:
        out = next(n for n in tree.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
        surface = out.inputs['Surface'].links[0].from_socket
        extra = node(tree, 'ShaderNodeEmission', 'Small additive flame glow')
        tree.links.new(tex.outputs['Color'], extra.inputs['Color'])
        tree.links.new(mathn(tree, 'MULTIPLY', alpha, .12), extra.inputs['Strength'])
        add = node(tree, 'ShaderNodeAddShader', 'Pigment plus additive flame glow')
        tree.links.new(surface, add.inputs[0]); tree.links.new(extra.outputs[0], add.inputs[1])
        tree.links.new(add.outputs[0], out.inputs['Surface'])
    verts, uvs, faces = [], [], []
    nx, ny = 4, 14
    for j in range(ny+1):
        for i in range(nx+1):
            u, v = i/nx, j/ny
            verts.append(((u-.5)*width, v*height, 0)); uvs.append((u,v))
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i; faces.append((k,k+1,k+nx+2,k+nx+1))
    ob=mesh(name, verts, faces, mat, uvs); ob.location=source
    ob.shape_key_add(name='Basis')
    for mode in range(2):
        key=ob.shape_key_add(name=f'Rising painted curl {mode}'); key.slider_min=-1
        for point, (u,v) in zip(key.data, uvs):
            point.co.x += width*.22*v*v*math.sin(v*6+mode*2)
            point.co.y += height*.09*v*math.sin(v*5+u*3+mode)
        for frame in range(1,FRAMES+1):
            key.value=math.sin(frame*(.19+mode*.07)+width*3+mode)
            key.keyframe_insert('value',frame=frame)
    return ob


def fire(args, depth):
    source=projected(390,676,FIRE_Z)
    # Separate narrow tongues leave holes between their tips; never a broad
    # blurred fire sprite. The rear orange strokes are taller than the cores.
    for index in range(FLAME_LAYERS):
        width=1.5*(3.4,3.0,2.7,2.6,2.3,2.1)[index]
        height=1.5*(12.5,10.2,13.4,8.2,10.5,7.0)[index]
        offset=Vector(((-2.0,1.6,-.4,2.3,-1.1,.6)[index],0,index*.12))
        ob=painted_fx_card(args,f'GEO-painted-flame-{index}',f'flame-{index}.png',
                          width,height,source+offset,1.85,.94)
        for frame in range(1,FRAMES+1):
            ob.scale=(1+.08*math.sin(frame*.31+index),
                      1+.16*math.sin(frame*.27+index*1.7),1)
            ob.keyframe_insert('scale',frame=frame)
    light=bpy.data.lights.new('LGT-brazier-warmth','POINT')
    light.color=(1,.39,.075); light.shadow_soft_size=1.3
    ob=bpy.data.objects.new(light.name,light); bpy.context.collection.objects.link(ob)
    ob.location=source+Vector((0,1,2))
    for frame in range(1,FRAMES+1):
        light.energy=2600*fire_flicker(frame); light.keyframe_insert('energy',frame=frame)
    fire_sparks(source)
    # A small hazed beacon on the right bay's remote headland, behind the CG
    # harbour. No foreground smoke, simulation, pre-roll or bake dependency.
    x,y=BEACON_PIXEL
    z=beacon_depth(depth)
    anchor=projected(x,y,z)
    plume=painted_fx_card(args,'GEO-distant-beacon-plume','beacon-plume.png',
                          BEACON_WIDTH,BEACON_HEIGHT,anchor,1.,.92)
    for frame in range(1,FRAMES+1):
        plume.rotation_euler.z=-.05-.025*math.sin(frame*.035)
        plume.keyframe_insert('rotation_euler',frame=frame)
    painted_fx_card(args,'GEO-distant-beacon-fire','flame-4.png',1.15,1.6,
                    anchor+Vector((0,0,.10)),2.6,.95)


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
    setv(kuw,'Type','Anisotropic'); setv(kuw,'Size',2*args.pixel_scale); setv(kuw,'Uniformity',2)
    tree.links.new(grade.outputs[0],kuw.inputs['Image'])
    cg=mix('Only 25 percent filtering','MIX',grade.outputs[0],kuw.outputs[0],.25)
    canvas=node(tree,'CompositorNodeImage','Fixed canvas tooth')
    canvas.image=bpy.data.images.load(str(args.masters/'textures'/
                                        ('canvas-full.png' if args.full else 'canvas.png')),
                                     check_existing=True)
    canvas.image.colorspace_settings.name='Non-Color'
    cg=mix('Subtle CG canvas grain','MULTIPLY',cg,canvas.outputs['Image'],.30)
    beauty=mix('Keep original painting crisp','MIX',original,cg,rl.outputs['CGMask'])
    # Painted flames and hazed beacon bypass the CG brush blur. HDR cores and
    # sun glints receive the same restrained soft compositor halo as v8.
    glare=node(tree,'CompositorNodeGlare','Restrained fire and sun-glint glare')
    setv(glare,'Type','Fog Glow'); setv(glare,'Quality','High')
    setv(glare,'Threshold',1.2); setv(glare,'Strength',.24); setv(glare,'Size',.18)
    tree.links.new(beauty,glare.inputs['Image'])
    out=node(tree,'NodeGroupOutput','Finished image')
    tree.links.new(glare.outputs['Image'],out.inputs['Image'])


def validate_vfx(scene, depth):
    """Every delivery frame: evaluated meshes vs painted ships under the real camera."""
    from bpy_extras.object_utils import world_to_camera_view
    hull=bpy.data.objects['GEO-rounded-planked-hull']
    root=bpy.data.objects['GEO-sailing-galley']
    width,height=scene.render.resolution_x,scene.render.resolution_y
    pixel_scale=width/PREVIEW_SIZE[0]
    painted=painted_ship_points(depth)
    scale_report=ship_scale_report(depth)
    descendants=[]
    for ob in scene.objects:
        parent=ob.parent
        while parent and parent!=root:
            parent=parent.parent
        if parent==root and ob.type=='MESH':
            descendants.append(ob)
    samples=[]; clearances=[]; projection_error=0.; contact_error=0.
    for frame in range(1,FRAMES+1):
        scene.frame_set(frame); bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get()
        def screen(points):
            projected_points=[world_to_camera_view(scene,scene.camera,Vector(p)) for p in points]
            return np.array([(p.x*width,(1-p.y)*height) for p in projected_points])
        actual=[]
        for ob in descendants:
            evaluated=ob.evaluated_get(dg)
            actual.extend(evaluated.matrix_world @ Vector(p) for p in evaluated.bound_box)
        hero_box=bounds2(screen(actual))
        checks=[]
        for name,points in painted.items():
            actual_screen=screen(points)
            projection_error=max(projection_error,float(np.abs(actual_screen-screen_array(points,frame,width)).max()))
            checks.append((box_clearance(hero_box,bounds2(actual_screen)),name))
        distance,name=min(checks)
        clearances.append({'frame':frame,'minimum_clearance_px':round(distance,3),
                           'nearest_painted_ship':name,'hero_bounds_px':hero_box})
        if distance<3*pixel_scale:
            raise RuntimeError(f'Galley clearance below 3 preview pixels at {frame}: {distance}px vs {name}')
        points=screen([hull.matrix_world @ Vector(p) for p in hull.bound_box])
        hull_width=float(np.ptp(points[:,0]))
        reference_width=scale_report['per_frame'][frame-1]['depth_matched_painted_width_px_1080']*width/1920
        ratio=hull_width/reference_width
        assert .9<=ratio<=1.2,(frame,hull_width,reference_width,ratio)
        _,_,_,water_point=ship_placement(depth,frame)
        actual_contact=screen([root.matrix_world @ Vector((0,0,SHIP_WATERLINE))])[0]
        contact_error=max(contact_error,float(np.linalg.norm(actual_contact-screen([water_point])[0])))
        if frame in (1,72,144):
            centre=screen([root.matrix_world.translation])[0]
            samples.append({'frame':frame,'hull_width_px':hull_width,
                            'depth_matched_painted_width_px':reference_width,
                            'relative_ship_scale':ratio,'centre_px':centre.tolist()})
    # Confirm that Python-only projection measurements match Blender before
    # accepting them. No render or simulation is involved in either check.
    assert projection_error<.05,projection_error
    assert contact_error<.05,contact_error
    worst=min(clearances,key=lambda row:row['minimum_clearance_px'])
    assert not any(mod.type=='FLUID' for ob in scene.objects for mod in ob.modifiers)
    return {'hero_ship_projection':samples,
            'depth_scale_calibration':scale_report,
            'water_contact_error_px':contact_error,
            'hero_ship_travel_px':samples[0]['centre_px'][0]-samples[-1]['centre_px'][0],
            'ship_clearance':{'method':'evaluated descendant mesh boxes vs painted ship boxes',
                              'frames_checked':FRAMES,'resolution':[width,height],
                              'minimum_clearance_px':worst['minimum_clearance_px'],
                              'worst_frame':worst['frame'],'nearest_painted_ship':worst['nearest_painted_ship'],
                              'projection_error_px':projection_error,'per_frame':clearances},
            'gulls':7,'blue_banner_cutouts':2,'brazier_spark_pool':SPARK_POOL,
            'spark_alive_range':spark_alive_range(),'spark_streak_px_960':[2.8,4.0],
            'spark_width_px_960':[1.0,1.35],
            'flame_cards':FLAME_LAYERS,'beacon_source_pixel':BEACON_PIXEL,
            'beacon_projection':beacon_report(depth),
            'oar_spray_particles':72}


def configure_output(scene,args):
    """Apply output-only settings even when reusing a differently sized scene.

    Camera, source-pixel shore polygons, UV masks and animation stay in their
    original 1920x1080 authoring space. Only raster-sized finishing scales.
    """
    scene.render.resolution_x,scene.render.resolution_y=args.width,args.height
    scene.render.resolution_percentage=100
    tree=scene.compositing_node_group
    if tree is not None:
        setv(tree.nodes['Small CG brush unification'],'Size',2*args.pixel_scale)
        texture='canvas-full.png' if args.full else 'canvas.png'
        canvas=tree.nodes['Fixed canvas tooth']
        canvas.image=bpy.data.images.load(str(args.masters/'textures'/texture),check_existing=True)
        canvas.image.colorspace_settings.name='Non-Color'


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
    configure_output(scene,args)
    scene.render.fps=FPS; scene.render.fps_base=1
    scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.color_depth='8'; scene.render.image_settings.compression=15
    scene.render.use_sequencer=False; scene.render.compositor_device='CPU'
    scene.eevee.taa_render_samples=32; scene.eevee.use_raytracing=True
    scene.eevee.ray_tracing_method='SCREEN'
    scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
    scene.view_settings.exposure=0; scene.view_settings.gamma=1
    scene.frame_start=1; scene.frame_end=FRAMES
    stats=base.relief(args.masters/'plates')
    relief=bpy.data.objects['Continuous painted relief']
    stats['cloth_modes']=cloth_motion(relief)
    water(args,relief)
    with np.load(args.masters/'plates/relief.npz') as data:
        depth=data['depth'].copy()
    ship(args,depth); banners(args,depth); gulls(); fire(args,depth)
    lighting_camera(scene); compositor(scene,args)
    # Original builder hardcodes its old sample frame 145. The last key extrapolates
    # constantly, so this also checks our 144 endpoint with the same geometry.
    stats.update(base.validate_deformation(scene))
    stats.update(validate_vfx(scene,depth))
    scene.frame_set(1); bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    stats.update({'resolution':[args.width,args.height],'frames':FRAMES,'fps':FPS,'threads':6,
                  'camera_dolly':DOLLY,'camera_drift':DRIFT,'relief':RELIEF,
                  'bake_required':False, 'status':'built; not rendered'})
    return scene,stats


def signature(args):
    manifest=json.loads((args.masters/'prepared.json').read_text())
    if manifest['recipe']!=digest(__file__):
        raise RuntimeError('Scene recipe changed: rerun Python --prepare first')
    for path,expected in manifest['files'].items():
        if digest(args.masters/path)!=expected:
            raise RuntimeError(f'Prepared asset changed: {path}; rerun --prepare')
    return hashlib.sha256((digest(__file__)+digest(BASE)+json.dumps(manifest,sort_keys=True)
                           +bpy.app.version_string).encode()).hexdigest()


def parse_args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--masters',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,help='Existing classical plates; default: masters sibling/classical')
    p.add_argument('--frames',default='1-144',help='Inclusive global frames, e.g. 1-1 or 72-96')
    p.add_argument('--full',action='store_true',help='1920x1080 output; default 960x540, identical framing')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--prepare',action='store_true',help='Python-only asset preparation; no bpy required')
    mode.add_argument('--dry-run',action='store_true',help='Build/validate/save only, no bake/render')
    mode.add_argument('--bake-only',action='store_true',help='Compatibility alias: build/save scene only; no bake required')
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    args=p.parse_args(argv)
    args.width,args.height=FULL_SIZE if args.full else PREVIEW_SIZE
    args.pixel_scale=args.width/PREVIEW_SIZE[0]
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
    scene,report=build(args)
    report['source_signature']=stamp; report['blender']=bpy.app.version_string
    bpy.ops.wm.save_as_mainfile(filepath=str(args.masters/'scene.blend'))
    (args.masters/'scene-report.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.dry_run or args.bake_only:
        print('BUILD ONLY: saved scene.blend; no bake requirement',flush=True)
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
