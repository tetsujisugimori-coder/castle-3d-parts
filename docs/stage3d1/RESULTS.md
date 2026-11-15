# Stage 3-D-1 scope and evidence interpretation

## Technical result
The new verifier separates certified separation, proven violations and insufficient evidence. It does not certify the current gate's complete continuous motion. Research/physical result remains PARTIAL. All dimensions remain prototype D; no strength, durability or historical claim.

Local and initial successful CI data: 8 representative pairs, 128 terminal continuous intervals: PASS 0, FAIL 0, UNKNOWN 128. Numerical intersection volume at retained interval midpoints is 0 mm³, but lack of a validated OCC absolute-error enclosure prevents continuous PASS. The original 91 angles, 141 bolt positions and 32,650 pair observations are unchanged. Twenty-four selected poses (three per pair) were independently remeasured, not a replacement for the full prior inventory. All 23 CAD IDs match, the original FCStd hash is unchanged, and three invalid interlock transitions reject. A fresh final-HEAD formal workflow remains required; its run IDs and artifact identities are recorded in the PR report, not inferred from these earlier results.

| motion / pair | smallest **terminal midpoint sample** distance, mm | continuous result |
|---|---:|---|
| door / Door–Doorstop | 54.6613892007 | UNKNOWN |
| door / Spindle_Upper–Bearing_Upper | 0.4999999999998 | UNKNOWN |
| door / Door–Post_Right | 7.3659526633 | UNKNOWN |
| door / Door–Joint_Right | 103.9226493398 | UNKNOWN |
| door / Door–Stop_Open | 14.6660978275 | UNKNOWN |
| bolt / Bolt–BoltGuide_Left | 1 | UNKNOWN |
| bolt / Bolt–BoltGuide_Right | 1 | UNKNOWN |
| bolt / Bolt–BoltReceiver | 1 | UNKNOWN |

These are NOT continuous minima. Terminal midpoints exclude exact endpoints; three baseline crosschecks include endpoints separately. Contact at an endpoint must not be inferred from the table. Raw terminal samples and crosscheck deltas are in native.json. Geometry bounds are explicitly for the last sampled pose, not a swept envelope. Rotation is about the existing Z pivot (-540,0,100) mm, range 0..90 degrees with bolt=0. Bolt translates along +X, 0..140 mm with door=0. Native CAD/spec/build remain the authoritative dimensions; bolt nominal size is 900×20×40 mm and guide gap 1 mm. No geometry is regenerated.

## Complexity and proof boundary
Depth d uses at most 2^(d+1)-1 distance observations and 2^d terminal intervals per pair. Native depth4 means 31 interval observations plus 3 existing-pose checks per pair. Interval arithmetic is exact for supplied rational values; that does not establish accuracy of an external geometry oracle or a supplied speed bound. A valid absolute distance error and conservative displacement bound are preconditions for PASS. Contact remains separate, and strict clearance equality yields UNKNOWN. Swept BRep construction/error validation and complete fence/all-pair analysis remain NOT_TESTED. Adaptive extra sampling alone never certifies an interval.

## Contrasts, review and regressions
Three exact synthetic point/obstacle fixtures at 1/2, 1/4 and 3/4 are false-accepted by endpoint-only sampling and rejected by the new verifier. A positive-gap normal fixture passes; touching remains UNKNOWN without a penetration claim. This is separate from real FreeCAD solids.

Independent review found a bounded-recursion input defect: negative public depth bypassed max_depth, including a finite -1 counterexample and -10000 RecursionError. Original reviewer evidence is retained. Non-boolean integer validation now enforces 0<=depth<=max_depth<=12; the same inputs reject as invalid contracts, and normal geometry expectations remain unchanged. Ten unit tests include the regression. Reviewer's independent rational-geometry and raw-artifact audit are separately preserved and reported, including their limitations.

Existing 497 Node tests, CAD portable checks/faults, history19 and parity1 passed locally before submission; their execution records identify the dirty precommit state and are not labeled final-HEAD CI. Existing Stage3C/3B/3A/2D, native history, STEP/Blender/GLB and browser formal workflows are unchanged. Final CI must be read separately. No manual FreeCAD/Blender GUI or real Safari acceptance, no physical tests, no original deletion and no Issue28 blocked transfer override.

## Preservation and decisions
First CI (43649532425, artifact14135612394) failed before tests because the inherited recorder used unscoped Git in a container-owned checkout; it is preserved. The dedicated recorder uses command-only trust for this checkout and no permanent/global Git change. The next CI (43649924009) passed on d40ed97 before the review fix; final-HEAD evidence supersedes it only for current acceptance, never deletes it. Raw ZIPs are saved unchanged with official digest, size, SHA, CRC and internal manifest checks. Library re-download integrity is independent of access-list/retention UNKNOWN. No merge or release is authorized here. A limited verifier merge recommendation must not be read as continuous native-gate safety acceptance.
