# D5B preserved test correspondence

This is newly derived auxiliary material. It is not a new historical input log or transplanted-code result.

| ID | Count kind | Expected | Historical actual | Evidence |
|---|---|---|---|---|
| E1-radius-enlarged | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E2-radius-shrunk | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E3-center-shift | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E4-axis-reversed | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E5-normal-reversed | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E6-face-missing | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E7-open-solid | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E8-placement-missing | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E9-double-placement | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E10-unit-conversion | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E11-rounding-direction | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E12-tolerance-excess | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E13-shape-swap | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E14-evidence-missing | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E14-manifest-missing | input | FAIL | FAIL | fault-results.json / candidate-tests-v3.log |
| E15-normal | input | PASS | PASS | fault-results.json / candidate-tests-v3.log |

13 unittest methods are listed individually in test-correspondence.json with source excerpts; they are not 13 input cases.
17 independent mutation inputs overlap the E-series in purpose and must not be added as 17 disjoint geometric guarantees.
The 10,000 rectangle and 5,000 rounding inputs are deterministic generated groups; original per-case input dumps were not saved.
Full independent mutation inputs here were derived now from preserved source and are explicitly labelled as such.

## Post-transplant independent path

A new checker must accept --candidate-dir and import the transplanted files, record SHA-256, and avoid fixed old HERE paths.
Use independent corner expressions/divmod plus exact tangent, 1e-12 inward/outward cases. Share Fraction and declared set semantics explicitly.
Keep tests/inputs/statuses separate from BRep and from the 128 interval counters.

## Evidence classes

Original local result records, corrected local records, later SHA-matched source reconstruction, and this newly derived table are separate.
The old reconstruction can support a new same-input execution, but cannot become the original saved source artifact.

2026-11-15, Asia/Tokyo.

## Publication and old paths

Old repository-relative run paths in the JSON identify preserved original local
archive material. Those old run directories have not been copied into this
transplanted checkout. They are provenance identifiers, not claims that every
referenced historical file is published here. No personal archive path or
private URL is included.

## Current checkout execution

The preserved suite contains 13 methods. The new `test_contact.py` adds one
method with three subtest inputs, so the current suite is **14 methods**, not
the same 13-method execution as the old run. The E-series has 15 fault inputs
and one E15 normal input; the independent 17 faults overlap those purposes.

Commands from the transplanted checkout:

```text
python -B -m unittest discover -s cad/stage3d5b -p test_*.py -v
python -B cad/stage3d5b/run.py NEW_OUTPUT
python -B cad/stage3d5b/independent_check.py --candidate-dir cad/stage3d5b --output-dir NEW_OUTPUT
```

The dedicated CI artifact records unit logs under `tests/`, new E-series inputs
and results under `report/report.json`, and independent full inputs/results under
`independent/controls.json`, `independent/rectangle-inputs.jsonl` and
`independent/rounding-inputs.jsonl`. Each command's `execution.json` and source
snapshots bind the executed bytes and checkout. These paths refer to the
`stage3d5b-portable` artifact root; they are not pre-existing formal CI success.
The implementation lead must fill actual run IDs, checkout and final-HEAD
status after the CI completes.

The local independent 15,000-row outputs are not committed to the repository;
`evidence/stage3d5b/independent-local-summary.json` is a separate compact summary.
The formal CI re-executes the checker against its own checkout and captures all
full input files in its artifact.
