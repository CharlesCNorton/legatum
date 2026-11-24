"""Round-three physical silhouette and pigment refinements, before projection."""
# Executed by finish.py after finished-surface fitting, before rest contacts/UVs.
# Source features are measured in the committed 256px token coordinates.
kit_objects=[o for o in horse_objects if o.name!='Horse' and not o.name.startswith(('Mane','Tail'))]
fit_objects(kit_objects,[((151,147),(168,148)),((153,155),(170,161)),((139,162),(150,164))],17)
fit_objects([bpy.data.objects['Horse']],[((157,150),(165,150)),((186,80),(184,78)),((194,100),(195,102))],11)
fit_objects(horse_objects,[((188,74),(183,79)),((190,92),(190,94)),((197,113),(199,114))],8)
# Broaden the armored shoulder and relax the forearm onto the painted rein grip.
fit_objects(rider_objects,[((97,88),(95,88)),((114,96),(112,96)),((140,112),(137,109))],7)
# A full anatomical sleeve continues to the wrist. The old fitted shirt omitted
# the lower far arm, which exposed pale flesh in the painting's steel sleeve.
body=bpy.data.objects['Rider MPFB CC0 anatomy']
armor=bpy.data.materials['Bronze • hammered']
body.data.materials.append(armor);armor_index=len(body.data.materials)-1
arm_groups={body.vertex_groups[n].index for n in ['upperarm_l','lowerarm_l','upperarm_r','lowerarm_r'] if n in body.vertex_groups}
for p in body.data.polygons:
 coverage=sum(sum(g.weight for g in body.data.vertices[i].groups if g.group in arm_groups) for i in p.vertices)/len(p.vertices)
 if coverage>.55:p.material_index=armor_index
# Register the rigid lance as one straight object, retaining cylindrical depth.
# Shaft centerline target: butt (84,224), tip (142,13); blade remains rigid to it.
for o in [bpy.data.objects['Spear ash shaft'],bpy.data.objects['Iron spear blade']]:
 for v in o.data.vertices:
  w=o.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,w);x,y=q.x*256,(1-q.y)*256
  # old shaft centerline from measured evaluated extrema; preserve cross-section.
  old_x=140.0+(y-20)*(-.238)
  yy=13+(y-15.73)*(224-13)/(218.29-15.73)
  new_x=142+(yy-13)*(84-142)/(224-13)
  delta=(right*(new_x-old_x)-up*(yy-y))*(sc.camera.data.ortho_scale/256)
  v.co+=o.matrix_world.to_3x3().inverted()@delta
 o.data.update()
# Base stays a circular horizontal solid. Shorter rim and slight fore/aft shift
# bring the support disc into registration without painting stationary hooves.
view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
away=Vector((-view.x,-view.y,0)).normalized()
base.location+=away*.12
for v in base.data.vertices:v.co.z=.05+(v.co.z-.05)*.78
bpy.context.view_layer.update()
# Register the generated clean plate to the actual base footprint. Alpha is
# ignored by the material; geometry alone determines the silhouette.
stone_image=bpy.data.images.load(str(A/'stone-projection.png'),check_existing=True)
uv=base.data.uv_layers.new(name='Clean stone painting')
for loop in base.data.loops:
 q=world_to_camera_view(sc,sc.camera,base.matrix_world@base.data.vertices[loop.vertex_index].co)
 uv.data[loop.index].uv=(q.x,q.y)
stone=base.data.materials[0];nodes=stone.node_tree.nodes;links=stone.node_tree.links
coord=nodes.new('ShaderNodeUVMap');coord.uv_map=uv.name
tex=nodes.new('ShaderNodeTexImage');tex.image=stone_image;tex.extension='EXTEND';links.new(coord.outputs[0],tex.inputs['Vector'])
# Preserve the existing live contact AO; replace only synthetic stone pigment.
for node in nodes:
 if node.bl_idname=='ShaderNodeMixRGB' and node.blend_type=='MULTIPLY':
  incoming=node.inputs[1].links
  if incoming and incoming[0].from_node.bl_idname=='ShaderNodeValToRGB':links.new(tex.outputs['Color'],node.inputs[1])
sc['round3_finish']='Full-depth barding registration; continuous armored forearms; rigid source-aligned lance; generated clean stone pigment with live AO'
