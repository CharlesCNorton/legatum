"""Lower-limb silhouette sculpture in the finished, posed mesh; retain full depth."""
# Executed in finish.py's namespace after all volume/modifier finishing.
horse = bpy.data.objects['Horse']
ev = horse.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
worlds = [ev.matrix_world @ v.co for v in me.vertices]
screen = [world_to_camera_view(sc,sc.camera,w) for w in worlds]
screen = [(q.x*256,(1-q.y)*256) for q in screen]
ev.to_mesh_clear()
profiles = {
 'front.R':[(166,145,6),(180,142,4),(196,141,3),(211,140,3),(218,141,4),(224,144,6)],
 'front.L':[(166,158,6),(180,156,4),(196,153,3),(210,153,3),(216,155,4),(221,159,6)],
 'back.R':[(166,77,5),(181,74,4),(197,72,3),(212,71,3),(219,72,4),(223,74,5)],
 'back.L':[(166,93,5),(181,92,4),(196,88,3),(208,87,3),(215,90,4),(219,92,6)],
}
def interpolate(profile,y):
    if y <= profile[0][0]: return profile[0][1:]
    for a,b in zip(profile,profile[1:]):
        if y <= b[0]:
            t=(y-a[0])/(b[0]-a[0]); return (a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t)
    return profile[-1][1:]

arm = bpy.data.objects['AnimalArmature']; Ato = arm.matrix_world.inverted() @ horse.matrix_world
for limb,profile in profiles.items():
    family,side=limb.split('.')
    names = ([f'FrontUpperLeg.{side}',f'FrontLowerLeg.{side}',f'FF.{side}',f'IKFrontLeg.{side}']
             if family=='front' else [f'BackUpperLeg.{side}',f'BackLowerLeg.{side}',f'FFB.{side}',f'IKBackLeg.{side}'])
    groups={horse.vertex_groups[n].index for n in names if n in horse.vertex_groups}
    indices=[v.index for v in horse.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.6 and screen[v.index][1]>164]
    assert indices,limb
    old_bottom=max(screen[i][1] for i in indices); bottom=profile[-1][0]
    for index in indices:
        x,y=screen[index]; t=max(0,min(1,(y-164)/20)); t=t*t*(3-2*t)
        yy=164+(y-164)*(bottom-164)/(old_bottom-164)
        section=[screen[j][0] for j in indices if abs(screen[j][1]-y)<3]
        center=(min(section)+max(section))/2; radius=max((max(section)-min(section))/2,.6)
        target,width=interpolate(profile,yy)
        xx=target+(x-center)*min(2.5,width/radius)
        delta=(right*(xx-x)-up*(yy-y))*(sc.camera.data.ortho_scale/256)*t
        v=horse.data.vertices[index]; local=horse.matrix_world.to_3x3().inverted()@delta
        weighted=Matrix(((0.,0.,0.,0.),)*4);total=0
        for g in v.groups:
            name=horse.vertex_groups[g.group].name
            if name not in arm.pose.bones: continue
            bone=arm.pose.bones[name];weighted+=(bone.matrix@bone.bone.matrix_local.inverted())*g.weight;total+=g.weight
        if total>.001: local=(Ato.inverted()@(weighted*(1/total))@Ato).to_3x3().inverted_safe()@local
        v.co+=local
horse.data.update();bpy.context.view_layer.update()
