"""Package the intermediate assets, evidence and repeatable Blender scripts."""
from pathlib import Path
import hashlib
import json
import zipfile

root=Path(__file__).resolve().parent.parent
source=root/'artifacts/layout-pass-02'
assets=root/'public/assets/winterfell-town'
paths=[p for p in assets.iterdir() if p.suffix in {'.glb','.json','.png'}]
paths += [p for p in source.iterdir() if p.suffix in {'.blend','.md','.png'} or p.name.endswith('validation.json')]
paths += [root/'tools/blender'/name for name in ['generate.py','layout_town.py','config.json','town-config.json','build.ps1']]
paths += [root/'tools'/name for name in ['validate-assets.mjs','validate-town-layout.mjs','render-town-review.mjs']]
paths += [root/'lib/collision.mjs']
destination=root/'artifacts/winterfell-town-layout-pass-02.zip'
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as package:
    for path in sorted(paths):package.write(path,path.relative_to(root).as_posix())
with zipfile.ZipFile(destination) as package:
    assert package.testzip() is None
report={'archive':str(destination.relative_to(root)),'files':len(paths),'bytes':destination.stat().st_size,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'integrity':'passed'}
(source/'package-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
