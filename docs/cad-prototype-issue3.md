# Issue #3: editable CAD prototype v1

## Scope and research boundary
Baseline main **68c039d8c1c40b81cac0f7e16fa800678ccc6de8**, tree **6662636d218d2e359de694aede3b25a208f9cd99**. Stage4 PR13 was merged before this work. All 125 baseline files remain byte-identical; this is an additive prototype page, not a replacement of v0. No deployment, formal adoption or change to `reference_only`/`write_allowed=false`.

`cad/prototype-v1/reference-snapshot.json` fixes DEC-0001/r1 and DEC-0002/r1, their complete read-only parameter records, hashes of source files and baseline commit/tree. Those decisions remain held, with historical/hypothesis values null. Only D prototype values feed this model: height2m, centres1.2m, count5, square width0.15m, rails2. Total width4.95m. Square cross-section, flat top, linear layout, rear-face butt contact, rail section0.66×0.56 of post width, evenly spaced rail heights and surface texture are **new explicitly provisional D geometry**, not findings or endorsements of HYP-0001/2. No joint strength/engineering certification is claimed.

Track B reports SRC-0001 printed p68/PDF76 approximately30cm **posthole diameter**. This is not post width, not an identified individual, and does not modify the D0.15m width. Research→production influence is a review candidate only. Follow Issue #9 for independently verified citation status. Sources/OBS/CMP/HYP/DEC are unchanged by this track.

## Files and regeneration
- `cad/prototype-v1/build.py`: actual FreeCAD1.0 module builder, input guard, same-document edit/rebuild, STEP and mesh export, TechDraw page/SVG, save/reopen tests.
- `cad/prototype-v1/regenerate.FCMacro`: GUI helper for an opened original. Change Parameters in FreeCAD, run macro to rebuild component count. GUI macro execution itself is NOT_TESTED. The imported regenerate function was executed headlessly.
- `cad/prototype-v1/generated/palisade.FCStd`: editable document, named Parameters/Post_001–005/Rail_001–002, length expressions and TechDraw page. Count/rail count changes require regenerate, not merely recompute. Height/width/spacing use expressions. Save/reopen/change/save/reopen checked.
- `palisade.step`: seven independent solids, reimported and dimensions/volume checked. `mesh-transfer.json`: each CAD solid tessellated separately, actual millimetres divided by1000 into metres, Z-up.
- `palisade-drawing.svg`: actual `TechDraw.projectToSVG` projection, units/version/prototype status printed. Headless TechDraw creation PASS; visual GUI layout/PDF NOT_TESTED.
- `blender/prototype-v1/build.py`: Blender4.3.2 background conversion of that mesh transfer. STEP direct import is **not** used. Original deterministic256×256 wood grainD, UV coordinates, roughness. `palisade.blend` is compressed/packed and editable.
- `site/cad/palisade.glb`: real Blender GLB, embedded image; Y-up export. GLB imported in a fresh scene and independently parsed for component counts and world dimensions.
- `site/cad/index.html`: separate Three.js0.180.0 GLB viewer. Rotation/zoom/reset, pointer and keyboard buttons, load/WebGL errors. Old v0 link explains different origins. No CAD size edits on this page: change CAD and regenerate instead.

Commands from repository root:

```sh
/usr/bin/python3 cad/prototype-v1/build.py
blender -b -t 1 --python blender/prototype-v1/build.py
node --test
node scripts/cad-prototype.mjs
node scripts/build-site.mjs
python3 -m http.server 8000 -d dist
# open http://localhost:8000/cad/
```

FreeCAD Python module search path defaults `/usr/lib/freecad/lib`, adjust for an installed official FreeCAD build if needed. Python ABI must match the FreeCAD module. A host without FreeCAD cannot regenerate CAD; Node tests check delivered artifacts/contracts only and are not a substitute for real software runs. Blender background does not prove GUI operations.

CAD internal unit **mm**, X across width, Y depth, Z up, origin at centre of post-base line. Export mesh metres/Z-up; Blender metres/Z-up; GLB metres/Y-up. No ground mesh affects bounding checks. Pairwise solid intersections measured0mm³ (face contact allowed), three alternate configurations and seven invalid inputs checked. This does not establish physical joinery or structural safety.

## Failures and verification limits
`evidence/cad-prototype/environment-failures.md` retains actual initial GUI CLI crashes and headless TechDraw template failure. A later independent final-FCStd-edit/save check found an included-template transient-directory failure; fixed by restoring the SVG **from the FCStd ZIP** into a unique temporary directory, recreating the template object and reconnecting the page. Original error and RED→GREEN are separately preserved. No user setting or permissions changed.

Node tests protect125 baseline files, snapshot contract and real GLB geometry. Source hashes, original logs and independent reports distinguish delivered evidence from tests rerun by a reviewer. The additive Actions workflow runs Node/browser checks; it does **not** claim FreeCAD or Blender was installed/executed on GitHub Actions. Original binary production is locally headless-executed evidence.

Browser matrix: Chromium/WebKit ×375/390/765/1280px ×normal/reduced-motion, plus failure controls. For stable controlled module delivery, tests may map CDN URLs to unmodified installed Three.js0.180.0 files; this tests UI/GLB, **not CDN availability**. Initial direct-CDN run produced no screenshots and was cancelled exit130; not counted PASS. Runtime page still requires CDN. Native iPhone Safari, physical touch/VoiceOver, GPU variability, FreeCAD/Blender GUI manipulation and full offline distribution are NOT_TESTED/not provided.

## Licenses
Generated geometry, scripts, original wood-grain image and drawings are authored for this repository; no copied archaeological figure or texture is bundled. Three.js0.180.0 is MIT, fetched at runtime from jsDelivr; https://github.com/mrdoob/three.js/blob/r180/LICENSE. FreeCAD1.0 and Blender4.3.2 are tools, not redistributed. Their generated output does not establish rights to any archaeological source figure; none was copied.

## Next
Use source verification to propose revisions rather than overwrite snapshots. Any real A/B/C parameter adoption requires a separately approved generalized research contract. Add official GUI and iPhone checks, more joinery variants and offline dependency packaging as follow-ups. Neither technical CAD success nor PR merge proves Yamanaka fence morphology.
