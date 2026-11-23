# Spearman running log

- Round 4 start: requested prior spearman-log.md and gpu-logs-spearman-r3.log do not exist; gpu.sh is also absent in this checkout. Read the complete checked-in round-3 REVIEW.md instead; no GPU success inferred. Existing c manifest explicitly says CPU Cycles, 384 px / 24 samples.
- Opened c-textured-lit, f-restpose-compare, all five e strips, c-details and sampled round3.mp4 frames before editing; preserved received evidence under spearman-round3-preserved/.
- Honest round-3 critique at 256 px: same palette and identity, but shield ornament is visibly doubled and smeared, crest too broad and smooth, sleeve/shoulder outline abrupt, feet carry pale base contamination, base too shiny/smooth with a dark rim. Rest is readily distinguishable from the painting. At 64 px the red/gold/cream hierarchy reads correctly; feet, wider shield and crest still differ.
- Motion critique: idle subtle, move reads as marching but lifted foot texture fragments are visible; attack is readable with stretched shoulder paint; death cape forms a rigid triangular shelf. Supplied movie is sequential rather than five clips side by side. No PASS warranted.
- Read all 216 lines/all chapters of PLAYBOOK, all 22 shared feedback items and entire spearman feedback; loaded modeling, materials, cameras, lighting, animation and rendering Blender skills. Read project instructions, art skill, asset licences and source prompt.
- Plan: align actual shield relief and crest before frozen UV projection, prevent base paint leaking onto feet, retain generated backside fills and modeled straps/folds; keep one fixed histogram grade. Add unit-local 160 px trimmed packing, independent decoded validation, 512/256 master export and an eight-second five-column movie plus executable GPU entry point.
- First round-4 preview caught a reversed-normal assumption in the shield mask: it blanked the painting. Fixed the visibility test using ray distance (compatible with the existing shell winding) and rerendered before proceeding. Shield ornament is now much cleaner; no failed preview is treated as passing evidence.
- Round 4: shield center aligned to (163,139) on the 256px painting; real rays narrowed and shortened, crest narrowed with depth preserved, ankle moved inward/back before frozen UVs. CPU rest IoU 0.8511 versus received 0.8394; RGB union error 33.30/38.15/39.58 versus 35.58/41.26/42.70. Diagnostics only, no PASS.
- Death lower-cape pin weights reduced to 15 percent with shoulder pins retained; CPU strip shows the triangular cape shelf removed, and the 10-sample saved-rig audit reports zero findings. Found a separate release-transform issue: converting shield matrix to quaternion discarded its scale; preserve scale and regenerate death after other clips.
- Round 4: rebuilt and CPU-rendered idle at 256 px / 12 samples.
- Round 4: rebuilt and CPU-rendered move at 256 px / 12 samples.
- Round 4: rebuilt and CPU-rendered attack at 256 px / 12 samples.
- Round 4: rebuilt and CPU-rendered hit at 256 px / 12 samples.
- Plain-material review caught buried shield relief after lateral registration: the convex surface depth changed beneath the moved rays. Corrected with per-vertex ray intersection against the true shell plus nonzero raised keel/boss/rim depth. Rebuilding dependent renders and clips again; the earlier visually cleaner painted result was insufficient geometry evidence.
- Final round-4 master: rebuilt and CPU-rendered idle, 256 px / 12 samples.
- Final round-4 master: rebuilt and CPU-rendered move, 256 px / 12 samples.
