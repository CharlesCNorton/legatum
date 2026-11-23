"""Fit complete mechanical components before freezing UVs; never flatten depth."""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


def refine(scene, camera, wheels, base, folder):
    right = camera.rotation_euler.to_matrix() @ Vector((1, 0, 0))
    up = camera.rotation_euler.to_matrix() @ Vector((0, 1, 0))
    scale = camera.data.ortho_scale / 256
    report = {}
    # Both complete wheels stay round, with real tread/hubs and local rolling axes.
    # The painting includes modest perspective; physical mounting yaw accommodates it.
    for wheel, target, size, yaw in zip(wheels, [(112, 148), (195, 139)], [.96, .88], [-12, -12]):
        center = wheel.matrix_world.translation.copy()
        new_center = center.copy()
        new_center.z = .13 + .414 * size
        screen = world_to_camera_view(scene, camera, new_center)
        delta = right * (target[0] - screen.x * 256) * scale - up * (target[1] - (1-screen.y) * 256) * scale
        # Keep ground contact by continuing the camera ray to the same z plane.
        ray = camera.rotation_euler.to_matrix() @ Vector((0, 0, 1))
        delta -= ray * delta.z / ray.z
        new_center += delta
        transform = Matrix.Translation(new_center) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Scale(size, 4) @ Matrix.Translation(-center)
        children = list(wheel.children_recursive)
        matrices = {o.name: transform @ o.matrix_world for o in children}
        wheel.matrix_world = Matrix.Translation(new_center) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
        bpy.context.view_layer.update()
        for o in children:
            o.matrix_world = matrices[o.name]
        bpy.context.view_layer.update()
        p = world_to_camera_view(scene, camera, new_center)
        report[wheel.name] = {'target_px': target, 'actual_px': [p.x*256, (1-p.y)*256], 'radius': .414*size, 'mount_yaw_degrees': yaw}
    # Refit the full solid axle to the registered wheel hubs.
    axle = bpy.data.objects['GEO-Axle']
    a,b = [o.matrix_world.translation.copy() for o in wheels]
    axle.location = (a+b)/2
    axle.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()
    axle.scale.z = (b-a).length / 1.64
    # Trace the shield's actual plate outline at its fixed, full-depth x plane.
    # Screen landmarks constrain geometry only; texture UVs remain one camera map.
    ray = camera.rotation_euler.to_matrix() @ Vector((0,0,1))
    def on_plate(pixel, x=.25):
        center=camera.location-camera.rotation_euler.to_matrix()@Vector((0,0,5))
        point=center+right*(pixel[0]-128)*scale-up*(pixel[1]-128)*scale
        return point+ray*((x-point.x)/ray.x)
    outlines=[[(101,67),(119,65),(128,73),(142,72),(144,128),(136,129),(122,109),(101,106),(97,81)],
              [(190,79),(198,95),(187,100),(184,107),(181,126),(168,127),(168,105),(178,93)]]
    for sign,outline in zip([-1,1],outlines):
        o=bpy.data.objects['GEO-Shield wing '+str(sign)]
        world=[on_plate(p,x) for x in [.2325,.2675] for p in outline]
        inverse=o.matrix_world.inverted(); count=len(outline)
        faces=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]
        faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        data=bpy.data.meshes.new(o.name+' fitted plate')
        data.from_pydata([inverse@v for v in world],[],faces);data.update()
        for material in o.data.materials:data.materials.append(material)
        o.data=data
    # Move the existing solid fastenings onto the registered plates.
    rivets=sorted([o for o in scene.objects if o.name.startswith('GEO-Shield rivet')],key=lambda o:o.name)
    for o,pixel in zip(rivets,[(104,96),(133,94),(135,119),(140,126),(175,114),(191,82),(181,97),(173,125)]):
        o.matrix_world.translation=on_plate(pixel,.282)
    # The hidden rear braces must remain behind the thicker fitted plates.
    for o in scene.objects:
        if o.name.startswith('GEO-Shield folded brace'):o.hide_render=True
    # Apply all rigid finish before projection: curves and bevels become real vertices.
    for o in list(scene.objects):
        if o.type not in {'MESH','CURVE'}: continue
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.context.view_layer.objects.active=o
        if o.type=='CURVE': bpy.ops.object.convert(target='MESH')
        for modifier in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        # Long faces need interior confidence samples, especially the solid shield.
        if 'Shield wing' in o.name or 'Pressed wheel dish' in o.name or 'Hollow tapered' in o.name:
            bmesh.ops.triangulate(bm,faces=list(bm.faces))
            edges=[e for e in bm.edges if e.calc_length()>.12]
            if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
        bm.to_mesh(o.data);bm.free();o.data.update()
    (folder/'registration.json').write_text(json.dumps(report,indent=2))
