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



# KayKit Character Animations Free 1.1 (CC0), tested with Spearman Hit_B.
KAYKIT_MAP = {'pelvis': 'hips', 'spine_01': 'spine', 'spine_02': 'chest',
       'spine_03': 'chest', 'neck_01': 'head', 'head': 'head'}
for side in ('l', 'r'):
    for target, source in [('upperarm', 'upperarm'), ('lowerarm', 'lowerarm'),
                           ('hand', 'wrist'), ('thigh', 'upperleg'),
                           ('calf', 'lowerleg'), ('foot', 'foot'), ('ball', 'toes')]:
        KAYKIT_MAP[target+'_'+side] = source+'.'+side

KAYKIT_ACTIONS = {'hit': 'Hit_B', 'death': 'Death_B'}
