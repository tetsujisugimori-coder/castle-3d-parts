# Stage 2-B real CAD pipeline

Run from repository root: `/usr/bin/python3 cad/stage2b/run.py /tmp/new-stage2b-output`.
The destination must not already exist. Requires actual FreeCAD Python module (`/usr/lib/freecad/lib`) and Blender on PATH. No addon is required. B0/B1/B2 source parameters are in spec.json. Public dimensions use metres, native CAD uses millimetres; Z up transfers to glTF Y up through Blender.

Every revision is an independent editable native document. Each part is a Part::Box with expressions referencing its unit parameter object. Height/width/spacing and placement edits recompute without recreating geometry. Count changes require regeneration; this is not advertised as a dynamic object-count feature. Unit.FCStd contains the first seven-component unit; B2's single unit is the retained B1 version, whereas the second assembly unit is B2. Assembly parts carry stable instance names and part/version properties.

B0: two copies of the Stage 2-A 2.2 m trial geometry at X=0 and X=6 m. B1 changes height only to 2.4 m. B2 retains U01/B1, changes U02 spacing to 1.3 m. These are separate, unconnected trial units. Their free gap is intentional; no historically asserted joint is supplied. All geometry is D, reference_only.

STEP is actually exported and reopened component-by-component. Its reconstructed geometry is tessellated in metres and passed to Blender. Native blend and GLB are saved and reloaded, checking every instance bounding box, part/version and total extent. GLB node extras are supplementary; external manifests remain required.

## Drawings and limits

Each FCStd has an actual TechDraw page and Front/Top/Side views referencing the CAD objects. drawing.svg is actual `TechDraw.projectToSVG` geometry with CAD-bound dimensions and dimension witness lines, at 1:50. It is not a screenshot.

**Native linked TechDraw dimension/vertex validation is NOT_TESTED.** Initial attempted DrawViewDimension records returned zero and `getVertexByIndex(1)` failed in this headless environment. Those invalid dimension objects were removed, not accepted. A Qt offscreen QApplication probe also returned Wrong vertex index. The failed originals and logs are in evidence/stage2b/cad. Native view display in FreeCAD GUI is NOT_TESTED. SVG numeric dimensions update from real CAD bounds on each regeneration; that is not represented as successful native linked dimension validation.

All software executions here are headless/background, not GUI hand operation. Physical iPhone, historical shape/dimensions and formal CAD adoption are not tested/approved.

## Reproduction

Two actual complete builds gave identical geometric audits, GLB bytes, mesh-transfer bytes and SVG bytes for all revisions. FCStd/STEP/blend bytes differ; structural consistency is verified but bitwise reproducibility is not claimed. Native format timestamps/session metadata may differ; not all byte-level causes were diagnosed. See evidence/stage2b/cad/reproducibility.json.

## Independent drawing review correction

The initial SVG TOP transform rotated the plan and clipped the drawing. Initial equal-length decorative lines were not accepted as geometric dimension witnesses. Those original files, source and the independent screenshot are preserved. The corrected drawing uses separate Front/Top/Side projection transforms, 0.25 mm model-edge lines, true endpoint-based dimensions for total width/height/depth, measured post centre spacing for both units and actual rail-centre heights. `drawing-measurements.json` stores each dimension's page endpoints, scale and measured mm value. The renderer asserts that page span divided by scale equals the measured value. The actual CAD-derived renderer is separated into `drawing.py` for independent re-rendering.

Native view scale defaults to Page and addView resets placement. Both were corrected: explicit Custom 0.02 scale and placement after addView. All three native scales and placements were checked after FCStd reload. This does not claim successful native linked-dimension validation or GUI visual inspection.

Both build.py and run.py run the research/spec preflight before creating output directories. They fail closed on invalid references or input specifications.
