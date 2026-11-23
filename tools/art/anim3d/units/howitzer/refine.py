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
    for wheel, target, size, yaw in zip(wheels, [(107.5, 159), (213, 153)], [1, .96], [-21, -21]):
        center = wheel.matrix_world.translation.copy()
        new_center = center.copy()
        new_center.z = .13 + .53 * size
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
        report[wheel.name] = {'target_px': target, 'actual_px': [p.x*256, (1-p.y)*256], 'radius': .53*size, 'mount_yaw_degrees': yaw}
    # Register the actual solid spokes, not a painted wheel card. Each endpoint is
    # intersected with its wheel's physical dish plane; beam width/depth stay real.
    source_wheels = [
        ((98,159), [(104,119),(116,125),(122,141),(124,158),(122,177),(115,193),
                    (104,200),(92,193),(85,179),(82,161),(87,142),(95,127)]),
        ((207,155), [(211,116),(224,119),(232,135),(235,153),(232,172),(225,188),
                    (214,193),(203,185),(197,171),(193,153),(197,135),(204,121)])]
    view = camera.rotation_euler.to_matrix() @ Vector((0,0,1))
    image_center = camera.location-view*5
    for wheel,(hub,ends) in zip(wheels,source_wheels):
        def wheelpoint(pixel,depth):
            q=image_center+right*(pixel[0]-128)*scale-up*(pixel[1]-128)*scale
            normal=wheel.matrix_world.to_3x3()@Vector((0,1,0))
            plane=wheel.matrix_world@Vector((0,depth,0))
            return q+view*((plane-q).dot(normal)/view.dot(normal))
        spokes=sorted([o for o in wheel.children if o.name.startswith('GEO-Dished wheel spoke')],key=lambda o:o.name)
        sockets=sorted([o for o in wheel.children if o.name.startswith('GEO-Spoke socket')],key=lambda o:o.name)
        for spoke,socket,end in zip(spokes,sockets,ends):
            start=(hub[0]+(end[0]-hub[0])*.15,hub[1]+(end[1]-hub[1])*.15)
            a,b=wheelpoint(start,-.10),wheelpoint(end,-.025)
            # A source silhouette includes tread thickness and perspective. Its
            # ray/plane intersection is not a safe radius: keep sockets inside
            # the real circular rim throughout a complete wheel revolution.
            local=wheel.matrix_world.inverted()@b
            radial=Vector((local.x,0,local.z)).normalized()
            radius=.53 if wheel==wheels[0] else .53*.96
            a=wheel.matrix_world@(radial*.085+Vector((0,-.13,0)))
            b=wheel.matrix_world@(radial*(radius-.054)+Vector((0,-.025,0)))
            for obj,first,last in [(spoke,a,b),(socket,a+(b-a)*.88,b)]:
                length=max(v.co.z for v in obj.data.vertices)-min(v.co.z for v in obj.data.vertices)
                d=last-first
                obj.matrix_world=Matrix.Translation((first+last)/2)@d.to_track_quat('Z','Y').to_matrix().to_4x4()@Matrix.Diagonal((1,1,d.length/length,1))
        bpy.context.view_layer.update()
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
    outlines=[[(92,63),(127,63),(130,74),(140,74),(147,125),(134,140),(115,136),(104,114),(99,92)],
              [(150,64),(174,63),(183,73),(203,78),(210,94),(198,108),(185,115),(169,106),(159,92)]]
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
    for o,pixel in zip(rivets,[(98,69),(106,91),(122,120),(136,117),(170,69),(199,84),(193,101),(174,97)]):
        o.matrix_world.translation=on_plate(pixel,.282)
    # The hidden rear braces must remain behind the thicker fitted plates.
    for o in scene.objects:
        if o.name.startswith('GEO-Shield folded brace'):o.hide_render=True
    # Register barrel pivot as a full assembly; preserve rigid radii, recoil axis and depth.
    pivot=bpy.data.objects['RIG-elevation']
    point=pivot.matrix_world.translation.copy();screen=world_to_camera_view(scene,camera,point)
    delta=right*(145-screen.x*256)*scale-up*(102-(1-screen.y)*256)*scale
    pivot.location+=delta
    pivot.scale=(1.10,1.10,1.10)
    bpy.context.view_layer.update()
    # Yokes connect the axle to the moved trunnion instead of hovering under the tube.
    for o in scene.objects:
        if o.name.startswith('GEO-Trunnion'):
            o.location+=delta*.65
    bpy.context.view_layer.update()
    # Align sight handwheel and the rear trail with source landmarks as complete volumes.
    center=Vector((.14,-.35,.91));screen=world_to_camera_view(scene,camera,center)
    shift=right*(153-screen.x*256)*scale-up*(138-(1-screen.y)*256)*scale
    for o in scene.objects:
        if any(k in o.name for k in ['handwheel','Handwheel']):o.location+=shift
    for trail in [o for o in scene.objects if o.name.startswith('RIG-trail')]:
        # Grounded trail start remains under carriage; align the spade by rotating about it.
        trail.rotation_euler.z=-.04
        trail.location.x-=.12
    bpy.context.view_layer.update()
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
        if 'Shield wing' in o.name or 'wheel spoke' in o.name or 'Hollow tapered' in o.name:
            bmesh.ops.triangulate(bm,faces=list(bm.faces))
            edges=[e for e in bm.edges if e.calc_length()>.12]
            if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
        bm.to_mesh(o.data);bm.free();o.data.update()
    # Fail before expensive rendering if fitted spokes can lift the round rim.
    for wheel in wheels:
        inverse=wheel.matrix_world.inverted()
        rim=next(o for o in wheel.children if 'Rolled steel wheel rim' in o.name)
        radius=max(math.hypot(q.x,q.z) for v in rim.data.vertices for q in [inverse@(rim.matrix_world@v.co)])
        for obj in wheel.children:
            if any(k in obj.name for k in ['Dished wheel spoke','Spoke socket']):
                extent=max(math.hypot(q.x,q.z) for v in obj.data.vertices for q in [inverse@(obj.matrix_world@v.co)])
                assert extent<=radius+.001,(obj.name,'spoke outside rim',extent,radius)
    (folder/'registration.json').write_text(json.dumps(report,indent=2))
