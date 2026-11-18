# Independent post-transplant review

Reviewer: `/root/resume_test_mapping`, separate from the implementation lead.
Review date: 2026-11-15, Asia/Tokyo. This is a local source-and-output review,
not GitHub Submit review or official final-HEAD CI.

## Limited result

**PASS** for unchanged transplanted synthetic routines, the listed contract
controls, and separate rational reference calculations. Overall acceptance,
real BRep correspondence/inclusion and merge remain outside this result.
Real BRep inclusion is **UNKNOWN**; this reviewer executed no FreeCAD/OCCT.

The new checkout is based on main commit
`18ffb29eeb3db067d47513f76e3a2ef44865c45a`, tree
`423d33c5a8283445832ea3c5495dc94090796090`. The reviewed branch is
`feat/stage3d5b-brep-containment`. Later commits and CI must be matched to the
source hashes in the output; this base commit is not a submitted implementation
HEAD.

## Which implementation was tested

The new `cad/stage3d5b/independent_check.py` requires `--candidate-dir` and checks
the actual imported module paths. The fresh execution imported this checkout's
`cad/stage3d5b/boundary_contract.py` and `circular_contract.py`, rather than the
old run's fixed `HERE/candidate`. All four transplanted source/test byte hashes
match the preserved D5B v3 hashes. `summary.json` records these identities and
the checker hash. No source or original evidence file was changed by this
reviewer, except the newly authored independent checker and this review.

Actual invocation from the new checkout:

```text
python -B cad/stage3d5b/independent_check.py --candidate-dir cad/stage3d5b --output-dir evidence/stage3d5b/independent-local
```

Exit code: 0. Log: `evidence/stage3d5b/independent-local.log`.
Output manifest: `evidence/stage3d5b/independent-local/manifest.json`.
This fresh local execution is distinct from the preserved pre-transplant run.
To reproduce, use a new output directory; existing output is never overwritten.

## Inputs, counts and results

The checker saved complete, individually identified inputs, expected results
and actual results for:

- 17 reviewer fault inputs and one independently defined normal fixture.
- Three explicit contact controls: the original exact tangent, an inward
  half-width shift of `1/10^12 m`, and an outward shift of `1/10^12 m`.
- One real-input gate, which must remain UNKNOWN.
- 10,000 exact rational rectangle input cases in `rectangle-inputs.jsonl`.
- 5,000 exact rational rounding input pairs in `rounding-inputs.jsonl`.

All controls matched. The 17 mutations overlap the purpose of the E-series;
they are not 17 disjoint geometric proofs. The 13 preserved unittest methods
are method count, not input count. Running those methods and earlier-stage
regressions is a separate validation activity reported by the implementation
lead.

## Mathematical independence and shared premises

The rectangle reference computes all four signed corner expressions and takes
their maximum squared distance, whereas the implementation directly combines
the rounded half-extents. Generated rectangle half-extents are integral grid
multiples, so the reference does not reuse implementation rounding to judge its
geometric result. Grid rounding is checked separately with rational `divmod`.
The deterministic random seed is 35052, and its sequence is recorded by the
actual per-input files, not only by the seed.

Both paths share Python Fraction arithmetic and the declared exact primitive
model. The reference calls the candidate only as the system under test; it
does not import candidate rounding into the reference equations. Observation
guards call candidate `circular.rigid`; this checker does not independently
extract or classify real placement transforms. The reviewer fixture/mutations
come from the earlier independent fixture family, not the implementation's
`test_boundary_contract.fixture()`. Reusing this declared synthetic premise
does not supply evidence that an actual CAD body has that geometry.

## Contact semantics

The synthetic material is closed stock minus an **open** through-cylinder.
Its inner circular wall is material boundary. A **closed** rectangular cell
is guaranteed empty only if `hx^2 + hy^2 < rho^2`. Equality places a corner on
material boundary and violates that declared empty-space contract. The tangent
FAIL is therefore a specification-level rejection of contact, rather than an
UNKNOWN produced by numerical precision. It does not classify actual-CAD
contact, interference or mechanics.

The exact tangent with half-extents `3/5,4/5`, radius 1, is the same input that
the initial local implementation wrongly admitted. The final code rejects it;
the exact inward/outward controls are PASS/FAIL respectively. Their quantum is
`1/10^12 m`, so the offset survives rounding.

## Provenance and remaining limits

The preserved old D5B manifest's 41 payload files were reread and matched by
size and SHA-256 during preparation of the new test correspondence table.
Old original result records, corrected records, SHA-matched reconstructed v1
source, and this new execution remain separate evidence classes. The old
independent 17-case JSON did not save full input bodies; newly derived inputs
were labelled as auxiliary derivations. In this new execution all independent
inputs are actually saved.

No real BRep extraction, closed-Solid proof, surface/hole correspondence,
geometry tolerance-to-inclusion bound, continuous motion or 128-interval
geometry was independently established here. A source-hash match and a
synthetic PASS cannot discharge those conditions. Native extractor changes,
official CI checkout/merge-ref attribution, artifact digests and final PR
review require separate results.

2026-11-15 JST.
