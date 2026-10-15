"""Deterministic, self-contained northern fortress. Blender 4.5 LTS / 5.2.
Run through build.ps1. Metres, Blender Z-up; glTF exports Y-up.
Original procedural architecture: no third-party/game assets.
"""
import argparse
import array
import json
import math
import random
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

args = argparse.ArgumentParser()
args.add_argument('--root', required=True)
args.add_argument('--skip-preview', action='store_true')
args.add_argument('--layout', choices=['prototype','town'], default='prototype')
opt = args.parse_args(sys.argv[sys.argv.index('--') + 1:])
ROOT = Path(opt.root)
OUT = ROOT / ('public/assets/winterfell-town' if opt.layout == 'town' else 'public/assets/winterfell')
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / ('artifacts/layout-pass-02' if opt.layout == 'town' else 'artifacts')
SOURCE.mkdir(parents=True, exist_ok=True)
sys.stdout = open(SOURCE / 'generation.log', 'w', buffering=1, encoding='utf-8')
sys.stderr = sys.stdout
print('Blender', bpy.app.version_string, flush=True)
CFG = json.loads((Path(__file__).parent / 'config.json').read_text())
if opt.layout == 'town':
    CFG.update(json.loads((Path(__file__).parent / 'town-config.json').read_text()))
layout_info = {}
random.seed(CFG['seed'])
started = time.time()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
visual = bpy.data.collections.new('WF_Architecture_LOD0')
scene.collection.children.link(visual)
collision_collection = bpy.data.collections.new('WF_Collision_Proxies')
scene.collection.children.link(collision_collection)
colliders = []
surfaces = []
library = {}
materials = {}


def texture(name, base, kind):
    """Small seamless base/normal maps: glTF-compatible image nodes only."""
    if opt.layout == 'town' and CFG['texture_size'] == 256:
        import shutil
        previous = ROOT / 'public/assets/winterfell'
        base_path, normal_path = previous/(name+'_base.png'), previous/(name+'_normal.png')
        if base_path.exists() and normal_path.exists():
            for path in [base_path, normal_path]: shutil.copy2(path, OUT/path.name)
            base_image=bpy.data.images.load(str(OUT/base_path.name))
            normal_image=bpy.data.images.load(str(OUT/normal_path.name))
            normal_image.colorspace_settings.name='Non-Color'
            return base_image, normal_image
    n = CFG['texture_size']
    heights = []
    pixels = array.array('f')
    rng = random.Random(CFG['seed'] + sum(map(ord, name)))
    for y in range(n):
        for x in range(n):
            grain = rng.random() * .13
            if kind == 'stone':
                row = y // 32
                mortar = y % 32 < 2 or (x + (row % 2) * 32) % 64 < 2
                h = .16 if mortar else .65 + grain + .07 * math.sin(x * .25) * math.sin(y * .18)
            elif kind == 'wood':
                h = .5 + .15 * math.sin(x * .3 + math.sin(y * math.tau / n) * 2) + grain
                if x % 64 < 2: h = .18
            elif kind == 'roof':
                h = .4 + (y % 32) / 90 + grain
                if y % 32 < 2 or (x + (y // 32 % 2) * 16) % 32 < 2: h = .2
            else:
                h = .6 + grain + .08 * math.sin(x * math.tau / n * 5) * math.cos(y * math.tau / n * 4)
            heights.append(h)
            value = .55 + h * .6
            pixels.extend((min(1, base[0] * value), min(1, base[1] * value), min(1, base[2] * value), 1))
    image = bpy.data.images.new(name + '_BaseColor', n, n)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(OUT / (name + '_base.png'))
    image.file_format = 'PNG'
    image.save()
    normal = array.array('f')
    for y in range(n):
        for x in range(n):
            dx = heights[y*n + (x+1)%n] - heights[y*n + (x-1)%n]
            dy = heights[((y+1)%n)*n+x] - heights[((y-1)%n)*n+x]
            v = Vector((-dx*1.1, -dy*1.1, 1)).normalized()
            normal.extend((v.x*.5+.5, v.y*.5+.5, v.z*.5+.5, 1))
    nm = bpy.data.images.new(name + '_Normal', n, n)
    nm.colorspace_settings.name = 'Non-Color'
    nm.pixels.foreach_set(normal)
    nm.filepath_raw = str(OUT / (name + '_normal.png'))
    nm.file_format = 'PNG'
    nm.save()
    return image, nm


def material(name, color, roughness=.85, kind=None, metallic=0):
    mat = bpy.data.materials.new('WF_' + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if kind:
        base, normal = texture(name, color, kind)
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = base
        mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        texn = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texn.image = normal
        normal_node = mat.node_tree.nodes.new('ShaderNodeNormalMap')
        normal_node.inputs['Strength'].default_value = .55
        mat.node_tree.links.new(texn.outputs['Color'], normal_node.inputs['Color'])
        mat.node_tree.links.new(normal_node.outputs['Normal'], bsdf.inputs['Normal'])
    materials[name] = mat
    return mat


stone = material('AgedStone', (.34,.38,.40), kind='stone')
trim = material('CutStone', (.47,.49,.49), kind='stone')
wood = material('WeatheredWood', (.23,.16,.105), kind='wood')
metal = material('DarkIron', (.09,.115,.13), .48, metallic=.75)
snow = material('Snow', (.82,.89,.92), .96, 'snow')
ground = material('FrozenGround', (.25,.30,.31), .96, 'ground')
roof_mat = material('SlateRoof', (.13,.19,.23), .87, 'roof')
dirt = material('Gravel', (.31,.285,.23), .98, 'ground')
cloth = material('StarkBanner', (.24,.29,.30))
window = material('WindowRecess', (.035,.055,.06), .8)
ember = material('Ember', (.9,.31,.055), .5)
bsdf = ember.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Emission Color'].default_value = (.9,.17,.018,1)
bsdf.inputs['Emission Strength'].default_value = 2


def relocate(obj, name, mat):
    obj.name = 'WF_' + name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    visual.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def box(name, loc, size, mat, bevel=0, rotation=0, collide=False):
    key = ('box', tuple(round(s,4) for s in size), mat.name, bevel)
    if key not in library:
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.object
        obj.scale = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel:
            mod = obj.modifiers.new('Soft stone edges', 'BEVEL')
            mod.width = bevel
            mod.segments = 1
            bpy.ops.object.modifier_apply(modifier=mod.name)
        # UV scale in metres, repeated every ~3 metres.
        for p in obj.data.polygons:
            axis = max(range(3), key=lambda i: abs(p.normal[i]))
            axes = [i for i in range(3) if i != axis]
            for li in p.loop_indices:
                v = obj.data.vertices[obj.data.loops[li].vertex_index].co
                obj.data.uv_layers.active.data[li].uv = (v[axes[0]]/3, v[axes[1]]/3)
        relocate(obj, name, mat)
        library[key] = obj.data
    else:
        obj = bpy.data.objects.new('WF_' + name, library[key])
        visual.objects.link(obj)
    obj.location = loc
    obj.rotation_euler.z = rotation
    if collide:
        if rotation: raise ValueError('Axis aligned box collider expected')
        add_box_collider(name, loc, size)
    return obj


def add_box_collider(name, loc, size):
    colliders.append({'name':name,'type':'box','center':[loc[0],loc[2],-loc[1]],'size':[size[0],size[2],size[1]]})


def cylinder(name, loc, radius, depth, mat, vertices=20, collide=False):
    key = ('cylinder',radius,depth,mat.name,vertices)
    if key not in library:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
        obj = relocate(bpy.context.object, name, mat)
        for p in obj.data.polygons:
            if abs(p.normal.z) < .5:
                for li in p.loop_indices:
                    uv = obj.data.uv_layers.active.data[li].uv
                    uv.x *= math.tau * radius / 3
                    uv.y *= depth / 3
        library[key] = obj.data
    else:
        obj = bpy.data.objects.new('WF_'+name,library[key]); visual.objects.link(obj)
    obj.location = loc
    if collide: colliders.append({'name':name,'type':'cylinder','center':[loc[0],loc[2],-loc[1]],'radius':radius,'height':depth})
    return obj


def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new('WF_'+name, data)
    visual.objects.link(obj); data.materials.append(mat)
    # UVs for roofs and terrain, no Blender-only generated coordinates.
    uv = data.uv_layers.new(name='UVMap')
    for p in data.polygons:
        for li in p.loop_indices:
            v=data.vertices[data.loops[li].vertex_index].co
            uv.data[li].uv=(v.x/3,(v.y+v.z)/3)
    return obj


def roof(name, x,y,z,w,d,h):
    verts=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),(x,y-d/2,z+h),(x,y+d/2,z+h)]
    faces=[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4),(0,3,2,1)]
    mesh(name,verts,faces,roof_mat)
    # Snow caps only on the upper slopes, ridge remains a real silhouette.
    sv=[(vx,vy,vz+.09) for vx,vy,vz in verts]
    mesh(name+'_Snow',sv,[(0,4,5,3),(1,2,5,4)],snow)
    box(name+'_Ridge',(x,y,z+h+.13),(.24,d+.35,.20),trim,.04)


def crenels(x,y,z,span,side='x', step=2.1):
    for i in range(round(span/step)+1):
        offset=-span/2+i*span/max(1,round(span/step))
        loc=(x+offset if side=='x' else x,y if side=='x' else y+offset,z)
        size=(1.15,1.2,1.25)
        box('Merlon',loc,size,trim,.055)
        box('MerlonSnow',(loc[0],loc[1],z+.66),(1.19,1.24,.12),snow,.03)


def wall_run(name,x,y,length,side='x', height=None):
    height=height or CFG['wall_height']
    count=math.ceil(length/6); segment=length/count
    for i in range(count):
        v=-length/2+(i+.5)*segment
        cx=x+v if side=='x' else x; cy=y if side=='x' else y+v
        size=(segment,2.3,height) if side=='x' else (2.3,segment,height)
        box(name+'_Module',(cx,cy,height/2),size,stone,.08,collide=True)
        box('WallPlinth',(cx,cy,.55),(size[0]+.25,size[1]+.25,1.1),trim,.04)
        box('WallCornice',(cx,cy,height-.25),(size[0]+.3,size[1]+.3,.38),trim,.04)
        box('WallWalkSnow',(cx,cy,height+.035),(size[0],size[1],.08),snow)
        surfaces.append({'name':'WallWalk','min':[cx-size[0]/2,-cy-size[1]/2],'max':[cx+size[0]/2,-cy+size[1]/2],'height':height+.08})
        # Pilaster provides scale and a readable modular rhythm.
        box('Buttress',(cx,cy,3),(1.0,3.2,6) if side=='x' else (3.2,1.0,6),stone,.05)
    crenels(x,y,height+.6,length,side)


def tower(name,x,y,r=4,h=13,cone=False):
    cylinder(name+'_Foot',(x,y,.55),r+.45,1.1,trim,24)
    cylinder(name+'_Shaft',(x,y,h/2),r,h,stone,24,True)
    for z in [h*.35,h*.7,h-.7]: cylinder('TowerBelt',(x,y,z),r+.12,.25,trim,24)
    cylinder('TowerCrown',(x,y,h-.05),r+.42,.65,trim,24)
    cylinder('TowerSnow',(x,y,h+.30),r+.24,.10,snow,24)
    for i in range(12):
        a=i*math.tau/12
        ob=box('TowerMerlon',(x+math.cos(a)*(r+.15),y+math.sin(a)*(r+.15),h+.85),(1.15,1.05,1.25),trim,.045,rotation=a)
        box('TowerMerlonSnow',(ob.location.x,ob.location.y,h+1.51),(1.2,1.1,.12),snow,.025,rotation=a)
    for i in range(8):
        a=i*math.tau/8
        # Dark inset panels framed by a small projecting lintel.
        o=box('ArrowSlit',(x+math.cos(a)*(r+.018),y+math.sin(a)*(r+.018),h*.65),(.20,.045,1.5),window,rotation=a-math.pi/2)
    if cone:
        bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=r+.65,radius2=.12,depth=5,location=(x,y,h+3))
        relocate(bpy.context.object,name+'_Spire',roof_mat)
        cylinder('SpireFinial',(x,y,h+5.7),.12,1,metal,8)


if opt.layout == 'prototype':
    # Terrain disc-like platform, distant original low-poly peaks, and snow drifts.
    box('FrozenTerrain',(0,0,-.65),(CFG['terrain_size'],CFG['terrain_size'],1.2),ground)
    box('SnowField',(0,0,-.07),(CFG['terrain_size']-1,CFG['terrain_size']-1,.12),snow)
    box('Courtyard',(0,0,-.04),(69,57,.12),dirt)
    box('SouthRoad',(0,-57,.025),(7,55,.10),dirt)
    box('KeepRoad',(0,0,.035),(6.5,60,.10),trim)
    box('CrossPath',(0,-2,.04),(65,4,.12),trim)
    for i in range(130):
        x=random.uniform(-100,100); y=random.uniform(-100,100)
        if abs(x)<41 and abs(y)<42: continue
        r=random.uniform(1.5,5)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,0))
        ob=relocate(bpy.context.object,'SnowDrift',snow);ob.scale=(r,r*.7,random.uniform(.15,.6))
    for i in range(21):
        a=i*math.tau/21; radius=random.uniform(95,110)
        x=math.cos(a)*radius;y=math.sin(a)*radius
        h=random.uniform(16,36);r=random.uniform(14,22)
        # Irregular concentric rings share the same upper slope, avoiding intersecting
        # cone caps and striped silhouettes. Deterministic asymmetry reads as rock.
        count=11; angles=[j*math.tau/count for j in range(count)]
        rings=[]
        for factor,z in [(1,-.4),(.58,h*.4),(.3,h*.72)]:
            rings.extend([(x+math.cos(a)*r*factor*random.uniform(.8,1.2),y+math.sin(a)*r*factor*random.uniform(.8,1.2),z+random.uniform(-1,1)) for a in angles])
        rings.append((x+r*.1,y-r*.08,h))
        faces=[]
        for ring in range(2):
            for j in range(count):faces.append((ring*count+j,ring*count+(j+1)%count,(ring+1)*count+(j+1)%count,(ring+1)*count+j))
        faces += [(2*count+j,2*count+(j+1)%count,3*count) for j in range(count)]
        mesh('NorthernPeak',rings,faces,stone)
        caps=[(vx,vy,vz+.045) for vx,vy,vz in rings[2*count:]]
        mesh('PeakSnow',caps,[(j,(j+1)%count,count) for j in range(count)],snow)

    # 76 x 64 m curtain wall. A 7 m wide, 6.5 m high south passage stays open.
    wall_run('WestCurtain',-38,0,64,'y')
    wall_run('EastCurtain',38,0,64,'y')
    wall_run('NorthCurtain',0,32,76)
    wall_run('SouthWestCurtain',-23,-32,30)
    wall_run('SouthEastCurtain',23,-32,30)
    for x in [-38,38]:
        for y in [-32,32]: tower('CornerTower',x,y)
    tower('WestWatch',-38,5,3.7,16,True)
    tower('EastWatch',38,5,3.7,16,True)
    tower('GateWest',-7.6,-32,3.5,12)
    tower('GateEast',7.6,-32,3.5,12)
    box('GatehouseBridge',(0,-32,9),(8,6,5),stone,.07,collide=True)
    crenels(0,-35,12.1,8)
    crenels(0,-29,12.1,8)
    # Dressed voussoir arch over the open portal.
    for i in range(13):
        a=i*math.pi/12
        x=3.7*math.cos(a);z=3.8+2.6*math.sin(a)
        box('GateArchStone',(x,-35.1,z),(.68,.55,1.0),trim,.025,rotation=0)
    # Open gate leaves, entirely outside central traversal corridor.
    for sign in [-1,1]:
        x=sign*3.85
        box('OpenOakGate',(x,-30.0,2.55),(.30,4.2,5.1),wood,.03,collide=True)
        for z in [.8,2.5,4.3]: box('GateIronStrap',(x+sign*.17,-30,z),(.08,4.25,.16),metal)
        for yy in [-31.8,-30.9,-30,-29.1,-28.2]:
            for zz in [.8,2.5,4.3]: cylinder('GateRivet',(x+sign*.22,yy,zz),.055,.05,metal,8)

    # Great Hall and main keep in the northern half, with separate flanking towers.
    box('GreatHall',(0,16,6.5),(18,20,13),stone,.10,collide=True)
    box('HallFoundation',(0,16,.65),(19.2,21.2,1.3),trim,.08)
    roof('GreatHallRoof',0,16,13.1,20.5,22,7)
    box('Keep',(0,26,11),(13,9,22),stone,.10,collide=True)
    crenels(0,21.5,22.5,13)
    crenels(0,30.5,22.5,13)
    crenels(-6.5,26,22.5,9,'y')
    crenels(6.5,26,22.5,9,'y')
    box('KeepTopSnow',(0,26,22.03),(13,9,.1),snow)
    tower('HallWestTower',-11,21,3,19,True)
    tower('HallEastTower',11,21,3,19,True)
    # Keep door is decorative: courtyard, gate, buildings and exterior stairs are explorable.
    box('HallDoor',(0,5.93,2.1),(3.0,.2,4.2),wood,.03)
    box('DoorLintel',(0,5.7,4.4),(4.0,.6,.6),trim,.04)
    for x in [-2,2]:box('DoorColumn',(x,5.7,2),(.65,.65,4),trim,.04)
    for x in [-6,-3,3,6]:
        for z in [6.3,10]:
            box('HallWindow',(x,5.94,z),(.75,.08,1.8),window)
            box('WindowSill',(x,5.72,z-.95),(1.1,.45,.18),trim,.025)
    for side in [-1,1]:
        for y in [10,15,20]:
            box('HallButtress',(side*9.3,y,4),(.8,1.1,8),trim,.06)
            box('HallSideWindow',(side*9.02,y+1.8,9),(.08,.8,2),window)
    # Stone stairs to east wall walk: 0.24 m steps, each represented as a walkable surface.
    for i in range(32):
        z=(i+1)*.25;y=-23+i*.7
        box('WallStair',(34,y,z/2),(3,.73,z),stone,.02)
        surfaces.append({'name':'WallStair','min':[32.5,-y-.365],'max':[35.5,-y+.365],'height':z})
        box('StairParapet',(35.8,y,z+.6),(.4,.73,1.2),stone,.03,collide=True)
    box('StairLanding',(36,-.35,7.85),(6,1.2,.45),stone,.03)
    surfaces.append({'name':'StairLanding','min':[33,-.25],'max':[39,.95],'height':8.08})


    def house(name,x,y,w,d,h=4.5):
        box(name+'_Base',(x,y,.45),(w+.4,d+.4,.9),stone,.04)
        box(name+'_Frame',(x,y,h/2+.4),(w,d,h),wood,.05,collide=True)
        for sx in [-1,1]:
            box('CornerPost',(x+sx*(w/2-.15),y-d/2-.04,h/2+.5),(.25,.25,h+.2),metal)
        for z in [1.1,h]:box('TimberBeam',(x,y-d/2-.07,z),(w,.22,.22),wood,.02)
        roof(name+'_Roof',x,y,h+.45,w+1,d+1,h*.6)
        box('CottageDoor',(x,y-d/2-.03,1.5),(1.4,.12,2.5),wood,.015)
        box('CottageWindow',(x+w*.28,y-d/2-.08,2.7),(.8,.07,.9),window)
        box('Chimney',(x-w*.25,y+1,h+2),(1,1.2,3),stone,.04)
        box('ChimneySnow',(x-w*.25,y+1,h+3.55),(1.2,1.4,.15),snow,.03)


    house('Smithy',-24,7,11,12)
    house('Stable',24,12,11,17,4)
    house('Barracks',-24,-15,12,13,5)
    house('Storehouse',23,-17,10,10,4)
    for x in [-32,-19,18,31]:
        for y in [-25,-21,-17]:
            box('FencePost',(x,y,.85),(.22,.22,1.7),wood,.015)
    for y in [-25,-17]:
        for x in [-25.5,24.5]:
            for z in [.6,1.3]:box('FenceRail',(x,y,z),(13,.14,.14),wood)
            add_box_collider('Fence',(x,y,.85),(13,.25,1.7))
    # Well, carts, hay, crates, barrels, fire baskets, shields, banners.
    cylinder('WellStone',(13,-3,.8),1.6,1.6,stone,16,True)
    cylinder('WellWater',(13,-3,1.62),1.15,.03,window,16)
    for x in [11.5,14.5]:box('WellPost',(x,-3,2.4),(.2,.2,3.2),wood)
    roof('WellRoof',13,-3,4.0,4,3,1.3)
    for i in range(22):
        x=random.choice([-1,1])*random.uniform(16,30);y=random.uniform(-9,0)
        if i%2:
            cylinder('Barrel',(x,y,.7),.48,1.4,wood,12,True)
            for z in [.2,1.1]:cylinder('BarrelHoop',(x,y,z),.50,.10,metal,12)
        else:
            box('Crate',(x,y,.6),(1.15,1.1,1.2),wood,.025,collide=True)
            for z in [.15,1.05]:box('CrateBrace',(x,y-.57,z),(1.18,.1,.12),trim)
    for x,y in [(-10,-26),(10,-26),(-5,3),(5,3)]:
        cylinder('BrazierFoot',(x,y,.3),.5,.6,metal,10,True)
        cylinder('BrazierBasket',(x,y,.85),.65,.55,metal,10)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.45,location=(x,y,1.2))
        ob=relocate(bpy.context.object,'Fire',ember);ob.scale=(1,1,1.6)
        for i in range(8):
            a=i*math.tau/8;box('BrazierRib',(x+math.cos(a)*.6,y+math.sin(a)*.6,1.1),(.05,.05,.75),metal)
    for x in [-5.3,5.3]:
        cylinder('BannerPole',(x,-35.5,10),.06,6,metal,8)
        verts=[(x,-35.6,11.8),(x+1.5,-35.6,11.8),(x+1.4,-35.7,8.4),(x+.75,-35.55,8),(x,-35.6,8.4)]
        mesh('GateBanner',verts,[(0,1,2,3,4)],cloth)
        for z in [9,9.4,9.8,10.2]:box('BannerSigil',(x+.7,-35.72,z),(.42,.025,.10),trim)
    for x in [-15,15]:
        box('CartBed',(x,-11,1.0),(2.1,3.5,.25),wood,.03,collide=True)
        for sx in [-1,1]:
            box('CartSide',(x+sx,-11,1.45),(.12,3.5,.8),wood)
            for yy in [-12,-10]:
                ob=cylinder('CartWheel',(x+sx*1.2,yy,.65),.65,.14,wood,12)
                ob.rotation_euler.y=math.pi/2
        box('CartHandle',(x,-13.6,.8),(.2,2,.2),wood)
    # Sparse pine forest, shared low-poly geometry.
    for i in range(75):
        x=random.uniform(-85,85);y=random.uniform(-85,85)
        if abs(x)<48 and abs(y)<46 or abs(x)<7 and y<0: continue
        h=random.uniform(5,10)
        cylinder('PineTrunk',(x,y,h*.35),.18,h*.7,wood,6)
        for k in range(3):
            bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=h*(.23-k*.045),radius2=0,depth=h*.45,location=(x,y,h*(.44+k*.19)))
            relocate(bpy.context.object,'SnowPine',snow)

else:
    sys.path.insert(0, str(Path(__file__).parent))
    from layout_town import build
    build(globals())

# Exact browser collision data and explicit proxy .blend collection.
for entry in colliders:
    x,z,ny=entry['center']; loc=(x,-ny,z)
    if entry['type']=='box':
        sx,sz,sy=entry['size'];bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        ob=bpy.context.object;ob.scale=(sx,sy,sz)
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=entry['radius'],depth=entry['height'],location=loc)
        ob=bpy.context.object
    ob.name='COL_'+entry['name']
    for c in list(ob.users_collection):c.objects.unlink(ob)
    collision_collection.objects.link(ob)
    ob.display_type='WIRE';ob.hide_render=True
    ob['collision_proxy']=True
collision_collection.hide_viewport=True
collision_collection.hide_render=True
collision_data={'schemaVersion':1,'units':'metres','coordinateSystem':'right-handed Y-up; Blender (x,y,z) -> glTF (x,z,-y)','capsule':{'radius':.36,'height':1.8,'stepHeight':.30},'spawn':[0,1.8,48],'gateClearance':{'width':7.0,'height':6.5},'colliders':colliders,'walkableSurfaces':surfaces,'floor':0.12,'bounds':[-108,108,-108,108]}
if layout_info:
    collision_data.update(spawn=layout_info['spawn'], bounds=layout_info['bounds'], gateClearance={'width':10,'height':8})
(OUT/'collision.json').write_text(json.dumps(collision_data,indent=2))

# Camera and lightweight lighting, one shadowed sun, no Cycles.
world=bpy.data.worlds.new('NorthernOvercast');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.36,.44,.52,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='SUN',location=(30,-40,60))
sun=bpy.context.object;sun.name='NorthernSun';sun.data.energy=2.4;sun.rotation_euler=(.45,-.55,-.55);sun.data.angle=.18
bpy.ops.object.light_add(type='AREA',location=(-35,-30,50))
fill=bpy.context.object;fill.data.energy=1700;fill.data.shape='DISK';fill.data.size=50
def camera_at(name,loc,target,lens=42):
    bpy.ops.object.camera_add(location=loc)
    cam=bpy.context.object;cam.name=name
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    return cam
camera=camera_at('FortressOverview',layout_info.get('overviewCamera',(92,-116,87)),layout_info.get('overviewTarget',(0,0,5)),44)
if layout_info:
    plan_camera=camera_at('TownLayoutPlan',(0,-.001,350),(0,0,0),44)
    plan_camera.data.type='ORTHO';plan_camera.data.ortho_scale=294
    reverse_camera=camera_at('TownNorthReview',(-225,260,205),(0,8,8),44)
scene.camera=camera
engine_keys=bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
scene.render.engine='BLENDER_EEVEE' if bpy.app.version >= (5,0,0) else 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x,scene.render.resolution_y=CFG['preview_resolution']
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.render.threads_mode='FIXED';scene.render.threads=4
if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=CFG['preview_samples']
for area in (bpy.context.screen.areas if bpy.context.screen else []):
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.type='MATERIAL'
# Editable source retains linked modular meshes; pack all small textures.
for image in bpy.data.images:
    if image.source=='FILE' and image.has_data:image.pack()
scene['pipeline_seed']=CFG['seed'];scene['asset_license']='Original generated geometry; project-owned'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'winterfell_fortress.blend'))

# Export optimized meshes: bake world transforms and batch geometry per material.
# Editable .blend stays modular; temporary batches keep browser draw calls bounded.
export_collection=bpy.data.collections.new('WF_Export_Batches');scene.collection.children.link(export_collection)
def batch_objects(objects, prefix):
    buckets={}
    for obj in objects:
        if obj.type!='MESH':continue
        for poly in obj.data.polygons:
            mat=obj.data.materials[poly.material_index]
            bucket=buckets.setdefault(mat.name,{'v':[],'f':[],'uv':[],'mat':mat})
            offset=len(bucket['v']);indices=[]
            for li in poly.loop_indices:
                co=obj.matrix_world@obj.data.vertices[obj.data.loops[li].vertex_index].co
                bucket['v'].append(tuple(co));indices.append(offset);offset+=1
                uv=obj.data.uv_layers.active.data[li].uv if obj.data.uv_layers.active else (0,0)
                bucket['uv'].append(tuple(uv))
            bucket['f'].append(indices)
    result=[]
    for name,b in buckets.items():
        data=bpy.data.meshes.new(prefix+name);data.from_pydata(b['v'],[],b['f']);data.materials.append(b['mat']);data.update()
        uv=data.uv_layers.new(name='UVMap')
        for p in data.polygons:
            for li in p.loop_indices:uv.data[li].uv=b['uv'][data.loops[li].vertex_index]
        obj=bpy.data.objects.new(prefix+name,data);export_collection.objects.link(obj);result.append(obj)
    return result
def export_glb(path,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        if not any(mod.type=='TRIANGULATE' for mod in obj.modifiers):obj.modifiers.new('ExportTriangulate','TRIANGULATE')
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
visual_objects=list(visual.all_objects)
batched=batch_objects(visual_objects,'ENV_')
export_glb(OUT/'winterfell_fortress.glb',batched)
# Low-detail future LOD: silhouette and material structure with decimated surfaces.
for ob in batched:
    mod=ob.modifiers.new('LOD1_Decimate','DECIMATE');mod.ratio=.45
export_glb(OUT/'winterfell_fortress_lod1.glb',batched)
for ob in batched:
    for mod in list(ob.modifiers):ob.modifiers.remove(mod)
# Reusable local-origin modules, separate from environment.
modules={}
for label,match in [('wall_module','WestCurtain_Module'),('tower_shaft','CornerTower_Shaft'),('barrel','Barrel'),('crate','Crate')]:
    src=next((o for o in visual_objects if o.name=='WF_'+match), None)
    if src is None: continue
    clone=bpy.data.objects.new('ASSET_'+label,src.data);export_collection.objects.link(clone)
    clone.location=(0,0,src.dimensions.z/2)
    path=OUT/(label+'.glb');export_glb(path,[clone]);modules[label]=path.name
    bpy.data.objects.remove(clone,do_unlink=True)
triangles=sum(len(p.vertices)-2 for obj in batched for p in obj.data.polygons)
assert triangles<=CFG['triangle_budget'],f'Triangle budget exceeded: {triangles}'
assert (OUT/'winterfell_fortress.glb').stat().st_size<CFG['glb_size_budget_mb']*1024**2
assert all(o.data.uv_layers and len(o.data.materials)>0 for o in visual_objects)
manifest={'schemaVersion':1,'name':'Winterfell-inspired Northern Fortress','generator':'tools/blender/generate.py','blenderVersion':bpy.app.version_string,'seed':CFG['seed'],'units':'metres','upAxis':'Y','source':'artifacts/winterfell_fortress.blend','scene':'winterfell_fortress.glb','lods':[{'level':0,'url':'winterfell_fortress.glb','triangles':triangles},{'level':1,'url':'winterfell_fortress_lod1.glb','decimationRatio':.45}],'modules':modules,'collision':'collision.json','materials':list(materials.keys()),'textureResolution':CFG['texture_size'],'visualObjects':len(visual_objects),'uniqueSourceMeshes':len({o.data.name for o in visual_objects}),'renderMeshes':len(batched),'collisionProxies':len(colliders),'sourceLicense':'Original procedural architecture. No extracted game assets.','preview':'/assets/winterfell/overview.png','generationSeconds':round(time.time()-started,2)}
if layout_info:
    manifest.update(name=layout_info['name'],source=str((SOURCE/'winterfell_fortress.blend').relative_to(ROOT)).replace('\\','/'),layout='layout.json',preview='/assets/winterfell-town/overview.png')
    (OUT/'layout.json').write_text(json.dumps(layout_info,indent=2))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
(SOURCE/'blender-validation.json').write_text(json.dumps({'passed':True,'blenderVersion':bpy.app.version_string,'triangles':triangles,'materialCount':len(materials),'allMeshesHaveUVs':True,'allMeshesHaveMaterials':True,'glbBytes':(OUT/'winterfell_fortress.glb').stat().st_size,'collisionCount':len(colliders),'gateClearanceMetres':[7,6.5],'generationSeconds':round(time.time()-started,2)},indent=2))
for ob in list(export_collection.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.collections.remove(export_collection)
if not opt.skip_preview:
    scene.camera=camera;scene.render.filepath=str(OUT/'overview.png');bpy.ops.render.render(write_still=True)
    close=camera_at('GateInspection',(32,-142,22) if layout_info else (18,-57,10),(0,-88,8) if layout_info else (0,-27,5),34)
    scene.camera=close;scene.render.filepath=str(OUT/'gate.png');bpy.ops.render.render(write_still=True)
    if layout_info:
        scene.camera=plan_camera;scene.render.filepath=str(OUT/'layout-plan.png');bpy.ops.render.render(write_still=True)
        scene.camera=reverse_camera;scene.render.filepath=str(OUT/'north-review.png');bpy.ops.render.render(write_still=True)
    scene.camera=camera
print('PIPELINE_COMPLETE',json.dumps(manifest))
(SOURCE/'build-success.json').write_text(json.dumps({'blenderVersion':bpy.app.version_string,'finishedAtUnix':time.time(),'previewRendered':not opt.skip_preview}))
