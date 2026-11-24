"""Quaternius Standard -> MPFB game_engine; CC0 source hashes checked by retarget."""
ACTIONS = {'idle': 'Idle_Loop', 'move': 'Walk_Loop',
           'hit': 'Hit_Chest', 'death': 'Death01'}
MAP = {'pelvis': 'DEF-hips', 'spine_01': 'DEF-spine.001',
       'spine_02': 'DEF-spine.002', 'spine_03': 'DEF-spine.003',
       'neck_01': 'DEF-neck', 'head': 'DEF-head'}
for side, suffix in [('l', 'L'), ('r', 'R')]:
    for target, source in [('clavicle', 'shoulder'), ('upperarm', 'upper_arm'),
                           ('lowerarm', 'forearm'), ('hand', 'hand'),
                           ('thigh', 'thigh'), ('calf', 'shin'),
                           ('foot', 'foot'), ('ball', 'toe')]:
        MAP[target+'_'+side] = 'DEF-'+source+'.'+suffix


