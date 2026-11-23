"""Check planted ankle travel and toe heading from evaluated retargeted poses."""
import json, math, os
from pathlib import Path
root=Path(os.environ['ANIM_ROOT']);master=root/'masters/legionary'
data=json.loads((master/'clips/move.json').read_text())
contact=data['motion']['contact'];speed=contact['virtual_forward_speed_m_s'];rows=data['contact_samples']
heading=[];slip=[]
for side in 'lr':
    previous=None
    for row in rows:
        if not contact['planted'][str(row['frame'])][side]:previous=None;continue
        ankle=row['feet'][side];toe=row['toes'][side]
        heading.append(abs(math.degrees(math.atan2(toe[0]-ankle[0],ankle[1]-toe[1]))))
        if previous:
            dt=(row['frame']-previous['frame'])/24
            dx=ankle[0]-previous['feet'][side][0]
            dy=ankle[1]-previous['feet'][side][1]-speed*dt
            slip.append(math.hypot(dx,dy))
        previous=row
assert heading and slip
result={'status':'PASS','max_stance_heading_degrees':max(heading),
        'max_stance_ankle_slip_m':max(slip),'virtual_forward_speed_m_s':speed,
        'max_root_correction_m':contact['max_root_xy_correction_m'],
        'limits':'Ankle XY relative to implied map travel during source-designated stance; not a full sole contact solver. Review top/front feet sheet for toe roll and strap contact.'}
assert max(heading)<20,result
assert max(slip)<.005,result
(root/'review/3d-v2/legionary-feet-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
