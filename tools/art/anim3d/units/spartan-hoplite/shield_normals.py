"""Repair inherited ring winding; preserve mesh topology, UVs and skinning."""
import bpy,bmesh

def repair():
 obj=bpy.data.objects['Convex bronze aspis']
 if obj.data.get('hoplite_outward_rings'):return
 bm=bmesh.new();bm.from_mesh(obj.data);bm.faces.ensure_lookup_table()
 # The initial 96-triangle fan points out; inherited quad rings point inward.
 bmesh.ops.reverse_faces(bm,faces=[f for f in bm.faces if f.index>=96])
 bm.to_mesh(obj.data);bm.free();obj.data.update();obj.data['hoplite_outward_rings']=True
