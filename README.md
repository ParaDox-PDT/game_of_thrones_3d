# Westeros Explorer · Northern Fortress

A runnable Next.js / React Three Fiber explorer and deterministic Blender production pipeline for `game_of_thrones_3d`. All geometry and textures are original procedural work inspired by a northern medieval fortress; no game assets were downloaded.

## Published explorer

Repository: https://github.com/ParaDox-PDT/game_of_thrones_3d

Production: https://game-of-thrones-3d.netlify.app

The website renders the complete winter environment using its 278,618-triangle LOD1 (about 32.4 MB). The asset library also offers the full 819,490-triangle model. Both use the expanded fortress, current terrain collision and embedded torch lights. The default camera and walking spawn match the expanded town. Review passes below record the historical stages of this scene.

Netlify serves the static Next.js export from `out/`; no server functions or environment secrets are required. `npm run build` generates the deploy directory. Deploy the built files with `netlify deploy --dir out --prod --no-build`. The first publication uses a CLI upload; GitHub pushes do not automatically deploy until Git continuous deployment is connected.

## Intermediate fortress-town layout, pass 02

The expanded massing export is separate from the first playable scene: `artifacts/layout-pass-02/winterfell_fortress.blend` and `public/assets/winterfell-town/winterfell_fortress.glb`. It has a 208 × 188 m outer enclosure, three defensive rings, 32 major buildings/complexes, nine courtyards, and a 480 × 480 m snowy setting. Read `artifacts/layout-pass-02/REVIEW.md` for zoning and review views. This was an intermediate layout review before the published winter environment.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/blender/build.ps1 -Layout town
node tools/validate-assets.mjs public/assets/winterfell-town artifacts/layout-pass-02
node tools/validate-town-layout.mjs
node tools/render-town-review.mjs
```

This pass reuses the existing material kit, organizes editable geometry into named zone collections, and checks pedestrian and 3 m supply-route clearance. No new small props or material polish are included.

## Architectural detail pass 03

The expanded layout now also has a separate detailed version: `artifacts/detail-pass-03/winterfell_fortress_detailed.blend` and `public/assets/winterfell-detailed/winterfell_fortress.glb`. Read `artifacts/detail-pass-03/REVIEW.md` for architecture changes, close-up images, validation and model-size information. It retains pass-02 building positions and zoning while developing facades, towers, wall construction, gatehouses, roofs, chimneys and wall access. Interiors remain closed.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/blender/build.ps1 -Layout detail
```

## Winter atmosphere pass 04

`artifacts/environment-pass-04/winterfell_fortress_winter.blend` and `public/assets/winterfell-environment/` add a snowy northern valley, pine forests, mountain ranges, rocky relief, muddy/slushy roads, snow banks and working-yard supplies to the detailed fortress. Torches, braziers and northern banners establish occupied wards. The fortress layout is preserved. See `artifacts/environment-pass-04/REVIEW.md` for images, model budgets, checks and runtime fog settings. This environment is now used by the published explorer.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/blender/build.ps1 -Layout environment
node tools/validate-environment.mjs
```

## Run

Node 22+ and npm are required.

```powershell
npm install
npm run dev
```

Open http://127.0.0.1:3000. Orbit with drag/scroll. Choose a point of interest to reframe. Enter the courtyard to walk with WASD/arrows, mouse to look, Shift to run, and Esc to release the cursor. Click the scene to capture it again. Dawn, Overcast, and Blue hour change actual scene lighting. The library offers all GLBs for download.

## Rebuild the assets

```powershell
npm run assets:build
# Or explicitly select an executable:
powershell -File tools/blender/build.ps1 -BlenderPath 'C:/path/to/blender.exe'
# Geometry/export only:
powershell -File tools/blender/build.ps1 -SkipPreview
```

The builder detects the Microsoft Store `blender-launcher` alias first; directly executing the Store package binary can return Access denied. Tested with Blender 5.2.2 LTS. No administrative installation is required. Four CPU threads, tiny generated textures, Eevee previews, and a free-RAM preflight limit resource use. The final artifacts use the installed Store version.

Configure seed, texture resolution, wall height, previews, and budgets in `tools/blender/config.json`. Generation replaces only the named generated files in `public/assets/winterfell` and `artifacts`. Blender source keeps linked modules and a separate wireframe collision collection. Export batches the visible geometry into one mesh per material. LOD1 uses a separate simplified GLB for downstream distance switching; the explorer currently renders LOD0.

## Deliverables

- `artifacts/winterfell_fortress.blend`: editable source, linked architecture, packed generated materials, cameras and lights.
- `public/assets/winterfell/winterfell_fortress.glb`: complete render environment, embedded PBR textures, no lights/cameras/proxies.
- `public/assets/winterfell/winterfell_fortress_lod1.glb`: simplified geometry.
- `wall_module.glb`, `tower_shaft.glb`, `barrel.glb`, `crate.glb`: reusable local-origin modules. Origins are at bottom centre; tower shaft is a component rather than a complete tower.
- `collision.json`: named analytical collision proxies and stair/wall support surfaces.
- `manifest.json`: source, modules, budgets, statistics, version, and coordinate conventions.
- `overview.png`, `gate.png`: Eevee inspection renders.
- `artifacts/*validation.json`: Blender assertions, Khronos glTF validation, browser evidence.

## Coordinates and collision contract

One unit = one metre. Blender Z-up maps to glTF Y-up: `(x, y, z) → (x, z, -y)`. South gate is at glTF `z=32`, spawn at `z=48`. No runtime scale/rotation is applied to the model. The ground eye height is 1.92 m: terrain support at 0.12 m plus 1.8 m capsule height. Radius 0.36 m, stair step allowance 0.30 m. Gate clearance is at least 7 m wide and 6.5 m high.

`collision.json` box `center`/`size` arrays use `[x,y,z]`; cylinders use `center`, `radius`, `height` with a vertical Y axis. `walkableSurfaces` store horizontal `[x,z]` min/max and Y height. `COL_*` wire proxies in the Blender source correspond to this data. They are intentionally excluded from visual GLBs. The lightweight grounded controller subdivides horizontal movement into ≤0.12 m steps, resolves X/Z separately for wall sliding, and steps onto exported treads. This is static capsule collision, without jumping, rigid-body dynamics, or simulated falling. Keep and cottage interiors are closed; the gate, courtyard, and east stair are traversable. Decorative plinths, cornices, and small details use simplified proxies.

## Checks

```powershell
npm run assets:validate
npm test
npm run typecheck
npm run build
# With the server running and Google Chrome installed:
npm run test:browser
```

The asset validator checks every GLB with Khronos glTF Validator, PBR materials, UV/normal attributes, real LOD triangle reduction, and source/proxy presence. Movement tests use the actual exported collision data, including gate clearance, tunnelling, towers, wall sliding, stair ascent and world bounds. Browser tests verify real GLB rendering, walkthrough entry, keep collision, lighting controls, downloads, responsive overflow, runtime errors, and screenshots. Performance numbers are local observations, not a cross-device guarantee.

Blender native Computer Use is unavailable in this session. Visual inspection uses actual Eevee images and browser screenshots; the editable source can be opened in Blender for further review.

For Vercel deployment, installing its CLI is strongly recommended: `npm i -g vercel`. It enables `vercel deploy`, `vercel env pull`, and `vercel logs`. Deployment has not been requested or performed.
