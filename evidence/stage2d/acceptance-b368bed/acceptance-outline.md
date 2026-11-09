# Stage 2-D acceptance record

Implementation candidate: `b368bedd2cfa67cf6eeda53e8234ef8460aebaf2`, tree `9d6620277aead6021a3da070bbd41d8646916c08`.
Issue #22 / Draft PR #23. No merge.

This branch contains acceptance evidence only. It is not the candidate implementation or a new deployed build. The candidate HEAD is intentionally unchanged during independent review and deployment verification.

## Scope and limitations
- Reuse merged Stage 2-C from main `dec85b596f6b82bfd69129e4b1edbc75d182318c`; no duplicate CAD regeneration.
- 948 pre-existing paths retained. 939 are byte-identical; 9 executable/workflow paths are exact approved migrations with original bytes and before/after hashes. Research/CAD/STEP/Blender/GLB/SVG remain unchanged.
- 57 true dimensions, 14 parts per revision, B0/B1/B2, all prototype D/reference_only.
- Actual native TechDraw exports are provided separately; interactive linked drawing is CAD projection with validated true dimensions, not misrepresented as native TechDraw.
- Physical iPhone Safari, pinch, finger precision, gesture/scroll arbitration and app-return behavior remain NOT_TESTED.
- Thin fit-page members can be ~1.5 CSS px; accepted automated pointer path first uses pan/zoom, then ordinary click/emulated tap. No claim of unzoomed finger-sized targets. Native part list is the accessible fallback.
- Revision changes use document navigation and reset camera, drawing pan/zoom and selection. No unmeasured speed-up claim.
- Production verification temporarily deploys the candidate from its exact approved branch, then restores original main content and main-only environment policy. Temporary production is not a PR preview or permanent integration.

## Preserved failed runs
| Run | Stage | Evidence |
| --- | --- | --- |
| 42597615624 | historical baseline consumer missed exact code migration | artifact13663683188, SHA256 cd82627b8c133beca5a63586e0640402814ef6dbb8f371c95a630797380fe8c4 |
| 42597615732 | original browser failures | artifact13663724929, SHA2562438bea57043b09c3a09fac48dd8b8bb1fff1a1beee6dde1a3eac5dcf6184bb6 |
| 42598179554 | same-document WebKit history crash | artifact13665330989, SHA256 fdae4ae647c96d8869c8a65d05522296125f57eb2c055a4d8d8e4e1d6f660446 |
| 42601316671 | exposed but very thin SVG rail input failures | artifact13666236369, SHA2566b457a8a03381eef2ae673c4a6c1820326e162130cd378b120a797d6c5c79a73 |
| 42602227003 | main matrix160+20 PASS, minimal Chromium fixture prematurely traversed before load | artifact13666917083, SHA256b69799c55e42795b61648fb7bf973831cfc5ba18cbed04272de15c8d90397f48 |

The final minimal fixture records original WebKit legacy crash as an observation. The ordinary-document counterpart must succeed. It requires loaded URLs and the final B2 select value; native form-state restoration during intermediate traversal is recorded separately. The product suite asserts actual URL, select value, model revision and all19 displayed dimensions independently.
