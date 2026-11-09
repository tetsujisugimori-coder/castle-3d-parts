# Independent CAD and Web review

Separate reviewer; no implementation edits. Actual FreeCAD1.0.0 Qt-offscreen reopens and STEP imports used. Same execution machine, separate process and independent assertions. Manual GUI operation and iPhone Safari NOT_TESTED.

## Public evidence

`assertion-results.json` records meaningful before/after verdicts. `reload-final.json` contains final native and STEP geometry checks; `glb-final.json` contains binary glTF checks. Public scripts use repository-relative paths. SHA256 manifest covers all public files.

- Exact front-view source-removal counterexample changed from incorrect acceptance to rejection.
- All three final FCStd and STEP revisions contain14 parts/solids and matching assembly extents. Native heights and spacing match independent expected values.
- Binary glTF bounds converted from Y-up to CAD Z-up match every part within1e-5m.
- Pre-enhancement audits are explicitly preserved; final dimensions19, scale.025; templates identify each revision.
- Final B2 front/side drawings visually checked. Side superposes both units; it is not exploded.
- Web contract tests42 passed and extended static build passed independently.

## Private raw originals

Unstructured execution logs and original harness copies remain in the private original archive. `private-original-hashes.json` identifies them by filename/hash; public GitHub contains no raw log bodies. These raw originals were not deleted or replaced. Initial harness limitations occurred before corrected final checks and were not treated as successful verification.

Native checks require opening TechDraw pages after recomputation. Verify explicit result assertions, not process exit alone.

Final remote HEAD and CI artifact review pending separately.
