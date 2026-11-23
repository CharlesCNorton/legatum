"""Pass-4 spearman: painted occlusion masters and planar retarget of the 3D poses.

Motion reference: anim3d/model.py::pose on astra/unit-anim-pilot-3d, 929c71e.
Keep its phase, lunge and recoil samples; retarget to the painting's proportions.
Death deliberately retains pass 3. This module is also usable without Blender.
"""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

# Front to back. Ownership masks describe VISIBLE paint, not the completed part.
# The skirt belongs to the torso, never to the rotating thighs.
PARTS = [
    ('spear', (99,115), [(97,8),(104,8),(101,106),(101,124),(98,211),(92,213),(95,124),(95,106)], 'hand'),
    ('hand', (99,115), [(91,108),(102,106),(106,112),(103,123),(95,124),(90,119)], 'forearm'),
    ('shield', (146,132), [(143,104),(157,105),(169,112),(179,124),(183,141),(180,158),(173,170),(160,176),(145,171),(136,159),(132,143),(133,124),(137,111)], 'shield_hand'),
    ('head', (134,98), [(115,54),(151,54),(150,96),(140,104),(129,104),(117,96)], 'body'),
    ('forearm', (109,120), [(98,109),(107,110),(114,115),(115,123),(107,128),(99,125)], 'arm'),
    ('arm', (119,110), [(108,103),(121,101),(125,111),(120,122),(111,126),(105,119)], 'body'),
    ('leg_l_lower', (110,187), [(103,182),(118,183),(113,204),(113,215),(100,220),(87,220),(88,210),(100,199)], 'leg_l'),
    ('leg_r_lower', (151,187), [(142,182),(158,182),(160,204),(170,220),(147,221),(143,205)], 'leg_r'),
    ('leg_l', (116,167), [(106,168),(129,168),(120,185),(116,193),(103,193),(101,185)], 'root'),
    ('leg_r', (143,168), [(135,168),(155,168),(159,185),(158,194),(144,194),(138,185)], 'root'),
    ('shield_hand', (146,132), [(141,127),(150,127),(152,138),(141,140)], 'shield_forearm'),
    ('shield_forearm', (157,122), [(148,118),(161,117),(161,130),(150,141),(141,137)], 'shield_arm'),
    ('shield_arm', (145,109), [(140,102),(151,104),(161,114),(162,126),(152,129),(143,118)], 'body'),
    ('cloak', (126,106), [(113,101),(143,101),(153,114),(168,182),(156,188),(138,186),(127,188),(109,185),(99,180),(101,149)], 'body'),
]
# Full hidden shapes, bounded to anatomy. Interior paint is completed BEFORE posing.
SUPPORT = {
    'body': [(120,98),(142,99),(153,112),(151,141),(158,168),(141,174),(120,169),(105,166),(112,140),(111,114)],
    'cloak': [(116,102),(143,104),(150,118),(165,181),(152,185),(137,183),(126,186),(110,183),(101,180),(105,145)],
    'arm': [(111,102),(122,102),(126,110),(119,125),(110,128),(104,120),(107,110)],
    'forearm': [(97,108),(106,108),(116,115),(117,123),(110,129),(99,126),(94,120)],
    'hand': [(94,108),(102,108),(104,113),(103,122),(95,123),(91,118)],
    'leg_l': [(108,161),(125,164),(122,180),(117,194),(104,193),(101,185)],
    'leg_r': [(135,163),(151,161),(157,176),(159,193),(145,194),(138,183)],
    'leg_l_lower': [(104,181),(116,181),(117,191),(111,207),(109,214),(99,219),(89,219),(89,214),(100,204)],
    'leg_r_lower': [(144,181),(156,181),(159,192),(159,205),(168,216),(166,219),(154,219),(146,212),(143,198)],
    'head': [(123,91),(141,91),(143,104),(126,105)],
    'shield_arm': [(139,104),(148,103),(161,116),(162,126),(153,130),(144,119)],
    'shield_forearm': [(150,116),(160,117),(162,125),(151,141),(140,139),(140,130)],
    'shield_hand': [(142,126),(151,127),(152,138),(141,140)],
}
LUNGE = (0,-.08,-.10,.25,.8,1,1,.6,.2,0)
RECOIL = (0,1,.55,0)


def mask(points):
    result = Image.new('L', (256,256))
    ImageDraw.Draw(result).polygon(points, fill=255)
    return result


def prepare_layers(src, figure, dest, cfg, donor_path=None):
    """Persist extracted paint + explicit hidden-paint masks under masters/layers.

    The image-model donor supplies hidden cuirass/skirt/cloak. Small joint caps
    clone nearby brushwork, never averaged RGB or a flat fill. Every original
    visible pixel keeps its pigment and alpha; the generated art is underneath.
    """
    folder = dest / 'layers'
    folder.mkdir(exist_ok=True)
    donor_path = donor_path or folder / 'occlusion-paint-master.png'
    if not donor_path.exists():
        raise FileNotFoundError(f'Missing approved local fill master: {donor_path}; see review/pass-4-spearman.md')
    donor = Image.open(donor_path).convert('RGBA').resize((256,256), Image.Resampling.LANCZOS)
    donor.save(folder / 'occlusion-paint-256.png')
    taken = Image.new('L', src.size)
    owned = {}
    for name, _, points, _ in PARTS:
        region = mask(points)
        if name == 'spear':
            # The fist travels with the wrist, never as a rotated shaft lump.
            ImageDraw.Draw(region).rectangle((89,107,107,123), fill=0)
        if name == 'cloak':
            # Red only: the cuirass and linen skirt remain on the torso.
            pigment = src.point(lambda v: v)
            red = Image.new('L', src.size)
            for y in range(99,190):
                for x in range(98,169):
                    r,g,b,a = pigment.getpixel((x,y))
                    if r > g*1.45 and r > b*1.8:
                        red.putpixel((x,y),255)
            region = ImageChops.multiply(region, red)
        alpha = ImageChops.multiply(ImageChops.subtract(region,taken),figure.getchannel('A'))
        layer = src.copy(); layer.putalpha(alpha); owned[name] = layer
        taken = ImageChops.lighter(taken,region)
    body = src.copy()
    body.putalpha(ImageChops.subtract(figure.getchannel('A'),taken))
    owned['body'] = body
    # Assign any outer source scraps to the closest anatomical layer, not torso.
    allowed = mask(SUPPORT['body'])
    for y in range(256):
        for x in range(256):
            if body.getpixel((x,y))[3] and not allowed.getpixel((x,y)):
                candidates = [(name,im) for name,im in owned.items() if name != 'body']
                name,im = min(candidates, key=lambda pair: _distance_to_mask(pair[1],x,y))
                im.putpixel((x,y),body.getpixel((x,y)))
                body.putpixel((x,y),(0,0,0,0))
    report = {'source_sha256':hashlib.sha256(src.tobytes()).hexdigest(),
              'donor_sha256':hashlib.sha256(donor_path.read_bytes()).hexdigest(), 'layers':{}}
    for name, layer in owned.items():
        layer.save(folder / f'{name}-visible.png')
        support = mask(SUPPORT[name]) if name in SUPPORT else Image.new('L',src.size)
        # Never expand the silhouette of already-complete metal kit or the feet.
        if name.endswith('_lower'):
            support = ImageChops.multiply(support, mask([(80,179),(175,179),(175,196),(80,196)]))
        if name == 'spear':
            ImageDraw.Draw(support).polygon([(97,105),(100,105),(100,125),(96,125)],fill=255)
        hidden = ImageChops.subtract(support,layer.getchannel('A'))
        fill = Image.new('RGBA',src.size)
        # Source patches for tiny caps, selected by material to avoid cloning stone.
        if name == 'spear': patch = (96,85,100,104)
        elif name.startswith('shield_') or name in ('forearm','hand'): patch = (104,113,111,121)
        elif name == 'arm': patch = (111,106,120,115)
        elif name.startswith('leg_l'): patch = (106,176,114,188)
        elif name.startswith('leg_r'): patch = (145,177,154,190)
        elif name == 'head': patch = (128,94,138,99)
        else: patch = None
        for y in range(256):
            for x in range(256):
                if not hidden.getpixel((x,y)): continue
                if patch:
                    x0,y0,x1,y1=patch
                    # Reflected patch tiling keeps neighbouring brush strokes;
                    # no single edge pixel is dragged into a smeared strip.
                    px=_mirror(x-x0,x1-x0)+x0; py=_mirror(y-y0,y1-y0)+y0
                    rgb=src.getpixel((px,py))[:3]
                elif name == 'cloak':
                    # Sample the uninterrupted model-painted red folds, never
                    # the donor's foreground skirt, armour or legs.
                    px=94+_mirror(x-101,11); py=120+_mirror(y-106,52)
                    rgb=donor.getpixel((px,py))[:3]
                else:
                    rgb=donor.getpixel((x,y))[:3]
                    if donor.getpixel((x,y))[3] < 128:
                        px=120+_mirror(x-110,25);py=105+_mirror(y-100,62)
                        rgb=donor.getpixel((px,py))[:3]
                fill.putpixel((x,y),rgb+(255,))
        hidden.save(folder / f'{name}-fill-mask.png')
        fill.save(folder / f'{name}-fill.png')
        fill.alpha_composite(layer)
        fill.save(folder / f'{name}.png')
        report['layers'][name]={'visible_pixels':sum(a>0 for a in layer.getchannel('A').getdata()),
                                'filled_pixels':sum(a>0 for a in hidden.getdata())}
    (folder/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    layers=[dict(name=n,pivot=p,parent=parent,texture=f'layers/{n}.png') for n,p,_,parent in PARTS]
    (dest/'model.json').write_text(json.dumps(dict(**cfg,layers=layers,body_texture='layers/body.png'),indent=2)+'\n')
    print(f'spearman: {len(owned)} completed painted layers in {folder}')


def _mirror(value, length):
    value %= length*2
    return value if value < length else 2*length-1-value


def _distance_to_mask(im,x,y):
    # Only a few source-edge scraps reach here; search locally then use bounds.
    for r in range(1,10):
        for dx,dy in ((r,0),(-r,0),(0,r),(0,-r)):
            if 0<=x+dx<256 and 0<=y+dy<256 and im.getpixel((x+dx,y+dy))[3]>128:
                return r
    box=im.getbbox()
    return 1000 if box is None else 10+math.hypot(x-(box[0]+box[2])/2,y-(box[1]+box[3])/2)


# Affine camera-plane transforms: (a,b,c,d,tx,ty). All live clips are rigid paint.
def transform(pivot, target, angle=0):
    c,s=math.cos(angle),math.sin(angle)
    return (c,-s,s,c,target[0]-c*pivot[0]+s*pivot[1],target[1]-s*pivot[0]-c*pivot[1])


def apply(m,p):
    a,b,c,d,x,y=m
    return (a*p[0]+b*p[1]+x,c*p[0]+d*p[1]+y)


def segment(start,end,a,b):
    angle=math.atan2(b[1]-a[1],b[0]-a[0])-math.atan2(end[1]-start[1],end[0]-start[0])
    return transform(start,a,angle)


def ik(start,knee,end,target_start,target_end):
    l1=math.dist(start,knee);l2=math.dist(knee,end)
    dx,dy=target_end[0]-target_start[0],target_end[1]-target_start[1]
    raw=math.hypot(dx,dy);dist=max(abs(l1-l2)+.001,min(raw,l1+l2-.001))
    ux,uy=dx/raw,dy/raw
    target_end=(target_start[0]+ux*dist,target_start[1]+uy*dist)
    along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    height=math.sqrt(max(0,l1*l1-along*along))
    cross=(end[0]-start[0])*(knee[1]-start[1])-(end[1]-start[1])*(knee[0]-start[0])
    sign=1 if cross>=0 else -1
    joint=(target_start[0]+ux*along-uy*height*sign,target_start[1]+uy*along+ux*height*sign)
    return segment(start,knee,target_start,joint),segment(knee,end,joint,target_end),target_end


def motion(clip,index):
    """3D phase/key poses in a painting-sized rig; returns world paint transforms."""
    n={'idle':8,'move':8,'attack':10,'hit':4}[clip]
    phase=math.tau*index/n; s=math.sin(phase)
    lunge=LUNGE[index] if clip=='attack' else 0
    recoil=RECOIL[index] if clip=='hit' else 0
    shift=(0,0);lean=0
    if clip=='idle': shift=(1.7*s,-1.8*s);lean=.018*s
    if clip=='move': shift=(1.7*s,-1.9*(1+math.cos(phase*2)));lean=.035*s
    if clip=='attack': shift=(9*lunge,8*max(0,lunge));lean=.27*lunge
    if clip=='hit': shift=(-4*recoil,3*recoil);lean=-.32*recoil
    body=transform((130,165),(130+shift[0],165+shift[1]),lean)
    poses={'root':transform((130,165),(130+shift[0],165+shift[1])), 'body':body}
    poses['head']=transform((134,98),apply(body,(134,98)),lean-.10*recoil)
    poses['cloak']=transform((126,106),apply(body,(126,106)),lean+(.035*s if clip=='move' else .012*s if clip=='idle' else 0))
    for side,hip,knee,foot in [('l',(116,167),(110,187),(102,213)),('r',(143,168),(151,187),(157,214))]:
        target=foot
        if clip=='move':
            p=phase+(math.pi if side=='r' else 0)
            target=(foot[0]+7*math.cos(p),foot[1]-9*max(0,math.sin(p)))
        if clip=='attack':
            target=(foot[0]+(7 if side=='r' else -3)*max(0,lunge),foot[1])
        upper,lower,_=ik(hip,knee,foot,apply(poses['root'],hip),target)
        poses['leg_'+side]=upper;poses['leg_'+side+'_lower']=lower
    shoulder=(119,110);elbow=(109,120);hand=(99,115)
    hand_target=apply(body,hand)
    # Raise the grip to the shoulder before the forward thrust. At full reach,
    # the 204-pixel spear still fits the unchanged 256-pixel camera framing.
    ready=max(0,lunge)
    hand_target=(hand_target[0]+12*ready,hand_target[1]-10*ready)
    if clip=='move': hand_target=(hand_target[0]+2*s,hand_target[1]-1.8*s)
    arm,fore,grip=ik(shoulder,elbow,hand,apply(body,shoulder),hand_target)
    poses['arm']=arm;poses['forearm']=fore;poses['hand']=transform(hand,grip,lean)
    # Source shaft leans slightly right. Cancel it at the world-space peak;
    # do not accumulate torso/elbow rotations onto the weapon angle.
    upright=math.atan2(6,200)
    angle=(math.pi/2-upright)*ready + (.012*s if clip in ('idle','move') else 0)
    poses['spear']=transform(hand,grip,angle)
    shoulder=(145,109);elbow=(157,122);hand=(146,132)
    target=apply(body,hand)
    target=(target[0]-4*ready-3*recoil,target[1]-5*ready-5*recoil)
    if clip=='move':target=(target[0]-2.5*s,target[1]+2*s)
    arm,fore,grip=ik(shoulder,elbow,hand,apply(body,shoulder),target)
    poses['shield_arm']=arm;poses['shield_forearm']=fore
    poses['shield_hand']=transform(hand,grip,lean)
    poses['shield']=transform(hand,grip,lean-.18*ready-.22*recoil+(.045*s if clip=='move' else 0))
    return poses
