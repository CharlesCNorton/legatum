"""R11b broad rest-space folds; preserve R10 colour and painted highlights.

No geometry, normals, UV, rig, lighting or motion edits. Frozen corner pigment
follows the existing pleats and shoulder seam through the original deformation.
"""
import math
from coverage import linear, smooth, CLOAK, SLEEVE, PAINT

FILL = 'R11b sewn folds'


def gauss(x, width):
    return math.exp(-.5*(x/width)**2)


def mix_pigment(nodes, links, socket, attr, label):
    original=socket.links[0].from_socket
    mix=nodes.new('ShaderNodeMixRGB');mix.label=label
    links.new(attr.outputs['Alpha'],mix.inputs[0])
    links.new(original,mix.inputs[1]);links.new(attr.outputs['Color'],mix.inputs[2])
    links.new(mix.outputs[0],socket)


def garment(ob):
    mesh=ob.data
    coords=[tuple(v.co) for v in mesh.vertices]
    visibility=mesh.color_attributes['Painting visibility']
    old=mesh.color_attributes.get(PAINT)
    attr=mesh.color_attributes.new(name=FILL,type='FLOAT_COLOR',domain='CORNER')
    xs=[v[0] for v in coords];centre=(min(xs)+max(xs))/2;span=max(max(xs)-min(xs),.02)
    for loop in mesh.loops:
        x,y,z=coords[loop.vertex_index]
        if ob.name==CLOAK:
            color=list(old.data[loop.index].color[:3])
            # Troughs of the existing modeled pleats; preserve their ridges.
            trough=((1-math.cos(x*39))*.5)**3
            shade=.10*trough
            # Interior hanging lining behind the thighs: keep dark red, never
            # replace it with an average skin/linen colour from another part.
            shade+=.05*gauss(x+.035,.14)*(1-smooth(.72,1.02,z))
            color=[c*(1-shade) for c in color]
            weight=old.data[loop.index].color[3]
        elif ob.name==SLEEVE:
            color=list(old.data[loop.index].color[:3])
            seam=1.445-.40*max(0.,abs(x)-.16)
            d=seam-z+.18*(y+.05)
            shadow=sum(gauss(d-c,.017)*a for c,a in [(0.035,.55),(.102,.45),(.169,.32)])
            ridge=sum(gauss(d-c,.022)*a for c,a in [(0.006,.08),(.074,.07),(.143,.05)])
            color=[c*max(.30,1-shadow+ridge) for c in color]
            weight=old.data[loop.index].color[3]
        else:
            # Unseen skirt lining: broad centre plane with dark sewn edges.
            face=gauss((x-centre)/span,.29)
            low,high=linear((69,43,26)),linear((143,108,66))
            color=low*(1-face)+high*face
            color*=.78+.22*smooth(.85,1.10,z)
            weight=1-smooth(.10,.85,visibility.data[loop.index].color[0])
        attr.data[loop.index].color=(*color,weight)
    lining = None
    if ob.name == CLOAK:
        lining = mesh.color_attributes.new(name='R11b inner hanging lining',type='FLOAT_COLOR',domain='CORNER')
        for loop in mesh.loops:
            x,y,z=coords[loop.vertex_index]
            # Mesh-space pocket directly below the skirt hem. This is where
            # the old red/green gate admits tan projection onto red cloth.
            weight=.55*gauss(x+.155,.070)*gauss(z-.550,.025)
            color=linear((58,16,9))*(.85+.15*math.cos(x*39))
            lining.data[loop.index].color=(*color,weight)
    for mat in mesh.materials:
        nodes,links=mat.node_tree.nodes,mat.node_tree.links
        emit=next(n for n in nodes if n.label=='Generated fill pigment, camera only')
        shade=emit.inputs['Color'].links[0].from_node
        paint=nodes.new('ShaderNodeVertexColor');paint.layer_name=FILL
        mix_pigment(nodes,links,shade.inputs[1],paint,'R11b broad sewn folds')
        if lining is not None:
            pocket=nodes.new('ShaderNodeVertexColor');pocket.layer_name=lining.name
            projected=next(n for n in nodes if n.label=='Painted illumination, fixed rest UV')
            for socket in [shade.inputs[1],projected.inputs['Emission Color']]:
                mix_pigment(nodes,links,socket,pocket,'R11b dark lining beneath skirt')
    return len(mesh.vertices)


def restore_dark_projection(mat):
    """Prevent the physical 4% blend from lifting painted cloak/rim recesses.

    Existing visibility, alpha, wool semantic and camera-only gates stay intact.
    Only dark source pigment changes from 96% to 99.5%; highlights stay at 96%.
    """
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    pigment=next(n for n in nodes if n.label=='Painted illumination, fixed rest UV')
    projected=next(link.to_node for link in pigment.outputs[0].links if link.to_node.type=='MIX_SHADER')
    camera_gate=projected.inputs[0].links[0].from_node
    source=pigment.inputs['Emission Color'].links[0].from_socket
    lum=nodes.new('ShaderNodeRGBToBW');links.new(source,lum.inputs[0])
    amount=nodes.new('ShaderNodeMapRange');amount.clamp=True
    amount.inputs['From Min'].default_value=.015;amount.inputs['From Max'].default_value=.18
    amount.inputs['To Min'].default_value=.995/.96;amount.inputs['To Max'].default_value=1.
    links.new(lum.outputs[0],amount.inputs['Value'])
    previous=camera_gate.inputs[0].links[0].from_socket
    mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.label='R11b restore painted cavity value'
    links.new(previous,mul.inputs[0]);links.new(amount.outputs[0],mul.inputs[1]);links.new(mul.outputs[0],camera_gate.inputs[0])


def apply(scene):
    if scene.get('spearman_fold_paint'):
        raise RuntimeError('R11b already applied; restart from round 10')
    report={}
    for ob in scene.objects:
        if ob.type!='MESH':continue
        if ob.name in {CLOAK,SLEEVE} or ob.name.startswith('Linen pteruges '):
            report[ob.name]=garment(ob)
        if ob.name in {'Convex bronze aspis','Aspis turned rim','Aspis turned rim.001'}:
            for mat in ob.data.materials:
                restore_dark_projection(mat)
    scene['spearman_fold_paint']=11
    return report
