# Stage 3-D-4 independent local review

Reviewer separate from implementation. Review baseline e63b07a / remote equivalent e364f39, tree7fa5b1e. Final review covers the subsequently modified local D4 files recorded in reviewed-files-final.json, not a later CI claim. No repository implementation file was edited by this reviewer. All test packages here are synthetic packaging, not formal CI originals.

## Boundary derivation
The exact-rational orthogonal checker reconstructs bounded material cells using signed X crossings, requires every supplied elementary face to equal the reconstructed oriented boundary along all three axes, then checks connected material and edge/vertex manifoldness. Its input denotes exact rational geometry, not rounded FreeCAD observations. Outward floor/ceil rounding and strict void separation are conservative for this defined representation. An exact arithmetic error of zero is restricted to that representation.

An independent voxel-membership oracle checked 40 seeded connected box unions against reconstructed material. Separately, for the fixed D2 dimensions, the translated bolt X interval contains guide X over the full 0..140mm range. YZ cross-section wall gaps give exact minimum distance1mm. The proposed inner-hole box has minimum wall gap0.1mm. This calculation does not invoke pair_relation or the D2 proof routine. Existing 128 equal-width intervals have midpoint motion bound35/64mm and clearance lower29/64mm. These checks do not connect the analytical model to imported CAD.

The native reader records actual FreeCAD1.0/OCC7.8 original and 7 in-memory mutations. Real BRep-to-exact-boundary conversion, hole-inner containment, placement and native continuous transform errors remain unproved. CAD128UNKNOWN and physical safety NOT_TESTED are correct; no collision claim follows just from enclosing-box overlap. Source identity is scoped to raw source bytes, not native correspondence.

## P2-1, closed locally after same semantic counterexamples
Initial cad/stage3d4/audit.py accepted missing native inputs, empty analytical interval arrays and empty analytical guide faces while trusting summary counts. Its shipped minimal normal ZIP had only workflow source in each command, no native geometry or analytical interval evidence, yet statusPASS. Saved minimal-accepted.zip and minimal-result.json preserve that actual pre-fix result.

Four single semantic mutations were recorded using existing actual native/analytical raw data in an explicitly synthetic command package: missing original bolt faces, wrong row input-source identity, missing analytical intervals, empty guide boundary. All were accepted by the old auditor. First strengthened-auditor experiment also exposed the separate native-control inconsistency below, so its analytical rejection was not credited as semantic detection.

Final full-source packages in after-isolation/ contain the newly isolated native raw evidence, all current source bytes, BRep files and original analytical report. Each immutable package is fed to both old auditor and new auditor. Normal is accepted by both. All four mutations are accepted by old and rejected by new for NATIVE_TOPOLOGY_MISSING, NATIVE_INPUT_MISSING or ANALYTICAL_RECOMPUTATION_MISMATCH. The source set is not mocked in this independent run. Existing minimal package now fails the fixed source set requirement. Tests' explicitly scoped source mock is not represented as a production source-set audit.

## P2-2 native control isolation, closed locally
Stronger audit rejected the existing final-native normal data: hole_shrunk row changed the supposedly unchanged Bolt BRep hash as well as Guide. All observed Bolt fields except hash matched, but the prior row-specific unchanged Bolt BRep bytes were not captured. Therefore the cause is not established; kernel shared state/serialization is a hypothesis only. Original CAD bytes remained unchanged.

The runner now imports each original and mutation operand independently from fixed serialized BRep, saves both part BReps for every fault row, checks repeat export hash stability and unchanged-side identity. Existing old raw data is preserved. In native-isolated, only Guide changes for hole_shrunk and only Bolt for each other mutation. New complete raw normal package passes the strengthened auditor. The isolation change is not proof of a root cause or native geometric containment.

## Validation and limits
- Independent initial D4 suite39 PASS; corrected suite40 PASS.
- 40 independent exact voxel unions PASS and separate fixed-pair/inner-hole calculations PASS.
- Four immutable semantic counterexample packages: old4 accepted/new4 rejected; complete normal accepted.
- Fullsource checks include1,498 source instances and1,544 ZIP entries in these synthetic packages.
- Actual native raw JSON/BRep from implementation was inspected, but this reviewer did not independently rerun FreeCAD or import every BRep into another geometry kernel.
- Formal final HEAD CI, original artifact retention and Library readback are PENDING and not certified here.
- No remaining blocking P1/P2 found in reviewed local scope after corrections. Limited local technical review PASS, overall PARTIAL until final CI/evidence audits. CAD128UNKNOWN remains.
