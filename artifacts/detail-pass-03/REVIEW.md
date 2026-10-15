# Architectural detail pass 03

The pass-02 fortress-town layout is retained: 208 × 188 m outer enclosure, 32 major buildings/complexes, nine courtyards, three defensive rings and 480 × 480 m terrain. The website continues to use its original playable prototype; this is a separate architecture review export.

## Architectural work

- All 31 ordinary building masses now have constructed facade panels around recessed openings, with reveals, sills, lintels, shutters or stone arches. The main keep is detailed separately.
- Timber buildings use limewashed infill, structural posts, tie beams, knee braces and gable rafters. Stone buildings have quoins and horizontal storey courses.
- Roofs include gabled, hipped and stable clerestory forms, exposed slate or oak shingle eaves, ridge caps, 14 dormers and 27 chimneys with open flue surrounds.
- Stable ranges have large gates and raised louvred ridge vents. Bulk stores and the granary have loading hatches, projecting hoist arms, braces and ropes. The inn and quartermaster have covered galleries.
- 250 curtain modules have raised bedded masonry courses, battered buttresses, string courses, supported battlement edges and low inner parapets. Curtain merlons are placed on the outer edge to leave a wall walk.
- 31 towers have rebuilt 64-sided shells, deep window/arrow openings, recessed backing, projecting sills and hoods, crown corbels and projecting cornices.
- Three gatehouses have masonry portal arches, passage arch ribs, grille grooves, raised portcullises, strapped/braced gates, guard windows and covered upper galleries.
- The great keep has deep arched windows, a framed entrance, quoins, belt courses and stepped thresholds. New outer and inner wall stairs have treads, supports, railings and landings through gaps in the parapets.

## Review files

- `winterfell_fortress_detailed.blend` in this folder: editable source, with the previous zone hierarchy and named `DETAIL_*` groups.
- `public/assets/winterfell-detailed/winterfell_fortress.glb`: master export, 606,858 triangles, 11 material batches, approximately 67.6 MB.
- `winterfell_fortress_lod1.glb` beside it: 254,876 triangles, approximately 28.6 MB.
- Eevee previews in the same asset folder: `overview.png`, `gatehouse-detail.png`, `town-street.png`, `keep-detail.png`, `wall-and-tower.png`, `inner-courtyard.png`.
- `glb-review.png`, `glb-gatehouse.png`, `glb-street.png` in this folder: actual exported geometry inspected in Chrome.

## Verification and limits

Both GLBs pass Khronos glTF validation with zero errors and warnings. A strict metadata comparison preserves the building footprints and positions, courtyards, wards, gates and original routes. Pedestrian and 3 m supply-route checks pass for all three main routes. Separate movement tests verify both stair ascents, their landings and access onto the wall walks. The exported model loads with 11 meshes, assigned materials and no browser runtime errors.

This is a detailed static architecture model. Building interiors remain closed, portcullises remain raised, and hoists and doors are not animated. Collision uses the original building envelopes plus buttress proxies and new stair/threshold support surfaces; small trim is simplified. The master is intended for close architectural review; LOD1 is supplied for lighter rendering. No cross-device FPS claim is made.

Rebuild from the project root with Blender 5.2.2 installed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/blender/build.ps1 -Layout detail
node tools/validate-assets.mjs public/assets/winterfell-detailed artifacts/detail-pass-03
node tools/validate-town-layout.mjs public/assets/winterfell-detailed artifacts/detail-pass-03
node tools/validate-architecture.mjs
node tools/render-town-review.mjs public/assets/winterfell-detailed artifacts/detail-pass-03
```

Gatehouse organization was informed by English Heritage descriptions of [Dunstanburgh Castle](https://www.english-heritage.org.uk/visit/places/dunstanburgh-castle/history/description/) and its portcullis/upper-room arrangement. This remains an original Winterfell-inspired environment rather than a reconstruction of a particular historic castle.
