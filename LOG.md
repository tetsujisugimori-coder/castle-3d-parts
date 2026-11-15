
## Stage 3-D-1 continuous interval diagnostics (2026-11-14)

Issue #30, baseline main 7f327810 / tree 7e0efb7. Read-only reference to the Stage3C CAD and 32650 discrete pair record. Added exact-rational interval classifier, bounded native observations and independent-evidence workflow. No source CAD or product changes. Native OCC numerical error is not certified: continuous native intervals remain UNKNOWN. Exact synthetic controls are explicitly separate. CLI dry-run push failed for unavailable credentials; use approved GitHub connector non-force normal-parent submission, not claim CLI push success. Final CI and review outcomes belong in PR/Issue results; this entry does not predeclare acceptance.

Initial CI run 43649532425 stopped before tests because the inherited stage3c recorder used unscoped Git in a container-owned checkout. Raw failure retained (artifact 14135612394). Added a dedicated recorder with command-only repository-specific trust, no persistent/global config, and no unrelated Node dependency. Existing recorder and product remain unchanged.

Independent review P2: externally supplied negative recursion depth bypassed max_depth. Preserved reviewer finite counterexamples; strictly require non-boolean integer 0 <= depth <= max_depth <= 12. Same inputs now reject with ValueError, not recursion failure. Added regression without weakening geometry expectations.
