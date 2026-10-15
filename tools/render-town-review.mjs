// Inspect the actual exported GLB with installed Three.js in isolated Chrome.
// All requests are fulfilled from local files; the application is untouched.
import { chromium } from '@playwright/test';
import { readFile,writeFile,stat } from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {createServer} from 'node:http';
import assert from 'node:assert/strict';
import path from 'node:path';
const assetDirectory=process.argv[2] || 'public/assets/winterfell-town';
const reportDirectory=process.argv[3] || 'artifacts/layout-pass-02';
const modelFile=process.argv[4] || 'winterfell_fortress.glb';
const environment=await readFile(path.join(assetDirectory,'environment.json'),'utf8').then(JSON.parse).catch(()=>null);
const files={
  '/vendor/three.module.js':'node_modules/three/build/three.module.js',
  '/vendor/three.core.js':'node_modules/three/build/three.core.js',
  '/vendor/GLTFLoader.js':'node_modules/three/examples/jsm/loaders/GLTFLoader.js',
  '/utils/BufferGeometryUtils.js':'node_modules/three/examples/jsm/utils/BufferGeometryUtils.js',
  '/utils/SkeletonUtils.js':'node_modules/three/examples/jsm/utils/SkeletonUtils.js',
  '/scene.glb':path.join(assetDirectory,modelFile)
};
const html=`<!doctype html><html><head><style>body{margin:0;background:#8e9fa9}canvas{display:block}</style><script type="importmap">{"imports":{"three":"/vendor/three.module.js"}}</script></head><body><script type="module">
import * as THREE from 'three';
import {GLTFLoader} from '/vendor/GLTFLoader.js';
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(1600,1200);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;
document.body.append(renderer.domElement);
const settings=${JSON.stringify(environment)};
const scene=new THREE.Scene();scene.background=new THREE.Color(settings?.background || '#99aab4');
if(settings)scene.fog=new THREE.FogExp2(settings.fog.color,settings.fog.density);
// At this town-wide distance a 2 m near plane preserves depth separation
// between the snow surface and the frozen base beneath it.
const camera=new THREE.PerspectiveCamera(42,4/3,2,2500);camera.position.set(252,247,307);camera.lookAt(0,7,0);
const hemi=new THREE.HemisphereLight(settings?.hemisphere.sky || '#d8e9f3',settings?.hemisphere.ground || '#424949',settings?.hemisphere.intensity || 1.65);scene.add(hemi);
const sun=new THREE.DirectionalLight(settings?.sun.color || '#e5eff7',settings?.sun.intensity || 2.4);sun.position.set(-90,180,80);sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-170,right:170,top:170,bottom:-170,far:500});sun.shadow.bias=-.0001;sun.shadow.normalBias=.1;scene.add(sun);
new GLTFLoader().load('/scene.glb',async gltf=>{
 window.__reviewStage='loaded-model';
 let meshes=0,missingMaterials=0,pointLights=0;const materials=new Set();
 gltf.scene.traverse(o=>{if(o.isPointLight)pointLights++;if(o.isMesh){meshes++;o.castShadow=true;o.receiveShadow=true;if(!o.material)missingMaterials++;else materials.add(o.material.uuid);}});
 scene.add(gltf.scene);const bounds=new THREE.Box3().setFromObject(gltf.scene);const size=bounds.getSize(new THREE.Vector3());
 await renderer.compileAsync(scene,camera);renderer.render(scene,camera);
 window.__review={loaded:true,meshes,materials:materials.size,missingMaterials,pointLights,bounds:[size.x,size.y,size.z],drawCalls:renderer.info.render.calls,renderedTriangles:renderer.info.render.triangles};
 window.__setReviewCamera=(position,target)=>{camera.position.set(...position);camera.lookAt(...target);renderer.render(scene,camera);};
 window.__setBlueHour=()=>{sun.intensity=.12;hemi.intensity=.45;scene.background.set('#263c52');if(scene.fog)scene.fog.color.set('#263c52');renderer.render(scene,camera);};
},undefined,error=>{window.__loadError=String(error);});
</script></body></html>`;
// Stream large GLBs over ordinary HTTP instead of base64 through CDP. Large
// route.fulfill payloads can close the preview connection before model loading.
const server=createServer(async(req,res)=>{
 const pathname=new URL(req.url,'http://127.0.0.1').pathname;
 if(pathname==='/'){res.writeHead(200,{'Content-Type':'text/html'});return res.end(html);}
 const file=files[pathname];
 if(!file){res.writeHead(404);return res.end('Not found');}
 try{const info=await stat(file);res.writeHead(200,{'Content-Type':pathname.endsWith('.glb')?'model/gltf-binary':'text/javascript','Content-Length':info.size});createReadStream(file).pipe(res);}catch{res.writeHead(500);res.end('Read error');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const address=server.address();
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1600,height:1200}});
 page.on('crash',()=>console.error('REVIEW_PAGE_CRASH',modelFile));
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:'+address.port+'/');
 await page.waitForFunction(()=>window.__review?.loaded || window.__loadError,{timeout:90000});
 const report=await page.evaluate(()=>({scene:window.__review,error:window.__loadError}));
 assert.equal(report.error,undefined);assert.equal(errors.length,0,JSON.stringify(errors));
 assert.equal(report.scene.missingMaterials,0);assert.ok(report.scene.meshes>=7);
 assert.ok(report.scene.bounds[0]>=478 && report.scene.bounds[2]>=478);
 await page.screenshot({path:path.join(reportDirectory,'glb-review.png')});
 if(assetDirectory.includes('detailed')){
  await page.evaluate(()=>window.__setReviewCamera([25,13,128],[0,9,92]));
  await page.screenshot({path:path.join(reportDirectory,'glb-gatehouse.png')});
  await page.evaluate(()=>window.__setReviewCamera([-8,8,52],[-35,6,72]));
  await page.screenshot({path:path.join(reportDirectory,'glb-street.png')});
 }
 if(environment){
  assert.equal(report.scene.pointLights,18);
  await page.evaluate(()=>window.__setReviewCamera([33,12,151],[0,10,92]));
  await page.screenshot({path:path.join(reportDirectory,'glb-approach.png')});
  await page.evaluate(()=>window.__setReviewCamera([5,6,54],[-22,4.5,73]));
  await page.screenshot({path:path.join(reportDirectory,'glb-market.png')});
  await page.evaluate(()=>{window.__setReviewCamera([33,12,151],[0,10,92]);window.__setBlueHour();});
  await page.screenshot({path:path.join(reportDirectory,'glb-blue-hour.png')});
 }
 await writeFile(path.join(reportDirectory,'browser-glb-validation.json'),JSON.stringify({passed:true,modelFile,...report,errors},null,2));
 console.log(JSON.stringify(report,null,2));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
