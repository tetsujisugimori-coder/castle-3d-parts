# Stage 2-A: authorized D working-copy CAD regeneration

This path does **not** revise the historical claim or the prototype-v1 originals. All dimensions remain D (provisional). A local DEC record is an auditable human-review record, not a cryptographic identity or authentication system. No publication, merge, or production adoption is implied.

## Entry point

```
/usr/bin/python3 scripts/cad-regenerate.py --application /absolute/application.json --output /absolute/new-run-directory
```

The output parent must already exist, but the output directory must not. Symbolic links in application/output/source paths, existing output directories, and output paths within original CAD/Blender, site, or research trees are rejected. Failed runs are preserved as failed evidence, never reused. Use a fresh directory to retry.

The runner invokes `node scripts/research-cad.mjs validate-application --application …` at preflight, immediately before CAD, and immediately before Blender. The engine verifies the application envelope, candidate digest, current frozen research inputs, explicit working-copy approval, and fixed original CAD binding. Only its normalized response is consumed. Parameters are additionally range/type checked by both runner and original CAD module.

## Actual conversion chain

1. Hash tracked files; validate approval and source CAD SHA-256.
2. Copy original FCStd to `input.FCStd` and verify byte identity.
3. Open **the copy**, import the unchanged prototype-v1 build module, remove baseline-only TechDraw drawing/view/template from the working copy to avoid stale dimension annotations, assign approved parameters, and regenerate existing document geometry.
4. Save `palisade.FCStd`, close and reopen it, then verify dimensions, post/rail counts, valid single-solid components, volume, and non-overlap.
5. Export STEP from that reopened document, reopen STEP through FreeCAD/OCCT, and check dimensions, solids and volume.
6. Match reopened STEP solids to CAD components by bounding boxes, tessellate **the reopened STEP solids**, and convert millimetres to metres in `mesh-transfer.json`.
7. Blender imports this mesh, assigns provisional material and basis metadata, saves and reopens blend, exports and reimports GLB. Mesh counts, named posts/rails, triangles and overall dimensions are verified at each stage. GLB Y-up export is converted back to Z-up on import.
8. Emit `manifest.json` containing actual commands, source/application/output SHA-256, software versions, audits and final original-tracked-file hash comparison. Software stdout/stderr is retained in command logs. Any failed command or missing deliverable is a failure, even if Blender exits zero after a Python exception.

This is headless FreeCAD 1.0.0 and background Blender 4.3.2 execution when those versions are reported in each run. GUI interaction, rendering/browser display and TechDraw visual correctness are **NOT_TESTED** by this runner. The baseline-only TechDraw drawing, view and template are omitted from the working copy to avoid stale annotations; regenerated geometry is measured directly. No original texture/look-development identity is claimed for the minimal provisional working-copy Blender material.

## Repeatability and evidence

Run the **same application file** twice into separate new directories. Compare the CAD/STEP and Blender structural audits and STEP-derived mesh separately from binary hashes. A changed FCStd, STEP or blend hash alone does not establish a geometry difference: archive metadata, timestamps, saved file paths and native serialization may differ. Report actual equality or differences and inspect relevant serialized metadata; do not assume byte-for-byte determinism.

Evidence lives under `evidence/stage2a/real-run/`. `comparison.json` records the actual two-run result once execution completes. Baseline-original dimensions are 4.95 × 0.249 × 2.0 m; the demonstration uses 4.95 × 0.249 × 2.2 m, 5 posts and 2 rails. Baseline is retained; the change is a D working-copy example, not historical evidence.

Fast negative checks: `python3 tests/cad-regeneration.test.py`. Full application/candidate invalidity tests belong to the research-CAD engine. No software installation or GUI success is inferred from these unit tests.

## Recorded real execution

Both `run1/manifest.json` and `run2/manifest.json` report PASS with original tracked bytes unchanged. Actual FreeCAD result: 4.95 × 0.249 × 2.2 m, 5 posts, 2 rails, 7 valid solids, zero pairwise intersection volume. Blender 4.3.2 save/reopen and GLB import both verify 7 meshes and 84 triangles; floating-point bounds agree within 1e-5 m.

`comparison.json`: FreeCAD audits, Blender audits, and STEP-derived mesh JSON are exactly equal across runs. GLB is byte-identical (SHA-256 `dbcee2d446610348049087ef511e487696853690e430f569b9b9b4d671ccfc72`). FCStd differs only in `Document.xml` LastModifiedDate plus ZIP timestamps; STEP is identical after timestamp normalization. Native blend bytes differ; the exact native fields responsible were not isolated, so only saved/reopened structural and geometry equality is claimed. Eight negative controls pass, including a revoked-approval boundary test that records FAIL without running CAD.

Reproduce comparison with:

```
python3 cad/stage2a/compare.py evidence/stage2a/real-run/run1 evidence/stage2a/real-run/run2 --output /new/comparison.json
```
