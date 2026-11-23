"""Closed swept hair locks with native Tail1..7 weights, before projection."""
# Replace the narrow source tail rather than leaving two diverging silhouettes.
import bmesh
horse=bpy.data.objects['Horse']
tail_groups={g.index for g in horse.vertex_groups if g.name.startswith('Tail')}
remove={v.index for v in horse.data.vertices if sum(g.weight for g in v.groups if g.group in tail_groups)>.55}
bm=bmesh.new();bm.from_mesh(horse.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index in remove],context='VERTS');bm.to_mesh(horse.data);bm.free()

view=sc.camera.matrix_world.to_quaternion() @ Vector((0,0,1))
right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0));up=sc.camera.matrix_world.to_quaternion() @ Vector((0,1,0))
hrig=bpy.data.objects['AnimalArmature'];inv=hrig.matrix_world.inverted()
anchor=hrig.matrix_world @ hrig.pose.bones['Tail2'].head
hair=bpy.data.materials['Black mane and tail']
for lock in range(20):
 verts=[];faces=[];skin=[]
 for j in range(17):
  t=j/16;x=88-(62+(lock%5)*2.5)*t
  y=132+((lock-9.5)*1.45)*math.sin(math.pi*t*.85)+8*t+2*math.sin(t*8+lock)
  c=pixel_target(x,y,anchor)+view*((lock%4-1.5)*.018)
  r=.045*(1-t)**.65+.004
  aidx=min(6,int(t*6));bn=f'Tail{aidx+1}';bn2=f'Tail{min(7,aidx+2)}';blend=t*6-aidx
  weights={bn:1-blend,bn2:blend} if bn!=bn2 else {bn:1.}
  matrix=Matrix(((0.,0.,0.,0.),)*4)
  for n,w in weights.items():matrix+=(hrig.pose.bones[n].matrix @ hrig.data.bones[n].matrix_local.inverted())*w
  for i in range(8):
   a=math.tau*i/8;world=c+up*math.sin(a)*r+view*math.cos(a)*r
   verts.append(matrix.inverted_safe() @ inv @ world);skin.append(weights)
 for j in range(16):
  for i in range(8):faces.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
 faces.extend([tuple(reversed(range(8))),tuple(range(128,136))])
 me=bpy.data.meshes.new('Swept tail lock');me.from_pydata(verts,[],faces);me.update()
 o=bpy.data.objects.new(f'GEO-weighted tail lock {lock:02}',me);sc.collection.objects.link(o);o.matrix_world=hrig.matrix_world.copy();me.materials.append(hair)
 for n in {n for weights in skin for n in weights}:o.vertex_groups.new(name=n)
 for i,weights in enumerate(skin):
  for n,w in weights.items():o.vertex_groups[n].add([i],w,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 mod=o.modifiers.new('Native weighted tail','ARMATURE');mod.object=hrig

# Reins are full-thickness skinned ropes with both moving endpoints attached.
for o in list(sc.objects):
 if o.name.startswith('Slack leather rein'):bpy.data.objects.remove(o,do_unlink=True)
for side in [-1,1]:
 verts=[];faces=[];skin=[]
 start=pixel_target(231,141,hrig.matrix_world @ hrig.pose.bones['Head'].head)+view*side*.13
 end=pixel_target(157,132,hrig.matrix_world @ hrig.pose.bones['Torso2'].head)+view*side*.20
 for j in range(25):
  t=j/24;c=start.lerp(end,t)-up*.09*math.sin(math.pi*t)
  weights={'Head':1-t,'Torso2':t};matrix=Matrix(((0.,0.,0.,0.),)*4)
  for name,w in weights.items():matrix+=(hrig.pose.bones[name].matrix @ hrig.data.bones[name].matrix_local.inverted())*w
  for i in range(8):
   a=math.tau*i/8;world=c+up*math.sin(a)*.007+view*math.cos(a)*.007
   verts.append(matrix.inverted_safe() @ inv @ world);skin.append(weights)
 for j in range(24):
  for i in range(8):faces.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
 faces.extend([tuple(reversed(range(8))),tuple(range(192,200))])
 me=bpy.data.meshes.new('Closed rein');me.from_pydata(verts,[],faces);me.update()
 o=bpy.data.objects.new(f'GEO-endpoint rein {side}',me);sc.collection.objects.link(o);o.matrix_world=hrig.matrix_world.copy();me.materials.append(bpy.data.materials['Oxide leather'])
 for name in ['Head','Torso2']:o.vertex_groups.new(name=name)
 for i,weights in enumerate(skin):
  for name,w in weights.items():o.vertex_groups[name].add([i],w,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 mod=o.modifiers.new('Head and saddle endpoints','ARMATURE');mod.object=hrig
