# Independent Stage 3-D-1 review

Reviewed submitted HEAD d40ed97d94be47555b01a3d9dc4b7cd7e7dbb898 / tree 18e3feb81a5239a084c989aef2a3dfb299a4e41c. Read AGENTS, PLAN, classifier, controls, native runner, and actual CI ZIP independently. Reviewer did not implement product code.

## Verdict before correction
PARTIAL / one blocking P2 in the reusable bounded-recursion API. No continuous native safety PASS is established. Preserve Draft, research PARTIAL.

### R31-D1-P2-01: caller-supplied recursion depth escapes bound
`classify(..., max_depth=0, depth=-1)` returns two leaves rather than the bound of one; `depth=-10000` raises RecursionError before a classified result. `depth=True` is also accepted. Counterexample: zero distance, uncertified oracle, zero speed on [0,1]. Evidence `reviewer-depth-input.json`. Validate recursion state as non-boolean integer in range, or remove it from public API and recurse privately. Also reject boolean max_depth rather than accepting Python bool as int. This is resource/fail-closed correctness, not proof of a false continuous-separation PASS. Keep failure evidence and recheck same inputs.

## Independent mathematical checks
For a distance function with proven Lipschitz constant L, proven oracle error epsilon, and interval [a,b], d(mid)-epsilon-L*(b-a)/2 > clearance implies separation everywhere by triangle inequality. Equality correctly remains UNKNOWN. Exact rational arithmetic avoids extra arithmetic-rounding loss but does not validate a caller's oracle certificate or speed bound.
123 independently generated point/obstacle geometries (41 centers, 3 radii) were checked against exact interval-to-obstacle distance. Every PASS leaf had strictly positive independently calculated minimum; every FAIL leaf had a strict interior witness. `reviewer-independent.json`. Original nine unit tests and five fixed controls rerun successfully (`reviewer-controls.json`). Endpoint-only old comparator is a synthetic demonstrator, not evidence that the old CAD implementation accepted this exact geometry.

## Independent native execution
Actual FreeCAD execution (not mock), `reviewer-native/native.json` and `reviewer-native.log`: eight representative pairs, 128 UNKNOWN / zero PASS / zero FAIL continuous leaves, 23 IDs equal spec, 24 original discrete comparisons, max distance discrepancy 5.551115123125783e-17 mm, volume discrepancy zero, interlocks rejected, source FCStd hash unchanged. Native numerical error remains uncertified; 128 UNKNOWN is correct and must not become a safety PASS. Full 91-angle/141-position / 32,650-pair collections were inventoried, NOT independently remeasured in this reviewer run. Sweep, fence and other pair coverage remain NOT_TESTED. Rotation speed is calculated with floating point, so even its outward rounding is not independently certified; current uncertified-oracle path cannot use it to award PASS.

## CI original and Library readback
`castle-stage3d1-d40ed97-ci.zip`: 18,295 bytes, SHA-256 468051e246b7f84717c02d55507de7b5e1145970ea598aa907d9058b04fc2296, CRC all entries valid; all 21 internal manifest size/hash pairs valid. Saved runner source bytes equal submitted Git files. Actual merge commit 759a84a5907117f05bfdbbcd8572097d4defd534 has submitted tree 18e3feb81a5239a084c989aef2a3dfb299a4e41c. The initial failure ZIP remains distinct.
Both original ZIPs were compared with separately Library-materialized files in refetched-first: full byte equality, size, SHA-256, CRC and internal manifest PASS (initial failure 9 entries / corrected 21 entries). `reviewer-library-audit-first.json`. Access scope and retention UNKNOWN, not inferred from byte identity. This is not final-HEAD CI acceptance after correction; subsequent artifacts require fresh audit.

## R31-D1-P2-01 correction recheck
Local correction inspected: both recursion depth arguments require exact int (excluding bool), and 0 <= depth <= max_depth <= 12. Same three counterexample inputs now raise ValueError; boolean max_depth and depth above maximum also rejected. `reviewer-depth-fixed-independent.json` preserves five checks; ten unit tests PASS. Finding CLOSED at local corrected source, subject to final submitted source/tree and artifact verification. No new blocking P1/P2 identified in this review scope.
