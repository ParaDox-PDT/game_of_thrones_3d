import {readFile,writeFile,stat} from 'node:fs/promises';
import assert from 'node:assert/strict';
import validator from 'gltf-validator';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import draco3d from 'draco3dgltf';
const dir='public/assets/winterfell-reference/';
const manifest=JSON.parse(await readFile(dir+'manifest.json','utf8'));
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco3d.createDecoderModule()});
const files=[];
for(const module of manifest.modules){
  const bytes=await readFile('public'+module.url);
  const report=await validator.validateBytes(new Uint8Array(bytes),{maxIssues:30});
  assert.equal(report.issues.numErrors,0,`${module.id}: ${JSON.stringify(report.issues.messages)}`);
  const doc=await io.read('public'+module.url);let triangles=0;
  for(const mesh of doc.getRoot().listMeshes())for(const p of mesh.listPrimitives()){
    assert.ok(p.getAttribute('POSITION')&&p.getAttribute('NORMAL'),`${module.id}: missing geometry attributes`);
    if(p.getMaterial()?.getBaseColorTexture())assert.ok(p.getAttribute('TEXCOORD_0'),`${module.id}: textured primitive lacks UVs`);
    triangles+=p.getIndices().getCount()/3;
  }
  const mats=doc.getRoot().listMaterials();
  assert.ok(mats.some(m=>m.getBaseColorTexture()),`No PBR textures in ${module.id}`);
  files.push({id:module.id,bytes:bytes.length,triangles,errors:report.issues.numErrors,warnings:report.issues.numWarnings,messages:report.issues.messages});
}
assert.equal(manifest.districts.length,11);
assert.equal(new Set(manifest.modules.map(m=>m.id)).size,manifest.modules.length);
assert.ok((await stat('artifacts/reference-pass-05/winterfell_reference.blend')).size>1000000);
const collision=JSON.parse(await readFile(dir+'collision.json','utf8'));
assert.ok(collision.colliders.some(c=>c.type==='wall'));
assert.ok(collision.terrainHeightField.heights.every(Number.isFinite));
const result={passed:true,createdAt:new Date().toISOString(),modules:files.length,triangles:files.reduce((s,f)=>s+f.triangles,0),bytes:files.reduce((s,f)=>s+f.bytes,0),collisionProxies:collision.colliders.length,files};
await writeFile('artifacts/reference-pass-05/export-validation.json',JSON.stringify(result,null,2));
console.log(JSON.stringify({...result,files:undefined},null,2));
