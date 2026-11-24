"""Spearman profile over the shared Quaternius/MPFB retarget and foot-lock kit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'units/spearman'))
import motion
from kit.retarget import apply_matrices, contact_ik, stabilize_walk
from kit.retarget import prepare as prepare_donor

def prepare(rig, root, clip, phases):
    if clip in ('hit', 'death'):
        from donor_motion import prepare as prepare_reaction
        return prepare_reaction(rig, root, clip, phases)
    return prepare_donor(rig, root, clip, phases, motion)
