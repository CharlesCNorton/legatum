# Round-two review

Candidate only; **no PASS marker**. At 64px the camouflage, swept wings, eight
jets and cream stand read as the same painting. At 256px the fuller fuselage,
longer paired nacelles, smaller warm base and restored wing/tail brushwork are
closer. Intake highlights and some wing/pod contours still differ; frozen
source lighting is apparent during larger banks. The crash reads as a bent
miniature, with a continuously collapsing support and a held final pose.
Round-two GPU art approval remains pending. No runtime wiring changes.

The supplied round-one GPU pass succeeded: all stages at 512px / 96 samples,
189,538-byte Q80 atlas and verified movie. Original reviews, raw frames and
four decoded movie samples are preserved in `masters/jet-bomber/driver-r1-gpu/`.
Round-two CPU interims use Cycles / 12 samples, actual 512px renders and derived
256px masters. All b/c/details/d, five e-strips/WebPs, f-restpose comparison and
g top/nose move-cycle evidence live in `review/3d-v2/` outside git. CPU movie:
`jet-bomber-round2-cpu.mp4`; the lead writes `jet-bomber-round2.mp4`.

The unit checks cover closed fuselage/wings/fin/intake geometry, eight jets,
six AO/curvature maps, a fixed base, physical support attachment, finite
collapsed-support volume, accelerated bomb release, idle/move endpoint closure
and a two-frame terminal wreck. Delivery checks all 40 frames, 160px logical
cells, quality >=75, <=200,000 bytes, exact alpha reconstruction, trim offsets,
nonoverlapping transparent gutters, clipping margins, current source/grade
hashes and identical decoded death hold. Movie checks H.264/yuv420p, 1600x348,
240 frames and 8.000 seconds. Exact latest results are appended below.

Run from the repository root on the lead's Metal-enabled host:

```sh
ROUND=2 tools/art/anim3d/units/jet-bomber/gpu.sh
```

It renders every stage, exports both master sizes, writes review comparisons,
audits, packs, validates and encodes the round movie. No silent CPU fallback,
upload, push or PASS is implicit.

Non-obvious findings: sparse airfoil faces let hidden root vertices fade the
projection over visible wing surfaces. Simple subdivision before ray testing
localizes that mask, and visible thin airfoils need not reject pigment because
their smooth normals graze the camera. A matching hero silhouette can also hide
a physical support gap; alternate views and a world-space attachment check
caught it. All source painting remains UV pigment on genuine solid geometry.

Final round-two CPU results: **180,130 bytes at Q85**, all 40 frames, 160px
trimmed atlas; geometry/motion audit, input preflight, alpha/offset/source/grade
validation and movie metadata all pass. Eight Python syntax checks, both shell
syntax checks and `git diff --check` pass. The browser art gate's
`render-sets.mjs` failed in this sandbox and is not claimed as passed.

Final silhouette IoU is 0.889 at 256 and 0.900 at 64 (round-one GPU256: 0.821).
Opaque RGB mean error is 4.18 / 3.90 levels out of 255 respectively. These
numbers do not establish painting parity. The support's inner edge is too dark
in the final CPU hero view; compare it again on the GPU along with the bright
intake rims, wing contours and banked hidden-surface fill. No PASS was written.
