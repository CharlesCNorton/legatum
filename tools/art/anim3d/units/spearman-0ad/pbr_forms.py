"""Round-three rest geometry. The approved skeleton and all clip bytes stay fixed."""
from math import sin, cos, pi, exp
from mathutils import Vector


def crest(mesh, mod, tube, material):
    hair=material('team','crest','helmet','crest')
    dark=material('darkbronze','crest_base','helmet')
    # A single full, scalloped mass. Paired ring samples form rounded locks;
    # unlike independently decimated tubes, no stray triangular tips survive.
    n,k=48,8
    verts,faces=[],[]
    for i in range(n+1):
        t=-.10+(pi+.16)*i/n
        scallop=.0008*sin(i*2*pi/12)
        for j in range(k):
            a=2*pi*j/k;f=(1+cos(a))/2
            ry=.153*(1-f)+(.323+scallop)*f
            rz=.145*(1-f)+(.238+scallop)*f
            width=(.043*(1-f)+.030*f)*(.8+.2*sin(pi*i/n))+.002*cos(i*pi)*sin(a)**2
            verts.append((width*sin(a),1.57+ry*sin(t),.006+rz*cos(t)))
    for i in range(n):
        for j in range(k):faces.append((i*k+j,i*k+(j+1)%k,(i+1)*k+(j+1)%k,(i+1)*k+j))
    faces.extend([tuple(reversed(range(k))),tuple(n*k+j for j in range(k))])
    mesh('full horsehair arc',verts,faces,hair,'helmet')
    tube('crest mounting rail',[(0,1.57+.146*sin(t),.006+.142*cos(t))
         for t in [(-.10+(pi+.16)*i/24) for i in range(25)]],[.014]*25,dark,'helmet',6)


def helmet(mesh,mod,tube,material):
    bronze=material('bronze','helmet','helmet');edge=material('edge','helmet','helmet')
    dark=material('darkbronze','helmet','helmet')
    n=40;verts=[(0,1.708,.003)];faces=[]
    for row in range(1,9):
        theta=row*pi/16
        for j in range(n):
            a=j*2*pi/n
            verts.append((.110*sin(theta)*cos(a),1.56+.148*cos(theta),.003+.143*sin(theta)*sin(a)))
    for j in range(n):faces.append((0,1+j,1+(j+1)%n))
    for row in range(7):
        for j in range(n):faces.append((1+row*n+j,1+(row+1)*n+j,1+(row+1)*n+(j+1)%n,1+row*n+(j+1)%n))
    mesh('helmet dome',verts,faces,bronze,'helmet')
    # Closed cheeks/back surround the face. Only eye slits and mouth are open.
    # Separate fine rows define a brow-to-nose bridge without a flat face slab.
    rows=[(1.568,1.0),(1.548,1.01),(1.528,1.01),(1.485,1.02),(1.440,1.01),(1.402,.93)]
    n=40;verts=[];faces=[]
    for row,(y,scale) in enumerate(rows):
        for j in range(n):
            a=-pi+2*pi*j/n
            # a=0 is face; back flares into the nape guard.
            x=.110*sin(a)*scale;z=.003+.146*cos(a)*scale
            if row>=3 and cos(a)>0:
                # Cheeks sweep toward the mouth rather than hanging as a tube.
                x*=1-.16*(row-2)/3
                z+=.012*(row-2)/3*cos(a)
            if row>=3 and cos(a)<0:z-=.009*(row-2)/3
            yy=y+(.025*max(0,-cos(a)) if row>2 else 0)
            if row in (1,2):yy+=.009*sin(abs(a)*2)
            if row==5:yy+=.055*abs(sin(a))
            verts.append((x,yy,z))
    for row in range(len(rows)-1):
        for j in range(n):
            a=-pi+2*pi*(j+.5)/n
            # Continuous central nasal, narrow eyes, central breathing opening.
            if row==1 and .16<abs(a)<.98:continue
            if row>=3 and abs(a)<.38:continue
            faces.append((row*n+j,row*n+(j+1)%n,(row+1)*n+(j+1)%n,(row+1)*n+j))
    ob=mesh('closed Corinthian face',verts,faces,bronze,'helmet')
    for side in (-1,1):
        tube('arched brow',[(side*.010,1.570,.151),(side*.045,1.573,.143),(side*.091,1.561,.094)], [.0045]*3,edge,'helmet',6)
        # The eye's dark inset is physical geometry behind the real opening.
        eye=[(side*.018,1.548,.142),(side*.095,1.548,.075),(side*.095,1.527,.074),(side*.018,1.527,.141)]
        mesh('eye recess',eye,[(0,1,2,3)],material('leather','helmet','helmet'),'helmet')
        tube('cheek rim',[(side*.037,1.485,.150),(side*.037,1.441,.150),(side*.039,1.404,.139),(side*.098,1.414,.077)], [.0026]*4,edge,'helmet',5)
    tube('nasal keel',[(0,1.570,.156),(0,1.531,.160),(0,1.486,.162)],[.007,.006,.008],edge,'helmet',6)
    tube('helmet lower nape',[(.106*sin(a),1.433,.003+.143*cos(a)) for a in [pi/2+i*pi/16 for i in range(17)]],[.003]*17,dark,'helmet',5)


def cuirass(mesh,mod,tube,material,torso_weights):
    bronze=material('bronze','muscle cuirass');edge=material('edge','muscle cuirass')
    dark=material('darkbronze','muscle cuirass')
    # More sample rows across pec/ab relief, less geometry hidden inside a shell.
    rows=[(.905,.193,.14),(.935,.202,.153),(.970,.210,.16),(1.0,.215,.164),
          (1.035,.219,.168),(1.07,.224,.173),(1.105,.237,.179),(1.14,.253,.185),
          (1.175,.267,.186),(1.21,.272,.180),(1.245,.266,.169),(1.28,.245,.146),
          (1.31,.217,.120),(1.335,.172,.087)]
    n=32;verts=[];faces=[]
    for y,rx,rz in rows:
        for i in range(n):
            a=2*pi*i/n;x=rx*cos(a);z=rz*sin(a)
            if sin(a)>0:
                pec=.043*exp(-((abs(x)-.112)/.078)**2-((y-1.205)/.044)**2)
                ab=.020*exp(-((abs(x)-.060)/.046)**2)*sum(exp(-((y-h)/.021)**2) for h in (1.005,1.065,1.125))
                z+=(pec+ab-.012*exp(-(x/.020)**2))*sin(a)
            verts.append((x,y,z+.006))
    for row in range(len(rows)-1):
        for i in range(n):faces.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
    mesh('sculpted muscle cuirass',verts,faces,bronze,weights=torso_weights(verts))
    def weighted_tube(name,pts,radius,mat):
        ob=tube(name,pts,[radius]*len(pts),mat,'chest',5);ob.vertex_groups.clear()
        for j in range(30):ob.vertex_groups.new(name='j'+str(j))
        for v,ws in zip(ob.data.vertices,torso_weights([v.co for v in ob.data.vertices])):
            for j,w in ws.items():ob.vertex_groups['j'+str(j)].add([v.index],w,'REPLACE')
        return ob
    for y,rx,rz in (rows[0],rows[-1]):
        weighted_tube('cuirass finished hem',[(rx*cos(a),y,rz*sin(a)+.006) for a in [2*pi*i/32 for i in range(33)]],.004,edge)
    # Dark incised pectoral border, with a narrow bright rolled ridge.
    for side in (-1,1):
        pts=[(side*x,y,z) for x,y,z in [(.024,1.183,.195),(.07,1.170,.215),(.14,1.169,.207),(.205,1.187,.157)]]
        weighted_tube('pectoral incised border',pts,.0038,dark)
    # Broad leather belt and bronze piping below the abdominal mass.
    verts=[];faces=[];n=32
    for y in (.901,.945):
        for i in range(n):
            a=2*pi*i/n;verts.append((.211*cos(a),y,.169*sin(a)+.006))
    for i in range(n):faces.append((i,(i+1)%n,n+(i+1)%n,n+i))
    mesh('cuirass waist belt',verts,faces,material('leather','muscle cuirass'),weights=torso_weights(verts))


def chiton(mesh,mod,material):
    n,m=64,4;verts=[];weights=[];faces=[]
    for row in range(m+1):
        t=row/m;y=.92-.315*t
        for j in range(n):
            a=2*pi*j/n;fold=.012*(.3+.7*t)*cos(a*16)
            rx=.205+.080*t+fold;rz=.151+.060*t+fold
            verts.append((rx*cos(a),y+.006*sin(a*3)*t,rz*sin(a)))
            # Upper pleats hang from pelvis; the low skirt softly follows thighs.
            thigh=26 if cos(a)<0 else 23
            weights.append({0:1-.28*t,thigh:.28*t})
    for row in range(m):
        for j in range(n):faces.append((row*n+j,row*n+(j+1)%n,(row+1)*n+(j+1)%n,(row+1)*n+j))
    ob=mesh('pleated linen chiton',verts,faces,material('linen','chiton'),weights=weights)
    # A sewn dark hem has thickness and follows exactly the cloth's skinning.
    hem=material('leather','chiton');ob.data.materials.append(hem)
    for p in ob.data.polygons:
        if p.index//n==m-1:p.material_index=1 if p.index%n%4==0 else 0


def cloak(mesh,material):
    n,m=16,8;verts,weights,faces=[],[],[]
    for row in range(m+1):
        t=row/m;y=1.365-.82*t;width=.27+.11*sin(t*pi/2)
        for col in range(n+1):
            u=2*col/n-1
            # Keep cloth behind torso and armour; no almost-coplanar lining.
            z=-.210-.047*t+(.026*sin(u*pi*5)+.009*sin(u*pi*9+.6))*sin(pi*t/2)
            verts.append((u*width*(.82 if u>0 else 1),y-.028*u*u,z))
            if y>1.071:
                f=max(0,min(1,(1.329-y)/.258));weights.append({4:1-f,5:f})
            else:
                f=max(0,min(1,(1.071-y)/.258));weights.append({5:1-f,6:f})
    for row in range(m):
        for col in range(n):faces.append((row*(n+1)+col,row*(n+1)+col+1,(row+1)*(n+1)+col+1,(row+1)*(n+1)+col))
    wool=material('wool','body');trim=material('team','body',team='cloak trim')
    ob=mesh('wide folded wool cloak',verts,faces,wool,weights=weights);ob.data.materials.append(trim)
    for p in ob.data.polygons:
        row,col=divmod(p.index,n)
        if row==m-1 or col in (0,n-1):p.material_index=1
    lining=material('wooldark','body')
    mesh('cloak dark lining',[(x,y,z+.010) for x,y,z in verts],[tuple(reversed(f)) for f in faces],lining,weights=weights)


def mantle(mesh,material):
    # Compact scarf around neck/upper chest, leaving deltoids naturally exposed.
    # A broad rigid poncho intersected shoulders whenever the approved arms rose.
    verts,faces=[],[];n=32
    for row in range(6):
        t=row/5
        for j in range(n):
            a=2*pi*j/n
            rx=.092+.120*t;rz=.110+.074*t
            y=1.465-.120*t-.026*max(0,sin(a))*t
            fold=.008*sin(a*5+t*11)*sin(pi*t)
            verts.append((rx*cos(a),y+fold,rz*sin(a)-.015))
    for row in range(5):
        for j in range(n):faces.append((row*n+j,row*n+(j+1)%n,(row+1)*n+(j+1)%n,(row+1)*n+j))
    mesh('folded shoulder mantle',verts,faces,material('wool','shoulder mantle','chest'),'chest')
