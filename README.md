# Westeros Explorer · Winterfell reference reconstruction

A Next.js / React Three Fiber explorer with an editable Blender 5.2.2 production pipeline. Pass 05 rebuilds the earlier rectangular prototype around the user's **Image A** site plan.

- Repository: https://github.com/ParaDox-PDT/game_of_thrones_3d
- Production: https://game-of-thrones-3d.netlify.app
- Review report: [artifacts/reference-pass-05/REVIEW.md](artifacts/reference-pass-05/REVIEW.md)
- Editable source: `artifacts/reference-pass-05/winterfell_reference.blend`
- Portable modules: `public/assets/winterfell-reference/`
- Review package: `artifacts/winterfell-reference-pass-05.zip`

## Reference layout

The approximately 350 × 362 metre outer enclosure follows an irregular perimeter, with north/south gates, a central inner ward and an eastern godswood. Northwestern stables and a training yard face northeastern guest houses. Western storehouses connect to a riverside mill; kitchens, the Great Hall, family quarters and maester towers occupy the southern districts. The river follows the west and southwest approach and passes beneath the south bridge.

Thirty-five buildings and forty-six towers form distinct districts. Recessed openings, stone string courses, corbels, buttresses, roof variants, chimneys, uneven roof snow, timber framing and stairs develop the architecture. Carts, barrels, wood stores, targets, garden beds, torches and banners establish working courtyards. Pine boughs, bare trees, a pale sacred tree with crimson leaves, rocky banks and a pool distinguish the landscape.

This is an original procedural interpretation of the supplied illustration. Building interiors are closed. The accompanying review identifies the remaining art polish.

## Run and explore

```powershell
npm install
npm run dev
```

Open http://127.0.0.1:3000. Drag/scroll to orbit; choose a named district to reframe. **Map plan** uses an orthographic overhead camera. **Enter the courtyard** starts on the southern approach: WASD/arrows to move, mouse to look, Shift to run, Escape to release the cursor. The asset library downloads each district independently.

## Rebuild

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/blender/build.ps1 -Layout reference -SkipPreview
node tools/optimize-reference.mjs
# Use the installed Microsoft Store launcher for review rendering:
blender-launcher --background artifacts/reference-pass-05/winterfell_reference.blend --threads 4 --python tools/blender/render_reference.py
```

`tools/blender/reference-layout.json` defines the reference interpretation, gates, districts and routes. `rebuild_reference.py` creates the geometry, materials, editable collections, cameras, GLBs, manifest and collision data. The optimizer welds/deduplicates data, applies Draco geometry compression and WebP texture compression. The website includes its own Draco decoder, without a third-party decoder request. Rebuilding raw GLBs must be followed by the optimizer before publication.

The Blender source retains packed PNG textures and editable component geometry. Architecture textures are 512² base/normal/roughness maps; the landscape has a separate 2048² snow/wear map. Twenty-three exported modules retain independent origins and material batches. The manifest supplies each module's translation, URL, triangle count and download size. Models use metres without runtime scaling.

## Coordinates and collision

Blender `(x, y, z)` maps to glTF `(x, z, -y)`. North is Blender +Y and browser -Z. The south gate is near browser `z=188`; the walking spawn is at `z=306`. `manifest.modules[].position` reassembles local district GLBs.

`collision.json` contains a sampled landscape heightfield, oriented building boxes, tower cylinders, finite oblique wall segments, supported bridge surfaces, stair treads and wall walks. Positions use `[x,y,z]`; horizontal surface centers use `[x,z]`. A box/surface `yaw` follows the Blender-to-glTF rotation convention used in `lib/collision.mjs`.

The grounded capsule is 1.8 m high, radius 0.36 m, with a 0.30 m step allowance. Movement is subdivided into at most 0.12 m horizontal increments. This controller supports static walking, without jumping or rigid-body simulation. Small ornamental objects use simplified collision coverage.

## Verification

```powershell
npm test
node tools/validate-reference.mjs
npm run typecheck
npm run build
# Against a running local or deployed server:
npm run test:browser
```

Khronos validation and an independent Draco decode check cover every module. Movement tests follow all fourteen route polylines, the river bridge, rotated building collisions and wall access. Browser checks verify rendered meshes, district controls, the map camera, walking, downloads, responsive layout and runtime errors. `source-validation.json` records a reopened Blender source and its packed images. Native Blender inspection uses the Computer Use plugin.

## Publication

Next.js exports a static site to `out/`. No application secrets or server functions are required.

```powershell
npm run build
netlify deploy --dir out --prod --no-build
```

The project is linked to the existing `game-of-thrones-3d` Netlify site. Deployment uses CLI uploads; GitHub pushes do not trigger a deploy until Git continuous deployment is connected.

## Earlier review stages

Passes 02–04 remain in their original artifact/asset folders for comparison: expanded town layout, architectural detailing, and winter atmosphere. The source and metrics in those historical reports describe those older exports. The active website now assembles the Image A reconstruction.
