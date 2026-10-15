'use client';
import { Component, Suspense, useEffect, useRef, type ReactNode } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, OrthographicCamera, useGLTF } from '@react-three/drei';
import { Vector3, Euler, ACESFilmicToneMapping, SRGBColorSpace, Mesh, Material } from 'three';
import collision from '@/public/assets/winterfell-reference/collision.json';
import environment from '@/public/assets/winterfell-reference/environment.json';
import manifest from '@/public/assets/winterfell-reference/manifest.json';
import { moveCapsule } from '@/lib/collision.mjs';

type Props = { mode: 'orbit' | 'walk'; weather: string; place: string; onReady: () => void; onError: (s: string) => void };
const views: Record<string, { position: [number,number,number]; target: [number,number,number] }> = {
  Fortress: { position: [0,540,420], target: [0,7,10] },
  'Map plan': { position: [0,850,20], target: [0,0,20] },
  Gatehouse: { position: [35,20,279], target: [0,18,181] },
  'Great Hall': { position: [32,29,167], target: [-13,13,111] },
};
for(const district of manifest.districts){
  const [x,y]=district.center;
  views[district.label]={position:[x+42,65,-y+65],target:[x,10,-y]};
}
class Boundary extends Component<{children: ReactNode; onError: (s: string) => void},{failed:boolean}> {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  componentDidCatch(error:Error){this.props.onError(error.message);}
  render(){return this.state.failed ? null : this.props.children;}
}
function Fortress({ onReady }: { onReady: () => void }) {
  const assets = useGLTF(manifest.modules.map(module=>module.url),'/assets/draco/');
  useEffect(() => {
    const shared=new Map<string,Material>();
    for(const asset of assets) asset.scene.traverse(object=>{
      if(!(object instanceof Mesh))return;
      object.castShadow=true;object.receiveShadow=true;
      const deduplicate=(material:Material)=>{
        if(shared.has(material.name))return shared.get(material.name)!;
        shared.set(material.name,material);return material;
      };
      object.material=Array.isArray(object.material)?object.material.map(deduplicate):deduplicate(object.material);
    });
    onReady();
  },[assets,onReady]);
  return <>{assets.map((asset,index)=><group key={manifest.modules[index].id} name={manifest.modules[index].id} position={manifest.modules[index].position as [number,number,number]}><primitive object={asset.scene}/></group>)}{manifest.torches.map((torch,index)=><pointLight key={index} position={torch.position as [number,number,number]} color={torch.color} intensity={torch.intensity} distance={torch.distance}/>)}</>;
}
function PlanCamera(){const {size}=useThree();return <OrthographicCamera makeDefault position={[0,850,20]} zoom={Math.min(size.width,size.height)/500} near={1} far={2500}/>;}
function Controller({mode,place}: Pick<Props,'mode'|'place'>) {
  const { camera, gl } = useThree();
  const keys=useRef(new Set<string>());
  const position=useRef([...collision.spawn]);
  const look=useRef(new Euler(0,0,0,'YXZ'));
  const metrics=useRef({ elapsed:0,frames:0 });
  useEffect(()=>{
    camera.near=mode==='walk' ? .1 : 2;camera.updateProjectionMatrix();
    camera.up.set(0,place==='Map plan' && mode==='orbit'?0:1,place==='Map plan' && mode==='orbit'?-1:0);
    if(mode==='walk') { position.current=[...collision.spawn]; camera.position.set(...(collision.spawn as [number,number,number])); look.current.set(0,0,0,'YXZ'); camera.rotation.copy(look.current); }
    else { const view=views[place]||views.Fortress;camera.position.set(...view.position);camera.lookAt(...view.target); }
    keys.current.clear();
  },[mode,place,camera]);
  useEffect(()=>{
    const down=(e:KeyboardEvent)=>{if(e.code==='Escape'){document.exitPointerLock?.();keys.current.clear();}if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight'].includes(e.code)){keys.current.add(e.code);if(mode==='walk')e.preventDefault();}};
    const up=(e:KeyboardEvent)=>keys.current.delete(e.code);
    const blur=()=>keys.current.clear();
    const move=(e:MouseEvent)=>{if(mode==='walk' && document.pointerLockElement===gl.domElement){look.current.y-=e.movementX*.002;look.current.x=Math.max(-1.35,Math.min(1.35,look.current.x-e.movementY*.002));camera.rotation.copy(look.current);}};
    const click=()=>{if(mode==='walk' && !document.pointerLockElement)gl.domElement.requestPointerLock();};
    window.addEventListener('keydown',down);window.addEventListener('keyup',up);window.addEventListener('blur',blur);document.addEventListener('mousemove',move);gl.domElement.addEventListener('click',click);
    return()=>{window.removeEventListener('keydown',down);window.removeEventListener('keyup',up);window.removeEventListener('blur',blur);document.removeEventListener('mousemove',move);gl.domElement.removeEventListener('click',click);};
  },[mode,camera,gl]);
  useFrame((_,dt)=>{
    if(mode==='walk') {
      const k=keys.current;const forward=Number(k.has('KeyW')||k.has('ArrowUp'))-Number(k.has('KeyS')||k.has('ArrowDown'));const right=Number(k.has('KeyD')||k.has('ArrowRight'))-Number(k.has('KeyA')||k.has('ArrowLeft'));
      const v=new Vector3(right,0,-forward).normalize().applyAxisAngle(new Vector3(0,1,0),look.current.y).multiplyScalar(Math.min(dt,.08)*(k.has('ShiftLeft')||k.has('ShiftRight')?8:4.5));
      position.current=moveCapsule(position.current,[v.x,v.z],collision);
      camera.position.set(position.current[0],position.current[1],position.current[2]);
    }
    metrics.current.elapsed+=dt;metrics.current.frames++;
    if(metrics.current.elapsed>=1){
      const detail={fps:Math.round(metrics.current.frames/metrics.current.elapsed),calls:gl.info.render.calls,triangles:gl.info.render.triangles,position:[...position.current],locked:document.pointerLockElement===gl.domElement,mode,place,cameraType:camera.type,loaded:true};
      window.dispatchEvent(new CustomEvent('world-metrics',{detail}));
      // Read-only runtime diagnostics used by automated model-loading tests.
      (window as Window & {__world?:unknown}).__world=detail;
      metrics.current={elapsed:0,frames:0};
    }
  });
  return mode==='orbit' ? <OrbitControls key={place} target={(views[place]||views.Fortress).target} minDistance={10} maxDistance={1100} minZoom={.5} maxZoom={12} maxPolarAngle={Math.PI/2.08} enableRotate={place!=='Map plan'} enableDamping dampingFactor={.08} makeDefault/> : null;
}
function Lighting({weather}:{weather:string}) {
  const dawn=weather==='Dawn',night=weather==='Blue hour';
  const sky=dawn?'#b8b7b1':night?'#263c52':environment.background;
  return <><color attach="background" args={[sky]}/><fogExp2 attach="fog" args={[sky,environment.fog.density]}/><hemisphereLight args={[environment.hemisphere.sky,environment.hemisphere.ground,night?.45:environment.hemisphere.intensity]}/><directionalLight castShadow position={dawn?[170,195,130]:[-180,320,160]} intensity={night?.12:dawn?2.1:environment.sun.intensity} color={dawn?'#ffe0ae':environment.sun.color} shadow-mapSize={[2048,2048]} shadow-camera-left={-220} shadow-camera-right={220} shadow-camera-top={220} shadow-camera-bottom={-220} shadow-camera-far={850} shadow-bias={-.0001} shadow-normalBias={.12}/></>;
}
export default function World(props:Props) {
  return <Boundary onError={props.onError}><Canvas shadows dpr={[1,1.5]} camera={{position:[0,540,420],fov:42,near:2,far:2500}} gl={{antialias:true,powerPreference:'high-performance',toneMapping:ACESFilmicToneMapping,outputColorSpace:SRGBColorSpace}} onCreated={({gl})=>{gl.setClearAlpha(1);gl.domElement.setAttribute('aria-label','Interactive 3D Winterfell fortress');gl.domElement.addEventListener('webglcontextlost',()=>props.onError('The graphics context was lost. Reload to restore the environment.'));}}>{props.mode==='orbit' && props.place==='Map plan' && <PlanCamera/>}<Lighting weather={props.weather}/><Suspense fallback={null}><Fortress onReady={props.onReady}/></Suspense><Controller mode={props.mode} place={props.place}/></Canvas></Boundary>;
}
