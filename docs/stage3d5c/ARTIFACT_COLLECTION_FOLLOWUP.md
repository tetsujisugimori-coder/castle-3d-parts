# PR #40: CAD contract hidden-source collection follow-up (2026-11-19 JST)

## Historical evidence is immutable
- Original PR #40 HEAD: `923bda856015398e1578f66bfc9b5d6553cf49a1`.
- Regression artifact `14181928387`: manifest expected 1,413 source entries, ZIP contained 1,383; the 30 missing paths are all hidden.
- Original artifact digest/CRC can match despite *incomplete content*. It remains PARTIAL and is not rewritten, retroactively completed, or represented as a passing collection.
- The original `cad-prototype.yml` used `git archive HEAD` and `actions/upload-artifact@v4` without `include-hidden-files: true`. This explains the observed pattern strongly; the original pre-upload file set itself was not retained, so full historical causality remains unproven.
- The 18 separate source-free ZIPs and regression image/semantic auditing remain independently unresolved. Actual native BRep containment, finite real error, and continuous motion remain UNKNOWN/NOT_TESTED.

## New forward-only gate
1. `git archive HEAD` creates `cad-ci/source/` with dot-prefixed paths. Preserve existing unit/geometry/build commands and the original manifest.
2. `verify_cad_contract_archive.py` independently reads the *Git HEAD tree* (not manifest claims), validates exact source paths, bytes, SHA-256, and manifest, including hidden paths. Save `source-audit-pre.json` before upload. Reject absent/extra/mutated or unsupported sources.
3. The existing `cad-prototype.yml` is a byte-protected historical baseline. It is **not changed**. A separate `cad-contract-source-completeness.yml` collects a forward-only `cad-contract-complete` artifact and uses `upload-artifact@v4` with `include-hidden-files: true`. The old `cad-contract` artifact remains incomplete where its legacy upload excludes hidden paths.
4. A distinct downstream Actions job uses `download-artifact@v4` to read back the newly uploaded `cad-contract-complete`, re-derives the Git tree expected set, and compares the pre-upload count/digest/HEAD/tree. Fail on any mismatch and archive the post-audit report.
5. Synthetic regressions include the historical pattern of **exactly 30 hidden path omissions**, one ordinary omission, modified bytes, extra bytes, malformed manifest, and untrusted pre-audit.

The initial attempt to modify the protected legacy workflow at `c8021c4458e375edbdee417729b8d4420c409563` triggered 14 legacy byte-preservation failures; that failed raw result is retained, and the legacy workflow was restored byte-for-byte in the next corrective commit. The separate workflow is additive and does not silently relax historical invariants.

This is a new-version CI check, not an independent external auditor or automatic permanent preservation. GitHub upload/download and source set matching do not prove old artifact completeness, long-term availability, or CAD safety. Preserve the old ZIP; archive new artifacts under the applicable v0.2.0 owner-approved conditions, with a separate independent readback before considering the P2 closed.

## Acceptance gates
- Verify final submitted HEAD, merge-ref tree, upload action version and downloaded artifact name against the CI run.
- Expect the complete source set, including all 30 historically omitted hidden paths. Record actual counts and fixed SHA/manifest values rather than assuming 1,413 on future HEADs.
- Report normal and fault test results, every workflow/job outcome, original archive source separately, and all unsupported verification scope.
- Maintain PR #40 Draft / HOLD, PR #41 Draft / HOLD and Issue #42 recovery BLOCKED until separate owner decisions.
