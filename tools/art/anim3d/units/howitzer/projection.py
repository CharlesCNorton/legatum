"""Frozen projection on finished volumes; camera-only pigment preserves painted light."""
import bpy, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view


def project(scene, camera, base, assets, folder):
    image=bpy.data.images.load(str(assets/'projection.png'));image.pack()
    machine_image=bpy.data.images.load(str(assets/'machine-projection.png'));machine_image.pack()
    view=camera.rotation_euler.to_matrix() @ Vector((0,0,1))
    objects=[o for o in scene.objects if o.type=='MESH']
    verts=[];faces=[]
    for o in objects:
        start=len(verts)
        verts.extend(o.matrix_world @ v.co for v in o.data.vertices)
        faces.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
    tree=BVHTree.FromPolygons(verts,faces)
    records=[]
    for o in objects:
        if o==base or (o.parent and o.parent.name.startswith('RIG-wheel')):continue  # Never paint stationary wheel shadows onto the stone.
        eligible=[m for m in o.data.materials if m and any(k in m.name for k in ['Olive','Dusty','Worn','baked finish'])]
        if not eligible:continue
        uv=o.data.uv_layers.new(name='RestPainting')
        mask=o.data.color_attributes.new(name='ProjectionConfidence',type='FLOAT_COLOR',domain='CORNER')
        normal_matrix=o.matrix_world.to_3x3().inverted().transposed()
        weights={};coords={}
        for v in o.data.vertices:
            point=o.matrix_world@v.co
            p=world_to_camera_view(scene,camera,point);coords[v.index]=(p.x,p.y)
            facing=max(0,min(1,((normal_matrix@v.normal).normalized().dot(view)-.01)/.25))
            hit,_,_,_=tree.ray_cast(point+view*5,-view,5.01)
            visible=hit is not None and (hit-point).length<.008
            weights[v.index]=facing if visible else 0
        for loop in o.data.loops:
            uv.data[loop.index].uv=coords[loop.vertex_index]
            w=weights[loop.vertex_index];mask.data[loop.index].color=(w,w,w,1)
        for index,original in enumerate(list(o.data.materials)):
            if original not in eligible:continue
            material=original.copy();material.name=o.name+' frozen pigment';o.data.materials[index]=material
            n=material.node_tree.nodes;l=material.node_tree.links
            physical=n.get('Principled BSDF');output=n.get('Material Output')
            uvn=n.new('ShaderNodeUVMap');uvn.uv_map=uv.name
            im=n.new('ShaderNodeTexImage');im.image=machine_image if any(k in o.name for k in ['trail','Trail','spade','Spade','Axle']) else image;im.extension='CLIP';l.new(uvn.outputs[0],im.inputs[0])
            confidence=n.new('ShaderNodeVertexColor');confidence.layer_name=mask.name
            factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(confidence.outputs['Color'],factor.inputs[0]);l.new(im.outputs['Alpha'],factor.inputs[1])
            camera_ray=n.new('ShaderNodeLightPath')
            camera_factor=n.new('ShaderNodeMath');camera_factor.operation='MULTIPLY';l.new(factor.outputs[0],camera_factor.inputs[0]);l.new(camera_ray.outputs['Is Camera Ray'],camera_factor.inputs[1])
            # Principled pigment branch: source illumination appears only to camera rays.
            pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera-only painted illumination'
            pigment.inputs['Base Color'].default_value=(0,0,0,1)
            pigment.inputs['Specular IOR Level'].default_value=0
            l.new(im.outputs['Color'],pigment.inputs['Emission Color']);pigment.inputs['Emission Strength'].default_value=1
            strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.96;l.new(camera_factor.outputs[0],strength.inputs[0])
            mix=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mix.inputs[0]);l.new(physical.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs['Surface'])
        records.append({'name':o.name,'vertices':len(o.data.vertices),'covered_vertices':sum(w>.5 for w in weights.values())})
    (folder/'projection.json').write_text(json.dumps({'meshes':records,'method':'finished volumetric geometry; frozen rest-camera UV; ray visibility/facing/source-alpha confidence; camera-only pigment; generated olive unseen fill','strength':.96,'base':'physical stone; no source shadows'},indent=2))
    return records
