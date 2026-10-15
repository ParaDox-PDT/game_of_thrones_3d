import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dedup,prune,draco,textureCompress} from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';
import sharp from 'sharp';
import {readFile,writeFile,mkdir,copyFile,stat} from 'node:fs/promises';
const dir='public/assets/winterfell-reference/';
const manifest=JSON.parse(await readFile(dir+'manifest.json','utf8'));
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.encoder':await draco3d.createEncoderModule(),'draco3d.decoder':await draco3d.createDecoderModule()});
await mkdir('public/assets/draco',{recursive:true});
for(const f of ['draco_decoder.js','draco_decoder.wasm','draco_wasm_wrapper.js'])await copyFile('node_modules/three/examples/jsm/libs/draco/gltf/'+f,'public/assets/draco/'+f);
const report=[];
for(const m of manifest.modules){
  const path='public'+m.url;const before=(await stat(path)).size;const doc=await io.read(path);
  await doc.transform(dedup(),prune(),textureCompress({encoder:sharp,targetFormat:'webp',quality:90,effort:35}),draco({quantizePosition:18,quantizeNormal:12,quantizeTexcoord:16,encodeSpeed:5}));
  await io.write(path,doc);m.bytes=(await stat(path)).size;
  report.push({id:m.id,before,after:m.bytes});console.log(m.id,`${(before/1e6).toFixed(1)} → ${(m.bytes/1e6).toFixed(1)} MB`);
}
manifest.stats.exportBytes=manifest.modules.reduce((s,m)=>s+m.bytes,0);
manifest.compression={geometry:'KHR_draco_mesh_compression',textures:'EXT_texture_webp',positionQuantizationBits:18,decoder:'/assets/draco/'};
await writeFile(dir+'manifest.json',JSON.stringify(manifest,null,2));
await writeFile('artifacts/reference-pass-05/compression.json',JSON.stringify(report,null,2));
