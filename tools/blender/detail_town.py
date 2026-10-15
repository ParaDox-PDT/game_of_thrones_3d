"""Architectural fidelity pass over the approved pass-02 layout.
Keeps building footprints, ward hierarchy, terrain, and primary circulation.
"""
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
import bpy
from mathutils import Vector

opt=argparse.ArgumentParser();opt.add_argument('--root',required=True);opt.add_argument('--skip-preview',action='store_true')
args=opt.parse_args(sys.argv[sys.argv.index('--')+1:])
ROOT=Path(args.root);OUT=ROOT/'public/assets/winterfell-detailed';SOURCE=ROOT/'artifacts/detail-pass-03'
OUT.mkdir(parents=True,exist_ok=True);SOURCE.mkdir(parents=True,exist_ok=True)
sys.stdout=open(SOURCE/'generation.log','w',encoding='utf-8',buffering=1);sys.stderr=sys.stdout
CFG=json.loads((Path(__file__).parent/'detail-config.json').read_text());random.seed(CFG['seed']);started=time.time()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/CFG['source']))
sys.path.insert(0,str(Path(__file__).parent))
from architecture_kit import Kit,batches,export_glb
scene=bpy.context.scene
visual=bpy.data.collections['WF_Architecture_LOD0']
kit=Kit(visual)
layout=json.loads((ROOT/'public/assets/winterfell-town/layout.json').read_text())
collision=json.loads((ROOT/'public/assets/winterfell-town/collision.json').read_text())
stone,trim,wood,metal,snow,slate,dark=(bpy.data.materials['WF_'+n] for n in ['AgedStone','CutStone','WeatheredWood','DarkIron','Snow','SlateRoof','WindowRecess'])
plaster=bpy.data.materials.new('WF_LimewashedInfill');plaster.use_nodes=True
plaster.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.48,.455,.39,1)
plaster.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.95
shingles=bpy.data.materials.new('WF_OakShingles');shingles.use_nodes=True
shingles.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.19,.16,.12,1)
shingles.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
stats={'buildingsDetailed':0,'wallModulesDetailed':0,'towersDetailed':0,'windows':0,'doors':0,'chimneys':0,'dormers':0,'gatehouses':0,'stairs':0,'roofVariants':{}}


def remove(obj):
    bpy.data.objects.remove(obj,do_unlink=True)


def point(origin,tangent,normal,u,v,z):
    return (origin[0]+tangent[0]*u+normal[0]*v,origin[1]+tangent[1]*u+normal[1]*v,z)


def local_box(name,origin,tangent,normal,u,v,z,size,mat):
    return kit.box(name,point(origin,tangent,normal,u,v,z),size,mat,math.atan2(tangent[1],tangent[0]))


def quad(name,points,mat,depth=.12):
    # Thin solid roof planes have actual eaves rather than zero-thickness sheets.
    clean=[]
    for p in points:
        if not any((Vector(p)-Vector(q)).length<.00001 for q in clean):clean.append(p)
    if len(clean)<3:return
    points=clean;verts=points+[(x,y,z-depth) for x,y,z in points];n=len(points)
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return kit.mesh(name,verts,faces,mat)


def arch(name,origin,tangent,normal,u,z0,width,straight,mat,depth=.24,rim=.24):
    r=width/2;zc=z0+straight
    for i in range(11):
        a=i*math.pi/11+.008;b=(i+1)*math.pi/11-.008
        verts=[point(origin,tangent,normal,u+rr*math.cos(t),v,zc+rr*math.sin(t)) for v in [-depth,.08] for rr,t in [(r,a),(r,b),(r+rim,b),(r+rim,a)]]
        kit.mesh(name+'_Voussoir',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    for side in [-1,1]:local_box(name+'_Jamb',origin,tangent,normal,u+side*(r+rim/2),-.05,z0+straight/2,(rim,.38,straight),mat)


def facade(name,origin,tangent,normal,width,zbase,height,field,openings,timber=False):
    """Build a thick facade around holes; frames sit proud, panes sit recessed."""
    top=zbase+height
    levels=sorted(set([zbase,top]+[max(zbase,min(top,o[k])) for o in openings for k in ['bottom','top']]))
    for lo,hi in zip(levels,levels[1:]):
        if hi-lo<.015:continue
        holes=sorted([(o['u']-o['w']/2,o['u']+o['w']/2) for o in openings if o['bottom']<(lo+hi)/2<o['top']])
        left=-width/2
        for start,end in holes+[(width/2,width/2)]:
            start=max(-width/2,start)
            if start-left>.02:local_box(name+'_WallPanel',origin,tangent,normal,(left+start)/2,-.23,(lo+hi)/2,(start-left,.46,hi-lo),field)
            left=max(left,end)
    for o in openings:
        u,w,lo,hi=o['u'],o['w'],o['bottom'],o['top'];h=hi-lo;door=o.get('door',False)
        # A reveal tunnel leads from the visible facade plane to a recessed pane.
        local_box(name+'_Recess',origin,tangent,normal,u,-.53,(lo+hi)/2,(w,.045,h),wood if door else dark)
        for sign in [-1,1]:
            local_box(name+'_Reveal',origin,tangent,normal,u+sign*(w/2+.045),-.22,(lo+hi)/2,(.10,.60,h+.15),wood if timber else trim)
        local_box(name+'_Sill',origin,tangent,normal,u,.05,lo-.10,(w+.34,.55,.20),wood if timber else trim)
        if o.get('arch'):
            r=w/2;straight=h-r
            arch(name,origin,tangent,normal,u,lo,w,straight,trim)
            # Fill the upper corner pockets around the arch with solid masonry.
            zc=lo+straight
            for side in [-1,1]:
                verts=[];faces=[]
                for j in range(6):
                    t0=j*math.pi/12;t1=(j+1)*math.pi/12
                    ua=side*r*math.cos(t0);ub=side*r*math.cos(t1)
                    points=[point(origin,tangent,normal,u+ua,0,hi),point(origin,tangent,normal,u+ub,0,hi),point(origin,tangent,normal,u+ub,0,zc+r*math.sin(t1)),point(origin,tangent,normal,u+ua,0,zc+r*math.sin(t0))]
                    quad(name+'_ArchSpandrel',points,field,.40)
        else:local_box(name+'_Lintel',origin,tangent,normal,u,.06,hi+.12,(w+.4,.44,.24),wood if timber else trim)
        if door:
            stats['doors']+=1
            for z in [lo+h*.22,lo+h*.75]:local_box(name+'_DoorStrap',origin,tangent,normal,u,-.49,z,(w,.07,.10),metal)
            for du in [-w*.24,w*.24]:local_box(name+'_DoorPull',origin,tangent,normal,u+du,-.445,lo+h*.48,(.08,.06,.28),metal)
        else:
            stats['windows']+=1
            local_box(name+'_Mullion',origin,tangent,normal,u,-.48,(lo+hi)/2,(.075,.065,h),wood if timber else trim)
            local_box(name+'_Transom',origin,tangent,normal,u,-.46,lo+h*.55,(w,.07,.07),wood if timber else trim)
            if timber:
                for sign in [-1,1]:
                    local_box(name+'_OpenShutter',origin,tangent,normal,u+sign*(w*.8),.06,(lo+hi)/2,(w*.45,.10,h*.92),wood)
        if door and lo>.35:
            steps=max(1,round((lo-.12)/.24))
            for i in range(steps):
                zz=.12+(i+1)*(lo-.12)/steps
                # Entrances remain closed, with solid and correctly stepped thresholds.
                local_box(name+'_ThresholdStep',origin,tangent,normal,u,.35+(steps-i-1)*.30,zz/2,(w+.55,.32,zz),stone)
                xy=point(origin,tangent,normal,u,.35+(steps-i-1)*.30,0)
                sx,sy=(w+.55,.32) if tangent[0] else (.32,w+.55)
                collision['walkableSurfaces'].append({'name':'DoorThreshold','min':[xy[0]-sx/2,-xy[1]-sy/2],'max':[xy[0]+sx/2,-xy[1]+sy/2],'height':zz})
    if timber:
        for u in [-width/2+.12,0,width/2-.12]:local_box(name+'_StructuralPost',origin,tangent,normal,u,.07,zbase+height/2,(.22,.24,height),wood)
        for z in [zbase+.38,top-.1,zbase+height*.52]:local_box(name+'_TieBeam',origin,tangent,normal,0,.08,z,(width,.24,.20),wood)
        # Knee braces at corners avoid placing decorative diagonals over openings.
        for sign in [-1,1]:
            a=point(origin,tangent,normal,sign*(width/2-.23),.12,top-1.2)
            b=point(origin,tangent,normal,sign*(width/2-1.35),.12,top-.12)
            kit.beam(name+'_KneeBrace',a,b,.14,wood)


def roof(name,x,y,z,w,d,h,style,mat):
    stats['roofVariants'][style]=stats['roofVariants'].get(style,0)+1
    if style=='hipped':
        points=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),(x,y-d*.23,z+h),(x,y+d*.23,z+h)]
        panels=[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4)]
    else:
        points=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),(x,y-d/2,z+h),(x,y+d/2,z+h)]
        panels=[(0,4,5,3),(1,2,5,4)]
        for yy,normal in [(y-d/2,(0,-1)),(y+d/2,(0,1))]:
            kit.mesh(name+'_Gable',[(x-w/2,yy,z),(x+w/2,yy,z),(x,yy,z+h)],[(0,1,2)],plaster)
            for sx in [-1,1]:kit.beam(name+'_Rafter',(x+sx*w/2,yy-.02*normal[1],z),(x,yy-.02*normal[1],z+h),.20,wood)
            kit.beam(name+'_KingPost',(x,yy,z),(x,yy,z+h),.18,wood)
            kit.beam(name+'_GableTie',(x-w/2,yy,z+.2),(x+w/2,yy,z+.2),.20,wood)
    for indices in panels:
        p=[points[i] for i in indices];quad(name+'_SlatePlane',p,mat,.19)
        # Snow covers the upper slope; exposed eaves reveal roof materials and form.
        maxz=max(v[2] for v in p);cap=[]
        for vx,vy,vz in p:
            if vz==z:
                near=min([q for q in p if q[2]==maxz],key=lambda q:(q[0]-vx)**2+(q[1]-vy)**2)
                vx=near[0]+(vx-near[0])*.72;vy=near[1]+(vy-near[1])*.72;vz=maxz+(vz-maxz)*.72
            cap.append((vx,vy,vz+.075))
        quad(name+'_SnowCap',cap,snow,.045)
    for xx in [x-w/2,x+w/2]:kit.box(name+'_EavesFascia',(xx,y,z-.04),(.16,d+.2,.28),wood)
    kit.box(name+'_Ridge',(x,y,z+h+.06),(.22,d if style!='hipped' else d*.46,.18),trim)
    if style=='clerestory':
        kit.box(name+'_RidgeVentBody',(x,y,z+h+.45),(1.8,d*.60,.9),wood)
        for side in [-1,1]:
            for zz in [z+h+.2,z+h+.45,z+h+.7]:kit.box(name+'_VentLouvre',(x+side*.94,y,zz),(.10,d*.62,.10),dark)
        roof(name+'_VentRoof',x,y,z+h+.9,2.3,d*.66,.7,'gable',mat)


def front_for(b):
    name=b['name'];x,y=b['centerBlender']
    if name.startswith(('Merchant','WestWard')):return 'E'
    if name.startswith(('Craft','EastWard')):return 'W'
    if name in ['SouthBarracks','SouthStableRange','WestBulkStore','EastGranary','SouthwestInn','CartersLodge']:return 'N'
    if name.endswith('CouncilRange'):return 'N'
    return 'S'


print('DETAIL_STAGE_BUILDINGS',flush=True)
kit.group('01_Building_Facades_And_Roofs')
for index,b in enumerate(layout['buildings']):
    if b['name']=='GreatKeepComplex':continue
    name=b['name'];x,y=b['centerBlender'];w,d=b['size'];h=b['height'];timber=b['type']=='timber'
    candidates=[o for o in visual.all_objects if o.name.startswith('WF_'+name+'_Mass')]
    core=min(candidates,key=lambda o:(o.location.x-x)**2+(o.location.y-y)**2)
    core.dimensions=(w-1.3,d-1.3,h)
    front=front_for(b)
    for side,origin,tangent,normal,width in [('S',(x,y-d/2),(1,0),(0,-1),w),('N',(x,y+d/2),(1,0),(0,1),w),('W',(x-w/2,y),(0,1),(-1,0),d),('E',(x+w/2,y),(0,1),(1,0),d)]:
        openings=[];is_front=side==front
        stable='Stable' in name or name=='FodderBarn';storage=name in ['WestBulkStore','EastGranary','Quartermaster']
        if is_front:openings.append({'u':0,'w':3.7 if stable else 2.5 if storage else 1.5,'bottom':.65,'top':4.8 if stable else 3.4,'door':True,'arch':not timber and not stable})
        levels=[3.6] if stable else [2.1,5.1] if h>=6 else [2.1]
        if storage:levels=[3.0,6.2] if h>=8 else [3.3]
        count=max(2,int(width/4.0));spacing=width/(count+1)
        for z in levels:
            for j in range(count):
                u=-width/2+(j+1)*spacing;ww=.75 if storage or stable else 1.10
                if any(abs(u-o['u'])<(ww+o['w'])/2+.4 and z<o['top']+.1 for o in openings):continue
                openings.append({'u':u,'w':ww,'bottom':z,'top':min(z+(1.1 if storage or stable else 1.55),h+.3),'arch':not timber})
        facade(name+side,origin,tangent,normal,width,.65,h,plaster if timber else stone,openings,timber)
        if not timber:
            for u in [-width/2+.2,width/2-.2]:
                for iz,z in enumerate([1.4,2.3,3.2,4.1,5,5.9,6.8,7.7]):
                    if z>h:break
                    local_box('BuildingQuoin',origin,tangent,normal,u,.035,z,(.62 if iz%2 else .88,.16,.46),trim)
            local_box('StoreyStringCourse',origin,tangent,normal,0,.04,4.55,(width,.19,.18),trim)
    # Replace only each building's own roof, preserving its footprint and body.
    for obj in list(visual.all_objects):
        if obj.name.startswith('WF_'+name+'_Roof'):
            coordinates=[obj.matrix_world@Vector(corner) for corner in obj.bound_box]
            cx=sum(v.x for v in coordinates)/8;cy=sum(v.y for v in coordinates)/8
            if abs(cx-x)<.5 and abs(cy-y)<.5:remove(obj)
    style='clerestory' if 'Stable' in name else 'hipped' if name in ['SouthwestInn','OfficerBarracks','EastGranary'] else 'gable'
    roofmat=shingles if timber and index%3==0 else slate
    rh=min(5.8,w*.38);rz=h+.7
    roof(name,x,y,rz,w+1,d+1,rh,style,roofmat)
    if index%2==0 and not ('Stable' in name or 'Store' in name or name=='FodderBarn'):
        sign=1 if front=='E' else -1 if front=='W' else (1 if index%4==0 else -1)
        cx=x+sign*w*.26;cy=y-d*.12;dz=rz+rh*.48-.25
        kit.box(name+'_DormerCore',(cx,cy,dz+.8),(2.4,2.4,1.6),wood)
        facade(name+'_Dormer',(cx+sign*1.6,cy),(0,1),(sign,0),2.4,dz,1.6,plaster,[{'u':0,'w':.85,'bottom':dz+.22,'top':dz+1.4}],True)
        points=[(cx-1.8,cy-1.4,dz+1.6),(cx+1.8,cy-1.4,dz+1.6),(cx+1.8,cy+1.4,dz+1.6),(cx-1.8,cy+1.4,dz+1.6),(cx-1.8,cy,dz+2.55),(cx+1.8,cy,dz+2.55)]
        for indices in [(0,1,5,4),(3,4,5,2)]:quad(name+'_DormerRoof',[points[j] for j in indices],slate,.14)
        kit.mesh(name+'_DormerGable',[(cx+sign*1.8,cy-1.4,dz+1.6),(cx+sign*1.8,cy+1.4,dz+1.6),(cx+sign*1.8,cy,dz+2.55)],[(0,1,2)],plaster)
        stats['dormers']+=1
    if not ('Stable' in name or 'Store' in name or name=='FodderBarn'):
        cx=x+w*.20;cy=y+d*.21;bottom=rz+rh*.58
        kit.box(name+'_HearthChimney',(cx,cy,bottom+1.4),(.95,1.15,2.8),stone)
        kit.box(name+'_ChimneyShoulder',(cx,cy,bottom+2.65),(1.18,1.38,.20),trim)
        for sx,sy,ww,dd in [(-.48,0,.18,1.2),(.48,0,.18,1.2),(0,-.51,.82,.18),(0,.51,.82,.18)]:kit.box(name+'_FlueCap',(cx+sx,cy+sy,bottom+2.94),(ww,dd,.35),trim)
        kit.box(name+'_FlueVoid',(cx,cy,bottom+2.72),(.72,.88,.08),dark);stats['chimneys']+=1
    # Loading hatches and hoists make storage read differently from housing.
    if name in ['WestBulkStore','EastGranary']:
        yy=y+d/2
        local_box(name+'_LoadingHatch',(x,yy),(1,0),(0,1),0,.06,5.3,(2.0,.16,2.3),wood)
        kit.beam(name+'_HoistArm',(x,yy-.3,8.3),(x,yy+2.1,8.3),.22,wood)
        kit.beam(name+'_HoistBrace',(x,yy,6.9),(x,yy+1.6,8.3),.16,wood)
        kit.beam(name+'_HoistRope',(x,yy+1.9,8.3),(x,yy+1.9,4.2),.045,wood)
    stats['buildingsDetailed']+=1

# Sheltered arcades add useful spaces without filling the established routes.
kit.group('02_Covered_Galleries')
for name,x,y,w,depth,z in [('InnGallery',-57,-65.8,13,2.1,3.3),('QuartermasterPorch',-84,70.6,10,1.7,3.1)]:
    kit.box(name+'_Deck',(x,y,.45),(w,depth,.28),wood)
    for dx in [-w/2,0,w/2]:
        kit.box(name+'_Post',(x+dx,y+depth/2,z/2),(.20,.20,z),wood)
        kit.beam(name+'_Brace',(x+dx,y+depth/2,z-1.0),(x+dx+.7,y+depth/2,z-.15),.13,wood)
    quad(name+'_LeanTo',[(x-w/2,y-depth/2,z+.6),(x+w/2,y-depth/2,z+.6),(x+w/2,y+depth/2,z),(x-w/2,y+depth/2,z)],slate,.18)

print('DETAIL_STAGE_WALLS',flush=True)
kit.group('03_Curtain_Construction')
for obj in list(visual.all_objects):
    if obj.name.startswith('WF_Buttress'):remove(obj)
for obj in list(visual.all_objects):
    if 'Curtain' not in obj.name or '_Module' not in obj.name:continue
    x,y,z=obj.location;dx,dy,h=obj.dimensions
    tangent,normal,length=((1,0),(0,1),dx) if dx>dy else ((0,1),(1,0),dy)
    origin=(x,y)
    for side in [-1,1]:
        n=(normal[0]*side,normal[1]*side)
        for row,zz in enumerate([1.45,2.10]):
            count=max(3,round(length/1.45));step=length/count
            for j in range(count):
                u=-length/2+(j+.5)*step
                local_box('BeddedAshlar',origin,tangent,n,u,1.23,zz,(step-.045,.20,.57),trim if (j+row)%5==0 else stone)
        # Tapered buttress: substantial foot, sloped back and narrow upper support.
        verts=[point(origin,tangent,n,u,v,zz) for zz,projection,ww in [(.4,1.03,.66),(h*.72,.22,.42)] for u,v in [(-ww,1.1), (ww,1.1),(ww,1.1+projection),(-ww,1.1+projection)]]
        kit.mesh('BatteredButtress',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],stone)
        c=point(origin,tangent,n,0,1.615,h*.36)
        collision['colliders'].append({'name':'DetailButtress','type':'box','center':[c[0],c[2],-c[1]],'size':[1.32 if tangent[0] else 1.03,h*.72,1.03 if tangent[0] else 1.32]})
        local_box('ButtressCap',origin,tangent,n,0,1.37,h*.72+.10,(.96,.62,.22),trim)
        local_box('MasonryStringCourse',origin,tangent,n,0,1.20,h*.53,(length,.18,.22),trim)
    # Low inner parapet; existing merlons retain the outer defensive rhythm.
    inward=1 if ('West' in obj.name or 'South' in obj.name) else -1
    spans=[(-length/2,length/2)]
    gap=None
    if 'OuterCurtainNorth' in obj.name:gap=(-23.3-x,-20.7-x)
    if 'InnerCurtainWest' in obj.name:gap=(64.4-y,66.8-y)
    if gap:
        spans=[(a,min(b,gap[0])) for a,b in spans if a<gap[0]]+[(max(a,gap[1]),b) for a,b in spans if b>gap[1]]
    for a,b in spans:
        if b-a>.02:local_box('InnerWallWalkParapet',origin,tangent,normal,(a+b)/2,inward*.97,h+.42,(b-a,.24,.78),stone)
    local_box('OuterBattlementCorbelCourse',origin,tangent,normal,0,-inward*1.24,h-.04,(length,.66,.30),trim)
    stats['wallModulesDetailed']+=1


print('DETAIL_STAGE_TOWERS',flush=True)
kit.group('04_Tower_Reveals_And_Corbels')
for obj in list(visual.all_objects):
    if obj.name.startswith('WF_ArrowSlit'):remove(obj)
for obj in list(visual.all_objects):
    if not obj.name.startswith('WF_') or '_Shaft' not in obj.name:continue
    x,y,zc=obj.location;r=obj.dimensions.x/2;h=obj.dimensions.z
    count=64;bands=[0,h*.25,h*.25+1.6,h*.61,h*.61+1.8,h]
    verts=[];faces=[]
    def add_quad(points):
        i=len(verts);verts.extend(points);faces.append(tuple(range(i,i+4)))
    def ringp(rr,a,z):return (rr*math.cos(a),rr*math.sin(a),z-h/2)
    holes=[]
    for band,(lo,hi) in enumerate(zip(bands,bands[1:])):
        for j in range(count):
            a=j*math.tau/count;b=(j+1)*math.tau/count
            hole=band in [1,3] and j%8==0
            if hole:
                holes.append((a,b,lo,hi))
                add_quad([ringp(r,a,lo),ringp(r-.5,a,lo),ringp(r-.5,a,hi),ringp(r,a,hi)])
                add_quad([ringp(r,b,lo),ringp(r,b,hi),ringp(r-.5,b,hi),ringp(r-.5,b,lo)])
                add_quad([ringp(r,a,lo),ringp(r,b,lo),ringp(r-.5,b,lo),ringp(r-.5,a,lo)])
                add_quad([ringp(r,a,hi),ringp(r-.5,a,hi),ringp(r-.5,b,hi),ringp(r,b,hi)])
                continue
            add_quad([ringp(r,a,lo),ringp(r,b,lo),ringp(r,b,hi),ringp(r,a,hi)])
            add_quad([ringp(r-.5,a,lo),ringp(r-.5,a,hi),ringp(r-.5,b,hi),ringp(r-.5,b,lo)])
    for z in [0,h]:
        for j in range(count):
            a=j*math.tau/count;b=(j+1)*math.tau/count
            add_quad([ringp(r,a,z),ringp(r,b,z),ringp(r-.5,b,z),ringp(r-.5,a,z)])
    shell=kit.mesh('PiercedTowerShaft',verts,faces,stone,('towerShell',r,h),smooth=True)
    obj.data=shell.data;remove(shell)
    kit.cylinder('TowerDarkCore',(x,y,h/2),r-.63,h,dark,48)
    for a,b,lo,hi in holes:
        angle=(a+b)/2;normal=(math.cos(angle),math.sin(angle));tangent=(-normal[1],normal[0]);origin=(x+normal[0]*r,y+normal[1]*r)
        width=r*(b-a)
        local_box('TowerInsetShutter',origin,tangent,normal,0,-.46,(lo+hi)/2,(width,.04,hi-lo),dark)
        local_box('TowerWindowSill',origin,tangent,normal,0,.06,lo-.12,(width+.30,.42,.22),trim)
        local_box('TowerWindowHood',origin,tangent,normal,0,.09,hi+.13,(width+.34,.45,.22),trim)
        stats['windows']+=1
    for i in range(16):
        a=i*math.tau/16;normal=(math.cos(a),math.sin(a));tangent=(-normal[1],normal[0])
        origin=(x+normal[0]*r,y+normal[1]*r)
        kit.beam('TowerCrownCorbel',point(origin,tangent,normal,0,.04,h-1.5),point(origin,tangent,normal,0,.54,h-.40),.28,trim)
    kit.ring('TowerProjectingCornice',(x,y,h-.35),r+.65,.48,.22,trim)
    stats['towersDetailed']+=1

# Move curtain merlons onto their supported outer edge, leaving an actual walk.
for obj in list(visual.all_objects):
    if not obj.name.startswith('WF_Merlon'):continue
    zone=obj.get('zone','')
    limits={'01_Outer_Defences':(-104,104,-94,94,10),'06_Inner_Defences':(-64,64,-25,80,13),'08_Citadel_And_Great_Keep':(-32,32,25,74,16)}.get(zone)
    if not limits:continue
    x0,x1,y0,y1,h=limits
    if min(abs(obj.location.z-h-.6),abs(obj.location.z-h-1.26))>.12:continue
    x,y=obj.location.x,obj.location.y
    options=[(abs(x-x0),(-1,0)),(abs(x-x1),(1,0)),(abs(y-y0),(0,-1)),(abs(y-y1),(0,1))]
    distance,normal=min(options)
    if distance<.05:obj.location.x+=normal[0]*.95;obj.location.y+=normal[1]*.95

print('DETAIL_STAGE_GATEHOUSES',flush=True)
kit.group('05_Gatehouse_Architecture')
for gate in layout['gates']:
    name=gate['name'];x,y=gate['centerBlender'];gap=gate['width'];clear=gate['clearance']
    # Raised portcullises, real grooves, a ribbed passage vault and guard rooms.
    for yy in [y-3.8,y+3.8]:
        for sign in [-1,1]:
            kit.box(name+'_PortcullisGroove',(x+sign*(gap/2+.08),yy,clear/2),(.24,.30,clear),trim)
        arch(name+'_Portal',(x,yy),(1,0),(0,-1 if yy<y else 1),0,0,gap,clear-gap/2,trim,.50,.48)
    for yy in [y-2.4,y,y+2.4]:arch(name+'_VaultRib',(x,yy),(1,0),(0,-1),0,0,gap,clear-gap/2,trim,.18,.24)
    # Raised grille's lower tips stay well above standing / mounted clearance.
    for u in range(-int(gap/2)+1,int(gap/2)):
        kit.box(name+'_RaisedPortcullis',(x+u,y-3.5,clear+1.1),(.13,.14,3.4),metal)
    for zz in [clear-.2,clear+1.2,clear+2.4]:kit.box(name+'_PortcullisCrossbar',(x,y-3.5,zz),(gap-.8,.18,.15),metal)
    # Projecting upper gallery on stone corbels, with its own roof and windows.
    top=clear+6.4
    for u in [-gap*.34,0,gap*.34]:
        kit.beam(name+'_HoardingCorbel',(x+u,y-3.4,top-2),(x+u,y-5.0,top-.25),.3,trim)
    kit.box(name+'_HoardingDeck',(x,y-4.3,top),(gap+1,2.2,.32),wood)
    for u in [-gap*.36,0,gap*.36]:
        kit.box(name+'_GalleryPost',(x+u,y-5.25,top+1.25),(.20,.20,2.5),wood)
    quad(name+'_GalleryRoof',[(x-gap/2-.8,y-3.2,top+3.5),(x+gap/2+.8,y-3.2,top+3.5),(x+gap/2+.8,y-5.6,top+2.7),(x-gap/2-.8,y-5.6,top+2.7)],slate,.2)
    for u in [-gap*.27,gap*.27]:
        local_box(name+'_GuardWindow',(x,y-3.78),(1,0),(0,-1),u,.03,clear+3.7,(.95,.10,1.5),dark)
        arch(name+'_GuardHood',(x,y-3.78),(1,0),(0,-1),u,clear+2.95,.95,1.02,trim,.20,.17)
    # Cross-braced gate leaves and hinge straps reinforce their actual thickness.
    for sign in [-1,1]:
        gx=x+sign*(gap/2+.2)
        for zz in [1,3.5,6]:kit.box(name+'_GateStrap',(gx+sign*.16,y+2.3,zz),(.07,6.7,.15),metal)
        kit.beam(name+'_GateDiagonal',(gx,y-.7,.8),(gx,y+5.3,6.5),.18,wood)
    stats['gatehouses']+=1

print('DETAIL_STAGE_KEEP',flush=True)
kit.group('06_Great_Keep_Stonework')
for name,x,y,w,d,h,zbase in [('GreatKeepLower',0,55,30,27,26,0),('GreatKeepUpper',0,57,19,18,16,26)]:
    obj=bpy.data.objects['WF_'+name];obj.dimensions=(w-1.4,d-1.4,h)
    for side,origin,tangent,normal,width in [('S',(x,y-d/2),(1,0),(0,-1),w),('N',(x,y+d/2),(1,0),(0,1),w),('W',(x-w/2,y),(0,1),(-1,0),d),('E',(x+w/2,y),(0,1),(1,0),d)]:
        openings=[]
        if name=='GreatKeepLower' and side=='S':openings.append({'u':0,'w':3.6,'bottom':1.55,'top':7.3,'door':True,'arch':True})
        levels=[9,16.5,22] if zbase==0 else [29,35.5,39]
        for zz in levels:
            for u in [-width*.28,0,width*.28]:openings.append({'u':u,'w':1.15 if zz<20 else 1.5,'bottom':zz,'top':min(zbase+h-.7,zz+2.25),'arch':True})
        facade(name+side,origin,tangent,normal,width,zbase,h,stone,openings)
        for zz in ([7.8,14.8,24.9] if zbase==0 else [33.2,41.4]):local_box(name+'_BeltCourse',origin,tangent,normal,0,.08,zz,(width,.24,.30),trim)
        for u in [-width/2+.45,width/2-.45]:
            for zz in range(int(zbase)+2,int(zbase+h),2):local_box('KeepQuoin',origin,tangent,normal,u,.04,zz,(1.12,.18,.66),trim)


print('DETAIL_STAGE_STAIRS',flush=True)
kit.group('07_Wall_Walk_Access')
def stair(name,start,tangent,normal,rise,run,width):
    count=round(rise/.25);step=run/count
    x,y=start
    for i in range(count):
        u=(i+.5)*step;zz=.12+(i+1)*rise/count
        local_box(name+'_Tread',(x,y),tangent,normal,u,0,zz-.16/2,(step+.025,width,.16),trim)
        xy=point((x,y),tangent,normal,u,0,0)
        # Solid stair volume and explicit supports are both visible and collidable.
        local_box(name+'_Support',(x,y),tangent,normal,u,0,(zz-.16)/2,(step+.02,width*.75,zz-.16),stone)
        sx=step if tangent[0] else width;sy=width if tangent[0] else step
        collision['walkableSurfaces'].append({'name':name,'min':[xy[0]-sx/2,-xy[1]-sy/2],'max':[xy[0]+sx/2,-xy[1]+sy/2],'height':zz})
    for side in [-1,1]:
        kit.beam(name+'_HandRail',point(start,tangent,normal,0,side*width/2,1.15),point(start,tangent,normal,run,side*width/2,rise+1.15),.13,wood)
        for i in range(0,count,5):
            u=(i+.5)*step;zz=.12+(i+1)*rise/count
            kit.beam(name+'_RailPost',point(start,tangent,normal,u,side*width/2,zz),point(start,tangent,normal,u,side*width/2,zz+1.05),.10,wood)
    stats['stairs']+=1
stair('NorthOuterWallStair',(-44,91),(1,0),(0,1),10,22,1.8)
kit.box('NorthWallLanding',(-22,92,10),(2.6,4,.30),trim)
collision['walkableSurfaces'].append({'name':'NorthWallLanding','min':[-23.3,-94],'max':[-20.7,-90],'height':10.15})
stair('WestInnerWallStair',(-60,37),(0,1),(1,0),13,28.6,1.8)
kit.box('InnerWallLanding',(-62,65.6,13),(5.8,2.4,.30),trim)
collision['walkableSurfaces'].append({'name':'InnerWallLanding','min':[-64.9,-66.8],'max':[-59.1,-64.4],'height':13.15})

# Save the editable architecture before making temporary browser batches.
bpy.context.view_layer.update()
for image in bpy.data.images:
    if image.has_data and image.source=='FILE':image.pack()
def camera(name,loc,target,lens=44):
    data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
    obj.location=loc;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_end=1200
    return obj
cameras={
    'overview':camera('DetailOverview',(252,-307,247),(0,0,7)),
    'gatehouse-detail':camera('GatehouseDetail',(25,-128,13),(0,-92,9),36),
    'town-street':camera('TownStreet',(-8,-52,8),(-35,-72,6),32),
    'keep-detail':camera('GreatKeepDetail',(72,-14,46),(0,52,22),42),
    'wall-and-tower':camera('WallAndTower',(139,-69,22),(104,-42,11),36),
    'inner-courtyard':camera('InnerCourtyard',(18,-4,12),(-30,22,10),32)
}
scene.camera=cameras['overview'];scene['architecture_pass']=3
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x,scene.render.resolution_y=CFG['preview_resolution'];scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED';scene.render.threads=4
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'winterfell_fortress_detailed.blend'))
objects=list(visual.all_objects)
assert all(o.data.uv_layers and o.data.materials for o in objects if o.type=='MESH')
triangles=sum(len(p.vertices)-2 for obj in objects if obj.type=='MESH' for p in obj.data.polygons)
assert triangles<=CFG['triangle_budget'],triangles
collection=bpy.data.collections.new('DetailExportBatches');scene.collection.children.link(collection)
print('DETAIL_STAGE_EXPORT',len(objects),triangles,flush=True)
batched=batches(objects,collection)
export_glb(OUT/'winterfell_fortress.glb',batched)
for obj in batched:mod=obj.modifiers.new('LOD1','DECIMATE');mod.ratio=.42
export_glb(OUT/'winterfell_fortress_lod1.glb',batched)
assert (OUT/'winterfell_fortress.glb').stat().st_size<CFG['glb_size_budget_mb']*1024**2
for obj in list(collection.objects):remove(obj)
bpy.data.collections.remove(collection)
layout.update({'pass':'03-architectural-fidelity','name':'Northern Fortress-Town · Architectural Detail Pass 03','reviewScope':'Same pass-02 footprint, buildings, wards and gates; upgraded architecture. Interiors remain closed.'})
(OUT/'layout.json').write_text(json.dumps(layout,indent=2))
(OUT/'collision.json').write_text(json.dumps(collision,indent=2))
manifest={'schemaVersion':1,'name':layout['name'],'generator':'tools/blender/detail_town.py','blenderVersion':bpy.app.version_string,'seed':CFG['seed'],'units':'metres','upAxis':'Y','source':'artifacts/detail-pass-03/winterfell_fortress_detailed.blend','scene':'winterfell_fortress.glb','lods':[{'level':0,'url':'winterfell_fortress.glb','triangles':triangles},{'level':1,'url':'winterfell_fortress_lod1.glb','decimationRatio':.42}],'modules':{},'collision':'collision.json','layout':'layout.json','materials':sorted({m.name for o in objects if o.type=='MESH' for m in o.data.materials}),'textureResolution':256,'visualObjects':len(objects),'renderMeshes':len({m.name for o in objects if o.type=='MESH' for m in o.data.materials}),'collisionProxies':len(collision['colliders']),'details':stats,'preview':'/assets/winterfell-detailed/overview.png','sourceLicense':'Original procedural geometry; no game assets.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
(SOURCE/'architecture-report.json').write_text(json.dumps({'passed':True,'layoutPreserved':True,'triangles':triangles,'details':stats,'generationSeconds':round(time.time()-started,2)},indent=2))
if not args.skip_preview:
    for name,cam in cameras.items():
        print('DETAIL_RENDER',name,flush=True)
        scene.camera=cam;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
scene.camera=cameras['overview']
(SOURCE/'build-success.json').write_text(json.dumps({'blenderVersion':bpy.app.version_string,'finishedAtUnix':time.time(),'previewRendered':not args.skip_preview}))
print('DETAIL_COMPLETE',json.dumps(manifest),flush=True)
