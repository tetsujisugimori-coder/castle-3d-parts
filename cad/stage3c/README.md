# Stage 3-C native trial D CAD

The source in `cad/stage3b/generated/assembly.FCStd` is read-only input. New candidate `generated/assembly.FCStd` has 23 independent PartIDs. New stocks and Boolean bore tools are construction geometry without PartIDs; only the 23 final single solids are exported to STEP/GLB.

## Reproduction

Use a writable, sufficiently large temporary directory. The observed default `/tmp` was full; no unrelated files are removed.

```
mkdir -p /path/to/writable/runtime
TMPDIR=/path/to/writable/runtime python3 cad/stage3c/run.py /path/to/new/output
python3 cad/stage3c/check.py
python3 cad/stage3c/check_test.py
```

`run.py` refuses an existing destination. It runs actual FreeCAD Python/GUI modules with offscreen Qt, actual OpenCASCADE solids, native TechDraw and Blender background processing. These are not manual GUI tests. Exact observed versions are in the audit JSON. Qt/OpenGL warnings and failed earlier attempts are retained separately.

## Shared state authority

`spec.json` defines axes, ranges and baseline dimensions. `state.py` provides `transition(document, angle_degrees, bolt_m)` and `validate_document(document)`. Angle must be exactly zero for bolt displacement; bolt must be exactly zero for door rotation. Partially inserted bolts also block rotation. The standard FreeCAD property editor is **not** interlocked: direct edits can create an invalid tuple. Always validate after edits and after reopening. Invalid persisted tuples are rejected by the verifier, not silently accepted as safe geometry.

`load_document(path)` creates a document with a caller-owned transient directory, sets its FileName and invokes FreeCAD `restore()`. This extracts the SVG templates embedded in the FCStd, without rewriting paths to external source templates. In the observed Python console environment `openDocument()` left TransientDir empty and subsequent save failed; that failure is retained. The supported restore helper is required for this environment. The standard standalone desktop executable/manual GUI is NOT_TESTED.

## Geometry and limits

- Wooden bolt nominal 900 × 20 × 40 mm, travel 140 mm. At locked position its axial overlap with receiver is 40 mm. This is not a load-bearing or strength result.
- Left/right guides move with the door, bolt translates in door-local X. Receiver is fixed to the right post by geometric surface contact. Direct supporting fastener retention is unproven.
- Candidate supports 880–900 mm length,18–22 mm width,35–45 mm height,.5–2 mm bore clearance. Native Boolean bores follow width,height,clearance; the recorded dimension trials are samples, not proof for every parameter tuple.
- Doorstop contacts the closed door; upper keeper contacts upper bearing/spindle. Eleven contact-chain measurements are geometric only.
- Corner cleats are trial D external joint plates with surface contact to posts and beam. They are not a reconstructed mortise-and-tenon joint. Fasteners, material failure and actual load transmission remain NOT_TESTED.
- Door angles0–90 every1° and bolt travel0–140 every1mm are sampled. Overlapping bounding boxes always proceed to BRep Boolean; disjoint bounding boxes are used only as a conservative proof of zero intersection. All distances use BRep. Continuous intervals remain UNKNOWN.

## Native drawings

Six native pages plus locked-position SVG comparison: Assembly, Bolt, Positions, Doorstop, Support, Joinery. Linked native dimensions are bolt length/width/height,travel-limit witness,doorstop depth and corner-cleat thickness. The support page shows actual solid structure but has no new radius dimension. Joinery detail clips the original source post/beam solids to a local region without changing those parts. Web mesh projections are separate from these native TechDraw pages.

## Failure controls and preserved limits

Invalid persisted states, axis shift, undersized guide bore and forced1° rotation while engaged are tested. Earlier default GLB action export lost the slide animation; ACTIVE_ACTIONS merged export fixes it and six saved/reimported cycle poses are independently recalculated. Earlier left guide lost engagement after shortened bolt locked travel; repositioning the trial guide fixed the same case.

No history confirmation, real timber strength, friction, fastening, security performance, durability or continuous noncollision guarantee is made. All source assets stay unchanged.
