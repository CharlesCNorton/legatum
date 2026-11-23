"""Read source glTF foot trajectories without Blender; no retargeting or synthesis."""
import struct,json,math,bisect,os,sys
from pathlib import Path
r=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));raw=(r/'assets/horseman/Horse.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);b=raw[28+n:]
def acc(k):
 a=j['accessors'][k];v=j['bufferViews'][a['bufferView']];dim={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];fmt='<'+str(dim)+'f';stride=v.get('byteStride',dim*4);start=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from(fmt,b,start+i*stride) for i in range(a['count'])]
def mm(a,b):return [[sum(a[i][k]*b[k][q] for k in range(4)) for q in range(4)] for i in range(4)]
def matrix(t,q,s):
 x,y,z,w=q;m=[[1-2*y*y-2*z*z,2*x*y-2*w*z,2*x*z+2*w*y,t[0]],[2*x*y+2*w*z,1-2*x*x-2*z*z,2*y*z-2*w*x,t[1]],[2*x*z-2*w*y,2*y*z+2*w*x,1-2*x*x-2*y*y,t[2]],[0,0,0,1]]
 for i in range(3):
  for k in range(3):m[i][k]*=s[k]
 return m
parents={c:i for i,node in enumerate(j['nodes']) for c in node.get('children',[])};ids={x['name']:i for i,x in enumerate(j['nodes'])};clip=sys.argv[1] if len(sys.argv)>1 else 'Gallop';action=next(a for a in j['animations'] if a['name'].endswith('|'+clip));channels=[]
for c in action['channels']:
 sampler=action['samplers'][c['sampler']];channels.append((c['target']['node'],c['target']['path'],[v[0] for v in acc(sampler['input'])],acc(sampler['output'])))
records=[]
for frame in range(29 if clip=='Walk' else 15):
 time=frame/24;values={i:{'translation':x.get('translation',[0,0,0]),'rotation':x.get('rotation',[0,0,0,1]),'scale':x.get('scale',[1,1,1])} for i,x in enumerate(j['nodes'])}
 for idx,path,times,vs in channels:
  hi=min(len(times)-1,max(1,bisect.bisect_right(times,time)));lo=hi-1;f=max(0,min(1,(time-times[lo])/(times[hi]-times[lo])))
  v=[a+(b-a)*f for a,b in zip(vs[lo],vs[hi])]
  if path=='rotation':norm=math.sqrt(sum(x*x for x in v));v=[x/norm for x in v]
  values[idx][path]=v
 cache={}
 def world(i):
  if i not in cache:
   v=values[i];m=matrix(v['translation'],v['rotation'],v['scale']);cache[i]=mm(world(parents[i]),m) if i in parents else m
  return cache[i]
 record={'frame':frame}
 for name in ['FF.L','FF.R','FFB.L','FFB.R']:
  m=world(ids[name]);record[name]=[round(m[i][3],5) for i in range(3)]
 records.append(record)
(r/'masters/horseman-3d/source-gait.json').write_text(json.dumps(records,indent=2))
for v in records:print(v['frame'],*[round(v[n][1],3) for n in ['FF.L','FF.R','FFB.L','FFB.R']])
