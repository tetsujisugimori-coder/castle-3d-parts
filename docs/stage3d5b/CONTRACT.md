# Stage 3-D-5B acceptance and contact specification

Tracks [Issue #38](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/38)
and its [continuation review](https://github.com/tetsujisugimori-coder/castle-3d-parts/issues/38#issuecomment-6895873239).

## Material, void and contact

The synthetic material is a closed stock with an **open** cylindrical void
removed. Its cylindrical wall belongs to material. The query cell is closed.
The certificate means **every point of that closed cell is empty space**.
Consequently a cell touching the wall fails that certificate by specification;
this is not an UNKNOWN caused by inadequate numerical resolution. It does not
classify a real CAD mechanism as physically unsafe or penetrated.

For a centered closed rectangle in an open empty disk, the condition is
`hx^2 + hy^2 < rho^2`. Equality touches material; a larger value includes points
outside the guaranteed void. The test trio uses the same exact circle r=1 m,
hx=3/5 m, hy=4/5 m with dy=0,-10^-12,+10^-12 m and grid=10^-15 m. Expected results
are FAIL/PASS/FAIL. These synthetic perturbations are fixture choices, not
claimed tolerances or error bounds for FreeCAD. The exact tangent input is the
same one that the historical v1 checker incorrectly accepted. Historical raw
records and later hash-matched source reconstruction remain separately labelled.

An absence of proven BRep approximation/placement/error premises yields
UNKNOWN for real inclusion. Missing required observation evidence or a known
contract violation yields FAIL for that input contract. A successful schema
check is not proof that the metadata actually came from the BRep.

## Sufficient conditions and unproved link

For material A\VA and B\VB, A subset B and VB subset VA imply material
containment. An outer stock filling a hole can conservatively enlarge material
but cannot authorize passage through the hole. A finite-point sample, bbox,
volume, stored tolerance or hash does not prove this set relation.

If independently proven nonnegative errors ec,er,et bound center displacement,
radius shrinkage and relevant-point transform error, an open disk of radius
rho=r-ec-er-et is guaranteed empty. Center L1 error is a conservative Euclidean
bound. Inner half extents round down; external min/max coordinates round down/up.
All these calculations use exact Fraction inputs. Their premises are not
derived from OCCT by this implementation. Real finite errors remain UNKNOWN.

## Fixed input, transformations and native execution

The current-main FCStd SHA is
`c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a`.
The historical local candidate SHA was
`4597bee609eb4f3e262a60c8989f1cfb0ba90081408b4c3f0703c2ae8fd911a2`.
These are different input versions even if the two embedded Shape members have
equal bytes. No historical observation is substituted for current extraction.

`native.py` imports the two original Shape members from the FCStd ZIP. The
Document is not recomputed, repaired or saved. Serialized Shape Location is
imported once and XML Placement is recorded without another application. This
execution rule avoids intentionally applying the same transform twice; it does
not establish a certified world-coordinate error or document-pipeline theorem.
0/70/140 mm observations are isolated Shape translations from the saved-zero
input, not a proof of all positions or native Document-state equivalence.

Faces receive descriptor fingerprints using surfaces, orientation and trims;
face numbers are lookup indexes only. Nominal D4 plane candidates are recorded
without proving trim coverage, orientation semantics or Solid inclusion.
Unsupported surfaces, missing information and no certified numeric enclosure
cannot be silently converted into a real PASS. A zero count of cylindrical
candidates is an observation about this fixed input, not proof of general
mechanism semantics. The analytical circular fixture is independent of the
actual guide's bore type.

Stored OCCT tolerance is not an error certificate against this analytical model.
[BRep_Tool](https://www.occt3d.com/dev/doc/refman/html/class_b_rep___tool.html)
describes tolerance and surface Location access;
[BRepCheck_Analyzer](https://occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html)
describes validity controls and finite-point/default versus exact-method
conditions. These API contracts do not discharge the missing BRep-to-model
inclusion relation. Documentation version is not an asserted installed version.

## Regression and evidence acceptance

Keep D1-D4 interval definitions and all existing source/CAD/Web bytes unchanged.
The preserved 13 methods plus 1 new contact method are 14 methods; mutation,
normal and generated-input counts are separate. See TEST_MATRIX.md.
Existing D5 6 methods run separately. The independent checker imports the
transplanted path, captures its SHA and records every new input/expected/result.
Shared Fraction and semantic premises are explicitly documented.

Record actual checkout commit/tree/parents, submitted HEAD, command, exact
source bytes and failure logs. Official CI artifacts, historical raw records,
local executions and later reconstructions are distinct evidence classes.
No old HEAD CI substitutes for the final submitted HEAD. Preservation/readback
does not establish indefinite retention; retention remains UNKNOWN.

The exact-model 128-interval regression and real-CAD 128 intervals are counted
separately. This stage does not execute a certified native interval oracle;
its real intervals are NOT_TESTED128. Prior-stage real UNKNOWN128 is preserved
separately. No synthetic PASS is copied into real interval results.
