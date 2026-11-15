# Stage 3-D-5B transplant submission record

This document records the implementation scope before the submitted HEAD is
frozen. Final CI/native/archive results and exact submitted HEAD/tree are
reported in the Draft PR and Issue #38 after their actual execution; pending
items below are not historical successes. No merge, publication or Draft
conversion is requested.

## A. Overall verdict
PARTIAL, limited merge HOLD. Portable contracts and exact arithmetic are
separate from real BRep correspondence, Solid inclusion, finite-error proof and
continuous-motion safety. History/physical strength/durability are outside scope.

## B. Baseline and branch
Authenticated CLI account: tetsujisugimori-coder. Verified main is
18ffb29eeb3db067d47513f76e3a2ef44865c45a, tree
423d33c5a8283445832ea3c5495dc94090796090. Work is on
feat/stage3d5b-brep-containment in an isolated clone; the original detached tree
is untouched. Original source baseline was 445f37182f07dae98441bc2a57f103e140c628a9,
tree 9005551d740e5fc70451e8986df5056480d80d06, 24 commits behind current main.
The main branch API reports unprotected; protection endpoint reports 404 and
rulesets list is empty at retrieval. No required checks were configured there;
this does not waive the project's regression/independent-review requirements.

## C. Minimal transplant
evidence/stage3d5b/migration.json records six preserved code/test copies with
size/SHA and byte equality. Four D5B files and two D5 bound files are kept
isolated. Additional files implement evidence capture, contact controls,
current-path independent checking, native observations, report generation and
the dedicated workflow. Existing tracked CAD, Web, ledgers and tests are not
changed. D4 remains the authority for its existing orthogonal exact-model
contract; no refactoring or blind old-tree/cherry-pick replacement is used.

## D. Dependencies
PR29/31/33/35/37 are merged; each merge commit is an ancestor of the verified
main. The exact merge SHAs are in migration.json. D1-D4 sources and existing
FreeCAD/browser/native workflows are present. No open duplicate PR or same-name
remote branch existed at the initial authenticated check. Remote refs are
rechecked immediately before push.

## E. Real BRep correspondence
The current main's FCStd differs from the old local candidate. native.py pins
the current D2 input set and extracts the two Shape members without saving or
recomputing the original. Native execution is pending the new CI job at this
document's freeze. It records versions, raw bytes, faces/trims, orientation,
Placement, tolerances, errors and nominal-plane candidates. None is a certified
BRep-to-exact-cell correspondence theorem.

## F. Solid inclusion
Real inclusion remains UNKNOWN. The sufficient-condition specification in
CONTRACT.md separates outward material coverage from inward empty-space
coverage. Contact of a closed cell with the open void's wall is a specified
FAIL for empty-cell certification, not proof of native penetration. Sampling,
images, bbox, byte identity and validity are not used as substitute proofs.

## G. Finite error
Real approximation, extraction, coordinate/transform, arithmetic, rounding,
pose and continuous-motion bounds remain unproved. No arbitrary fixed epsilon
is introduced. Synthetic conditional radius/rounding theorems do not establish
these real premises. Static shape observations do not imply continuous safety.

## H. Cases and reproduction
TEST_MATRIX.md and evidence/stage3d5b/test-correspondence.json distinguish 15
E1-E14 fault inputs, E15 normal, preserved 13 methods, independent 17 faults,
10,000 rectangles and 5,000 rounding pairs. The new contact method adds three
subtests, not three independent test methods. Original failure records,
post-fix records and later source/input reconstructions are labelled separately.
Use `python -B -m unittest discover -s cad/stage3d5b -p 'test_*.py' -v` and the
commands in the matrix. Historical records are not post-transplant executions.

## I. Independent review
The separate reviewer checks the transplanted path and source hashes, uses
four-corner/divmod references, and saves full new inputs. Shared Fraction,
semantics and candidate transform helper use are disclosed. This review is
not an independent proof of real BRep semantics. See INDEPENDENT_REVIEW.md.

## J. Regressions, official CI and preservation
Initial Windows local regression detected CRLF checkout conversion against
fixed byte pins. Failures are preserved; no expected hashes or tolerances are
relaxed. Only the isolated clone's line-ending configuration/working copies
are corrected to Git-object bytes before rerun. Historical source originals
and CAD are not repaired. Official existing native/Web/CAD regressions remain
enabled, and new portable/native jobs retain failures and source bytes.
Final workflow/run/job/step states, checkout/merge-ref/submitted-tree relation,
official ZIP digest/SHA/size/CRC/internal manifest and independent readback are
pending actual execution and will be reported on the frozen PR HEAD. Local
copies and formal original CI archives are not interchangeable. Retention is
UNKNOWN even when byte readback succeeds.

## K. 128 intervals
run.py recomputes the unchanged D4 exact-model 128 intervals on current input,
counts PASS/FAIL/UNKNOWN/NOT_TESTED and requires a total of 128. The stage's
real-CAD intervals remain PASS0/FAIL0/UNKNOWN0/NOT_TESTED128 because no certified
native interval oracle runs. Prior D4 UNKNOWN128 is a separate stage assessment.
Final actual analytical counts are in the fresh CI report, not copied from
this prose or a historical result.

## L. Submission and next condition
The Draft PR references Issue #38 and the review comment. Final results are
added there without unrelated commits into the audited HEAD. Remaining CAD
correspondence/error/continuous premises keep overall PARTIAL/HOLD unless
separately established. No merge, force push, public deployment or Draft
release is performed. Personal storage paths and private download URLs are
kept out of the public discussion.
