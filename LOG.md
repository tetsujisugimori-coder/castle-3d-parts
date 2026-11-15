
## Stage 3-D-1 continuous interval diagnostics (2026-11-14)

Issue #30, baseline main 7f327810 / tree 7e0efb7. Read-only reference to the Stage3C CAD and 32650 discrete pair record. Added exact-rational interval classifier, bounded native observations and independent-evidence workflow. No source CAD or product changes. Native OCC numerical error is not certified: continuous native intervals remain UNKNOWN. Exact synthetic controls are explicitly separate. CLI dry-run push failed for unavailable credentials; use approved GitHub connector non-force normal-parent submission, not claim CLI push success. Final CI and review outcomes belong in PR/Issue results; this entry does not predeclare acceptance.

Initial CI run 43649532425 stopped before tests because the inherited stage3c recorder used unscoped Git in a container-owned checkout. Raw failure retained (artifact 14135612394). Added a dedicated recorder with command-only repository-specific trust, no persistent/global config, and no unrelated Node dependency. Existing recorder and product remain unchanged.

Independent review P2: externally supplied negative recursion depth bypassed max_depth. Preserved reviewer finite counterexamples; strictly require non-boolean integer 0 <= depth <= max_depth <= 12. Same inputs now reject with ValueError, not recursion failure. Added regression without weakening geometry expectations.

## 2026-11-15 Stage 3-D-3 (Issue #34)
- Baseline merged D2 main028f12f2/treee02508fc. Separate branch, only representative Bolt/Guide_Left, door0/travel0..140mm.
- Added actual FreeCAD topology/placement/BRep extraction and isolated native changes; original hashes unchanged. Observation agreement does not establish occupancy inclusion or inward void bounds, so realCAD128UNKNOWN remains.
- Portable19, D2 20, D1 10 and Node497 local tests PASS; actual FreeCAD history/reopen regression PASS. Final CI, independent review and archive audit tracked separately in docs/stage3d3/RESULTS.md; no overall safety claim.

Independent root reviewer found an empty-part observation falsely labelled observed_contract PASS (actualCAD still UNKNOWN). Same input saved before correction and after REJECTED/observed_contract FAIL. Empty reference and missing required shape fields now reject. Earlier16 tests are preserved; corrected suite19 tests. Independent final confirmation remains pending.

## Stage 3-D-4 boundary study (2026-11-15)
Issue #36. Start main4f9f973/tree2d57c701, PR31/33/35 merged. Added limited exact rational orthogonal boundary verifier, native trim/topology extraction, fail-closed bridge and explicit guarantee matrix. No CAD/product/ledger changes. Rational representation containment is separate from actual BRep: native128UNKNOWN, analytical128PASS. Initial native test-construction exits1 preserved; independent review/formalCI/archive gates pending in initial submission, not predeclared PASS. See docs/stage3d4/PLAN.md and RESULTS.md.
Independent D4 review found source/input/topology/count-only ZIP false acceptance. Same original counterexamples retained; audit now binds the complete source set to checkout bytes and recomputes native assessment/full analytical report. Public CI of first candidate e364f39 is separate from corrected candidate; no prior success reused.
Independent recheck additionally found unmodified-part BRep hash drift in hole-shrink evidence; old missing raw counterpart cannot establish its cause. Each fault now uses independently imported fixed BRep and preserves both parts per row with unchanged-side equality checks. Same hole-shrink condition passed without weakening the contract; old observations retained.

Stage3D4 post-submission packaging check: root-format normal ZIP false rejection fixed with exact or slash-delimited name matching; same control exit1→0. Existing deficient-evidence rejection unchanged, native128UNKNOWN. Final CI pending on subsequent submission.


## Stage 3-D-5C limited native proof obligations (2026-11-16 JST)
Issue #38; stacked on PR #39 HEAD6ed080ff. New isolated full-topology/pcurve capture, exact represented coefficient verifier, native-observation fault controls, eight real-error obligations and fixed first D2 interval gate. All original tracked bytes retained except this appended log. Actual material/void/errors/all-state correspondence UNKNOWN and representative/128 realCAD NOT_TESTED; no safety claim. Independent review corrections and local/formal evidence scopes are in docs/stage3d5c/RESULTS.md. Final CI and archive audit remain separate gates.
