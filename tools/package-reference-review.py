from pathlib import Path
import json,zipfile,hashlib
root=Path(__file__).resolve().parents[1];art=root/'artifacts/reference-pass-05'
files=list((root/'public/assets/winterfell-reference').glob('*'))
files+=[p for p in art.iterdir() if p.suffix in {'.blend','.png','.md','.json'} and p.name!='package-report.json']
files+=[p for p in (art/'browser').glob('*') if p.suffix in {'.png','.json'}]
files += [root/'tools/blender'/name for name in ['rebuild_reference.py','reference-layout.json','reference_architecture.py','reference_materials.py','reference_gate.py','architecture_kit.py','glb_lighting.py','build.ps1','render_reference.py','validate_reference_source.py']]
files += [root/'tools'/name for name in ['optimize-reference.mjs','validate-reference.mjs','package-reference-review.py']]
files += [root/name for name in ['components/world.tsx','app/page.tsx','app/globals.css','lib/collision.mjs','tests/reference.test.mjs','package.json','package-lock.json']]
dest=root/'artifacts/winterfell-reference-pass-05.zip'
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(files)):
        if p.is_file():z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
report={'archive':str(dest),'files':len(set(files)),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'integrity':'passed'}
(art/'package-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
