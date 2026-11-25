"""Round four: dressed bronze armour, continuous knees and PBR-lane aspis.

All construction is in the unchanged Y-up bind frame. No pose/action writes.
Aspis recipe and metal values adapted from the PBR lane's pbr_build.py.
"""
import math
import bpy
import numpy as np
from mathutils import Vector


def refine_round_four(ctx):
    objects=ctx['objects'];mesh=ctx['mesh'];tube=ctx['tube'];sphere=ctx['sphere']
    apply=ctx['apply'];bones=ctx['bones'];M=ctx['M'];material=ctx['material']
    def discard(ob):
        objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    inv=np.array(ctx['g'].accessor(ctx['g'].doc['skins'][0]['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    centres={name:Vector(np.linalg.inv(m)[:3,3]) for name,m in zip(bones,inv)}
    # The PBR lane's bronze/edge/recess palette and roughness variation, mixed
    # with the painted lane's directional pigment and lower metal response.
    def linear(hexcol):
        out=[]
        for i in (1,3,5):
            v=int(hexcol[i:i+2],16)/255
            out.append(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)
        return tuple(out)
    for key,color,rough,metal in [('bronze','#ad7b37',.57,.55),('gold','#e7bd68',.34,.75),
            ('shield','#a87938',.58,.62),('dark','#49311c',.75,.38),
            ('linen','#e8d8b2',.94,0),('skin','#c68c63',.8,0),('red','#8d1420',.96,0)]:
        M[key]=material('R4 '+key,linear(color),rough,metal,38 if metal else 90)
        # Skin and linen must not inherit the armour's very dark fixed shadows.
        if key in {'skin','linen','red'}:
            ramp=next(n for n in M[key].node_tree.nodes if n.type=='MAP_RANGE')
            ramp.inputs['To Min'].default_value=.55;ramp.inputs['To Max'].default_value=1.35
    for ob in objects:
        if ob['mat'] in M and ob['part']!='crest':
            # Preserve per-face skin/leather assignment on the MPFB body.
            if ob['part']=='heroicbody':
                ob.data.materials[0]=M['skin']
                for poly in ob.data.polygons:
                    if poly.center.y>.025:poly.material_index=0
                # Part-ID review exposed the native pelvis through the chiton.
                # Keep a continuous body, fitted inside the garment and driven
                # by the same hip/thigh blend. Do not cut idle-only holes.
                for vert in ob.data.vertices:
                    p=vert.co
                    if not (.60<p.y<.915 and abs(p.x)<.28):continue
                    lower=sum(w.weight for w in vert.groups if ob.vertex_groups[w.group].name
                              in {'hip','spine','spine1','chest','thigh_L','thigh_R'})
                    if lower<.65:continue  # Nearby hand/forearm vertices are not clothing.
                    t=max(0,min(1,(.875-p.y)/.29))
                    rx=.176+.085*t;rz=.143+.050*t
                    radius=math.sqrt((p.x/rx)**2+(p.z/rz)**2)
                    if radius>.80:p.x*=.80/radius;p.z*=.80/radius
                    leg='thigh_L' if p.x>=0 else 'thigh_R'
                    for group in ob.vertex_groups:group.remove([vert.index])
                    ob.vertex_groups['hip'].add([vert.index],1-.65*t,'REPLACE')
                    ob.vertex_groups[leg].add([vert.index],.65*t,'REPLACE')
            else:
                ob.data.materials.clear();ob.data.materials.append(M[ob['mat']])

    # Adapt the PBR lane's continuous dish, thick bronze lip, team inset and
    # bevelled broad rays. Its smooth boss replaces the old pinched ellipsoid.
    for ob in list(objects):
        if ob['part']=='aspis':discard(ob)
    point=ctx['shield_point'];c=ctx['center'];n=ctx['normal'];u=ctx['right'];v=ctx['up']
    vs=[point(0,0,.105)];fs=[];N=64
    for radius in (.09,.20,.30,.375,.389):
        for j in range(N):vs.append(point(radius,j*math.tau/N,.105*(1-(radius/.4)**2)))
    for j in range(N):fs.append((0,1+j,1+(j+1)%N))
    for row in range(4):
        for j in range(N):fs.append((1+row*N+j,1+(row+1)*N+j,1+(row+1)*N+(j+1)%N,1+row*N+(j+1)%N))
    ob=mesh('aspis:PBR convex dish',vs,fs,'shield','shield_arm');ob['keep_contour']=True
    for radius,depth,width,mat,team,segments in [(.392,.008,.012,'gold',None,4),(.374,.013,.005,'mask','shield rim',3),(.316,.045,.003,'gold',None,3)]:
        ob=tube('aspis:PBR rolled register',[point(radius,j*math.tau/64,depth) for j in range(65)],[width]*65,mat,'shield_arm',team,segments)
        ob['keep_contour']=True
    for j in range(12):
        a=j*math.tau/12;rad=u*math.cos(a)+v*math.sin(a);side=-u*math.sin(a)+v*math.cos(a)
        root=c+n*.110+rad*.065;tip=c+n*.046+rad*.30
        ray=mesh('aspis:PBR raised ray',[root-side*.024,root+side*.024,tip,root+n*.018+rad*.065],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],'gold','shield_arm')
        apply(ray,'BEVEL',width=.0015,segments=1)
        ray['keep_contour']=True
        for p in ray.data.polygons:p.use_smooth=False
    boss=sphere('aspis:PBR boss',(0,0,0),(1,1,1),'gold','shield_arm',seg=16,rings=8)
    boss['keep_contour']=True
    for vert in boss.data.vertices:
        q=vert.co.copy();vert.co=c+u*q.x*.069+v*q.y*.069+n*(.116+q.z*.028)
    for j in range(16):sphere('aspis:rim rivet',point(.354,j*math.tau/16,.029),(.004,)*3,'gold','shield_arm',seg=8,rings=4)

    # Sleeves sit over continuous MPFB anatomy and move with upper arm bones.
    # Flared, ivory cuffs make the bronze chest unmistakably a worn shell.
    for ob in list(objects):
        if ob['part']=='sleeve':discard(ob)
    for side in ['L','R']:
        origin=centres['arm_'+side];axis=(centres['forearm_'+side]-origin).normalized()
        across=axis.cross(Vector((0,0,1))).normalized();front=across.cross(axis).normalized()
        vs=[];fs=[];N=28
        for j in range(7):
            t=j/6;c0=origin+axis*(-.035+.175*t)
            for i in range(N):
                a=i*math.tau/N;r=.094+.013*math.sin(t*math.pi)+.005*math.cos(a*7+t*2)
                vs.append(c0+across*r*math.cos(a)+front*r*math.sin(a))
        for j in range(6):
            for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
        ob=mesh('sleeve:ivory chiton '+side,vs,fs,'linen','arm_'+side);apply(ob,'SOLIDIFY',thickness=.003)
        tube('sleeve:sewn cuff '+side,vs[-N:]+[vs[-N]],[.004]*(N+1),'linen','arm_'+side,seg=4)

    # Distinct cast bronze hems, belt and a restrained pectoral chase. Every
    # border follows the same spine/chest interpolation as its supporting shell.
    def torso_weights(y):
        t=(y-.89)/.455;f=max(0,min(1,(t-.15)/.60))
        return [(bones.index('spine1'),1-f),(bones.index('chest'),f)]
    def bind_torso(ob):
        ob.vertex_groups.clear();ob['bone']=''
        for b in bones:ob.vertex_groups.new(name=b)
        for vert in ob.data.vertices:
            for j,w in torso_weights(vert.co.y):
                if w:ob.vertex_groups[j].add([vert.index],w,'REPLACE')
    for ob in list(objects):
        if ob['part']=='cuirass' and 'rolled border' in ob.name:discard(ob)
        elif ob['part']=='cuirass' and 'muscle shell' in ob.name:
            for vert in ob.data.vertices:
                t=max(0,min(1,(vert.co.y-1.22)/.125))
                vert.co.x*=1-.25*t
            # The shell has rolled edges and side thickness; keep the muscular
            # modelling restrained enough to read as cast armour over clothing.
    for ob in objects:
        if ob['part']=='heroicbody':
            linen_slot=len(ob.data.materials);ob.data.materials.append(M['linen'])
            for poly in ob.data.polygons:
                p=poly.center
                if 1.22<p.y<1.39 and abs(p.x)<.23:poly.material_index=linen_slot
    for y,rx,rz in [(.902,.178,.124),(1.323,.202,.128)]:
        ob=tube('cuirass:finished bronze hem',[(rx*math.cos(a),y,rz*math.sin(a)) for a in np.linspace(0,math.tau,65)],[.008]*65,'gold','chest',seg=6);bind_torso(ob)
    def armour_surface(x,y):
        t=(y-.89)/.455;width=.166+.092*math.sin(t*math.pi*.68)
        angle=math.acos(max(-1,min(1,x/width)))
        z=(.117+.030*math.sin(t*math.pi))*math.sin(angle)
        pec=.043*math.exp(-((abs(x)-.105)/.079)**2-((y-1.225)/.068)**2)
        abdominal=.019*math.exp(-((abs(x)-.060)/.045)**2)*sum(math.exp(-((y-c)/.028)**2) for c in [1.015,1.075,1.135])
        return z+(pec+abdominal)*math.sin(angle)**.4+.003
    for side in [-1,1]:
        pts=[]
        for i in range(17):
            t=i/16;x=side*(.02+.18*t);y=1.205-.026*math.sin(t*math.pi)
            pts.append((x,y,armour_surface(x,y)))
        ob=tube('cuirass:chased pectoral highlight',pts,[.0025]*len(pts),'gold','chest',seg=4);bind_torso(ob)
    vs=[];fs=[]
    for y in [.915,.955]:
        for i in range(48):
            a=i*math.tau/48;vs.append((.19*math.cos(a),y,.142*math.sin(a)))
    for i in range(48):fs.append((i,(i+1)%48,(i+1)%48+48,i+48))
    ob=mesh('cuirass:oxhide waist belt',vs,fs,'leather',weights=[torso_weights(p[1]) for p in vs])
    sphere('cuirass:bronze belt clasp',(0,.936,.147),(.024,.018,.006),'gold','spine1',seg=12,rings=6)

    for ob in list(objects):
        if ob['part']=='pteruges':discard(ob)
    for i in range(14):
        a=i*math.tau/14;verts=[]
        for y,r,w in [(.915,.184,.13),(.78,.230,.12),(.754,.234,.08)]:
            for da in [-w,w]:verts.append((r*math.cos(a+da),y,r*.84*math.sin(a+da)))
        ob=mesh('pteruges:finished leather strip',verts,[(0,1,3,2),(2,3,5,4)],'leather','hip')
        apply(ob,'SOLIDIFY',thickness=.004)

    # Rebuild each greave as one continuous patella-to-ankle shell. The separate
    # spherical knees in r3 left a visible slit and read as toy hinges.
    for ob in list(objects):
        if ob['part'].startswith('greave_'):discard(ob)
    for side in ['L','R']:
        knee=centres['leg_'+side];ankle=centres['foot_'+side];vs=[];fs=[];N=24
        levels=[(.10,.044,.056),(.18,.060,.071),(.29,.074,.084),(.39,.075,.080),(.445,.070,.083),(.48,.058,.072),(.502,.035,.051)]
        for y,rx,rz in levels:
            t=max(0,min(1,(knee.y-y)/(knee.y-ankle.y)));centre=knee.lerp(ankle,t)
            for i in range(N+1):
                a=-1.90+3.80*i/N
                vs.append((centre.x+rx*math.sin(a),y+.008*math.cos(a),centre.z+.012+rz*math.cos(a)))
        for j in range(len(levels)-1):
            for i in range(N):a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
        ob=mesh('greave_'+side+':continuous knee shell',vs,fs,'bronze','leg_'+side);apply(ob,'SOLIDIFY',thickness=.0035)
        for row in [0,len(levels)-1]:tube('greave_'+side+':rolled edge',vs[row*(N+1):(row+1)*(N+1)],[.004]*(N+1),'gold','leg_'+side,seg=5)
        centreline=[Vector(vs[j*(N+1)+N//2])+Vector((0,0,.002)) for j in range(len(levels))]
        tube('greave_'+side+':raised shin keel',centreline,[.003]*len(centreline),'gold','leg_'+side,seg=5)

    # Jaw-length cheek guards, deep T aperture, and a separate outward-flared
    # nape. Preserve aperture boundary topology through LOD0 simplification.
    for ob in list(objects):
        if ob['part']=='helmet':discard(ob)
    rows=[(1.365,.085,.113),(1.40,.105,.137),(1.48,.114,.153),(1.535,.116,.154),
          (1.565,.117,.148),(1.59,.114,.141),(1.63,.095,.119),(1.66,.067,.087),(1.68,.028,.035)]
    vs=[];fs=[];N=48
    for j,(y,rx,rz) in enumerate(rows):
        for i in range(N):
            a=i*math.tau/N;front=math.cos(a)
            # Nape flares away from the neck; cheek edges taper toward the jaw.
            flare=.024*max(0,-front)*(1-j/2) if j<2 else 0
            lower_lift=(.09 if j==0 else .065 if j==1 else 0)*(1-front)/2
            brow_lift=.016*abs(math.sin(2*a)) if j in {3,4} else 0
            vs.append(((rx+flare)*math.sin(a),y+lower_lift+brow_lift,.006+(rz+flare)*front+.021*max(0,front)**20))
    for j in range(len(rows)-1):
        for i in range(N):
            a=(i+.5)*math.tau/N;front=math.cos(a)>.36
            if j==3 and front and abs(math.sin(a))>.135:continue
            if j<3 and front and abs(math.sin(a))<(.27 if j<2 else .15):continue
            k=j*N+i;l=j*N+(i+1)%N;fs.append((k,l,l+N,k+N))
    fs.append(tuple((len(rows)-1)*N+i for i in range(N)))
    ob=mesh('helmet:Corinthian jaw and flared nape',vs,fs,'bronze','helmet');ob['keep_contour']=True
    # Rolled boundaries supply physical thickness without duplicating the shell.
    for side in [-1,1]:
        pts=[(side*.026,1.532,.169),(side*.033,1.478,.160),(side*.031,1.405,.145),(side*.048,1.371,.118)]
        tube('helmet:jaw rim',pts,[.004]*4,'gold','helmet',seg=6)
        pts=[(.117*math.sin(side*a),1.568+.016*math.sin(a*2),.006+.150*math.cos(a)+.015*max(0,math.cos(a))**18) for a in np.linspace(.07,1.30,16)]
        tube('helmet:arched brow',pts,[.004]*16,'gold','helmet',seg=6)
    sphere('helmet:dark inner T',(0,1.505,.010),(.094,.127,.124),'dark','helmet',seg=16,rings=8)

    # Full cloak from the two shoulders, with no flat collar-disc. The rear
    # fabric uses the approved three cape bones; the yoke follows the chest.
    for ob in list(objects):
        if ob['part']=='cloak':discard(ob)
    def cape_weights(t):
        keys=[(0,'chest'),(.20,'cape1'),(.52,'cape2'),(.82,'cape3'),(1,'cape3')]
        for (lo,a),(hi,b) in zip(keys,keys[1:]):
            if lo<=t<=hi:
                f=(t-lo)/(hi-lo)
                return [(bones.index(a),1)] if a==b else [(bones.index(a),1-f),(bones.index(b),f)]
        raise ValueError(t)
    vs=[];fs=[];ww=[];N=40;rows=20
    for j in range(rows+1):
        t=j/rows;width=.285+.145*math.sin(t*math.pi/2)
        for i in range(N+1):
            u0=i/N*2-1;fold=(.010+.027*t)*math.cos(u0*math.pi*5+.6*t)
            vs.append((u0*width,1.365-.875*t+.018*t*math.cos(u0*math.pi),-.166-.040*t+fold+.135*u0*u0))
            ww.append(cape_weights(t))
    for j in range(rows):
        for i in range(N):a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
    for edge in [False,True]:
        faces=[f for i,f in enumerate(fs) if (i%N in (0,N-1))==edge]
        used=sorted(set(k for f in faces for k in f));remap={v:i for i,v in enumerate(used)}
        ob=mesh('cloak:team edge' if edge else 'cloak:deep wool folds',[vs[k] for k in used],[[remap[k] for k in f] for f in faces],
                'mask' if edge else 'red',team='cloak trim' if edge else None,weights=[ww[k] for k in used])
        apply(ob,'SOLIDIFY',thickness=.004,offset=-1)
    # Two folded shoulder panels, drawn over the sleeve tops into the rear cloth.
    for side in [-1,1]:
        vs=[];fs=[]
        for j in range(8):
            t=j/7;z=.13-.31*t
            for i in range(7):
                u0=i/6;x=side*(.095+.19*u0)
                y=1.385-.043*u0+.012*math.sin(t*math.pi*4)*math.sin(u0*math.pi)
                vs.append((x,y,z))
        for j in range(7):
            for i in range(6):a=j*7+i;fs.append((a,a+1,a+8,a+7))
        ob=mesh('cloak:folded shoulder '+str(side),vs,fs,'red','chest');apply(ob,'SOLIDIFY',thickness=.004)
        sphere('cuirass:cloak brooch',(side*.17,1.38,.125),(.018,.018,.007),'gold','chest',seg=12,rings=6)

    # Dark roots and finer painted streaks on the retained full horsehair arc.
    hair=ctx['M']['hair'];nodes=hair.node_tree.nodes;links=hair.node_tree.links
    angle=next(n for n in nodes if n.type=='MATH' and n.operation=='ARCTAN2')
    freq=next(l.to_node for l in angle.outputs[0].links);freq.inputs[1].default_value=180
    geo=next(n for n in nodes if n.type=='NEW_GEOMETRY')
    sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
    y=nodes.new('ShaderNodeMath');y.operation='SUBTRACT';y.inputs[1].default_value=1.545;links.new(sep.outputs['Y'],y.inputs[0])
    vec=nodes.new('ShaderNodeCombineXYZ');links.new(y.outputs[0],vec.inputs[0]);links.new(sep.outputs['Z'],vec.inputs[1])
    length=nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';links.new(vec.outputs[0],length.inputs[0])
    ramp=nodes.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.16;ramp.inputs['From Max'].default_value=.31;ramp.inputs['To Min'].default_value=.18;ramp.inputs['To Max'].default_value=1.1;links.new(length.outputs['Value'],ramp.inputs[0])
    multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    links.new(nodes[hair['paint_node']].outputs[0],multiply.inputs[1]);links.new(ramp.outputs[0],multiply.inputs[2]);links.new(multiply.outputs[0],next(n for n in nodes if n.type=='EMISSION').inputs[0]);hair['paint_node']=multiply.name
    # Fine irregular silhouette tips are a cheap connected edge, not floating spikes.
    for ob in objects:
        if ob['part']=='crest':
            for vert in ob.data.vertices:
                p=vert.co;a=math.atan2(p.y-1.545,p.z-.002);radius=math.hypot(p.y-1.545,p.z-.002)
                if radius>.275:
                    delta=.0035*math.sin(a*83)+.0015*math.sin(a*137)
                    p.y+=delta*math.sin(a);p.z+=delta*math.cos(a)
