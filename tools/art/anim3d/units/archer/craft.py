"""Round-three thick sleeve folds and a clean painted stone with live contact AO."""
from common import *
from bpy_extras.object_utils import world_to_camera_view


def crest():
    """One curved, closed horsehair fan instead of overlapping slatted tufts."""
    sc=bpy.context.scene;cam=sc.camera;rig=bpy.data.objects['Archer MPFB rig']
    old=[o for o in sc.objects if o.name.startswith('GEO-Pale horsehair crest')]
    points=[o.matrix_world@v.co for o in old for v in o.data.vertices]
    center=sum(points,Vector())/len(points)
    q=world_to_camera_view(sc,cam,center);rotation=cam.matrix_world.to_quaternion()
    right,up,depth=[rotation@Vector(v) for v in [(1,0,0),(0,1,0),(0,0,1)]]
    origin=center+right*(.5-q.x)*cam.data.ortho_scale+up*(.5-q.y)*cam.data.ortho_scale
    outer=[(114,33),(105,32),(96,35),(88,43),(84,55),(84,69)]
    inner=[(109,45),(105,44),(100,46),(95,50),(92,57),(88,67)]
    def sample(path,t):
        u=t*(len(path)-1);j=min(int(u),len(path)-2)
        return Vector(path[j]).lerp(Vector(path[j+1]),u-j)
    vertices=[];faces=[];count=101;unit=cam.data.ortho_scale/256
    for i in range(count):
        t=i/(count-1)
        for p,side in [(sample(inner,t),1),(sample(outer,t),1),
                       (sample(outer,t),-1),(sample(inner,t),-1)]:
            # A real curved 45mm-deep volume; shallow fibre ridges remain geometric.
            d=.035*math.sin(math.pi*t)+side*(.0225+.001*math.sin(t*math.pi*70))
            vertices.append(origin+right*(p.x-128)*unit-up*(p.y-128)*unit+depth*d)
    for i in range(count-1):
        for j in range(4):
            a=i*4+j;b=i*4+(j+1)%4;faces.append((a,b,b+4,a+4))
    faces.extend([(3,2,1,0),tuple((count-1)*4+j for j in range(4))])
    for o in old:bpy.data.objects.remove(o,do_unlink=True)
    obj=mesh('Pale horsehair crest continuous',vertices,faces,bpy.data.materials['MAT-linen'])
    obj['continuous_crest']=True
    attach(obj,rig,'head')


def sleeves():
    sc = bpy.context.scene
    cam = sc.camera
    rig = bpy.data.objects['Archer MPFB rig']
    rotation = cam.matrix_world.to_quaternion()
    right, up, depth = [rotation @ Vector(v) for v in [(1,0,0),(0,1,0),(0,0,1)]]
    unit = cam.data.ortho_scale / 256
    # Preserve the generated linen pigment when motion exposes an unprojected
    # fold. Half the response remains physically lit, with the existing live AO
    # and weave; this avoids a grey unpainted strip beside the lit source pigment.
    material=bpy.data.materials['MAT-linen']
    n=material.node_tree.nodes;l=material.node_tree.links
    s=n.get('Principled BSDF');out=n.get('Material Output')
    physical=out.inputs['Surface'].links[0].from_socket
    pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Generated linen underpaint'
    pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0
    pigment.inputs['Emission Strength'].default_value=.8
    l.new(s.inputs['Base Color'].links[0].from_socket,pigment.inputs['Emission Color'])
    ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.5
    l.new(ray.outputs['Is Camera Ray'],weight.inputs[0]);mix=n.new('ShaderNodeMixShader')
    l.new(weight.outputs[0],mix.inputs[0]);l.new(physical,mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    for side, inner, outer in [('l',(117,77,102),(134,77,92)),
                                ('r',(93,78,109),(80,81,96))]:
        old = bpy.data.objects['GEO-Ivory sleeve '+side]
        material = old.data.materials[0]
        center = old.matrix_world @ (sum((v.co for v in old.data.vertices),Vector()) / len(old.data.vertices))
        q = world_to_camera_view(sc,cam,center)
        origin = center + right*(.5-q.x)*cam.data.ortho_scale + up*(.5-q.y)*cam.data.ortho_scale
        bpy.data.objects.remove(old,do_unlink=True)
        vertices, faces = [], []
        rings, steps = 18, 64
        for j in range(rings+1):
            t = j/rings
            x = inner[0]*(1-t)+outer[0]*t
            top = inner[1]*(1-t)+outer[1]*t
            bottom = inner[2]*(1-t)+outer[2]*t
            for i in range(steps):
                a = 2*math.pi*i/steps
                fold = .75*math.sin(7*a+.5*math.sin(t*math.pi)) * math.sin(math.pi*t)
                y = (top+bottom)/2 + ((bottom-top)/2+fold)*math.cos(a)
                # A complete elliptical cuff, not a camera-facing patch. The
                # visible and reverse sides have ~20cm total physical depth.
                d = (.10+.008*math.cos(7*a))*math.sin(a)
                vertices.append(origin + right*(x-128)*unit - up*(y-128)*unit + depth*d)
        for j in range(rings):
            for i in range(steps):
                a=j*steps+i;b=j*steps+(i+1)%steps
                faces.append((a,b,b+steps,a+steps))
        if outer[0] < inner[0]:
            faces=[tuple(reversed(face)) for face in faces]
        obj = bevel(solid(mesh('Ivory sleeve '+side,vertices,faces,material),.006),.002)
        attach(obj,rig,'upperarm_'+side)


def stone():
    """Frozen color registration on the real rounded disc; alpha never hides it."""
    sc=bpy.context.scene;obj=bpy.data.objects['GEO-Stationary cream base']
    image=bpy.data.images.load(str(ASSETS/'stone-fill-source.png'),check_existing=True)
    # Generated clean plate occupies this normalized crop (thresholded alpha).
    # All color is clamped inside its edge; geometry supplies the silhouette.
    pixels=list(image.pixels);w,h=image.size
    occupied=[(i%w,i//w) for i in range(w*h) if pixels[i*4+3]>.5]
    x0=min(x for x,y in occupied)/w;x1=(max(x for x,y in occupied)+1)/w
    y0=min(y for x,y in occupied)/h;y1=(max(y for x,y in occupied)+1)/h
    points=[world_to_camera_view(sc,sc.camera,obj.matrix_world@v.co) for v in obj.data.vertices]
    lo=Vector((min(p.x for p in points),min(p.y for p in points)))
    hi=Vector((max(p.x for p in points),max(p.y for p in points)))
    uv=obj.data.uv_layers.new(name='Clean stone projection')
    for loop in obj.data.loops:
        p=points[loop.vertex_index]
        uv.data[loop.index].uv=(x0+(x1-x0)*(p.x-lo.x)/(hi.x-lo.x),y0+(y1-y0)*(p.y-lo.y)/(hi.y-lo.y))
    for material in obj.data.materials:
        n=material.node_tree.nodes;l=material.node_tree.links
        out=n.get('Material Output');physical=out.inputs['Surface'].links[0].from_socket
        tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='EXTEND'
        coords=n.new('ShaderNodeUVMap');coords.uv_map=uv.name;l.new(coords.outputs[0],tex.inputs[0])
        ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.10
        shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.55
        l.new(tex.outputs['Color'],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
        pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Clean stone pigment with live contact'
        pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0
        pigment.inputs['Emission Strength'].default_value=1;l.new(shade.outputs[0],pigment.inputs['Emission Color'])
        ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.88
        l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
        mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(physical,mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    sc['stone_fill']='Generated clean stone color only, live AO, unchanged closed geometry.'
