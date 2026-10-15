import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {floorAt,intersects,moveCapsule} from '../lib/collision.mjs';
const data=JSON.parse(readFileSync('public/assets/winterfell-reference/collision.json'));
const plan=JSON.parse(readFileSync('tools/blender/reference-layout.json'));
const at=(x,z)=>[x,floorAt(x,z,6,data)+data.capsule.height,z];
function follow(points){
  let p=at(points[0][0],-points[0][1]);
  for(const [x,y] of points.slice(1)){
    for(let i=0;i<10000;i++){
      const dx=x-p[0],dz=-y-p[2],distance=Math.hypot(dx,dz);
      if(distance<.16)break;
      const next=moveCapsule(p,[dx/distance*.1,dz/distance*.1],data);
      assert.ok(Math.hypot(next[0]-p[0],next[2]-p[2])>.0001,`Route blocked at ${next} toward ${x},${-y}`);
      p=next;
    }
    assert.ok(Math.hypot(x-p[0],-y-p[2])<.2);
  }
  return p;
}
for(const road of plan.roads)test(`Reference route: ${road.name}`,()=>follow(road.points));
test('Rotated building collision follows its orientation',()=>{
  const box={type:'box',center:[0,3,0],size:[2,6,10],yaw:Math.PI/2};
  assert.equal(intersects(4,0,0,box,.36,1.8),true);
  assert.equal(intersects(0,4,0,box,.36,1.8),false);
});
test('Oblique walls prevent tunnelling through a large movement frame',()=>{
  const wall={name:'angled',type:'wall',a:[-10,10],b:[10,-10],width:2,center:[0,5,0],height:10};
  const local={...data,terrainHeightField:undefined,floor:0,walkableSurfaces:[],colliders:[wall]};
  const end=moveCapsule([-5,1.8,-5],[20,20],local);
  assert.ok(end[0]+end[2]<0);
});
test('Bridge deck supports the river crossing at full human height',()=>{
  const end=follow([[0,-306],[0,-220],[0,-180]]);
  assert.ok(end[1]>3.5 && end[2]<181);
});
test('Inner stair climbs to the wall and its landing',()=>{
  let p=at(-88,.5);
  for(let i=0;i<310;i++)p=moveCapsule(p,[0,-.1],data);
  assert.ok(p[1]>14,`Stair top ${p}`);
  for(let i=0;i<55;i++)p=moveCapsule(p,[-.1,0],data);
  assert.ok(p[0]<-93 && p[1]>14,`Landing ${p}`);
});
test('Outer stair reaches the perimeter walk',()=>{
  let p=at(-149,-69);
  for(let i=0;i<420;i++)p=moveCapsule(p,[0,-.1],data);
  for(let i=0;i<65;i++)p=moveCapsule(p,[-.1,0],data);
  assert.ok(p[0]<-155 && p[1]>20,`Outer landing ${p}`);
});
