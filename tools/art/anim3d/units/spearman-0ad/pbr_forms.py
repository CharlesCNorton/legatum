"""Round-two rest-space silhouette work. Never edits the skeleton or clips."""
from math import sin, cos, pi, exp, atan2
from mathutils import Vector


def bulk_body(ob, g, bones):
    worlds = g.worlds(None, 0)
    points = {name: Vector(worlds[g.doc['skins'][0]['joints'][i]][12:15])
              for name, i in bones.items()}
    segments = {}
    for side in ('L', 'R'):
        for first, last, scale in [('arm', 'forearm', 1.90), ('forearm', 'hand', 1.40),
                                   ('thigh', 'leg', 1.32), ('leg', 'foot', 1.25)]:
            segments[bones[first+'_'+side]] = (points[first+'_'+side], points[last+'_'+side], scale)
    for vertex in ob.data.vertices:
        p = vertex.co.copy()
        weights = {int(ob.vertex_groups[w.group].name[1:]): w.weight for w in vertex.groups}
        cape = sum(weights.get(i, 0) for i in (4, 5, 6))
        if cape > .2:
            # Broad shoulder-to-knee wool, with deep irregular vertical folds.
            spread = 1.65 + .35 * max(0, min(1, (1.30-p.y)/.7))
            vertex.co.x *= 1 + (spread-1)*cape
            vertex.co.z -= .085*cape
            vertex.co.z += (.024*sin(p.x*70+p.y*1.8)+.009*sin(p.x*132-p.y*3))*cape
            continue
        delta = Vector()
        for j, (a, b, factor) in segments.items():
            axis = b-a
            t = max(0, min(1, (p-a).dot(axis)/axis.length_squared))
            radial = p-(a+axis*t)
            # The wrist, elbow and ankle transition taper into unchanged joints.
            envelope = .25 + .75*sin(pi*t)**.65
            delta += radial*((factor-1)*envelope*weights.get(j, 0))
        torso = sum(weights.get(i, 0) for i in (0, 1, 2, 3, 9, 16))
        if p.y > .86:
            delta.x += p.x*.25*torso
            delta.z += (p.z-.015)*.28*torso
        vertex.co += delta
        # Folds on the short tunic, retaining its native topology and weights.
        if .55 < p.y < .87 and abs(p.x)<.28:
            a = atan2(p.z, p.x)
            f = sin(pi*(p.y-.55)/.32)
            vertex.co.x += .012*cos(a)*sin(a*15)*f
            vertex.co.z += .012*sin(a)*sin(a*15)*f


def crest(mesh, mod, tube, material):
    hair = material('team', 'crest', 'helmet', 'crest')
    dark = material('darkbronze', 'crest_base', 'helmet')
    # Rounded volumetric cross-section along a front-to-back sagittal arc.
    # The irregular tip line comes from actual geometry, not alpha clipping.
    n, k = 52, 10
    verts, faces = [], []
    for i in range(n+1):
        t = -.12+(pi+.20)*i/n
        radius = .322 + .006*sin(i*2.17)+.003*cos(i*4.1)
        for j in range(k):
            a = 2*pi*j/k
            f = (1+cos(a))/2
            ry = .153*(1-f)+radius*f
            rz = .142*(1-f)+.239*f
            width = (.048*(1-f)+.032*f)*(sin(pi*i/n)*.25+.75)
            verts.append((width*sin(a),1.57+ry*sin(t),.006+rz*cos(t)))
    for i in range(n):
        for j in range(k):faces.append((i*k+j,i*k+(j+1)%k,(i+1)*k+(j+1)%k,(i+1)*k+j))
    faces.extend([tuple(reversed(range(k))),tuple(n*k+j for j in range(k))])
    ob=mesh('full horsehair arc',verts,faces,hair,'helmet')
    mod(ob,'SUBSURF',levels=1);mod(ob,'DECIMATE',ratio=.48)
    # Layered clumps splay outward, then bend back into individual tapered tips.
    for side in (-1,1):
        for i in range(45):
            t = -.1+(pi+.17)*i/44
            length = .307+.009*sin(i*1.97)
            points=[(side*.035,1.57+.162*sin(t),.006+.15*cos(t)),
                    (side*.047,1.57+.23*sin(t),.006+.20*cos(t)),
                    (side*(.031+.006*sin(i*1.7)),1.57+length*sin(t),.006+.244*cos(t)),
                    (side*.025,1.57+(length+.007)*sin(t+.018),.006+.241*cos(t+.018))]
            tube('tapered horsehair lock',points,[.0045,.005,.003,.0018],hair,'helmet',5)
    tube('crest mounting rail',[(0,1.57+.146*sin(t),.006+.142*cos(t))
                               for t in [(-.12+(pi+.20)*i/32) for i in range(33)]],
         [.017]*33,dark,'helmet',8)


def cuirass(mesh, mod, tube, material, torso_weights):
    bronze=material('bronze','muscle cuirass')
    edge=material('edge','muscle cuirass')
    verts,faces=[],[]
    rows=[(.902,.190,.139),(.925,.198,.151),(.98,.205,.155),(1.04,.213,.161),
          (1.10,.228,.17),(1.16,.247,.174),(1.22,.254,.168),(1.27,.246,.148),
          (1.31,.218,.119),(1.34,.171,.081)]
    n=40
    for y,rx,rz in rows:
        for i in range(n):
            a=2*pi*i/n;x=rx*cos(a);z=rz*sin(a)
            if sin(a)>0:
                # Sculpted pectorals, abdominal lobes and a narrow sternum groove.
                pec=.030*exp(-((abs(x)-.105)/.071)**2-((y-1.214)/.058)**2)
                ab=.014*exp(-((abs(x)-.058)/.045)**2)*sum(exp(-((y-h)/.024)**2) for h in (1.02,1.08,1.14))
                z+=(pec+ab-.009*exp(-(x/.017)**2))*sin(a)
            verts.append((x,y,z+.006))
    for row in range(len(rows)-1):
        for i in range(n):faces.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
    ob=mesh('sculpted muscle cuirass',verts,faces,bronze,weights=torso_weights(verts))
    mod(ob,'SOLIDIFY',thickness=.005,offset=-1)
    mod(ob,'SUBSURF',levels=1);mod(ob,'DECIMATE',ratio=.38)
    # Broad shaped hems follow the same continuous torso weights.
    for y,rx,rz in (rows[0],rows[-1]):
        ob=tube('cuirass finished hem',[(rx*cos(a),y,rz*sin(a)+.006) for a in [2*pi*i/40 for i in range(41)]],[.004]*41,edge,'chest',6)
        ob.vertex_groups.clear()
        for j in range(30):ob.vertex_groups.new(name='j'+str(j))
        for v,ws in zip(ob.data.vertices,torso_weights([v.co for v in ob.data.vertices])):
            for j,w in ws.items():ob.vertex_groups['j'+str(j)].add([v.index],w,'REPLACE')


def cloak(mesh, material):
    """A continuous draped surface, using the same three native cape joints."""
    n,m=24,14
    verts,weights,faces=[],[],[]
    for row in range(m+1):
        t=row/m;y=1.34-.83*t
        width=.255+.12*sin(t*pi/2)
        for col in range(n+1):
            u=2*col/n-1
            # Gentle shoulder curve and large alternating folds, tapered at pins.
            z=-.181-.053*t+(.028*sin(u*pi*5)+.009*sin(u*pi*9+.6))*sin(pi*t/2)
            verts.append((u*width*(.72 if u>0 else 1),y-.028*u*u,z))
            if y>1.071:
                f=max(0,min(1,(1.329-y)/(.258)));weights.append({4:1-f,5:f})
            else:
                f=max(0,min(1,(1.071-y)/(.258)));weights.append({5:1-f,6:f})
    for row in range(m):
        for col in range(n):faces.append((row*(n+1)+col,row*(n+1)+col+1,(row+1)*(n+1)+col+1,(row+1)*(n+1)+col))
    wool=material('wool','body');trim=material('team','body',team='cloak trim')
    ob=mesh('wide folded wool cloak',verts,faces,wool,weights=weights)
    ob.data.materials.append(trim)
    for p in ob.data.polygons:
        row,col=divmod(p.index,n)
        if row==m-1 or col in (0,n-1):p.material_index=1
    # A darker dyed lining, with thickness; it follows exactly the outer weights.
    lining=material('wooldark','body')
    mesh('cloak dark lining',[(x,y,z+.004) for x,y,z in verts],
         [tuple(reversed(f)) for f in faces],lining,weights=weights)


def mantle(mesh,material):
    """Continuous folded shoulder wool replaces the torn inherited scarf."""
    verts,faces=[],[]
    n=40
    for row in range(7):
        t=row/6
        for j in range(n):
            a=2*pi*j/n
            rx=.083+.193*t;rz=.09+(.075 if sin(a)>0 else .105)*t
            fold=.007*sin(a*8)*sin(pi*t)
            y=1.438-.122*t-.025*max(0,sin(a))*t+fold
            verts.append((rx*cos(a),y,rz*sin(a)-.01))
    for row in range(6):
        for j in range(n):faces.append((row*n+j,row*n+(j+1)%n,(row+1)*n+(j+1)%n,(row+1)*n+j))
    wool=material('wool','shoulder mantle','chest')
    mesh('folded shoulder mantle',verts,faces,wool,'chest')
