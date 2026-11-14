# Stage 3-C independent review (in progress)

This is independent evidence review, not acceptance of the implementation author's conclusion. Final HEAD/CI reconciliation remains pending.

## Findings and counterexamples

- Collision validator originally accepted removal of a pair or interior bolt sample. Requested exact expected pair sets (moving, fixed, bolt), identity uniqueness and complete sampled travel coverage. Current implementation includes these checks; RED/GREEN execution pending generated manifest.
- Bolt translation originally left measured bounds audit stale and used angle-only coverage labels. Requested refresh of measured GLB bounds and state-specific angle/bolt coverage. Current code includes both; fresh browser verification pending.
- BoltSlide origin/rotation/scale/parent/child validation was incomplete. Requested exact hierarchy and transform checks.
- Native joinery drawing overlapped its title/footer. Original and corrected rendered PNGs retained. Corrected focused detail is readable and has a CAD-derived 20 mm dimension.

## Independent executed evidence

- State truth table: 158 cases, valid/invalid state and operation boundaries, rejection without mutation (`state-review.json`).
- Native geometry: 23 valid single solids, original 15 members preserved by symmetric-difference volume; 14 discrete door/bolt poses and 3,542 unordered BRep pair checks. No positive overlap above 0.0001 mm³. These include between-production-sample angles and fractional-millimetre bolt positions. Full continuous path remains UNKNOWN (`native-pairs.json`).
- Blender and GLB freshly loaded independently: 16 format/pose sets, transformed source mesh vertices compared against actual imported object vertices, 0.0001 m tolerance (`blender-review.json`).
- FCStd copied alone to isolated directory. Six embedded SVG templates extracted using fresh TransientDir and restore; bolt changed to 70 mm, saved, closed, reopened, and position/geometry verified (`portable-review.json`).

## Runtime limitations and preserved failures

Ordinary Python `openDocument` leaves TransientDir empty in this environment. Save fails for embedded TechDraw templates. Qt/FreeCADGui initialization alone did not resolve it. Standalone `/usr/bin/freecad` exited with SIGSEGV in Py_EncodeLocale before the test macro. Those are recorded failures, not PASS. Explicit newDocument + temporary TransientDir + FileName + restore provides a tested batch loading route without rewriting original template paths. Manual GUI operation remains NOT_TESTED.

## Boundaries

Geometric contact and software interlock do not prove physical locking force, fastening, torque transmission, material strength, wear, or historical authenticity. Native direct property edits can create invalid states; persisted-state validation is required. Discrete checks do not prove continuous-path clearance. Physical iPhone Safari and touch are NOT_TESTED. Candidate Web only; no deployment or merge.

Additional native dimension recheck: three parameter sets (length/width/height 900/20/40, 880/18/35, 900/22/45 mm) independently read back as matching TechDraw raw values after page activation and Qt event processing. Guide/receiver bores follow width, height and clearance. Full collision clearance of these modified parameter sets is NOT_TESTED. Initial API-name error and zero values before activating pages remain in diagnostic logs; they are not counted as passing runs (`dimension-review.json`).

Baseline preservation independently recomputed from `git ls-tree` object IDs (not merely the submitted baseline JSON): 1,133 prior files, exactly two deliberate changes (`site/stage3b/app.mjs`, `scripts/build-stage3b-site.mjs`) for shared viewer integration. All other baseline bytes match (`preservation.json`).

## Completed RED/GREEN checks

The saved pre-fix collision validator accepted a deleted pair and a deleted interior bolt sample. The current validator rejects both. Positive overlap incorrectly labeled CLEAR is rejected before and after. The saved pre-fix portable checker accepted an empty source-hash dictionary and duplicate contact-chain pair; current checker rejects both. These are executed counterexamples, not code-review inference (`contract-counterexample.json`, `portable-counterexample.json`). Final native source hash matches independent geometry and portability evidence. Final regenerated blend/GLB were retested; all 16 independent format/pose sets pass with matching artifact hashes (`provenance-review.json`).

Fresh independent Chromium/WebKit 390px reduced-motion operations covered partial bolt translation with actual mesh bounds, unsampled-state label, prohibited opening/locking, unlock/open recovery, actual keyboard input and three part selections. Intermediate 0.0375m bolt value was deliberately injected by changing the test slider step, distinct from ordinary 1mm UI input. First launch lacked configured existing browser path; rerun with PLAYWRIGHT_BROWSERS_PATH used installed binaries. Original screenshot showed dropdown overflow; final CSS fix is being rechecked with explicit scrollWidth assertion, retaining before-fix evidence.

Final CSS rerun: both independent browsers passed the same actions and `document.documentElement.scrollWidth <= innerWidth + 1` at390px. Before-fix screenshots retained. Fresh final screenshots and trace archives are evidence, not physical iPhone/Safari testing.

## Local acceptance conclusion before submission

Main runner original `results.json` equals submitted `web-final-results.json`. Exactly 16 distinct browser/width/motion combinations and 34 distinct fault/engine combinations report PASS. Each normal row contains six performed-check groups and no page error. All 16 PNG and 16 trace ZIP files exist and have been hashed; ZIP integrity was checked. Every trace context independently confirms the stated Chromium/WebKit engine, initial375/390/765/1280 width, normal/reduced motion and Linux platform, with actual action calls and resizing. Screenshots capture the final resized width (initial width +10px), not a different unexplained baseline. Representative desktop WebKit and mobile Chromium screenshots were visually inspected. Manifest, GLB and collision hashes match the independently reviewed artifacts.

Local conclusion: limited prototype CAD/state/Web technical scope PASS; overall PARTIAL because continuous-path clearance, physical fastening/load/strength, historical authenticity and physical Safari/touch/manual GUI remain unverified. No unresolved P1/P2 found in the reviewed scope after fixes. Final submitted HEAD/tree, CI and original CI artifacts must still be reconciled before issuing the final merge recommendation. This is not merge/publication approval.
