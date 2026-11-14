# Stage 3-D-1: continuous interval evidence (trial D)

Baseline main 7f32781089b12d56d78392c985bfddb6bf5aca02, tree 7e0efb77520df4fbbba52b73e9db49fb668251a7. Issue #30. No change to CAD sources, 23 parts, placements, interlock, Web, history, or Yamanaka.

## Methods and acceptance
1. Adaptive midpoint subdivision: bounded to depth 4 for native data (16 terminal intervals per pair), and depth 6 for exact synthetic tests. Samples alone NEVER imply continuous PASS.
2. Swept solid Boolean: not selected; robust sweep construction and its error enclosure are not yet validated for the general BRep and compound support geometry. NOT_TESTED.
3. Distance bound: rigid translation is 1-Lipschitz per mm. Rotation displacement is at most R*abs(delta radians); R may be conservatively enclosed by the L1 XY radius. If a distance oracle supplies a *validated* absolute error epsilon, d(mid)-epsilon-L*(hi-lo)/2 > clearance proves strict separation throughout the closed interval. Equality and contact do not prove separation.

The portable classifier uses exact rational arithmetic for supplied numbers. This does not certify the oracle or the caller's speed bound. Native OpenCASCADE distToShape/common has no independently validated absolute error bound in this work. Therefore native observations set certified=false, error=null, and ALL continuous native intervals remain UNKNOWN even when numerical clearance is large. No epsilon is invented to obtain PASS. 1e-5 mm distance and 1e-4 mm3 volume are inherited *observation/crosscheck* thresholds only, never proof error bounds or physical accuracy claims.

Exact synthetic normal geometry and collision fixtures provide algebraic distances. The same narrow midpoint obstruction is missed by endpoint-only sampling and rejected by the new classifier. Contact is separate from verdict. Failures of numeric input validation must not be counted as semantic collision detection.

## Bounded native scope
Door 0..90 degrees, bolt 0; pairs Door/Doorstop, Spindle_Upper/Bearing_Upper, Door/Post_Right, Door/Joint_Right, Door/Stop_Open. Bolt 0..140 mm at angle 0: Bolt/Guide_Left, Bolt/Guide_Right, Bolt/Receiver. Fence and all other pairs NOT_TESTED in the continuous classifier; the existing 32650 discrete pair record is retained. Reuse source FCStd read-only. Native results include identity, bounds, sampled observation, coverage, contact and numerical volume. Three old discrete poses per selected pair are independently remeasured; full 91/141 baseline collections are inventoried, not called a new full rerun.

## Protection, budget and independent review
Dedicated scratch only. Initial free capacity 36 GiB, 3.88M inodes; local new native output expected <5 MiB, CI raw archive expected <1 GiB. No deletion of old Temp/evidence. Existing Stage3C workflow remains intact and supplies regression/native/history/browser evidence independently of the new classifier. Runtime versions, source bytes, HEAD/tree, exit, logs and manifest captured. Original artifacts retained unmodified; Library refetch audit is separate from unknown ACL/retention. No merge, Draft removal, issue close, publication, regeneration of original CAD, strength/history or all-path safety claim.
