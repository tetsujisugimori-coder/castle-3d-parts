# Planar continuation independent review

Reviewer: separate agent `/root/planar_independent`, distinct from planar math,
transform arithmetic and native integration implementers. This is a limited
technical review, not approval to merge or certify real CAD safety. Overall
PARTIAL / merge HOLD stays.

## Independence and exact derivations
`cad/stage3d5b/independent_planar.py` builds its own ten-face fixture from the
analytic set `[0,2] x [0,4] x [0,6]` minus the OPEN through-opening
`R x (1,3) x (2,4)`. It does not call the candidate boundary fixture/cell factory.
Independent reference: eight closed atomic material boxes, total volume40 m3.
All boundary points belong to material; the opening complement is open.
The script checks candidate cells against this analytic list, not just volume.

For affine error it separately enumerates coefficient and domain endpoint
combinations. Each coordinate error is multilinear in those inputs; its extrema
on their product box occur at endpoints. Summing maximum absolute coordinate
errors bounds the Euclidean error by the L1 inequality. This route does not
call candidate interval arithmetic to produce the expected bound. It tests
negative/asymmetric outward rounding and leaves geometric-real enclosure
provenance UNKNOWN.

Shared: Python Fraction, boundary schema, closed-material/open-void semantics,
and the candidate APIs called for comparisons. Native extraction, restored
Document state and the CAD kernel have NOT been independently rerun by this
reviewer. Copied IEEE coefficients enclose stored numbers only, not CAD reals.
No independence claim is made for those premises.

## Review findings and controls
The topology adapter initially trusted precomputed coverage booleans. Appending
an unreferenced vertex, edge or wire was silently omitted and the proposed
mathematical boundary still passed. Real inclusion was UNKNOWN throughout;
this was an inventory-contract defect, not a demonstrated real-safety falsePASS.
The implementer recomputed face/wire/edge/vertex coverage and incidence.
The reviewer replayed the identical four input objects: normal PASS remained,
all three appended-entity cases changed PASS to input-contract FAIL with
`UNCOVERED_OR_NONMANIFOLD_TOPOLOGY`. `inventory-recheck.json` records input and
source hashes; the hash-matched pre-fix source is preserved. Original before/
after full inputs and results remain private local evidence; this summary was
generated afterward and is not called an original execution log.

Review also noticed that material connectivity alone did not enforce the
contract's connected boundary. The implementer added atomic boundary-patch
connectivity and a closed-cavity fault. This was corrected before the reviewer's
counterexample execution, so no prior executed falsePASS is claimed for it.
Document local-domain construction now requires an exactly identity represented
baseline linear map before subtracting translation; unsupported baselines leave
the real-domain/error result UNKNOWN.

The independent runner executes31 comparison cases (not31 unittest methods):
one normal boundary, twelve malformed geometry inputs, six coherent hole-model
and containment checks, four through-opening/contact/microscopic queries,
one disconnected-boundary cavity, one affine bound, two rounding inputs and
four observation-adapter cases. These overlap implementation controls and are
not31 disjoint safety proofs. Coherent enlarged/shifted openings may be valid
mathematical shapes but fail A subset M; shrinking a hole conservatively covers
material and passes that one-way mathematical test. A closed through-query
strictly within the opening passes; touching/microscopic intrusion fails the
specified empty-space certificate. Unsupported geometry and missing trims fail.

## Limits and reproduction
Run `python -B cad/stage3d5b/independent_planar.py --output-dir NEW_DIRECTORY`.
The runner saves all inputs, expected/actual outcomes, source hashes and exact
reference cells/formulas.31 comparisons passed locally on the recorded source
bytes; `independent-local-summary.json` is an auxiliary summary. Final official
CI must rerun this script against the submitted HEAD; this local result does
not substitute for final CI/source/artifact verification.

Actual BRep material/void inclusion, pcurve/3D-curve/surface and tolerance
semantics, geometry-real extraction enclosures, Document/world equivalence and
continuous-motion safety remain UNKNOWN or NOT_TESTED as applicable. Exact
polygon coverage proves only the supplied rational model theorem. No review
finding discharges those real premises. Original artifact/readback and final
CI audits are reported separately after actual execution.

2026-11-16 JST.
