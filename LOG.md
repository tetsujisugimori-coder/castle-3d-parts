
## Stage 3-D-1 continuous interval diagnostics (2026-11-14)

Issue #30, baseline main 7f327810 / tree 7e0efb7. Read-only reference to the Stage3C CAD and 32650 discrete pair record. Added exact-rational interval classifier, bounded native observations and independent-evidence workflow. No source CAD or product changes. Native OCC numerical error is not certified: continuous native intervals remain UNKNOWN. Exact synthetic controls are explicitly separate. CLI dry-run push failed for unavailable credentials; use approved GitHub connector non-force normal-parent submission, not claim CLI push success. Final CI and review outcomes belong in PR/Issue results; this entry does not predeclare acceptance.

Initial CI run 43649532425 stopped before tests because the inherited stage3c recorder used unscoped Git in a container-owned checkout. Raw failure retained (artifact 14135612394). Added a dedicated recorder with command-only repository-specific trust, no persistent/global config, and no unrelated Node dependency. Existing recorder and product remain unchanged.

Independent review P2: externally supplied negative recursion depth bypassed max_depth. Preserved reviewer finite counterexamples; strictly require non-boolean integer 0 <= depth <= max_depth <= 12. Same inputs now reject with ValueError, not recursion failure. Added regression without weakening geometry expectations.

## 2026-11-15 Stage 3-D-3 (Issue #34)
- Baseline merged D2 main028f12f2/treee02508fc. Separate branch, only representative Bolt/Guide_Left, door0/travel0..140mm.
- Added actual FreeCAD topology/placement/BRep extraction and isolated native changes; original hashes unchanged. Observation agreement does not establish occupancy inclusion or inward void bounds, so realCAD128UNKNOWN remains.
- Portable19, D2 20, D1 10 and Node497 local tests PASS; actual FreeCAD history/reopen regression PASS. Final CI, independent review and archive audit tracked separately in docs/stage3d3/RESULTS.md; no overall safety claim.

Independent root reviewer found an empty-part observation falsely labelled observed_contract PASS (actualCAD still UNKNOWN). Same input saved before correction and after REJECTED/observed_contract FAIL. Empty reference and missing required shape fields now reject. Earlier16 tests are preserved; corrected suite19 tests. Independent final confirmation remains pending.
