# Spearman round 12 — combined candidate (CPU review; GPU pass pending)

Not PASS. Source ports on astra/unit-anim-3d-v2; Git refused ORIG_HEAD.lock.
The lead must run `ROUND=12 tools/art/anim3d/units/spearman/gpu.sh` from this
checkout. The shipped atlas remains the round-11 GPU atlas until that pass.

## Selected work

- Skill branch d7a87b11: latest SKILL, LOG and kit measurement/image helpers ported.
  Critique branch afa9a90f was inspected; the current kit critique already
  supersedes it (zero-offset blurred colour, regional reporting, focus-safe notes).
- Fable A ee83409f: retained the painted Eevee look, per-part projection/seam
  fill, calibrated registration and display-space reduction already in round 11.
- Fable B 28da82cb: selected measured greave/ankle shaping, guard placement,
  seated straps, cloak flare/hem, disc diameter/band and authored forward death.
  Did not import its old duplicated kit, old materials or permissive contact bounds.
- Astra A 190749cb: original-length foot fitting wins on contact. Selected its
  width-without-lengthening rule; dropped its competing shin/guard fit because
  Fable's same-region silhouette was stronger in the director's review. Did
  not stack both deformations. Sleeve shortening had already lost its A/B.
- Astra B e1c58d74: retained frozen brown sole undersides, shadowed skirt lining,
  rear shoulder continuity. Its own rest colour regressed very slightly
  (blurred 4.509 → 4.514) for the motion win (lining luminance 101 → 83).
  Shared implementation now lives in kit/continuity.py, called by the unit wrapper.
- Astra C 3ac739c9: selected KayKit Hit_B (CC0), wider Quaternius walk tracks
  and reduced walk shoulder swing. Dropped its donor death: improved over r11,
  but Fable's shield/crest ending is more readable at 64 and 160. The director's
  alleged Fable "cloak fin" was the crest; no corrective flattening was applied.

## Integration failures and decisions

Fable's x1.42 foot length failed the unchanged 40 mm contact bound: 42.6 mm
sole correction, then 56.5 mm root correction with the support IK solve.
The combined candidate uses x1.50 width, original length and x1.18 height,
plus Fable's guard/strap/shin fit. This deliberately sacrifices some of the
standalone Fable rest silhouette to retain a valid walking foot. Support-foot
IK preserves donor foot rotation and limb lengths; no check was loosened.

Idle and attack keep their source choreography. They must be rebuilt on the
changed guard and geometry, so this is a form rebase, not a claim that the
round-11 action or .blend hashes remain identical. The round-12 action receipt
pins the locally checked result for the GPU rebuild; the final appearance still
needs the lead's review.

The CPU painted-look proxy uses the real frozen pigment and Cycles AO, but an
analytic sun instead of Eevee Shader-to-RGB and no live cast shadow. GPU colour,
contact shadows and final byte size must be measured again; CPU and GPU numbers
are not interchangeable.

FOCUS a: Match sandal instep height, strap bands and remaining shin contour without lengthening feet beyond the contact budget.
FOCUS b: Review final GPU foot shadows, sandal tone and cloak lit folds; preserve the lining/sole continuity wins.
FOCUS c: Review death shield tilt and early spear release, and the hit peak at 160; keep the wider open-mocap walk contact-clean.
