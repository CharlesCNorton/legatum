"""Round-two bind-space form pass. No rig, joint or animation edits.

All distances are metres in the approved source's Y-up bind coordinates.
"""
import math
import numpy as np
import bpy
from mathutils import Vector


def refine(ctx):
    objects=ctx['objects'];g=ctx['g'];bones=ctx['bones']
    mesh=ctx['mesh'];tube=ctx['tube'];sphere=ctx['sphere'];apply=ctx['apply']
    inv=np.array(g.accessor(g.doc['skins'][0]['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    centers={name:Vector(np.linalg.inv(m)[:3,3]) for name,m in zip(bones,inv)}
    pairs={}
    for side in ['L','R']:
        for a,b,gain in [('arm','forearm',2.05),('forearm','hand',1.70),('thigh','leg',1.28),('leg','foot',1.30)]:
            pairs[a+'_'+side]=(centers[a+'_'+side],centers[b+'_'+side],gain)

    def discard(ob):
        objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)

    # Grow radial tissue around each native limb, blending the original weights.
    # Hands/feet and all bone endpoints keep their approved grip/contact location.
    for ob in list(objects):
        if ob['part']=='body':
            if ob['mat']=='linen':
                discard(ob);continue
            cape=ob['mat']=='red' or bool(ob['team'])
            if cape:
                # Native shoulder scarf stays; replace the hanging cape and trim.
                if min(v.co.y for v in ob.data.vertices)<1.20:
                    discard(ob);continue
            for v in ob.data.vertices:
                before=v.co.copy();delta=Vector()
                for group in v.groups:
                    name=ob.vertex_groups[group.group].name
                    if name not in pairs:continue
                    a,b,gain=pairs[name];axis=b-a;t=max(0,min(1,(before-a).dot(axis)/axis.length_squared))
                    c=a+axis*t;radial=before-c
                    # No length extension. Keep the wrist, ankle and joints compact.
                    envelope=.35+.65*math.sin(math.pi*t)**.55
                    delta+=radial*((gain-1)*envelope*group.weight)
                v.co+=delta
                if ob['mat']=='linen' and .56<v.co.y<.86:
                    angle=math.atan2(v.co.z,v.co.x)
                    fold=.009*math.sin(angle*16+v.co.y*4)
                    v.co.x+=fold*math.cos(angle);v.co.z+=fold*math.sin(angle)
        elif ob['part']=='cuirass':
            # All borders and decoration travel with the armour expansion.
            for v in ob.data.vertices:
                y=v.co.y;t=max(0,min(1,(y-.89)/.40));v.co.x*=1.10+.13*math.sin(t*math.pi/2);v.co.z*=1.22
                if v.co.z>0 and 'border' not in ob.name and 'engraving' not in ob.name and 'palmette' not in ob.name and 'rivet' not in ob.name and 'edge' not in ob.name:
                    # Muscular breast and abdominal plates sculpted into the shell.
                    x=v.co.x
                    v.co.z+=.022*math.exp(-((abs(x)-.115)/.075)**2-((y-1.18)/.065)**2)
                    v.co.z+=.014*math.exp(-((abs(x)-.055)/.038)**2)*(math.exp(-((y-1.035)/.035)**2)+math.exp(-((y-1.10)/.035)**2))
            if ob.name=='GEO-cuirass':apply(ob,'SUBSURF',levels=1)
        elif ob['part'].startswith('greave_'):
            side=ob['part'][-1];a,b,_=pairs['leg_'+side]
            for v in ob.data.vertices:
                t=max(0,min(1,(v.co.y-.10)/.32));c=a+(b-a)*max(0,min(1,(a.y-v.co.y)/(a.y-b.y)))
                v.co.x=c.x+(v.co.x-c.x)*(1.20+.10*math.sin(t*math.pi))
                v.co.z=c.z+(v.co.z-c.z)*(1.05+.12*math.sin(t*math.pi))
            if ':' not in ob.name:apply(ob,'SUBSURF',levels=1)
        elif ob['part']=='crest':discard(ob)

    # Rounded short linen sleeves replace the old fragmented shoulder facets.
    for side in ['L','R']:
        origin,end,_=pairs['arm_'+side];axis=(end-origin).normalized()
        across=axis.cross(Vector((0,0,1))).normalized();forward=across.cross(axis).normalized()
        vs=[];fs=[];segments=32;rows=8
        for j in range(rows+1):
            t=j/rows;c=origin+axis*(-.025+.155*t)
            radius=.071+.018*math.sin(t*math.pi)
            for i in range(segments):
                a=i*math.tau/segments;r=radius+.0035*math.sin(a*8+t*3)
                vs.append(c+across*(r*math.cos(a))+forward*(r*math.sin(a)))
        for j in range(rows):
            for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
        ob=mesh('sleeve:folded linen '+side,vs,fs,'linen','arm_'+side);apply(ob,'SOLIDIFY',thickness=.003)

    # Linen falls in full pleats beneath the leather pteruges. Broad fold shape
    # is geometry; the high-resolution bake contributes only surface grain.
    vs=[];fs=[];ww=[];segments=64;rows=10
    for j in range(rows+1):
        t=j/rows
        for i in range(segments):
            a=i*math.tau/segments;fold=(.004+.012*t)*math.cos(a*16+.25*t)
            x=(.176+.085*t+fold)*math.cos(a);z=(.143+.050*t+fold)*math.sin(a)
            vs.append((x,.875-.29*t+.008*t*math.cos(a*16),z))
            leg='thigh_L' if x>=0 else 'thigh_R';w=.65*t
            ww.append([(bones.index('hip'),1-w),(bones.index(leg),w)])
    for j in range(rows):
        for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
    ob=mesh('linen:pleated tunic',vs,fs,'linen',weights=ww);apply(ob,'SOLIDIFY',thickness=.003)

    # Bronze kneecaps and shaped shin ridges, not a straight cylindrical boot.
    for side in ['L','R']:
        c=centers['leg_'+side]
        sphere('greave_'+side+':knee',(c.x,.445,c.z+.037),(.071,.060,.047),'bronze','leg_'+side,seg=20,rings=10)
        sphere('greave_'+side+':knee boss',(c.x,.448,c.z+.080),(.024,.030,.010),'gold','leg_'+side,seg=16,rings=8)
        tube('greave_'+side+':knee brow',[(c.x+.064*math.cos(t),.446+.053*math.sin(t),c.z+.057) for t in np.linspace(0,math.pi,17)],[.0035]*17,'gold','leg_'+side,seg=6)

    # Continuous rounded under-mass stops the separated tips reading as spikes.
    vs=[];fs=[];arc_count=64;cross_count=10
    for i in range(arc_count+1):
        a=.035+(math.pi-.07)*i/arc_count
        for k in range(cross_count):
            q=k*math.tau/cross_count;ripple=.003*math.sin(i*2.4)
            vs.append((.039*math.sin(q),1.57+(.235+(.085+ripple)*math.cos(q))*math.sin(a),.012+(.198+.054*math.cos(q))*math.cos(a)-.008))
    for i in range(arc_count):
        for k in range(cross_count):a=i*cross_count+k;b=i*cross_count+(k+1)%cross_count;fs.append((a,b,b+cross_count,a+cross_count))
    mesh('crest:rounded hair mass',vs,fs,'mask','helmet','crest')

    # Rounded full horsehair tufts distributed along a sagittal arc. Three staggered
    # rows make a thick base and a broken fluffy edge, not one extruded fan plate.
    for row in range(3):
        for i in range(35):
            a=.035+(math.pi-.07)*(i+.28*(row%2))/35
            phase=i*2.399+row*1.17;vs=[];fs=[];rings=4;segments=5
            for j in range(rings):
                t=j/(rings-1);sweep=a+.10*t
                height=.145+.188*t+.008*t*math.sin(phase)
                y=1.57+height*math.sin(sweep)
                z=.012+(.15+.10*t)*math.cos(sweep)-.018*t*math.sin(a)
                x=(row-1)*(.021+.016*t)+.004*t*math.sin(phase)
                thick=[.009,.012,.008,.002][j]
                for k in range(segments):
                    q=k*math.tau/segments
                    vs.append((x+thick*math.cos(q),y+thick*.63*math.cos(sweep)*math.sin(q),z-thick*.63*math.sin(sweep)*math.sin(q)))
            for j in range(rings-1):
                for k in range(segments):
                    a0=j*segments+k;b=j*segments+(k+1)%segments;fs.append((a0,b,b+segments,a0+segments))
            fs.extend([tuple(range(segments-1,-1,-1)),tuple((rings-1)*segments+k for k in range(segments))])
            mesh('crest:horsehair tuft',vs,fs,'mask','helmet','crest')

    # Broad knee-length wool cloak with convex pleats and a deliberately dark lining.
    # Same three approved cape bones, blended by height; shoulder tops follow chest.
    def cape_weights(t):
        keys=[(0,'chest'),(.12,'cape1'),(.47,'cape2'),(.80,'cape3'),(1,'cape3')]
        for (ta,ba),(tb,bb) in zip(keys,keys[1:]):
            if ta<=t<=tb:
                f=(t-ta)/(tb-ta)
                if ba==bb:return [(bones.index(ba),1)]
                return [(bones.index(ba),1-f),(bones.index(bb),f)]
        raise ValueError(t)
    vs=[];fs=[];weights=[];rows=22;cols=40
    for j in range(rows+1):
        t=j/rows;width=.25+.17*math.sin(t*math.pi/2)
        for i in range(cols+1):
            u=i/cols*2-1;x=u*width;y=1.335-.82*t+.025*t*math.cos(u*math.pi)
            fold=.024*math.sin(u*math.pi*5+.4*t)*(.25+.75*t)
            z=-.140-.070*t+fold+.32*u*u*t
            vs.append((x,y,z));weights.append(cape_weights(t))
    for j in range(rows):
        for i in range(cols):a=j*(cols+1)+i;fs.append((a,a+1,a+cols+2,a+cols+1))
    ob=mesh('cloak:wool folds',vs,fs,'red',weights=weights)
    # A surface offset lining preserves deep red interior without another material at runtime.
    lining=mesh('cloak:dark lining',[(x,y,z+.008) for x,y,z in vs],[tuple(reversed(f)) for f in fs],'red',weights=weights)
    lining.data.materials.clear();lining.data.materials.append(ctx['material']('Burgundy cloak lining',(.075,.003,.004),.98,0,140))
    # Add it to the bake palette so the single packed ORM also covers the lining.
    ctx['M']['lining']=lining.data.materials[0]
    for edge in [-1,1]:
        trim=[];tw=[]
        for j in range(rows+1):
            t=j/rows
            for delta in [0,.012]:
                x,y,z=vs[j*(cols+1)+(0 if edge<0 else cols)];trim.append((x-edge*delta,y,z-.002));tw.append(cape_weights(t))
        mesh('cloak:team trim',trim,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(rows)],'mask',team='cloak trim',weights=tw)
    # Clasps and folded shoulder mantle tie the broadened torso into the cloak.
    for side in [-1,1]:
        sphere('cuirass:cloak clasp',(side*.19,1.30,.09),(.024,.024,.012),'gold','chest',seg=16,rings=8)

    vs=[];fs=[];ww=[]
    for j in range(5):
        t=j/4
        for i in range(48):
            a=i*math.tau/48
            vs.append(((.095+.16*t)*math.cos(a),1.46-.165*t+.009*math.sin(t*math.pi*4),(.088+.057*t)*math.sin(a)))
            ww.append([(bones.index('neck'),.85*(1-t)),(bones.index('chest'),.15+.85*t)])
    for j in range(4):
        for i in range(48):a=j*48+i;b=j*48+(i+1)%48;fs.append((a,b,b+48,a+48))
    ob=mesh('cloak:shoulder mantle',vs,fs,'red',weights=ww);apply(ob,'SOLIDIFY',thickness=.004)

    # Measured high-poly copies are captured before the low-poly simplification.
    # The main builder adds micro-displacement and performs the Cycles transfers.
