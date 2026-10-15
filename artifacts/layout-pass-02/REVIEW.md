# Layout pass 02 — fortress-town massing

Intermediate spatial review. Original prototype assets and website remain available separately.

| Element | This pass |
| --- | --- |
| Outer wall footprint | 208 × 188 m; 8.04× the original enclosed area |
| Snowy setting | 480 × 480 m, with low ridges and scattered tree groups |
| Defence | Outer curtain, higher inner ward, and a third citadel enclosure |
| Keep | Stepped lower keep and upper donjon, four corner towers, two hall wings; approximately 43 m total height |
| Building masses | 32 major buildings/complexes |
| Courtyards | Market, military drill yard, stable exercise yard, two unloading yards, great assembly court, two domestic courts, and keep forecourt |

Arrival flows from the south gate into a public trade ward. A cross street distributes supplies to western military and eastern stable/storage yards. The offset inner gate opens into a protected assembly and residential ward. A further gate controls the keep forecourt. The inner and outer walls leave separate side service lanes and a northern circulation route.

The west ward holds three barracks ranges and a quartermaster. The east ward holds two stable ranges, a fodder barn and a separate exercise yard. Bulk receiving stores sit close to the outer gate. Smaller houses, craft buildings, an inn and council ranges give the settlement a town scale.

Existing materials are reused unchanged. No new prop dressing or fine material work was added. Building interiors remain closed. This is an intermediate layout export, not the replacement website scene.

Review `overview.png` for overall scale, `layout-plan.png` for zoning and circulation, and `north-review.png` for the keep and rear service corridor in `public/assets/winterfell-town`. `glb-review.png` in this folder shows the exported GLB rendered in Chrome.

Editable source: `winterfell_fortress.blend` in this folder. Portable model, LOD1, collision proxies, manifest and layout metadata: `public/assets/winterfell-town`.

Rebuild from the project root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/blender/build.ps1 -Layout town
node tools/validate-assets.mjs public/assets/winterfell-town artifacts/layout-pass-02
node tools/validate-town-layout.mjs
node tools/render-town-review.mjs
```

The source is organized into named `ZONE_*` collections. Layout metadata records building footprints, courtyard sizes, defensive gates and review routes in Blender XY coordinates; GLB/collision exports use metres and Y-up.

Both GLBs pass Khronos validation with zero errors and zero warnings. The main model has 185,292 triangles and nine material batches; LOD1 has 83,377 triangles. Six route-clearance checks pass: pedestrian and 3 m supply clearance for the keep approach, military ward and stable ward. The actual main GLB was loaded and visually inspected in Chrome. At this larger orbit distance the review camera uses a 2 m near plane to preserve depth separation between ground layers; a later website integration should select near/far planes for each camera mode.
