# Planar continuation submission scope

Reviewed baseline563195c/treeadffd2d; main18ffb29/tree423d33c unchanged at start. Same Issue38/branch/DraftPR39. Overall PARTIAL/merge HOLD.

Research acceptance and real-safety acceptance are separate in PLANAR_CONTRACT.md, fixed before implementation. New exact rectilinear boundary theorem builds cells from all oriented trim polygons, verifies closed connected manifold boundary and all-axis incidence; compares closed material containment and strict open void. New affine interval arithmetic never projects a numerical matrix to an exact rotation and never fills missing error terms with zero. New native topology capture covers every Face/Wire/Edge/Vertex with within-input identities and incidence; winding changes are explicit proposal operations with native semantics UNKNOWN. A separate byte-identical isolated FCStd copy is used for restored/recomputed Document samples only, never saved. Original FCStd/member bytes remain pinned.

Local portable tests:58 unittest METHODS (legacy14 + exact planar21 + topology adapter9 + interval/transform14); separate D5 methods6. Independent runner31 INPUT COMPARISONS, not methods; its analytic8-cell/volume40 fixture and affine endpoint enumeration are independent derivations with shared Fraction/schema/premises. Legacy17 fault inputs/10000rectangle/5000rounding runner remains in CI. See PLANAR_INDEPENDENT.md and evidence/stage3d5b/planar-independent.

The independent reviewer found unused topology could be silently excluded. Full identical before/after inputs retained externally; normal remained PASS and unusedvertex/edge/wire changed candidate PASS->FAIL. Real CAD stayed UNKNOWN. Boundary connectivity omission was review-found and fixed before counterexample execution; no prior runtime failure claimed. No original failure evidence overwritten.

Final official CI/native results are pending this source freeze and must be reported at the actual submitted HEAD in PR39/Issue38, not inferred from baseline CI. Native/Document extraction is implemented for existing authorized CI; local FreeCAD invocation NOT_TESTED (no executable found in PATH/standard checked program folder). No local install/environment modification performed. CAD/world input enclosures, pcurve/3D/surface equivalence, orientation/material semantics and finite geometric error remain unproved. Conditional IEEE/rational-model bounds are not real CAD error certificates.

128 interval definitions unchanged: fresh exact analytical run in CI; real CAD interval oracle NOT_TESTED128 until shape/error/motion gates hold; prior D4 real UNKNOWN128 and prior D5B NOT_TESTED128 remain separate. No real interval PASS admission. New translation/distance helpers are conditional arithmetic only; nonpositive lower bounds mean UNKNOWN, not penetration.

Capture final submittedHEAD/actualcheckout/tree/parents and full source, incl.hidden workflows. Preserve rawZIP/logs/failures separately from auxiliary ledgers; independent external readback and final CI scope reported after actual execution. Retention/future retrieval UNKNOWN. No merge/publication/Draft release.

References for observed API semantics (not enclosure proofs):
- https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Placement.md
- https://github.com/FreeCAD/FreeCAD/blob/main/src/Mod/Part/App/TopoShape.h

2026-11-16 JST.
