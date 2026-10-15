'use client';
import dynamic from 'next/dynamic';
import { useState, useEffect, useCallback } from 'react';
import { ArrowUpRight, ArrowRight, Compass, Cube, Crosshair, X, Sun, Cloud, Moon, MapPin, NavigationArrow, DownloadSimple, Keyboard, Mountains } from '@phosphor-icons/react';
import manifest from '@/public/assets/winterfell-reference/manifest.json';
const World = dynamic(() => import('@/components/world'), { ssr: false, loading: () => <div className="loading-world">Preparing the northern frontier…</div> });
type Mode = 'orbit' | 'walk';
const landmarks=['Fortress','Map plan','Gatehouse',...manifest.districts.map(d=>d.label)];
export default function Home() {
  const [mode, setMode] = useState<Mode>('orbit');
  const [weather, setWeather] = useState('Overcast');
  const [place, setPlace] = useState('Fortress');
  const [panel, setPanel] = useState<'notes' | 'assets' | null>(null);
  const [ready, setReady] = useState(false);
  const worldReady = useCallback(() => setReady(true), []);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ fps: 0, calls: 0, triangles: 0, position: [0, 1.92, 125], locked: false });
  useEffect(() => {
    if (!panel) return;
    document.exitPointerLock?.();
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    dialog?.querySelector<HTMLButtonElement>('button')?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setPanel(null);
      if (e.key === 'Tab') {
        const items = Array.from(dialog?.querySelectorAll<HTMLElement>('button, a[href]') ?? []);
        const first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', key);
    return () => { document.removeEventListener('keydown', key); previous?.focus(); };
  }, [panel]);
  useEffect(() => {
    const listener = (event: Event) => setStats((event as CustomEvent).detail);
    window.addEventListener('world-metrics', listener);
    return () => window.removeEventListener('world-metrics', listener);
  }, []);
  function enter() {
    setMode('walk'); setPanel(null);
    document.querySelector('canvas')?.requestPointerLock();
  }
  function goTo(name: string) { setMode('orbit'); setPlace(name); document.exitPointerLock?.(); }
  return <main className={`explorer reference-atlas ${mode === 'walk' ? 'walking' : ''} ${place==='Map plan'?'map-view':''}`}>
    <div className="world"><World mode={mode} weather={weather} place={place} onReady={worldReady} onError={setError} /></div>
    <div className="vignette" />
    <header>
      <a className="brand" href="/" aria-label="Westeros Explorer home"><Compass size={37} weight="thin"/><span>WESTEROS<small>EXPLORER</small></span></a>
      <nav aria-label="Main navigation"><button className={!panel ? 'active' : ''} onClick={() => {setPanel(null);goTo('Fortress');}}>The atlas</button><button className={panel === 'notes' ? 'active' : ''} onClick={() => setPanel('notes')}>Field notes</button><button className={panel === 'assets' ? 'active' : ''} onClick={() => setPanel('assets')}>Asset library <ArrowUpRight size={13}/></button></nav>
      <div className="north-label"><span className="status-dot" /> A WORLD BEYOND THE WALL</div>
    </header>
    <div className="breadcrumb"><span>THE SEVEN KINGDOMS</span><span>/</span><strong>THE NORTH</strong></div>
    <aside className="location-rail" aria-label="Explore landmarks">
      <div className="eyebrow">EXPLORE THE GROUNDS <span>{landmarks.length}</span></div>
      <div className="landmark-list">{landmarks.map((name, i) => <button key={name} className={place === name ? 'selected' : ''} onClick={() => goTo(name)}><span className="index">{String(i+1).padStart(2,'0')}</span><span>{name}</span><ArrowUpRight size={14}/></button>)}</div>
      <div className="map"><div className="map-n">N</div><svg viewBox="-225 -205 450 550" role="img" aria-label="Fortress plan with current walking position"><polygon points={manifest.layout.outerWall.map(([x,y])=>`${x},${-y}`).join(' ')} fill="#9fb4c212" stroke="#a4bcc9" strokeWidth="3"/><polygon points={manifest.layout.keepWall.map(([x,y])=>`${x},${-y}`).join(' ')} fill="#9fb4c224" stroke="#a4bcc9" strokeWidth="2"/>{manifest.layout.roads.map((road,i)=><polyline key={i} points={road.points.map(([x,y])=>`${x},${-y}`).join(' ')} fill="none" stroke="#a4bcc950" strokeWidth={road.width/2}/>)}{manifest.districts.map(d=><circle key={d.id} cx={d.center[0]} cy={-d.center[1]} r={place===d.label?9:5} fill={place===d.label?'#f4ddd0':'#b5cbd4'}/>)}{mode==='walk'&&<circle cx={stats.position[0]} cy={stats.position[2]} r="7" fill="#fff"/>}</svg><span>THE WINTERFELL GROUNDS</span></div>
    </aside>
    {mode === 'orbit' ? <section className="intro">
      <div className="region"><Mountains size={19} weight="thin"/> 01 — THE NORTHERN FRONTIER</div>
      <h1>Winterfell<span>The North remembers.</span></h1>
      <p>{manifest.districts.find(d=>d.label===place)?.description || 'Follow the river to the southern gate. Explore eleven districts, the ancient godswood and the fortified heart of the North.'}</p>
      <div className="intro-actions"><button className="primary" disabled={!ready || !!error} onClick={enter}>{ready ? 'Enter the courtyard' : 'Preparing the world…'} <ArrowRight size={19}/></button><button className="icon-button" title="About this environment" aria-label="About this environment" onClick={() => setPanel('notes')}><Compass size={23} weight="thin"/></button></div>
      <div className="hint"><span className="mouse-icon"/> Drag to orbit <span>·</span> Scroll to discover</div>
    </section> : <div className="walk-info"><Crosshair size={16}/><span>{stats.locked ? 'WASD to walk · Mouse to look · Shift to run · Esc to release' : 'Click the world to look around · WASD to walk'}</span><button onClick={() => goTo('Fortress')}>Return to atlas <ArrowUpRight size={14}/></button></div>}
    {mode === 'walk' && <div className="crosshair">+</div>}
    <div className="environment-controls"><span>ATMOSPHERE</span><div>{[{name:'Dawn',Icon:Sun},{name:'Overcast',Icon:Cloud},{name:'Blue hour',Icon:Moon}].map(({name,Icon}) => <button key={name} className={weather === name ? 'chosen' : ''} onClick={() => setWeather(name)} aria-pressed={weather === name}><Icon size={16}/>{name}</button>)}</div></div>
    <div className="world-meta"><span><MapPin size={12}/> 54° N / THE NORTH</span><strong>{weather === 'Dawn' ? '−06' : weather === 'Blue hour' ? '−14' : '−09'}°<small> WINTER</small></strong><span className="live-metrics">{ready ? `${stats.fps || '—'} FPS · ${stats.calls || '—'} DRAW CALLS` : 'LOADING ENVIRONMENT'}</span></div>
    <footer><span>AN INDEPENDENT WORLD STUDY <span className="footer-line"/> VOL. 001</span><button onClick={() => setPanel('assets')}><Cube size={14}/> PROCEDURALLY CRAFTED <ArrowUpRight size={12}/></button><span>SCROLL THROUGH THE SEVEN KINGDOMS <NavigationArrow size={13}/></span></footer>
    {error && <div role="alert" className="error"><strong>The world could not load.</strong><p>{error}</p><button onClick={() => window.location.reload()}>Try again</button></div>}
    {panel && <div className="panel-backdrop" onClick={() => setPanel(null)}><section className="detail-panel" role="dialog" aria-modal="true" aria-label={panel === 'assets' ? 'Asset library' : 'Field notes'} onClick={e => e.stopPropagation()}><button className="close-panel" onClick={() => setPanel(null)} aria-label="Close panel"><X size={22}/></button><div className="eyebrow">WESTEROS EXPLORER / VOL. 001</div>{panel === 'assets' ? <><h2>The craft behind<br/>the stronghold.</h2><p>Independently placed district modules with embedded PBR textures, normal maps and roughness maps. An editable Blender source and portable glTF assets, built for this world.</p><div className="asset-stats"><div><strong>{(manifest.stats.triangles/1000).toFixed(0)}k</strong><span>TRIANGLES</span></div><div><strong>{manifest.modules.length}</strong><span>DISTRICT MODULES</span></div><div><strong>512²</strong><span>PBR TEXTURES</span></div></div>{manifest.modules.map(module=><a className="download-row compact" href={module.url} download key={module.id}><span>{module.id.replaceAll('_',' ')}<small>GLB · {(module.bytes/1e6).toFixed(1)} MB · LOCAL ORIGIN</small></span><DownloadSimple size={16}/></a>)}<a className="text-link" href="/assets/winterfell-reference/manifest.json" target="_blank">Inspect the asset manifest <ArrowUpRight size={14}/></a></> : <><h2>Built to weather<br/>the long winter.</h2><p>An original interpretation of a northern medieval stronghold, inspired by Winterfell. Rebuilt from the supplied illustrated plan: irregular curtain walls surround a central keep, an eastern godswood, northern service yards and southern residential courts. A river and arched bridge define the western and southern approaches.</p><ol className="notes"><li><strong>The curtain walls</strong><span>An irregular outer perimeter and inner ward, twin-drum gatehouses, battered tower bases, string courses and accessible wall stairs.</span></li><li><strong>Life within</strong><span>Training targets, water troughs, carts, firewood, garden beds and working courtyards give each district its own purpose.</span></li><li><strong>Explore at your pace</strong><span>Orbit the fortress, or pass through the gate on foot. Interiors remain closed; the streets, supply routes and wall stairs are accessible.</span></li></ol><div className="controls-note"><Keyboard size={24}/><p>WASD / arrow keys to walk<br/>Mouse to look · Shift to run<br/>Esc to release the cursor</p></div><p className="fine-print">An independent fan environment with original geometry and generated textures. No extracted game models or licensed production assets.</p></>}</section></div>}
  </main>;
}
