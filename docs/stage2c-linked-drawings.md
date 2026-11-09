# Stage 2-C: native dimensions and linked design viewer

## Scope and fixed baseline

Issue #20. Stage2-B PR #19 was merged before this branch: main `d1c367ca4b143cacc45ba8848b026701abf03b9c`, tree `7e631c39829614199fe08cc6aea1f9740c2dce52`. All 839 baseline files are preserved byte-for-byte; no old source, CAD, research, evidence or workflows are rewritten. Research remains 27 fixed records, held/reference_only; every new dimension is prototype **D**, not a historical measurement. Two units are placed independently, not a historically certified connection.

## Actual CAD implementation

FreeCAD 1.0.0 with Qt offscreen and FreeCADGui/TechDraw is executed, rather than synthesizing an FCStd or claiming a headless zero measurement succeeded. Its page event processing is necessary for native dimensions in this installed build. This is programmatic use of actual FreeCAD GUI modules, not manual desktop GUI acceptance or GPU rendering.

Each assembly has three native pages, FrontPage/TopPage/SidePage, 1:40 projection, and **19 native DrawViewDimension objects** using MeasureType=True. Measurements cover two units' post height, post centre interval, X/Y post section, unit width, each of four rails' length and centre elevation, and assembly width. Native dimensions reference semantic Part::Line witnesses whose coordinate expressions bind named Part::Box dimensions/placements. The witness is not a fixed display label. Independent BRep bounds are compared against witness length and native getRawValue at each recompute.

Semantic dimension IDs and object names are persistent. Only the single-edge witness uses Edge1; projected topology indices are not persistent identities. Source expressions, dimension references, view source object set, view direction/scale/page membership and measured values are validated. Unknown/missing references, wrong witness, arbitrary fixed labels and invalid edges are rejected. This is a finite box-part fixture, not a universal solution to FreeCAD topological naming for arbitrary future shapes.

All native measurements are checked after save/close/reopen. A live sequential edit increases U01 height by 200mm, then U02 spacing by 100mm, without rebuilding dimensions or rewriting labels; both are validated and restored. B0/B1/B2 generation additionally reproduces the Stage2-B geometries: 2.2→2.4m height; B2 U02 spacing1.3m. Native SVG exports retain actual dimension objects' generated labels. Three native SVG pages are saved alongside the interactive CAD projection SVG. Native SVGs include the revision, mm, scale, prototype D.

`pre-enhancement-*` audits describe the intermediate Stage2-B headless build only. Final `cad-audit.json`, `native-audit.json` and `drawing-measurements.json` describe the enhanced source. Old audits are not silently turned into evidence of new work.

## Conversion and preservation

New destination only:

```
/usr/bin/python3 cad/stage2c/run.py /tmp/new-stage2c-output
```

The script validates the old research/spec, uses the unchanged Stage2-B parametric generator into a new directory, enhances native pages/dimensions, converts reopened STEP mesh through actual Blender4.3.2 to blend/GLB, rereads both and checks 14 components/bounds. Units: FreeCAD/STEP mm, transfer mesh and GLB metres; CAD Z-up maps to glTF Y-up. Old B0/B1/B2 files stay intact. A partially failed new directory is kept for diagnosis and cannot be blindly overwritten. Use a different new destination after fixing a failure.

`generation-manifest.json` records baseline commit, exact source script hashes, spec hash and all deliverable hashes. `source_commit` is explicitly the baseline, not a claim that a future commit ID is self-embedded. The submitted PR HEAD pins final sources and manifest. FCStd/STEP/blend can contain nondeterministic serialization; compare geometry and semantic linkage separately from byte hashes.

## Linked Web viewer

New independent entry: `site/stage2c/index.html`, built into `/stage2c/` by `node scripts/build-stage2c-site.mjs`. The previous site's build/landing page are not changed because baseline preservation protects them. No Pages deployment is performed by this work. Launch a static server at built `dist/` for review; do not open index via file://.

The interface shows 3D and CAD-derived SVG side-by-side on desktop, tabs on narrow screens, native projected front/top/side views, part and revision selection, measurements in metres, version differences and fixed research record links. SVG zoom/pan and 3D camera controls remain distinct. Selecting either representation selects the exact unique instance, including duplicate kinds in separate units. The list supports keyboard access and selection clear. CAD editing/live FreeCAD execution in a browser is out of scope.

Before enabling selection, the consumer verifies requested revision, D/reference_only, exact 14 parts, GLB node IDs/bounds, geometry/extras, SVG revision/semantic IDs, dimension metadata, file SHA256, and safe paths. Failed or stale loads clear state; generation tokens prevent an older response from restoring old selection. SVG active content/external resources/duplicate IDs are rejected through a finite static allowlist. Native export files are separate view-only CAD deliverables; interactive SVG is a semantic wrapper around actual TechDraw per-part projections and measured native values.

## Verification commands

```
node --test
python3 cad/stage2c/check.py
python3 tests/stage2c-cad.test.py
node scripts/stage2c-browser.mjs
```

Portable CI checks archive/reference values, hashes and stored audits. It does **not** mean FreeCAD or Blender ran inside CI. Actual execution logs and originals are independently reviewed. Browser matrix: Chromium/WebKit ×375/390/765/1280 ×normal/reduced, with wrong-file version, missing/duplicate IDs, hostile SVG, loading races/failures and interaction checks. Desktop mouse and emulated touch are not physical iPhone input.

## Boundaries

Historical certainty, formal reconstruction approval, manual CAD UI usage, physical iPhone Safari/touch, structural/joint strength and actual on-site placement remain NOT_TESTED/out of scope. The model is the fixed 10-post/4-rail parallel box fixture. New kind/count/rotation requires explicit generator and verifier extension. Native linked dimensions are measured and accepted only within this verified scope. No merger or production deployment is authorized here.

## Local validation record before submission

- Node: 409/409, no skips (367 existing +42 new contract cases).
- Portable CAD suite: five test methods with injected type/value/reference/expression failures;839 preserved baseline files;19 dimensions and14 parts per revision.
- Independent reviewer: actual FCStd/STEP reopening, raw heights/spacing, and binary GLB bounds, all three versions. Same host but separate process, separate assertions; no implementation edits.
- Second actual full generation: all native numeric audits, geometry and mesh-transfer records agree; GLB and interactive SVG are byte-identical. FCStd/STEP/blend/native SVG bytes differ. STEP timestamps and SVG XML attribute ordering are observed differences, not shape changes; complete byte determinism is not claimed.
- Chromium local:8 normal conditions ×15 checks,10 fault rows,8 PNG, exit0. Local WebKit NOT_TESTED due absent libraries, retained separately. CI must supply final16 conditions and20 fault rows.
- Independent finding fixes: native view source completeness; dimension-to-part membership; exact revision-diff set. Same counterexample before/after evidence retained.
- Final remote HEAD, workflows, artifact digests and independent final review will be recorded on the Draft PR. These local results do not pre-claim CI acceptance.

The current production Pages workflow still builds the previous entry. This PR supplies the tested extended builder and static subpath output; changing the production publishing command and adding a navigation entry are later release steps requiring approval. Merging files alone would not publish the new viewer. No hidden deployment is performed.

### Public/private evidence boundary

Original local stdout/stderr logs are retained unchanged in a private archive rather than committed publicly. Public `evidence/stage2c/local-run-summary.json` records original filenames, SHA256/size/line counts and structured outcomes; environment-specific absolute paths and verbose tool warnings are omitted from the public log body. Numeric audits, executable verifiers, originals, images and original failure inputs remain in the public PR. The independent reviewer inspected the private raw logs before this split. This limits public readers' access to full local execution transcripts; public CI source/logs/artifacts provide a separate replay path, not proof that CAD ran in CI. No failure has been turned into success or evidence deleted. Private-log publication would require separate approval.
