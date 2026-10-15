import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { moveCapsule, intersects } from '../lib/collision.mjs';
const data=JSON.parse(readFileSync('public/assets/winterfell/collision.json','utf8'));
function march(position,delta,times=1){for(let i=0;i<times;i++)position=moveCapsule(position,delta,data);return position;}
test('a standing player can walk through the open south gate into the courtyard',()=>{
  const end=march([0,1.92,48],[0,-.1],400);
  assert.ok(end[2]<10,`Stopped at ${end}`);
  assert.ok(end[1]>=1.8);
});
test('curtain walls stop a player, including one huge movement frame',()=>{
  const end=march([20,1.92,45],[0,-100]);
  assert.ok(end[2]>=33.5,`Tunneled through south wall: ${end}`);
});
test('towers and keep block entry without blocking tangential sliding',()=>{
  const end=march([0,1.92,-4.5],[.1,-.1],120);
  assert.ok(end[0]>7,'Expected wall sliding');
  assert.ok(!data.colliders.some(c=>intersects(end[0],end[2],end[1]-1.8,c,.35,1.8)));
});
test('east stair treads support gradual ascent and connect to the curtain walk',()=>{
  let p=march([34,1.92,24],[0,-.05],480);
  assert.ok(p[1]>9.7,`Stair ascent failed: ${p}`);
  p=march(p,[.05,0],70);
  assert.ok(p[0]>37 && p[1]>9.7,`Landing connection failed: ${p}`);
});
test('world bounds clamp movement and diagonal motion stays finite',()=>{
  const end=march([90,1.92,90],[200,200]);
  assert.ok(end.every(Number.isFinite));
  assert.ok(end[0]<=107 && end[2]<=107);
});
test('overhead gate bridge allows a capsule beneath but its towers stay solid',()=>{
  const bridge=data.colliders.find(c=>c.name==='GatehouseBridge');
  assert.equal(intersects(0,32,.12,bridge,.36,1.8),false);
  const tower=data.colliders.find(c=>c.name==='GateWest_Shaft');
  assert.equal(intersects(-7.6,32,.12,tower,.36,1.8),true);
});
