"""Archive the review model, images, evidence and required Blender sources."""
from pathlib import Path
import hashlib
import json
import zipfile
root=Path(__file__).resolve().parent.parent
source=root/'artifacts/detail-pass-03';assets=root/'public/assets/winterfell-detailed'
paths=[p for p in assets.iterdir() if p.suffix in {'.glb','.json','.png'}]
paths += [p for p in source.iterdir() if p.suffix in {'.blend','.md','.png'} or p.name.endswith('validation.json') or p.name=='architecture-report.json']
paths += [root/'tools/blender'/name for name in ['detail_town.py','architecture_kit.py','detail-config.json','build.ps1']]
paths += [root/'tools'/name for name in ['validate-assets.mjs','validate-town-layout.mjs','validate-architecture.mjs','render-town-review.mjs']]
paths += [root/'lib/collision.mjs',root/'artifacts/layout-pass-02/winterfell_fortress.blend']
paths += [root/'public/assets/winterfell-town'/name for name in ['layout.json','collision.json']]
destination=root/'artifacts/winterfell-town-detail-pass-03.zip'
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as package:
    for path in sorted(set(paths)):package.write(path,path.relative_to(root).as_posix())
with zipfile.ZipFile(destination) as package:assert package.testzip() is None
report={'archive':destination.relative_to(root).as_posix(),'files':len(set(paths)),'bytes':destination.stat().st_size,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'integrity':'passed'}
(source/'package-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
