"""Render named review cameras from the saved editable scene."""
import bpy,sys,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'artifacts/reference-pass-05'
sys.stdout=open(out/'render.log','w',buffering=1);sys.stderr=sys.stdout
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_percentage=75
names=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if not names:names=sorted(o.name for o in bpy.data.objects if o.type=='CAMERA')
for name in names:
    print('RENDER',name,flush=True);scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
print('RENDER_DONE',flush=True)
