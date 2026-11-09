# Production browser smoke, 2026-11-09

Deployment run: https://github.com/tetsujisugimori-coder/castle-3d-parts/actions/runs/42605570058
Result: Success, 37s. workflow_dispatch, branch feat/stage2d-pages-integration.
Commit: b368bedd2cfa67cf6eeda53e8234ef8460aebaf2
Tree: 9d6620277aead6021a3da070bbd41d8646916c08

GitHub Pages environment temporarily allowed exact feature branch plus main. No merge performed.

Public root https://tetsujisugimori-coder.github.io/castle-3d-parts/ loaded Stage 2-D entry. Clicking top entry navigated to /castle-3d-parts/stage2c/ with Stage 2-D title.
Guide and deployment-manifest.json opened via visible links. Manifest matched exact commit/tree above, basis D, physical_iphone NOT_TESTED.
Research link opened /research-cad/ and research data status became loaded/read-only/no formal adoption.
Browser Back returned to stage2c, Forward returned to research-cad, Back and Reload returned to stage2c.

BLOCKED: configured cloud Chrome cannot create WebGL context. Public B0 displayed: 連携を停止しました: 3D表示を開始できません: Error creating WebGL context.
Console states GL_VENDOR = Disabled, GL_RENDERER = Disabled, Sandboxed = yes, BindToCurrentSequence failed.
B1 and B2 selector changes were exercised and both retained the same explicit fail-closed status with 3D, drawing and selection controls disabled. Reload also retained fail-closed state. Do not count these as successful model revision, geometry, or URL-state persistence tests.
Actual production GLB/SVG rendering, bidirectional part selection and per-part research links could not be exercised. They remain NOT_TESTED in this configured browser. This does not replace local/CI browser-matrix tests or physical iPhone tests.
No TLS warning occurred. No certificate bypass, browser security change or GPU setting change attempted.

Screenshots: public-b0-webgl-block.png; deploy-run-42605570058.png.
Awaiting parent instruction before main restoration and temporary-rule removal.
