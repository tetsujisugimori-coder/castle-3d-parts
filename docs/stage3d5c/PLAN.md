# Stage 3-D-5C: proof obligations fixed before implementation

2026-11-16 JST. Issue #38; stacked on Draft PR #39, which is open and unmerged.
Base HEAD `6ed080ff38e50c7cb808d42ff0c36aeafc118ecd`, tree `3aad541d92c1b6c28f7bd09f5dab0dfa5d1ebf64`.
Main `18ffb29eeb3db067d47513f76e3a2ef44865c45a`; no other open PR at initial lookup.
Authenticated GitHub account: tetsujisugimori-coder. Dedicated clean clone and branch
`feat/stage3d5c-native-proof`; target PR base `feat/stage3d5b-brep-containment`.
Initial cloud free space 45 GiB; existing FreeCAD 1.0.0 / OCCT 7.8.1 imports verified.
No install. A GUI version probe failed without display; no GUI acceptance is claimed.
Git CLI has no authentication; repository policy permits authenticated Git data API
normal-parent submission, which will not be described as CLI push success.

## Fixed scope and proof order
1. Fixed FCStd SHA c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a,
   Bolt and Guide_Left only. Read an isolated copy. Record all topology, pcurves,
   parameter ranges, surfaces, orientations, placements and API gaps. Identity
   binds input bytes, descriptor and incidence, not an index alone.
2. Check represented analytical line/plane/pcurve consistency over entire
   parameter ranges, not sampled positions. Such checks concern extracted
   coefficients only. Native material-set and open-void inclusion are separate
   obligations. Winding normalization, closed/valid, volume and bbox are not proofs.
3. Eight distinct real-error domains: geometry, extraction, kernel representation,
   coordinate transform, unit, arithmetic/rounding, state generation, continuous
   displacement. No assigned epsilon, no tolerance-as-error, no null-to-zero.
4. Preserve existing isolated 0/70/140 mm Document observation program and source;
   record parent/global/XML/Shape paths. A synthetic path proof is conditional,
   not a certificate for native Document execution or all states.
5. Select exactly one existing D2 interval by its unchanged ordinal and endpoints.
   Only after all premises hold could a positive conservative lower bound support
   actual safety. This implementation must refuse self-declared PASS certificates.
   Nonpositive lower bound is UNKNOWN, never a fabricated collision FAIL.

## Admission and evidence contract
A normal fixed BRep may have observation-contract PASS and proof UNKNOWN together.
Missing/repeated/unreferenced incidence or inconsistent data is input FAIL;
unsupported APIs/real bounds are UNKNOWN; unmet motion premises mean NOT_TESTED.
All controls preserve full inputs, expected and actual outputs, scope and source.
Synthetic controls never count as CAD collision evidence. Legacy analytical 128
PASS, D4 real UNKNOWN128, D5B real NOT_TESTED128 remain separate versions.

Only new `cad/stage3d5c`, `docs/stage3d5c`, dedicated workflow and additive LOG are
planned. Existing CAD, Web, diagrams, ledgers, previous tests/expectations and
workflows stay byte-identical. A baseline manifest of every tracked base file
(except additive LOG) will be compared by path, size and SHA, not counts alone.
No repair/save of FCStd, delete/move, force push, main edit, merge, Draft release,
public deployment, or expansion to 128 native intervals.

Formal evidence includes source bytes before/after, hidden workflow, fixed input,
HEAD/tree/parents/submitted SHA, logs/exit codes, controls and result matrix.
Original ZIPs are kept unchanged and independently retrieved from approved private
storage, with size/SHA/full-byte/CRC/manifest checks. Receipt != durability guarantee.
Independent reviewer does not author implementation. Unverified axes remain open.
