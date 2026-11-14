# Stage3C verification contract

## Fixed inputs
- main34956e1/treeff66be2a; Stage3B immutable CAD and original evidence.
- Coordinates: metres, Z up in CAD/transfer; glTF Y up = (x,z,-y).
- Original rotation pivot and 0/45/90 degree presets retained.
- New geometry and all dimensions trial D, not archaeological measurements.

## Acceptance, not counts alone
1. Source FCStd and STEP independently reloaded, part count/ID, bounds, volume, pivot and movement compared.
2. Parametric variation changes actual shape and native TechDraw linked dimension. Unsupported configurations must fail or remain unverified.
3. Bolt complete displacement samples, closed door stop, moving/fixed door sweep 0..90 degrees and ground/fence relation. Check raw pair set completeness and numerical non-finites. Positive overlap above stated tolerance cannot be CLEAR. Intended zero-volume contact distinguished from free gap.
4. Wrong axis, missing part, wrong units/ID/hash, wrong collision classification, omitted pair/sample, stale or contradictory state rejected. Keep failing counterexamples.
5. State transitions are absolute and reject opening during partial/full bolt insertion and insertion away from exact closed angle. Reset/reverse/repeated inputs, pause, hidden/offscreen cancellation and reduced motion checked.
6. New 16 browser configurations, old 3B/3A/2D regressions; real fresh browser inputs and screenshots/trace. Emulation not physical Safari.
7. Final remote HEAD/tree and CI artifact identity are recorded. Local code-under-development evidence is not relabelled as final CI.
8. Separate reviewer recalculates raw geometry and counterexamples, views screenshots and verifies declared limitations.

## Unproven unless explicit additional evidence
Continuous entire path, material deformation, strength, physical load transfer, retention fasteners, mechanical lock resistance, archaeology, hand-operated native GUI, physical iPhone and touch.
