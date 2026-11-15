# D4 local results and limits
Baseline main4f9f973/tree2d57c701. Original SHA256 c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a unchanged. User scope is boundary guarantee research, not native PASS target.

## What is established
The exact rational orthogonal representation supports closed, connected, manifold unions of axis-aligned rectangular grid cells. The verifier reconstructs cells via oriented X crossings, then recomputes all three-axis boundary faces and requires exact equality. The supplied numeric error/PASS assertions are not trusted. Outward rounding is floor(min)/ceil(max); inward candidate boxes require strictly positive separation from material. Touching is UNKNOWN, exact model open-interior overlap is PENETRATION only for that model. Outer-envelope overlap never proves native collision.

D2 exact rational model remains128PASS. Native128UNKNOWN. No conversion theorem relates floating-point FreeCAD trimmed surfaces, their stored tolerances and Boolean semantics to these rational faces. Thus actual material enclosure, inner bore, placement error, arithmetic error relative to BRep, and native continuous motion all remain separately UNKNOWN. Exact input arithmetic zero is not a BRep error bound. Source hash equality is identity only. Actual manufactured objects, strength, history and all other parts/rotations are NOT_TESTED.

## Actual native observations
FreeCAD1.0.0 / OCC7.8.1 executed read-only extraction of original and7 isolated in-memory mutations. Captured each face's type, orientation, ordered trim edges/vertices, normals, area, solid/shell closure/orientation, placement, BRep and source bytes. Enlarged bolt, reduced hole, placement shift and reversed orientation differ from original BRep but are still only observed representations. Missing face/open shell, curved replacement, extra solid are rejected by the eligibility checks. All actual results remain UNKNOWN, not a proof based on isValid/tolerance/volume/BBox/finite samples.

Initial native attempts v1–v4 exited1 without kernel diagnostics; recorded progress narrowed termination to Part.makeCompound. A tiny separate native reproduction also exited1. No root cause inferred. Replacing only that test-construction call with disjoint-solid fuse allowed the same extra-solid fault intent and all7 cases to complete (v5). Old failed raw records retained. This is a test-construction correction, not a product repair or historical failure attribution. Current final-source run and official CI will be recorded separately.

Local portable39 testsPASS (including synthetic ZIP controls; not native evidence), D1 10/D2 20/D3 19+4, Stage3C portable/fault/history/parity and Stage3B regressionsPASS; Node497PASS. Real FreeCAD history transactions and separate-process reopenPASS using dedicated copies. No local browser/GUI or physical safety tests were performed; unchanged formal regressions provide separate future results.

Independent review, finalHEAD CI and originalCI archive/readback audits PENDING at initial writing. OverallPARTIAL, limitedmergeNO until these complete. No unrelated document commits will be mixed into a fixed CI target; later results can be PR comments. No merge/publication.

## Minimal next prerequisite
A bounded, independently validated relation from this fixed serialized BRep's trimmed planar faces and orientations to exact/inward/outward halfspaces, including geometric and transformation error, is missing. Alternatively a separately approved authoring contract could define exact geometry as the authority. Neither is silently assumed. Repeated samples cannot discharge the missing premise; no general CAD prover or redesign is attempted here.
