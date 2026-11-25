# Spearman-q iteration log

| Round | Motion and look | Evidence | Remaining |
| --- | --- | --- | --- |
| 2 | Shared rigid grips; 39 cm straight thrust; guarded carry; hit recovery; released death props; three held death frames; existing painted armour and per-part emission look | 70 CPU frames; five three-repeat H.264 videos; 341,262-byte q95 atlas; source rig/body, floor, rigidity, trajectory and sampled contacts pass | GPU execution and playing-speed reviewer verdict; broad base and full cloak |

Non-obvious: evaluated imported armour can retain vertex groups despite having
no Armature modifier; clear those unused groups when making rigid copies.
Rigidity means an unchanged transform metric across frames, not unit object
scale: the old decorative kit has valid fixed scale transforms. Evaluate
cloth and hair after their contact keys when checking the floor.
