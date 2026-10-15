"""Package the winter environment, source, evidence and regeneration inputs."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parent.parent
source = root / 'artifacts/environment-pass-04'
assets = root / 'public/assets/winterfell-environment'
paths = [p for p in assets.iterdir() if p.suffix in {'.glb', '.json', '.png'}]
paths += [p for p in source.iterdir() if p.suffix in {'.blend', '.md', '.png'} or p.name.endswith('validation.json')]
paths += [p for p in (source / 'lod-review').iterdir() if p.suffix in {'.json', '.png'}]
paths += [root / 'tools/blender' / name for name in [
    'environment_town.py', 'environment-config.json', 'architecture_kit.py',
    'glb_lighting.py', 'build.ps1', 'validate_environment_source.py',
]]
paths += [root / 'tools' / name for name in [
    'validate-assets.mjs', 'validate-town-layout.mjs', 'validate-environment.mjs',
    'render-town-review.mjs', 'package-environment-review.py',
]]
paths += [root / name for name in [
    'lib/collision.mjs', 'tests/terrain.test.mjs',
    'package.json', 'package-lock.json',
    'artifacts/detail-pass-03/winterfell_fortress_detailed.blend',
]]
paths += [root / 'public/assets/winterfell-detailed' / name for name in [
    'layout.json', 'collision.json', 'manifest.json',
]]
paths += [p for p in (root / 'public/assets/winterfell').iterdir()
          if p.name.endswith(('_base.png', '_normal.png'))]
destination = root / 'artifacts/winterfell-town-environment-pass-04.zip'
for path in paths:
    assert path.is_file(), path
with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
    for path in sorted(set(paths)):
        package.write(path, path.relative_to(root).as_posix())
with zipfile.ZipFile(destination) as package:
    assert package.testzip() is None
report = {
    'archive': destination.relative_to(root).as_posix(),
    'files': len(set(paths)), 'bytes': destination.stat().st_size,
    'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'integrity': 'passed',
}
(source / 'package-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
