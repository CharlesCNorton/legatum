"""Fit full-depth aircraft parts, then finish their actual surfaces before UVs.
All registration edits are mesh coordinates. Camera depth is retained; no alpha
cutout, live camera mapping, or image-plane geometry substitutes for the model.
"""
import bpy, bmesh, json, os, math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

M = Path(os.environ['ANIM_ROOT']) / 'masters/biplane'
bpy.ops.wm.open_mainfile(filepath=str(M / 'biplane.blend'))
sc = bpy.context.scene
assert not sc.get('registered_round2'), 'Rebuild before registering again'
bpy.context.view_layer.update()
cam = sc.camera
right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
view = cam.matrix_world.to_3x3() @ Vector((0, 0, 1))
unit = cam.data.ortho_scale / 256
records = []

def screen(world):
    p = world_to_camera_view(sc, cam, world)
    return Vector((256*p.x, 256*(1-p.y)))

def offset(world, dx, dy):
    return world + unit*(right*dx - up*dy)

def edit(o, fn):
    inv = o.matrix_world.inverted()
    for v in o.data.vertices:
        world = o.matrix_world @ v.co
        v.co = inv @ fn(world, screen(world))
    o.data.update()

def bounds(o):
    ps = [screen(o.matrix_world @ v.co) for v in o.data.vertices]
    return [min(p.x for p in ps), min(p.y for p in ps),
            max(p.x for p in ps), max(p.y for p in ps)]

def bound_map(old, new):
    def fit(world, p):
        x = new[0]+(p.x-old[0])*(new[2]-new[0])/(old[2]-old[0])
        y = new[1]+(p.y-old[1])*(new[3]-new[1])/(old[3]-old[1])
        return offset(world, x-p.x, y-p.y)
    return fit

# Curves become genuine solid tubes. Apply geometry-generating modifiers first;
# projection on the un-beveled cage would move when Blender evaluates the bevel.
for o in list(sc.objects):
    if not o.name.startswith('GEO-') or o.type not in ('MESH', 'CURVE'):
        continue
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    if o.type == 'CURVE':
        bpy.ops.object.convert(target='MESH')
    for mod in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # Ensure closed lathe/wing surfaces shade from outward-facing normals.
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free()

upper = bpy.data.objects['GEO-upper-cambered-wing']
lower = bpy.data.objects['GEO-lower-cambered-wing']
upper_fit = bound_map(bounds(upper), [13, 20, 208, 94])
lower_fit = bound_map(bounds(lower), [18, 81, 209, 155])
body = bpy.data.objects['GEO-tapered-fuselage']
body_fit = bound_map(bounds(body), [54, 70, 223, 124])
cowl = bpy.data.objects['GEO-engine-cowling']
cowl_fit = bound_map(bounds(cowl), [39, 69, 83, 124])
fin_fit = bound_map(bounds(bpy.data.objects['GEO-vertical-tail']), [196, 45, 232, 82])

# Register each actual strut attachment, including its two solid brass shoes.
# The source has four interplane struts. Earlier construction accidentally made
# two coincident copies, and a bounds-only wing fit reversed their visible rake.
strut_targets=[((138,129),(147,84)),((164,137),(173,91)),
               ((42,86),(34,36)),((62,81),(59,46))]
strut_fits={};shoe_offsets=[]
for index,targets in enumerate(strut_targets):
    name='GEO-varnished-interplane-strut'+(f'.{index:03}' if index else '')
    o=bpy.data.objects[name]
    # Match the broad varnished spar face, retaining its closed cross section.
    for vertex in o.data.vertices:
        vertex.co.x *= 1.24
        vertex.co.y *= 1.24
    lo=min(v.co.z for v in o.data.vertices);hi=max(v.co.z for v in o.data.vertices)
    ends=[o.matrix_world@Vector((0,0,z)) for z in (lo,hi)]
    shifts=[Vector(target)-screen(w) for target,w in zip(targets,ends)]
    inv=o.matrix_world.inverted()
    def fit(world,p,lo=lo,hi=hi,inv=inv,shifts=shifts):
        t=max(0,min(1,((inv@world).z-lo)/(hi-lo)))
        d=shifts[0].lerp(shifts[1],t)
        return offset(world,d.x,d.y)
    strut_fits[name]=fit
    shoe_offsets.extend(zip(ends,shifts))

for o in list(sc.objects):
    if o.type != 'MESH' or not o.name.startswith('GEO-'):
        continue
    before = bounds(o); name = o.name
    if name.startswith('GEO-upper-cambered'): edit(o, upper_fit)
    elif name.startswith('GEO-lower-cambered'): edit(o, lower_fit)
    elif name.startswith('GEO-stitched-wing-rib'):
        z = sum(v.co.z for v in o.data.vertices)/len(o.data.vertices)
        edit(o, upper_fit if z > 0 else lower_fit)
    elif name in strut_fits: edit(o,strut_fits[name])
    elif name.startswith('GEO-strut-brass-shoe'):
        centre=o.matrix_world.translation
        point,delta=min(shoe_offsets,key=lambda pair:(pair[0]-centre).length)
        edit(o,lambda w,p:offset(w,delta.x,delta.y))
    elif name.startswith('GEO-cabane-strut'):
        edit(o,body_fit)
    elif name.startswith(('GEO-engine-cowling', 'GEO-cowling-bright', 'GEO-engine-hub', 'GEO-radial-cylinder', 'GEO-cooling-fin', 'GEO-propeller-shaft')):
        edit(o, cowl_fit)
    elif name.startswith(('GEO-tapered-fuselage', 'GEO-fuselage-panel-seam', 'GEO-rivet', 'GEO-seat-', 'GEO-cockpit-coaming', 'GEO-synchronized-gun')):
        edit(o, body_fit)
    elif name == 'GEO-horizontal-tail': edit(o, bound_map(before, [175, 60, 244, 94]))
    elif name == 'GEO-vertical-tail': edit(o, fin_fit)
    elif name.startswith('GEO-rudder-seam'): edit(o, fin_fit)
    # Wheels are already close: preserve true circular wheel geometry/axles.
    after = bounds(o)
    if any(abs(a-b)>.01 for a,b in zip(before,after)):
        records.append({'object':name,'before':before,'after':after})

# The source has small dull hubs, not prominent polished brass buttons.
for o in sc.objects:
    if o.name.startswith('GEO-wheel-brass-hub'):
        for vertex in o.data.vertices:
            vertex.co.x *= .70
            vertex.co.z *= .70
        o.data.materials[0] = bpy.data.materials['MAT-rubbed-steel']

# Shorten both solid blades around the spindle, not in image space. Move the
# spindle with its boss; propeller rotation remains about its real mechanical axis.
prop = bpy.data.objects['RIG-propeller']
for o in prop.children:
    if o.name.startswith('GEO-laminated-propeller'):
        o.location *= .70
        for v in o.data.vertices: v.co *= .70
prop_world = prop.matrix_world.translation.copy()
prop.location = prop.parent.matrix_world.inverted() @ offset(prop_world, -4, -10)

# Rebuild the swept support as a full solid with horizontal cross sections and
# real depth. Centre follows the source's curved silhouette at fixed world heights.
support = bpy.data.objects['GEO-curved-display-support']
oldmesh = support.data
levels = [(0,112,208,36),(.15,105,195,25),(.37,106,178,15),
          (.61,115,158,9),(.84,125,140,8),(1,128,130,8)]
vs=[]
forward = Vector((view.x,view.y,0)).normalized()
for i in range(33):
    t=i/32
    a,b=next((a,b) for a,b in zip(levels,levels[1:]) if a[0]<=t<=b[0])
    j=levels.index(a);s=(t-a[0])/(b[0]-a[0]);dt=b[0]-a[0]
    prev=levels[max(0,j-1)];after=levels[min(len(levels)-1,j+2)]
    def cubic(k):
        ma=(b[k]-prev[k])/(b[0]-prev[0]);mb=(after[k]-a[k])/(after[0]-a[0])
        return (2*s**3-3*s*s+1)*a[k]+(s**3-2*s*s+s)*dt*ma+(-2*s**3+3*s*s)*b[k]+(s**3-s*s)*dt*mb
    x,y,width=[cubic(k) for k in (1,2,3)]
    z=.13+1.46*t
    centre=offset(Vector((0,0,z)), x-screen(Vector((0,0,z))).x,
                  y-screen(Vector((0,0,z))).y)
    centre += view*((z-centre.z)/view.z)
    for side,depth in [(-1,-1),(1,-1),(1,1),(-1,1)]:
        vs.append(centre + right*(side*width*.5*unit) + forward*(depth*.065))
fs=[]
for i in range(32):
    for j in range(4): fs.append((4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j))
fs += [(3,2,1,0),(128,129,130,131)]
me=bpy.data.meshes.new('Curved full-depth limestone support');me.from_pydata(vs,[],fs);me.update()
me.materials.append(oldmesh.materials[0]);support.data=me
for polygon in me.polygons: polygon.use_smooth=True
bpy.context.view_layer.objects.active=support
be=support.modifiers.new('Rounded stone edge','BEVEL');be.width=.012;be.segments=3
bpy.ops.object.modifier_apply(modifier=be.name)
# Three closed stone sections coincide at their fracture faces at rest. They can
# break and settle as actual solid pieces, without deleting or shrinking geometry.
original=support.data.copy()
for index,(bottom,top) in enumerate(((0,.62),(.62,1.10),(1.10,2))):
 bm=bmesh.new();bm.from_mesh(original)
 for height,inner in ((bottom,True),(top,False)):
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,
                        plane_co=(0,0,height),plane_no=(0,0,1),
                        clear_inner=inner,clear_outer=not inner)
  edges=[e for e in bm.edges if e.is_boundary]
  if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 data=bpy.data.meshes.new('Solid stone fracture section');bm.to_mesh(data);bm.free()
 data.materials.append(original.materials[0])
 if index==0:support.data=data;piece=support
 else:
  piece=bpy.data.objects.new('GEO-curved-display-support',data);sc.collection.objects.link(piece)
 piece['stone_section']=index
bpy.data.meshes.remove(original)
# One stationary round disc. Translate on the ground, retaining its horizontal
# plane, rather than fitting its ellipse with a flattened screen-space transform.
base=bpy.data.objects['GEO-cream-stone-base']
base.location += forward*(5.0*unit / up.dot(forward)) - right*(2*unit)
base.scale.x=base.scale.y=.965

# Standard preserves the painting's display pigment; product lights are reduced
# because the painted layer already encodes illumination. Physical backs remain lit.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
for o in sc.objects:
    if o.type=='LIGHT': o.data.energy *= .55
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
for ma in bpy.data.materials:
    if not ma.use_nodes: continue
    for n in ma.node_tree.nodes:
        if n.type=='BUMP':
            n.inputs['Distance'].default_value=.0015
            n.inputs['Strength'].default_value=.10
sc['registered_round2']=True
bpy.context.view_layer.update()
(M/'registration.json').write_text(json.dumps(records,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'biplane.blend'))
print('REGISTERED',len(records),'full-depth parts; finished surfaces; unchanged camera')
