import {readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {moveCapsule} from '../lib/collision.mjs';
const folder=(process.argv[2] || 'public/assets/winterfell-town')+'/';
const reportDirectory=process.argv[3] || 'artifacts/layout-pass-02';
const layout=JSON.parse(await readFile(folder+'layout.json','utf8'));
const data=JSON.parse(await readFile(folder+'collision.json','utf8'));
const checks=[];
for(const route of layout.routes){
  // A wider capsule checks usable circulation, beyond a centreline-only test.
  for(const radius of [.36,1.5]){
    const config={...data,capsule:{...data.capsule,radius}};
    let position=[route.pointsBlender[0][0],1.92,-route.pointsBlender[0][1]];
    for(const [x,y] of route.pointsBlender.slice(1)){
      const z=-y,dx=x-position[0],dz=z-position[2];
      const count=Math.ceil(Math.hypot(dx,dz)/.1);
      for(let i=0;i<count;i++)position=moveCapsule(position,[dx/count,dz/count],config);
      assert.ok(Math.hypot(position[0]-x,position[2]-z)<.25,`${route.name} (radius ${radius}) blocked: ${position}; wanted ${x},${z}`);
    }
    checks.push({route:route.name,capsuleRadius:radius,passed:true});
  }
}
assert.ok(layout.buildingCount>=30);
assert.ok(layout.courtyards.length>=8);
assert.equal(layout.defensiveRings,3);
assert.ok(layout.footprintAreaMultiplier>=8);
assert.ok(layout.maximumKeepHeightMetres>40);
const report={passed:true,footprint:layout.footprintMetres,areaMultiplier:layout.footprintAreaMultiplier,buildings:layout.buildingCount,courtyards:layout.courtyards.length,rings:layout.defensiveRings,checks};
await writeFile(reportDirectory+'/layout-validation.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
