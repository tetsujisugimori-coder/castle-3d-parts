# Stage 3-D-5C results (initial submission)

Overall PARTIAL; limited merge HOLD pending final HEAD CI, retained original artifacts and independent archive audit. This document describes pre-submission runs; final HEAD-specific facts will be appended to the PR without changing these raw records.

## Scope and results

- Base HEAD6ed080ff38e50c7cb808d42ff0c36aeafc118ecd / tree3aad541d92c1b6c28f7bd09f5dab0dfa5d1ebf64. Stacked onto PR39 branch; Issue38. No original CAD/Web/ledger/test expected values changed.
- New full-topology/pcurve recorder pins FreeCAD1.0.0/OCCT7.8.1 and fixed FCStd SHA. Bolt24 and Guide48 pcurve uses. Native01 completed. Native02 is final local recheck with new contract corrections; its final disposition is reported on PR.
- Represented all-parameter coefficient identity is not native-real correspondence. Material outer UNKNOWN; void inner UNKNOWN; all8 real error axes UNKNOWN; all-state equivalence UNKNOWN. Representative ordinal0 NOT_TESTED. Current actual128 NOT_TESTED, prior D5B128 NOT_TESTED, historical D4 actual128 UNKNOWN, exact analytical128 PASS are version-separated.
- Fixed-observation fault controls use full copied observation inputs/outputs, not modified CAD solids. Topology missing/extra, direction, pcurve, surface, material orientation, inner-wire endpoint perturbation, location, self-rehashed corruption reject with semantic reasons. Normal observations remain accepted. No claim that these are actual collision experiments.
- Mathematical controls include false bounds, transform ordering/unit/parent errors and prior between-sample interference model. Normal/fault expectations retained. Actual modified-native-solid collisions NOT_TESTED.
- Existing5B and5 unit suites are rerun unchanged. All base tracked files must remain byte equal except append-only LOG. Existing source set retained; new paths limited to D5C code/docs/workflow. Execution source hashes copied into evidence and checked unchanged.

## Review-driven correction history

Independent review identified degenerate Plane axes were not rejected. New fail-closed gate rejects dependent axes; same represented counterexample retained as a regression. Earlier coefficient PASS concerned only an affine equation, not proof of a Plane.
Initial opening controls changed arbitrary vertex0 and were labelled too broadly. Earlier raw records are retained; final controls derive endpoint IDs from inner-wire incidence (Guide only) and explicitly label observation-only perturbations. This is a correction of coverage description, not a new native geometric proof.
LOG exception is now append-prefix checked. Initial control and test counts are not substituted for final versions.

## Failures and limits

Early exploratory Part-first import exited139 (cause UNKNOWN); FreeCAD-first import succeeds. A Line2dSegment lacked Direction; final extractor records endpoints/range-derived affine coefficients. Probe history is a later-created supplement, not original contemporaneous raw log. GUI command failed without display; GUI NOT_TESTED. No original repair/save/regeneration and no new software installation locally.

## Reproduction and evidence

`python3 -B cad/stage3d5c/run.py <new-dedicated-output> --native` refuses output reuse, uses dedicated TMPDIR, emits identity, all base/source manifests, exact128, representative selection, full controls, isolated document observations and command stdout/stderr/exit codes. Formal workflow records submitted HEAD separately from checkout/merge-ref HEAD and tree. `manifest.json` and outer `sha256.json` have different coverage: the outer hash file includes failure and all emitted evidence except itself. Raw artifact ZIP must be independently read back and verified; upload acknowledgement is not preservation completion.

Independent review: separate process, same kernel and extractor; independent Fraction72 equations/ranges/plane axes/raw BRep hashes. Full final source review and final CI artifact review PENDING at submission. No independent kernel or actual error-bound certificate. No whole realCAD safety, strength, historicity or GUI acceptance.

Next gate: resolve stored/generated provenance, native trim/material/void real-set theorem, finite API/kernel/transform/state bounds before a real interval can execute. Observation count increases cannot discharge those obligations. No automatic128 rollout. No merge, Draft release or publication authorized.
