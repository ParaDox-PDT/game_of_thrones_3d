# Northern Fortress-Town — Winter Atmosphere Pass 04

The fortress now sits in a cold northern valley, with inhabited yards and visible signs of winter work. The pass-03 architecture and pass-02 fortress layout are preserved: 208 × 188 m enclosure, three defensive rings, 32 building complexes and nine courtyards. Earlier review files remain available separately.

## What changed

- Expanded the surrounding terrain to 1,280 × 1,280 m, with irregular relief, exposed scree, 226 rocks, 412 snow-laden pines and four distant mountain ranges.
- Added 556 snow banks and drifts along defensive walls, roofs, eaves and sheltered building edges. Main approaches, gates, supply routes and both wall stairs remain usable.
- Built muddy roads with slushy margins, ten wheel ruts and 377 boot marks, suggesting traffic between the gates and working wards.
- Furnished the yards with 24 barrels, 20 crates, five carts, nine wood piles, fencing and four market stalls. Stable fodder, military supplies, stored timber and market goods give each ward a use.
- Added eight northern banners with an original angular animal emblem, twelve wall torches and six braziers. All eighteen point lights are embedded in both GLBs.
- Used cold overcast lighting, blue-gray valley haze and warm local firelight. A separate blue-hour render shows the evening atmosphere.

## Files and review views

`winterfell_fortress_winter.blend` is the editable daytime source. Geometry is named and organized in collections; cameras, materials, local lights and the native atmospheric volume are retained.

`public/assets/winterfell-environment/` contains the master and lighter LOD GLBs, collision and terrain data, prop placements, runtime atmosphere settings, road textures and seven Eevee images. Start with `overview.png`, then `southern-approach.png`, `stable-yard.png`, `market-street.png`, `winter-landscape.png` and `blue-hour.png`.

Browser screenshots in this review folder show the actual master GLB with Three.js. The `lod-review/` folder verifies the lighter GLB separately. The master has 819,490 triangles and is approximately 91.7 MB; LOD1 has 278,618 triangles and is approximately 32.4 MB. Both use 24 material batches.

## Atmosphere and runtime contract

GLB includes visible scenery, embedded PBR textures, emissive flames and eighteen normalized point lights. Apply `environment.json` for background, hemisphere/sun lighting and exponential distance fog. The Blender volume is excluded from GLB because native volumetric scattering is not portable through this format. Native and browser lighting are visually checked but do not render identically.

`collision.json` includes a sampled terrain heightfield and 1,917 analytical proxies. `lib/collision.mjs` now supports bilinear terrain height sampling while preserving existing walkable stair surfaces. These files are prepared for integration; the main website still loads the original prototype.

Props, flames and banners are static. Interiors remain closed. Mountains and trees follow the existing stylized geometry. The master is intended for detailed review; use LOD1 for lighter viewing. No device-independent frame-rate claim is made.

## Verification

- Both GLBs: Khronos validation passed with zero errors and zero warnings.
- Both GLBs: loaded in Chrome; 24 meshes, 24 materials, no missing materials and eighteen point lights.
- Fortress building positions, zones, courtyards, gates and routes match the previous pass.
- All three routes pass pedestrian and 3 m supply-clearance checks; both wall stairs and landings remain clear.
- Nine movement/terrain tests and TypeScript checking passed.
- Seven actual Eevee views and browser views were visually inspected.
- Saved Blender source reopened successfully with all twenty texture images packed and no missing image data.

## Reproduce

The review archive includes the pass-03 input `.blend` and JSON data needed to regenerate this environment. Run commands from the extracted project root. Blender 5.2.2 LTS was used through its Microsoft Store launcher alias. Node dependencies must be installed to run browser and GLB checks.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/blender/build.ps1 -Layout environment
node tools/validate-assets.mjs public/assets/winterfell-environment artifacts/environment-pass-04
node tools/validate-town-layout.mjs public/assets/winterfell-environment artifacts/environment-pass-04
node tools/validate-environment.mjs
node tools/render-town-review.mjs public/assets/winterfell-environment artifacts/environment-pass-04
python tools/package-environment-review.py
```
