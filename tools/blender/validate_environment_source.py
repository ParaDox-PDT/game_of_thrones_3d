"""Read back the saved pass-04 source and verify portable textures and scenery."""
import argparse
import json
import sys
from pathlib import Path
import bpy

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True)
parser.add_argument('--pack-textures', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = Path(args.root)
source = root / 'artifacts/environment-pass-04'
bpy.ops.wm.open_mainfile(filepath=str(source / 'winterfell_fortress_winter.blend'))
images = [image for image in bpy.data.images if image.type == 'IMAGE']
if args.pack_textures:
    for image in images:
        if image.filepath:
            image.source = 'FILE'
            image.reload()
            assert len(image.pixels) > 0, image.name
            image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(source / 'winterfell_fortress_winter.blend'))
# Access pixels to force lazy images to load before checking their contents.
pixel_counts = {image.name: len(image.pixels) for image in images}
missing = [image.name for image in images if not image.has_data]
external = [image.name for image in images if image.source == 'FILE' and not image.packed_file]
lights = [obj for obj in bpy.context.scene.objects if obj.type == 'LIGHT' and obj.data.type == 'POINT']
report = {
    'passed': not missing and not external and len(lights) == 18,
    'blenderVersion': bpy.app.version_string,
    'images': len(images),
    'pixelCounts': pixel_counts,
    'missingImageData': missing,
    'unpackedFileImages': external,
    'pointLights': len(lights),
    'environmentPass': bpy.context.scene.get('environment_pass'),
    'camera': bpy.context.scene.camera.name,
}
(source / 'source-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
assert report['passed'], report
