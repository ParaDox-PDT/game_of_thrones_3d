"""Read saved source back independently, including packed pixel data."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'artifacts/reference-pass-05'
images=[im for im in bpy.data.images if im.type=='IMAGE']
pixels={im.name:len(im.pixels) for im in images}
missing=[im.name for im in images if not im.has_data or not im.packed_file]
collections=[c.name for c in bpy.data.collections if c.name.startswith('WF5_')]
report={'passed':not missing and len(collections)==23,'blenderVersion':bpy.app.version_string,'images':len(images),'pixelCounts':pixels,'missingOrUnpacked':missing,'districtCollections':collections,'cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA'],'metresPerUnit':bpy.context.scene.unit_settings.scale_length}
(out/'source-validation.json').write_text(json.dumps(report,indent=2));assert report['passed'],report
print(json.dumps(report))
