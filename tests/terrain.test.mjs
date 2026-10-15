import {test} from 'node:test';
import assert from 'node:assert/strict';
import {floorAt,moveCapsule} from '../lib/collision.mjs';
const data={floor:.12,walkableSurfaces:[],colliders:[],capsule:{height:1.8,radius:.36,stepHeight:.3},bounds:[-10,10,-10,10],terrainHeightField:{origin:[0,0],step:2,columns:2,rows:2,surfaceOffset:.1,heights:[0,2,2,4]}};
test('terrain height supports bilinear sampling in glTF X/Z coordinates',()=>{
 assert.ok(Math.abs(floorAt(1,1,0,data)-2.1)<1e-8);
 assert.ok(Math.abs(floorAt(.5,1,0,data)-1.6)<1e-8);
});
test('grounded capsule follows continuous terrain height',()=>{
 const p=moveCapsule([0,1.9,0],[1,1],data);
 assert.ok(Math.abs(p[1]-3.9)<1e-8);
});
test('walk surfaces remain above terrain and respect the step allowance',()=>{
 const d={...data,walkableSurfaces:[{min:[0,0],max:[2,2],height:5}]};
 assert.ok(Math.abs(floorAt(1,1,1,d)-2.1)<1e-8);
 assert.equal(floorAt(1,1,4.8,d),5);
});
