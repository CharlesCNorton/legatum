"""Full-depth costume fitting before frozen projection; no opacity geometry masks."""
import math
import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view


def skin_in_pose(ob, rig, weights):
    """Bind finished geometry without moving its current posed surface."""
    world = [ob.matrix_world @ v.co for v in ob.data.vertices]
    ob.parent = rig
    ob.parent_type = 'OBJECT'
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = Matrix.Identity(4)
    ob.vertex_groups.clear()
    groups = {name: ob.vertex_groups.new(name=name) for name in weights[0]}
    transforms = {name: rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted()
                  for name in groups}
    for vertex, point, influence in zip(ob.data.vertices, world, weights):
        blend = Matrix([[sum(influence[name] * transforms[name][r][c] for name in groups)
                         for c in range(4)] for r in range(4)])
        vertex.co = blend.inverted() @ rig.matrix_world.inverted() @ point
        for name, weight in influence.items():
            groups[name].add([vertex.index], weight, 'REPLACE')
    mod = ob.modifiers.new('Continuous costume skin', 'ARMATURE')
    mod.object = rig
    ob['pose_bound_costume'] = True
    bpy.context.view_layer.update()


def lined_gusset(sc):
    """Sewn underskirt with two real leg openings, not a hollow cylinder.

    Each half joins the hem's elliptical perimeter to a thigh opening; the
    central seam is welded. The generated linen fills these unseen surfaces.
    """
    vertices, faces = [], []
    for side in [-1, 1]:
        start = len(vertices)
        for row in range(7):
            t = row / 6
            for j in range(64):
                a = -math.pi/2 + j*2*math.pi/64
                outer = Vector((-.107 + side*.248*max(0, math.cos(a)),
                                .215*math.sin(a), .723))
                inner = Vector((-.107 + side*(.125+.077*math.cos(a)),
                                .015+.09*math.sin(a), .84))
                point = outer.lerp(inner, t)
                point.z += .007*math.sin(a*9)*math.sin(math.pi*t)
                vertices.append(point)
        for row in range(6):
            for j in range(64):
                a = start + row*64 + j
                b = start + row*64 + (j+1)%64
                face = (a,b,b+64,a+64)
                faces.append(face if side==1 else tuple(reversed(face)))
    mesh = bpy.data.meshes.new('Sewn linen two-leg lining')
    mesh.from_pydata(vertices, [], faces); mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.0001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free()
    ob=bpy.data.objects.new('Lined tunic gusset',mesh);sc.collection.objects.link(ob)
    material=bpy.data.objects['Ivory hem'].data.materials[0].copy()
    material.name='Linen underside painted fill'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    fill = next(n for n in nodes if n.type=='TEX_IMAGE' and n.image and n.image.name.startswith('fill-linen'))
    # The inside of the robe is dyed plum-brown; it must not become a bright
    # beige plate when the camera sees it during the collapse.
    destinations=[link.to_socket for link in list(fill.outputs['Color'].links)]
    tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY'
    tint.inputs[0].default_value=1;tint.inputs[2].default_value=(.32,.18,.23,1)
    links.new(fill.outputs['Color'],tint.inputs[1])
    for socket in destinations:links.new(tint.outputs[0],socket)
    ob.data.materials.append(material)
    ob.data.uv_layers.new(name='Rest painting')
    ob.data.color_attributes.new(name='Projection facing',type='FLOAT_COLOR',domain='CORNER')
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    mod=ob.modifiers.new('Sewn lining thickness','SOLIDIFY');mod.thickness=.006
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for poly in mesh.polygons:poly.use_smooth=True
    return ob


def finish(sc, rig):
    # Finished leather lasts: the reference has a low, extended toe rather
    # than an ellipsoid sticking out toward the camera. Keep closed volumes.
    for side in ['r', 'l']:
        toe = bpy.data.objects['Leather toe ' + side]
        points = [toe.matrix_world @ v.co for v in toe.data.vertices]
        centre = sum(points, Vector()) / len(points)
        bottom = min(p.z for p in points)
        inv = toe.matrix_world.inverted()
        for vertex, point in zip(toe.data.vertices, points):
            point.x = centre.x + (point.x-centre.x) * (1.25 if side=='r' else .96)
            point.y = centre.y + (point.y-centre.y) * .78 + (.10 if side=='r' else .035)
            point.z = bottom + (point.z-bottom) * .72
            vertex.co = inv @ point
        boot = bpy.data.objects['Tall leather boot ' + side]
        inv = boot.matrix_world.inverted()
        for vertex in boot.data.vertices:
            point = boot.matrix_world @ vertex.co
            amount = max(0, min(1, (.37-point.z)/.16))
            point.y += (.10 if side=='r' else .035)*amount
            point.z -= .018*amount
            vertex.co = inv @ point
    # Lower the back neck edge into the wrapped shoulder mantle. Displace all
    # shape keys equally so its rest thickness and subsequent folds survive.
    up = sc.camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    pixel = sc.camera.data.ortho_scale / 256
    for name, drop in [('Full mantle back', 8), ('Purple shoulder mantle', 3)]:
        ob = bpy.data.objects[name]
        inv = ob.matrix_world.inverted()
        for key in ob.data.shape_keys.key_blocks:
            for vertex in key.data:
                world = ob.matrix_world @ vertex.co
                y = (1 - world_to_camera_view(sc, sc.camera, world).y) * 256
                amount = max(0, min(1, (85 - y) / 30)) ** 2
                vertex.co = inv @ (world - up * drop * pixel * amount)

    # Fit the hair-cap crown to the reference contour in camera space while
    # retaining every vertex's depth. This changes the solid model, never alpha.
    image = next(im for im in bpy.data.images if 'painting-aligned' in im.name)
    width, height = image.size
    pixels = list(image.pixels[:])
    right = sc.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    def fit_outline(world):
        q=world_to_camera_view(sc,sc.camera,world)
        x,y=q.x*256,(1-q.y)*256
        if not (20<=y<=58 and 98<=x<=141):return world
        yy=height-1-round(y*height/256)
        xs=[xx for xx in range(round(99*width/256),round(141*width/256))
            if pixels[4*(yy*width+xx)+3]>.8]
        if not xs:return world
        lo,hi=min(xs)*256/width+.25,max(xs)*256/width-.25
        target=max(lo,min(hi,x))
        return world+right*(target-x)*pixel
    def top_at(x):
        xx = round(x * width / 256)
        if not 101 <= x <= 136:
            return None
        for y in range(round(18 * height / 256), round(43 * height / 256)):
            if pixels[4 * ((height - 1 - y) * width + xx) + 3] > .85:
                return y * 256 / height
        return None
    for ob in sc.objects:
        if not ob.name.startswith(('Sculpted hair cap', 'Sculpted chestnut curl',
                                   'Gold crown', 'Crown cabochon')):
            continue
        inv = ob.matrix_world.inverted()
        for vertex in ob.data.vertices:
            world = ob.matrix_world @ vertex.co
            q = world_to_camera_view(sc, sc.camera, world)
            x, y = q.x * 256, (1 - q.y) * 256
            boundary = top_at(x)
            if boundary is not None and y < boundary + .4:
                world -= up * (boundary + .4 - y) * pixel
            vertex.co = inv @ fit_outline(world)

    # Pixel-placed belt jewels were 12 cm in front of their backing and became
    # detached dots during the fall. Fit their depth onto the actual surface
    # along the source-camera ray, preserving their projected rest positions.
    view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
    deps=bpy.context.evaluated_depsgraph_get()
    for ob in sc.objects:
        if not ob.name.startswith(('Raised golden bezel','Polished garnet')):continue
        name='Jewel belt' if '.' in ob.name else 'Purple shoulder mantle'
        backing=bpy.data.objects[name];ev=backing.evaluated_get(deps);me=ev.to_mesh()
        tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],
                                 [list(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()
        points=[ob.matrix_world@v.co for v in ob.data.vertices]
        centre=sum(points,Vector())/len(points)
        hit,_,_,_=tree.ray_cast(centre+view*10,-view)
        if hit is None:
            # The shoulder clasp slightly overhung the open mantle edge.
            # Seat it on the nearest sewn edge rather than leave it floating.
            hit,_,_,_=tree.find_nearest(centre)
        assert hit is not None,(ob.name,'No backing for jewel')
        offset=.012 if ob.name.startswith('Polished') else .005
        delta=hit+view*offset-centre;inv=ob.matrix_world.inverted()
        for vertex,point in zip(ob.data.vertices,points):vertex.co=inv@(point+delta)
        ob['attachment_surface']=name

    # Dark woven breeches cover the anatomical thighs revealed by the fall.
    # Keep the same weighted anatomy; assign fabric only to leg-dominant faces.
    body = bpy.data.objects['Heir MPFB anatomy']
    fabric = body.data.materials[0].copy()
    fabric.name = 'Painted dark woven breeches'
    nodes, links = fabric.node_tree.nodes, fabric.node_tree.links
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .92
    shader.inputs['Sheen Weight'].default_value = .18
    pigment = shader.inputs['Base Color'].links[0].from_node
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = next(im for im in bpy.data.images if im.name.startswith('fill-linen'))
    tex.projection = 'BOX'
    tex.projection_blend = .3
    coord = nodes.new('ShaderNodeTexCoord')
    links.new(coord.outputs['Generated'], tex.inputs['Vector'])
    tint = nodes.new('ShaderNodeMixRGB')
    tint.blend_type = 'MULTIPLY'
    tint.inputs[0].default_value = 1
    tint.inputs[2].default_value = (.075, .060, .045, 1)
    links.new(tex.outputs['Color'], tint.inputs[1])
    links.new(tint.outputs[0], pigment.inputs[1])
    body.data.materials.append(fabric)
    leg_groups = {g.index for g in body.vertex_groups
                  if g.name.startswith(('thigh_', 'calf_'))}
    # The pelvis was left skin-coloured, visible through the hem in the fall.
    pelvis_groups = {g.index for g in body.vertex_groups if g.name == 'pelvis'}
    covered = {v.index for v in body.data.vertices
               if sum(g.weight for g in v.groups if g.group in leg_groups | pelvis_groups) > .55}
    for poly in body.data.polygons:
        if all(i in covered for i in poly.vertices):
            poly.material_index = len(body.data.materials) - 1

    # The shaft used to follow only the calf, opening a gap whenever the foot
    # pitched. Blend a real overlapping leather ankle between calf and foot.
    for side in ['l', 'r']:
        ob = bpy.data.objects['Tall leather boot ' + side]
        weights = []
        for vertex in ob.data.vertices:
            world = ob.matrix_world @ vertex.co
            t = max(0, min(1, (.37 - world.z) / .16))
            t = t * t * (3 - 2 * t)
            weights.append({'calf_' + side: 1 - t, 'foot_' + side: t})
        skin_in_pose(ob, rig, weights)

    lined_gusset(sc)
    # A tunic follows the upper legs instead of remaining a rigid cylinder
    # through a backwards fall. Armour keeps a smaller, stiffer influence.
    for ob in list(sc.objects):
        if ob.name not in {'Lamellar skirt', 'Ivory hem', 'Lined tunic gusset'} and not (
                ob.name.startswith('Rounded lamella relief') and ob.parent_bone == 'pelvis'):
            continue
        if ob.name in {'Lamellar skirt', 'Ivory hem'}:
            # The old three-ring shell could only bend into a faceted bucket.
            # Subdivide the closed thickness before skin binding/projection.
            bm = bmesh.new(); bm.from_mesh(ob.data)
            bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=3,
                                     use_grid_fill=True)
            bm.to_mesh(ob.data); bm.free()
        worlds = [ob.matrix_world @ v.co for v in ob.data.vertices]
        centre = sum(worlds, Vector()) / len(worlds)
        rigid_plate = ob.name.startswith('Rounded lamella relief')
        weights = []
        for world in worlds:
            point = centre if rigid_plate else world
            t = max(0, min(1, (1.22 - point.z) / .48))
            t *= .92 if ob.name in {'Ivory hem','Lined tunic gusset'} else .64
            left = max(0, min(1, (point.x + .12) / .24))
            weights.append({'pelvis': 1 - t, 'thigh_l': t * left, 'thigh_r': t * (1 - left)})
        skin_in_pose(ob, rig, weights)
        if ob.name in {'Lamellar skirt', 'Ivory hem', 'Lined tunic gusset'}:
            ob['settle_garment'] = True
            ob.shape_key_add(name='Basis')

    # Macro-scale limestone mottling under fine grain, with a softly worn rim.
    stone = bpy.data.objects['Stationary cream stone'].data.materials[0]
    nodes, links = stone.node_tree.nodes, stone.node_tree.links
    grain = next(n for n in nodes if n.type == 'TEX_NOISE')
    pores = nodes.new('ShaderNodeTexNoise')
    pores.name = 'Limestone mineral clouds'
    pores.inputs['Scale'].default_value = 11
    pores.inputs['Detail'].default_value = 4
    mix = nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = .35
    links.new(grain.outputs['Fac'], mix.inputs[1])
    links.new(pores.outputs['Fac'], mix.inputs[2])
    return mix.outputs[0]
