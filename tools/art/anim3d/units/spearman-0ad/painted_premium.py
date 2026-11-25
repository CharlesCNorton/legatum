"""Round-three fitted armour and cloth, in locked Y-up bind coordinates.

Rebuild visible contour topology rather than decimating hundreds of tiny parts.
All geometry uses the existing joint names; this module never accesses actions.
"""
import math
import bpy
from mathutils import Vector


def finish_forms(ctx):
    objects=ctx['objects'];mesh=ctx['mesh'];tube=ctx['tube'];apply=ctx['apply'];bones=ctx['bones']
    def discard(ob):
        objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    for ob in list(objects):
        if ob['part'] in {'helmet','crest','crest_base','cuirass','sleeve'} or 'shoulder mantle' in ob.name or 'dark lining' in ob.name:
            discard(ob)

    # One continuous shell covers temples, ears and nape. Eye apertures are
    # actual omitted quads; the narrow central bridge becomes the nose guard.
    segments=64;rows=[(1.395,.078,.112),(1.43,.093,.130),(1.485,.112,.143),
        (1.535,.114,.145),(1.555,.113,.143),(1.575,.112,.140),
        (1.605,.103,.133),(1.64,.084,.109),(1.67,.050,.068),(1.687,.010,.014)]
    vs=[];fs=[]
    for y,rx,rz in rows:
        for i in range(segments):
            a=math.tau*i/segments
            # Front faces +Z. Slight forward keel gives Corinthian nasal relief.
            front=max(0,math.cos(a))
            eyelift=.013*abs(math.sin(a*2)) if 1.53<y<1.58 else 0
            vs.append((rx*math.sin(a),y+eyelift,.006+rz*math.cos(a)+.022*front**18))
    for j in range(len(rows)-1):
        for i in range(segments):
            a=(i+.5)*math.tau/segments;front=math.cos(a)>.42
            # Narrow paired eye slits, with a solid nasal bridge at the centre.
            if j==3 and front and abs(math.sin(a))>.14:continue
            # Central opening under the nose; cheek guards stay closed at sides.
            if j<2 and front and abs(math.sin(a))<.15:continue
            k=j*segments+i;l=j*segments+(i+1)%segments
            fs.append((k,l,l+segments,k+segments))
    ob=mesh('helmet:closed Corinthian',vs,fs,'bronze','helmet')
    apply(ob,'SOLIDIFY',thickness=.004,offset=-1)
    # Brow and cheek contour gilding are smooth continuous paths, not floating shards.
    for side in [-1,1]:
        pts=[]
        for i in range(17):
            a=side*(.09+1.12*i/16)
            pts.append((.114*math.sin(a),1.576+.009*math.sin(math.pi*i/16),.006+.145*math.cos(a)+.014*max(0,math.cos(a))**18))
        tube('helmet:arched brow',pts,[.0035]*len(pts),'gold','helmet',seg=6)
        pts=[(side*.018,1.522,.166),(side*.025,1.477,.156),(side*.028,1.43,.138),(side*.05,1.405,.111)]
        tube('helmet:cheek border',pts,[.0028]*4,'gold','helmet',seg=6)
    # A dark rigid liner behind the apertures; concealed MPFB facial topology
    # is removed to reserve the anatomy budget for moving limbs.
    ctx['sphere']('helmet:dark liner',(0,1.535,.008),(.093,.119,.117),'dark','helmet',seg=16,rings=8)
    # A recessed dark head surface removes distracting skin through the eye slots.
    for ob in objects:
        if ob['part']=='heroicbody':
            ob.data.materials.append(ctx['M']['dark']);dark=len(ob.data.materials)-1
            for p in ob.data.polygons:
                if p.center.y>1.39:p.material_index=dark

    # A single fluted horsehair volume. Rounded scallops replace 105 decimated
    # spikes; the tips terminate in the volume instead of protruding through it.
    arc=64;cross=8;vs=[];fs=[]
    for i in range(arc+1):
        a=.06+(math.pi-.12)*i/arc
        for k in range(cross):
            q=math.tau*k/cross
            scallop=.0015*math.cos(i*math.pi)
            radius=.235+(.077+scallop)*math.cos(q)
            vs.append((.035*math.sin(q),1.545+radius*math.sin(a),.002+(.192+.058*math.cos(q))*math.cos(a)))
    for i in range(arc):
        for k in range(cross):
            a=i*cross+k;b=i*cross+(k+1)%cross;fs.append((a,b,b+cross,a+cross))
    fs.extend([tuple(range(cross-1,-1,-1)),tuple(arc*cross+k for k in range(cross))])
    hair=mesh('crest:sculpted horsehair arc',vs,fs,'mask','helmet','crest')
    hairmat=ctx['M']['mask'].copy();hairmat.name='Painted horsehair streaks';ctx['M']['hair']=hairmat
    hair.data.materials[0]=hairmat
    nodes=hairmat.node_tree.nodes;links=hairmat.node_tree.links
    geo=next(n for n in nodes if n.type=='NEW_GEOMETRY')
    sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
    y=nodes.new('ShaderNodeMath');y.operation='SUBTRACT';links.new(sep.outputs['Y'],y.inputs[0]);y.inputs[1].default_value=1.545
    angle=nodes.new('ShaderNodeMath');angle.operation='ARCTAN2';links.new(y.outputs[0],angle.inputs[0]);links.new(sep.outputs['Z'],angle.inputs[1])
    freq=nodes.new('ShaderNodeMath');freq.operation='MULTIPLY';freq.inputs[1].default_value=110;links.new(angle.outputs[0],freq.inputs[0])
    wave=nodes.new('ShaderNodeMath');wave.operation='SINE';links.new(freq.outputs[0],wave.inputs[0])
    tone=nodes.new('ShaderNodeMapRange');tone.inputs['From Min'].default_value=-1;tone.inputs['From Max'].default_value=1;tone.inputs['To Min'].default_value=.48;tone.inputs['To Max'].default_value=1.15;links.new(wave.outputs[0],tone.inputs[0])
    paint=nodes[hairmat['paint_node']];streak=nodes.new('ShaderNodeMixRGB');streak.blend_type='MULTIPLY';streak.inputs[0].default_value=1;links.new(paint.outputs[0],streak.inputs[1]);links.new(tone.outputs[0],streak.inputs[2]);links.new(streak.outputs[0],next(n for n in nodes if n.type=='EMISSION').inputs[0]);hairmat['paint_node']=streak.name
    pts=[(0,1.545+.140*math.sin(math.pi*i/48),.002+.148*math.cos(math.pi*i/48)) for i in range(49)]
    tube('crest_base:bronze saddle',pts,[.013]*49,'gold','helmet',seg=8)

    # Muscular shell with anatomical pectorals and paired abdominal volumes.
    # Decor stays on the actual shaped shell instead of its former flat envelope.
    vs=[];fs=[];ww=[];segments=64;rows=18
    for j in range(rows+1):
        t=j/rows;y=.89+.455*t
        width=.166+.092*math.sin(t*math.pi*.68)
        depth=.117+.030*math.sin(t*math.pi)
        for i in range(segments):
            a=math.tau*i/segments;x=width*math.cos(a);z=depth*math.sin(a)
            if z>0:
                pec=.043*math.exp(-((abs(x)-.105)/.079)**2-((y-1.225)/.068)**2)
                abdominal=.019*math.exp(-((abs(x)-.060)/.045)**2)*sum(math.exp(-((y-c)/.028)**2) for c in [1.015,1.075,1.135])
                z+=(pec+abdominal)*max(0,math.sin(a))**.4
            vs.append((x,y,z));blend=max(0,min(1,(t-.15)/.60))
            ww.append([(bones.index('spine1'),1-blend),(bones.index('chest'),blend)])
    for j in range(rows):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
    ob=mesh('cuirass:muscle shell',vs,fs,'bronze',weights=ww);apply(ob,'SOLIDIFY',thickness=.004)
    for y,rx,rz,bone in [(.90,.171,.122,'spine1'),(1.329,.250,.124,'chest')]:
        pts=[(rx*math.cos(math.tau*i/64),y,rz*math.sin(math.tau*i/64)) for i in range(65)]
        tube('cuirass:rolled border',pts,[.004]*65,'gold',bone,seg=6)

    # Low draped shoulder mantle, with three broad folds. A collar rising to the
    # jaw had hidden the arms and clipped the neck in the previous round.
    vs=[];fs=[];ww=[];segments=64;rows=8
    for j in range(rows+1):
        t=j/rows
        for i in range(segments):
            a=math.tau*i/segments;front=max(0,math.sin(a))
            radius=.007*math.sin(t*math.pi*6)
            vs.append(((.082+.206*t+radius)*math.cos(a),1.407-.047*t-.018*front*t,
                (.087+.103*t+radius)*math.sin(a)))
            ww.append([(bones.index('chest'),1)])
    for j in range(rows):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
    ob=mesh('cloak:draped shoulder folds',vs,fs,'red',weights=ww);apply(ob,'SOLIDIFY',thickness=.004)
    # Team trim is a region of the same cloth surface, not an offset ribbon
    # that can separate from it or cross the shield during the locked clips.
    for ob in list(objects):
        if ob['part']=='cloak' and 'team trim' in ob.name:discard(ob)
    cloth=next(ob for ob in objects if ob['part']=='cloak' and 'wool folds' in ob.name)
    coords=[tuple(v.co) for v in cloth.data.vertices]
    weights=[[(bones.index(cloth.vertex_groups[w.group].name),w.weight) for w in v.groups] for v in cloth.data.vertices]
    for edge in [False,True]:
        faces=[tuple(p.vertices) for p in cloth.data.polygons if (p.index%40 in (0,39))==edge]
        used=sorted(set(i for f in faces for i in f));lookup={v:i for i,v in enumerate(used)}
        mesh('cloak:integrated trim' if edge else 'cloak:wool surface',[coords[i] for i in used],
             [[lookup[i] for i in f] for f in faces],'mask' if edge else 'red',
             team='cloak trim' if edge else None,weights=[weights[i] for i in used])
    discard(cloth)
    # Pull the rear cloth behind the armour and keep its side edges behind arms.
    for ob in objects:
        if ob['part']=='cloak' and 'shoulder' not in ob.name:
            for v in ob.data.vertices:
                t=max(0,min(1,(1.335-v.co.y)/.82));v.co.z-=.075+.24*(abs(v.co.x)/.42)**2*t

    # Protect a deliberately cheap, regular 96-sided rim from collapse decimation.
    for ob in list(objects):
        if ob['part']=='aspis' and ('rolled rim' in ob.name or 'engraving' in ob.name):discard(ob)
    point=ctx['shield_point'];radius=ctx['radius']
    pts=[point(radius,math.tau*i/96,0) for i in range(97)]
    ob=tube('aspis:continuous rolled rim',pts,[.012]*97,'mask','shield_arm','shield rim',4)
    ob['keep_contour']=True

    pts=[point(.373,math.tau*i/64,.014) for i in range(65)]
    ob=tube('aspis:gold inner register',pts,[.005]*65,'gold','shield_arm',seg=4)
    ob['keep_contour']=True
