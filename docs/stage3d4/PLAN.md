# Stage 3-D-4 fixed boundary study
Issue #36. Baseline main `4f9f973e5384b207a6dac0fd22d8e3e28a833cf3`, tree `2d57c701c164e0b67b62d1ccbe434ff5935d2664`; PR31/33/35 verified merged. Old Draft/PENDING text is historical, not current status.

Scope: GATE_Bolt / GATE_BoltGuide_Left only, door0°, translation0..140mm. Native world coordinates mm; project motion API metres (exact nominal scale1000). No original CAD, dimensions, mechanism, existing research ledger, Web, or Yamanaka files are changed.

## Bounded method fixed before execution
1. Read original through actual FreeCAD, export BRep and record every face surface, trim wire, edge curve/orientation and vertex; shell/solid orientation and placement. Observe original and isolated in-memory enlarged bolt, smaller bore, shift, reversed orientation, open shell, curved replacement and extra solid. These observations do not prove topology/geometry semantics.
2. Exact *synthetic* rational rectilinear boundaries: rectangular oriented faces, finite grid, x-ray material cells, independent all-axis face balance. Reject unsupported, missing, flipped, duplicate/extra or degenerate inputs. Derive outward occupied cell cover and verify inward void disjointness with exact arithmetic and directed grid rounding. This guarantees the defined rational model, not serialized CAD.
3. Native bridge checks pinned source hash, explicit scope/unit and complete evidence. Native trims/curves floating-point to rational conversion has no established enclosure theorem. Therefore all dependent CAD containment, inward void, placement/error and continuous-motion guarantees stay UNKNOWN. External PASS and zero-error fields cannot upgrade them. Whole-stock enclosure fills the hole and cannot prove separation; overlap of outer bounds is NOT actual collision FAIL.
4. Recompute D2 analytical128 results separately. The native128 remain UNKNOWN unless a certified BRep-to-boundary correspondence is established; this small PR does not implement a general CAD prover or alter authorship contracts.

## Controls and budget
Exact models: separated/contact/penetration; inward hole reduction, bolt expansion and shift; missing faces/wires, reversal, broken closure, unsupported faces, extra occupancy, wrong unit/hash, missing/empty/forged proof, understated error and wrong rounding. Native mutations are copies only. Existing old results are preserved, new controls are not alleged historical failures.
Local evidence budget250MiB; necessary CI originals plus readbacks1.5GiB. Start available12GiB, inodes3.27million; dedicated temp and exclusive run outputs. No deletion/movement of others' files. Capture actual source before commands (including hidden workflow), exit codes and all failure evidence. A planned fault plus unrelated failure is not success. Full CI and archive audit are separate.

D1/D2/D3 and Stage3C relevant regressions, actual FreeCAD availability, independent reviewer of premise/derivation/raw evidence, then CI artifact independent readback. No merge/Draft removal/publication; physical safety/history/strength/all-paths/manualGUI/Safari are NOT_TESTED.
