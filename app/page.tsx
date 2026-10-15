'use client';
import dynamic from 'next/dynamic';
import { useState, useEffect, useCallback } from 'react';
import { ArrowUpRight, ArrowRight, Compass, Cube, Crosshair, X, Sun, Cloud, Moon, MapPin, NavigationArrow, DownloadSimple, Keyboard, Mountains } from '@phosphor-icons/react';
import manifest from '@/public/assets/winterfell-environment/manifest.json';
const World = dynamic(() => import('@/components/world'), { ssr: false, loading: () => <div className="loading-world">Preparing the northern frontier…</div> });
type Mode = 'orbit' | 'walk';
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
  return <main className={`explorer ${mode === 'walk' ? 'walking' : ''}`}>
    <div className="world"><World mode={mode} weather={weather} place={place} onReady={worldReady} onError={setError} /></div>
    <div className="vignette" />
    <header>
      <a className="brand" href="/" aria-label="Westeros Explorer home"><Compass size={37} weight="thin"/><span>WESTEROS<small>EXPLORER</small></span></a>
      <nav aria-label="Main navigation"><button className={!panel ? 'active' : ''} onClick={() => {setPanel(null);goTo('Fortress');}}>The atlas</button><button className={panel === 'notes' ? 'active' : ''} onClick={() => setPanel('notes')}>Field notes</button><button className={panel === 'assets' ? 'active' : ''} onClick={() => setPanel('assets')}>Asset library <ArrowUpRight size={13}/></button></nav>
      <div className="north-label"><span className="status-dot" /> A WORLD BEYOND THE WALL</div>
    </header>
    <div className="breadcrumb"><span>THE SEVEN KINGDOMS</span><span>/</span><strong>THE NORTH</strong></div>
    <aside className="location-rail" aria-label="Explore landmarks">
      <div className="eyebrow">POINTS OF INTEREST <span>04</span></div>
      {['Fortress','Gatehouse','Great Hall','Watchtower'].map((name, i) => <button key={name} className={place === name ? 'selected' : ''} onClick={() => goTo(name)}><span className="index">0{i+1}</span><span>{name}</span><ArrowUpRight size={14}/></button>)}
      <div className="map"><div className="map-n">N</div><div className="map-outline"><i/><i/><i/><i/><div className="map-keep"/><div className="map-gate"/><div className="map-player" style={{left:`${50+stats.position[0]/2.7}%`,top:`${50+stats.position[2]/2.7}%`}}/></div><span>THE WINTERFELL GROUNDS</span></div>
    </aside>
    {mode === 'orbit' ? <section className="intro">
      <div className="region"><Mountains size={19} weight="thin"/> 01 — THE NORTHERN FRONTIER</div>
      <h1>Winterfell<span>The North remembers.</span></h1>
      <p>Beyond the frost, a fortress endures. Step inside the stone walls of the North and find a world built to be explored.</p>
      <div className="intro-actions"><button className="primary" disabled={!ready || !!error} onClick={enter}>{ready ? 'Enter the courtyard' : 'Preparing the world…'} <ArrowRight size={19}/></button><button className="icon-button" title="About this environment" aria-label="About this environment" onClick={() => setPanel('notes')}><Compass size={23} weight="thin"/></button></div>
      <div className="hint"><span className="mouse-icon"/> Drag to orbit <span>·</span> Scroll to discover</div>
    </section> : <div className="walk-info"><Crosshair size={16}/><span>{stats.locked ? 'WASD to walk · Mouse to look · Shift to run · Esc to release' : 'Click the world to look around · WASD to walk'}</span><button onClick={() => goTo('Fortress')}>Return to atlas <ArrowUpRight size={14}/></button></div>}
    {mode === 'walk' && <div className="crosshair">+</div>}
    <div className="environment-controls"><span>ATMOSPHERE</span><div>{[{name:'Dawn',Icon:Sun},{name:'Overcast',Icon:Cloud},{name:'Blue hour',Icon:Moon}].map(({name,Icon}) => <button key={name} className={weather === name ? 'chosen' : ''} onClick={() => setWeather(name)} aria-pressed={weather === name}><Icon size={16}/>{name}</button>)}</div></div>
    <div className="world-meta"><span><MapPin size={12}/> 54° N / THE NORTH</span><strong>{weather === 'Dawn' ? '−06' : weather === 'Blue hour' ? '−14' : '−09'}°<small> WINTER</small></strong><span className="live-metrics">{ready ? `${stats.fps || '—'} FPS · ${stats.calls || '—'} DRAW CALLS` : 'LOADING ENVIRONMENT'}</span></div>
    <footer><span>AN INDEPENDENT WORLD STUDY <span className="footer-line"/> VOL. 001</span><button onClick={() => setPanel('assets')}><Cube size={14}/> PROCEDURALLY CRAFTED <ArrowUpRight size={12}/></button><span>SCROLL THROUGH THE SEVEN KINGDOMS <NavigationArrow size={13}/></span></footer>
    {error && <div role="alert" className="error"><strong>The world could not load.</strong><p>{error}</p><button onClick={() => window.location.reload()}>Try again</button></div>}
    {panel && <div className="panel-backdrop" onClick={() => setPanel(null)}><section className="detail-panel" role="dialog" aria-modal="true" aria-label={panel === 'assets' ? 'Asset library' : 'Field notes'} onClick={e => e.stopPropagation()}><button className="close-panel" onClick={() => setPanel(null)} aria-label="Close panel"><X size={22}/></button><div className="eyebrow">WESTEROS EXPLORER / VOL. 001</div>{panel === 'assets' ? <><h2>The craft behind<br/>the stronghold.</h2><p>Original modular architecture. Small PBR textures. An editable Blender source and portable glTF assets, built for this world.</p><div className="asset-stats"><div><strong>{((manifest.lods[0].triangles ?? 0)/1000).toFixed(1)}k</strong><span>TRIANGLES</span></div><div><strong>{manifest.renderMeshes}</strong><span>MATERIAL BATCHES</span></div><div><strong>256²</strong><span>PBR TEXTURES</span></div></div><a className="download-row" href="/assets/winterfell-environment/winterfell_fortress.glb" download><Cube size={20}/><span>Complete winter fortress<small>FULL DETAIL · GLB · 91.7 MB</small></span><DownloadSimple size={19}/></a><a className="download-row" href="/assets/winterfell-environment/winterfell_fortress_lod1.glb" download><Cube size={20}/><span>Winter fortress · LOD 1<small>WEB VIEW · GLB · 32.4 MB</small></span><DownloadSimple size={19}/></a>{Object.entries(manifest.modules as Record<string,string>).map(([name,path])=><a className="download-row compact" href={`/assets/winterfell-environment/${path}`} download key={name}><span>{name.replaceAll('_',' ')}</span><DownloadSimple size={16}/></a>)}<a className="text-link" href="/assets/winterfell-environment/manifest.json" target="_blank">Inspect the asset manifest <ArrowUpRight size={14}/></a></> : <><h2>Built to weather<br/>the long winter.</h2><p>An original interpretation of a northern medieval stronghold, inspired by Winterfell. Three defensive rings protect nine courtyards, barracks, stables, market streets, and a central keep. Snow-laden pines and distant mountains surround the town.</p><ol className="notes"><li><strong>The curtain walls</strong><span>Layered stone walls, thirty-one towers, three gatehouses, and stairs to the parapets.</span></li><li><strong>Life within</strong><span>Market stalls, carts, stored timber, stable fodder, footprints and warm braziers reveal daily work in the cold.</span></li><li><strong>Explore at your pace</strong><span>Orbit the fortress, or pass through the gate on foot. Interiors remain closed; the streets, supply routes and wall stairs are accessible.</span></li></ol><div className="controls-note"><Keyboard size={24}/><p>WASD / arrow keys to walk<br/>Mouse to look · Shift to run<br/>Esc to release the cursor</p></div><p className="fine-print">An independent fan environment with original geometry and generated textures. No extracted game models or licensed production assets.</p></>}</section></div>}
  </main>;
}
