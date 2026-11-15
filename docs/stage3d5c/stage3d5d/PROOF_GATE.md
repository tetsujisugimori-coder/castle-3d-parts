# Native proof feasibility and stop gates

## What improved in5D

An already installed OCP binding reads isolated BRep member bytes using public OCCT7.8.1. Loaded ELF libraries/SONAME, SHA, CPython ABI and wheel metadata are recorded. This is a distinct build/process from FreeCAD1.0.0; same version is not binary or numeric equivalence.

Public BRep_Tool returns SameParameter/SameRange flags directly. For these fixed non-seam Plane uses, BRep_TEdge.Curves() representations can be matched by raw Surface handle and edge-relative Location; returned pcurve handle identity can be cross-checked against the stored representation. This avoids pretending the unexposed bool* isStored output was returned.72 uses were observed as stored. Handle identity is limited to this process/binding; geometric equality is not used as a replacement. A geometric Copy is a negative identity control. Seams with PCurve2/ambiguous matches remain UNKNOWN. Guide16 trimmed pcurves include BasisCurve, trim range and represented Line coefficients.

These observations improve access to evidence, not native set proofs. The flags are stored consistency assertions and do not independently establish continuous curve/surface correspondence. ShapeAnalysis_Edge.CheckSameParameter defaults to23equidistant points and returns sampled maximum deviation. It is NOT used as a continuous bound. Increasing samples does not change that distinction.

## Ordered propositions

P0 fixed original hash, API identity and full inventory: observed, bounded by binding access.
P1 represented coefficient identity: previous5C mathematical result remains conditional; new trimmed representations are not silently substituted into it.
P2 every trim/use/Location across complete native surfaces corresponds to a defined real domain: UNKNOWN. Ordering and flags do not prove full native set equality.
P3a native material M contained in outer model O: UNKNOWN.
P3b closed query Q contained in native void/complement with no wall contact: UNKNOWN. Extra internal material may satisfyP3a but violateP3b; the implication is invalid.
P4 eight finite actual-real error terms: UNKNOWN, null. No point sample, tolerance or exact IEEE coincidence supplies them.
P5 native global/parent/state trajectory versus modeled trajectory for all t: UNKNOWN. Static0/70/140mm does not prove it.
P6 whole interval movement bound attached to native trajectory: UNKNOWN.

Only P2–P6 established with supported proof objects plus positive residual lower bound could permit actual interval evaluation. Current code is a readiness gate, not a native theorem prover: no supported native proof calculus has been established. Caller status PASS, a hash or a claimed theorem method cannot unlock the gate. Data contract PASS does not mean proof PASS. D2 ordinal0 staysNOT_TESTED; no128expansion.

## Finite error definitions

Use unchanged5C ERRORS.json for eight definitions, finite conditions, exact-rational conditional rounding and insufficiency reasons. This5D supplement changes no upper value: all native upper_m remain null. Direct access to stored flags and pcurves does not establish error enclosure. The exact sum/subtraction controls are conditional arithmetic on supplied rational bounds, not their certification. Nonpositive residual is UNKNOWN, not collisionFAIL.

## Motion and material counterexamples

Observation JSON controls cover mislabelled pcurve origin, missing trim, reversed orientation, extra void material, open end and double transform. These reject deviation from a fixed synthetic record; they do not validate actual CAD occupancy. Separate actual copied-BRep controls mutate a stored flag, root orientation and root Location for each part. Full mutated BRep bytes and API output are retained, originals checked unchanged. Those6controls demonstrate observation sensitivity only, not collision or set-theorem validation. Actual cavity-extra-material/endface-removal/continuous interference faults remainNOT_TESTED.

## Official sources read2026-11-16JST

- OCCT7.8.1 BRep_Tool.hxx/.cxx: publicSameParameter/SameRange, CurveOnSurface and relativeLocation matching.
  https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRep/BRep_Tool.cxx
- Public representation APIs:
  https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRep/BRep_TEdge.hxx
  https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRep/BRep_CurveRepresentation.hxx
- Sampling limitation:
  https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/ShapeAnalysis/ShapeAnalysis_Edge.hxx#L143-L158

Same kernel family, two builds and a separately written check do not constitute independent CAD-kernel proof. No native safety, physical strength, history or GUI acceptance.
