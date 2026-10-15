"""Pass 04: northern landscape, weather and ward-specific environmental stories."""
import argparse
import array
import json
import math
import random
import sys
import time
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--skip-preview',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);ROOT=Path(args.root)
OUT=ROOT/'public/assets/winterfell-environment';SOURCE=ROOT/'artifacts/environment-pass-04'
OUT.mkdir(parents=True,exist_ok=True);SOURCE.mkdir(parents=True,exist_ok=True)
sys.stdout=open(SOURCE/'generation.log','w',encoding='utf-8',buffering=1);sys.stderr=sys.stdout
CFG=json.loads((Path(__file__).parent/'environment-config.json').read_text());rng=random.Random(CFG['seed']);started=time.time()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/CFG['source']))
sys.path.insert(0,str(Path(__file__).parent))
from architecture_kit import Kit,batches,export_glb
from glb_lighting import normalize_point_lights
scene=bpy.context.scene;visual=bpy.data.collections['WF_Architecture_LOD0'];kit=Kit(visual)
layout=json.loads((ROOT/'public/assets/winterfell-detailed/layout.json').read_text())
collision=json.loads((ROOT/'public/assets/winterfell-detailed/collision.json').read_text())
previous=json.loads((ROOT/'public/assets/winterfell-detailed/manifest.json').read_text())
stone,trim,wood,iron,snow,dark=(bpy.data.materials['WF_'+name] for name in ['AgedStone','CutStone','WeatheredWood','DarkIron','Snow','WindowRecess'])
stats={key:0 for key in ['pines','mountainRanges','rocks','snowDrifts','barrels','crates','carts','woodPiles','fenceSegments','torches','braziers','banners','marketStalls','footprints','wheelRuts','clutterClusters']}
placements=[];flames=[]


def mat(name,color,roughness=.95,metallic=0,emission=0):
    m=bpy.data.materials.new('ENV_'+name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness;p.inputs['Metallic'].default_value=metallic
    if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m


needles=mat('PineNeedles',(.035,.075,.065));bark=mat('PineBark',(.10,.075,.05))
rockmat=mat('ExposedRock',(.24,.28,.31));mud=mat('WetRoadMud',(.095,.075,.052),.40)
slush=mat('TrampledSlush',(.39,.44,.45),.61);cutwood=mat('CutTimber',(.40,.28,.15))
rutmat=mat('RutEarth',(.065,.052,.036),.32)
cloth=mat('NorthernCloth',(.075,.125,.14));sigil=mat('SilverWolf',(.68,.75,.77))
amber=mat('FlameAmber',(1,.19,.018),.5,emission=5);firecore=mat('FlameCore',(1,.61,.13),.4,emission=8)
straw=mat('WinterFodder',(.34,.29,.14));coal=mat('Coal',(.025,.028,.026))


def ground_texture(material,name,base,ice):
    n=256;pixels=array.array('f');heights=[];rr=random.Random(551)
    for y in range(n):
        for x in range(n):
            u=x/n*math.tau;v=y/n*math.tau
            coarse=math.sin(u*3+math.sin(v*2)*1.7)*math.cos(v*4+math.sin(u))* .22
            fine=rr.random()*.13
            grain=.65+coarse+fine;frozen=max(0,min(1,(coarse-.055)*3.8))
            pixels.extend(tuple(base[c]*grain*(1-frozen)+ice[c]*frozen for c in range(3))+(1,))
            heights.append(.5+coarse*.2+fine*.18)
    image=bpy.data.images.new(name+'_Base',n,n);image.pixels.foreach_set(pixels);image.file_format='PNG';image.filepath_raw=str(OUT/(name+'_base.png'));image.save()
    normals=array.array('f')
    for y in range(n):
        for x in range(n):
            dx=heights[y*n+(x+1)%n]-heights[y*n+(x-1)%n];dy=heights[((y+1)%n)*n+x]-heights[((y-1)%n)*n+x]
            q=Vector((-dx*3,-dy*3,1)).normalized();normals.extend((q.x*.5+.5,q.y*.5+.5,q.z*.5+.5,1))
    normal=bpy.data.images.new(name+'_Normal',n,n);normal.colorspace_settings.name='Non-Color';normal.pixels.foreach_set(normals);normal.file_format='PNG';normal.filepath_raw=str(OUT/(name+'_normal.png'));normal.save()
    nodes=material.node_tree.nodes;links=material.node_tree.links;bsdf=nodes.get('Principled BSDF')
    tex=nodes.new('ShaderNodeTexImage');tex.image=image;links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    nt=nodes.new('ShaderNodeTexImage');nt.image=normal;nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.4;links.new(nt.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
ground_texture(mud,'WinterMud',(.15,.115,.072),(.43,.48,.48))
ground_texture(slush,'RoadSlush',(.55,.60,.60),(.68,.72,.73))
ground_texture(rutmat,'WheelEarth',(.085,.065,.042),(.22,.26,.27))


def distance_segment(x,y,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy or 1)))
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)


routes=[r['pointsBlender'] for r in layout['routes']]
def clear_route(x,y,radius=0,extra=2.1):
    return all(distance_segment(x,y,a,b)>radius+extra for points in routes for a,b in zip(points,points[1:]))


def building_clear(x,y,radius=0):
    for b in layout['buildings']:
        if b['name']=='GreatKeepComplex':continue
        bx,by=b['centerBlender'];w,d=b['size']
        if abs(x-bx)<w/2+radius+.25 and abs(y-by)<d/2+radius+.25:return False
    return not (-30-radius<x<30+radius and 40-radius<y<74+radius)


def add_box(name,loc,size):
    collision['colliders'].append({'name':name,'type':'box','center':[loc[0],loc[2],-loc[1]],'size':[size[0],size[2],size[1]]})


def cylinder_proxy(name,x,y,z,r,h):
    collision['colliders'].append({'name':name,'type':'cylinder','center':[x,z,-y],'radius':r,'height':h})


def record(kind,x,y,radius):placements.append({'kind':kind,'centerBlender':[x,y],'radius':radius})


def terrain_height(x,y):
    distance=math.hypot(max(abs(x)-109,0),max(abs(y)-99,0));blend=min(1,distance/35)
    variation=1.4*math.sin(x/39)*math.cos(y/53)+.65*math.sin((x+y)/17)+4.2*math.sin(y/117)*math.sin(x/109)
    if y<-94:blend*=max(0,min(1,(abs(x)-8)/15))
    return -.055+blend*variation


def blob(name,x,y,rx,ry,h,material,seed=0,ground=None):
    # A low irregular drift / stone with a gently rising centre and tapered lip.
    rr=random.Random(seed);n=12;vertices=[(0,0,h)]
    for ring,z in [(0.55,h*.55),(1,0)]:
        for i in range(n):
            a=i*math.tau/n;factor=rr.uniform(.87,1.10)
            vertices.append((math.cos(a)*rx*ring*factor,math.sin(a)*ry*ring*factor,z))
    faces=[]
    for i in range(n):
        faces.append((0,1+i,1+(i+1)%n))
        faces.append((1+i,1+n+i,1+n+(i+1)%n,1+(i+1)%n))
    obj=kit.mesh(name,vertices,faces,material);obj.location=(x,y,terrain_height(x,y) if ground is None else ground)
    for p in obj.data.polygons:p.use_smooth=True
    return obj


def patch(name,points,width,material,z=.19):
    sampled=[]
    for a,b in zip(points,points[1:]):
        steps=max(1,math.ceil(math.dist(a,b)/1.4))
        sampled.extend([(a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps) for j in range(steps)])
    points=sampled+[points[-1]]
    vertices=[]
    for i,(x,y) in enumerate(points):
        before=Vector(points[max(0,i-1)]);after=Vector(points[min(len(points)-1,i+1)])
        direction=(after-before).normalized();normal=Vector((-direction.y,direction.x))
        w=width*(.93+.065*math.sin(i*.47)+.025*math.sin(i*1.7))
        for sign in [-1,1]:vertices.append((x+normal.x*w/2*sign,y+normal.y*w/2*sign,z+.012*math.sin(i*2.2)))
    kit.mesh(name,vertices,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)],material)


print('ENV_STAGE_LANDSCAPE',flush=True)
kit.group('ENV_01_Landscape')
for obj in list(visual.all_objects):
    if obj.name.startswith(('WF_TownFrozenTerrain','WF_TownSnowField','WF_SnowRidge','WF_HinterlandPine','WF_HinterlandSnowPine','WF_TownSnowBank')):bpy.data.objects.remove(obj,do_unlink=True)
size=CFG['terrain_size'];step=CFG['terrain_step'];n=int(size/step)+1;half=size/2
vertices=[(x*step-half,y*step-half,terrain_height(x*step-half,y*step-half)) for y in range(n) for x in range(n)]
terrain=kit.mesh('BrokenSnowTerrain',vertices,[(y*n+x,y*n+x+1,(y+1)*n+x+1,(y+1)*n+x) for y in range(n-1) for x in range(n-1)],snow)
# Sparse exposed ground uses actual terrain faces, with snow retained around it.
terrain.data.materials.append(rockmat)
for p in terrain.data.polygons:p.use_smooth=True
for i in range(90):
    x=rng.uniform(-420,420);y=rng.uniform(-380,410)
    if abs(x)<117 and abs(y)<108 or abs(x)<15 and y<0:continue
    rx,ry=rng.uniform(3,10),rng.uniform(2,6)
    points=[(x,y,terrain_height(x,y)+.13)]
    for j in range(18):
        angle=j*math.tau/18;radius=rng.uniform(.7,1.15);px=x+math.cos(angle)*rx*radius;py=y+math.sin(angle)*ry*radius
        points.append((px,py,terrain_height(px,py)+.13))
    kit.mesh('IrregularExposedScree',points,[(0,j+1,(j+1)%18+1) for j in range(18)],rockmat)
collision['terrainHeightField']={'origin':[-half,-half],'step':step,'columns':n,'rows':n,'surfaceOffset':.175,'heights':[terrain_height(x*step-half,-(z*step-half)) for z in range(n) for x in range(n)]}
collision['bounds']=[-580,580,-580,580]


def mountain_range(name,cx,cy,angle,length,height,seed):
    rr=random.Random(seed);cols=38;rows=7;verts=[];peaks=[rr.uniform(.50,1.15) for _ in range(cols)]
    for j in range(rows):
        across=(j/(rows-1)-.5)*150;ridge=math.sin(j/(rows-1)*math.pi)**1.5
        for i in range(cols):
            along=(i/(cols-1)-.5)*length;wave=peaks[i]*height*ridge
            px=cx+math.cos(angle)*along-math.sin(angle)*across;py=cy+math.sin(angle)*along+math.cos(angle)*across
            verts.append((px,py,max(-1,wave+rr.uniform(-5,5))))
    obj=kit.mesh(name,verts,[(j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i) for j in range(rows-1) for i in range(cols-1)],rockmat)
    obj.data.materials.append(snow)
    for p in obj.data.polygons:
        if p.center.z>height*.35 and abs(p.normal.z)>.32:p.material_index=1
    stats['mountainRanges']+=1
mountain_range('NorthernRidge',0,430,0,1280,155,701)
mountain_range('DistantHighPeaks',-70,590,0,1490,235,702)
mountain_range('WesternSpurs',-475,85,math.pi/2,650,115,703)
mountain_range('EasternSpurs',490,160,math.pi/2,700,155,704)


def pine(x,y,h,variant):
    # Five irregular bough tiers, dark needles visible under their snow loads.
    n=12;vertices=[];faces=[]
    for k in range(5):
        z=.20+k*.14;r=.25*(1-k*.16)
        first=len(vertices)
        for layer,scale,zz in [(0,1,z),(1,.58,z+.12)]:
            for i in range(n):
                a=i*math.tau/n+variant*.15;rr=r*scale*(1 if i%2 else .63)
                vertices.append((math.cos(a)*rr,math.sin(a)*rr,zz))
        apex=len(vertices);vertices.append((0,0,z+.31))
        for i in range(n):
            faces.append((first+i,first+(i+1)%n,first+n+(i+1)%n,first+n+i))
            faces.append((first+n+i,first+n+(i+1)%n,apex))
    obj=kit.mesh('NorthernSpruce',vertices,faces,needles,('spruce',variant));obj.location=(x,y,terrain_height(x,y));obj.scale=(h,h,h)
    # White upper bough faces, rather than entire white cone silhouettes.
    if len(obj.data.materials)==1:
        obj.data.materials.append(snow)
        for p in obj.data.polygons:
            if p.normal.z>.16 and p.index%4!=0:p.material_index=1
    trunk=kit.cylinder('SpruceTrunk',(x,y,terrain_height(x,y)+h*.40),.14,h*.80,bark,8)
    cylinder_proxy('PineTrunk',x,y,terrain_height(x,y)+h*.4,.22,h*.8)
    stats['pines']+=1


kit.group('ENV_02_Pine_Woods')
clusters=[(-155,-60),(-160,80),(155,65),(155,-65),(-25,160),(80,185),(-105,-180),(175,-180),(-230,150),(255,180),(-280,-210),(290,-250),(-100,290),(150,310)]
for ci,(cx,cy) in enumerate(clusters):
    for j in range(30):
        x=cx+rng.gauss(0,25);y=cy+rng.gauss(0,29)
        if abs(x)<120 and abs(y)<112 or abs(x)<15 and y<0:continue
        pine(x,y,rng.uniform(8,18),ci%3)


print('ENV_STAGE_SNOW_AND_ROCK',flush=True)
kit.group('ENV_03_Snow_Accumulation')
def bank(name,origin,tangent,normal,length,height=.65,depth=1.65):
    sections=9;verts=[]
    for i in range(sections):
        u=(i/(sections-1)-.5)*length;end=math.sin(i/(sections-1)*math.pi)**.35
        for v,z in [(0,.12),(.38,height*end+.10),(depth*.68,height*.38*end+.05),(depth,.045)]:
            verts.append((origin[0]+tangent[0]*u+normal[0]*v,origin[1]+tangent[1]*u+normal[1]*v,z))
    obj=kit.mesh(name,verts,[(i*4+j,i*4+j+1,(i+1)*4+j+1,(i+1)*4+j) for i in range(sections-1) for j in range(3)],snow)
    for p in obj.data.polygons:p.use_smooth=True
    stats['snowDrifts']+=1
    # Conservative shallow bank proxy; low lips can be stepped onto.
    if height>.45:
        center=(origin[0]+normal[0]*depth*.4,origin[1]+normal[1]*depth*.4,height*.42)
        add_box('SnowBank',center,(length*.82 if tangent[0] else depth*.65,depth*.65 if tangent[0] else length*.82,height*.84))


for obj in list(visual.all_objects):
    if 'Curtain' not in obj.name or '_Module' not in obj.name:continue
    x,y,z=obj.location;dx,dy,h=obj.dimensions
    tangent,normal,length=((1,0),(0,1),dx) if dx>dy else ((0,1),(1,0),dy)
    # Choose the leeward inner face; opposite outer faces get intermittent drifts.
    inward=1 if ('West' in obj.name or 'South' in obj.name) else -1
    directions=[inward,-inward]
    for side in directions:
        nn=(normal[0]*side,normal[1]*side);origin=(x+nn[0]*1.55,y+nn[1]*1.55)
        midx=origin[0]+nn[0]*.6;midy=origin[1]+nn[1]*.6
        if not clear_route(midx,midy,1.1,1.8):continue
        if 'InnerCurtainWest' in obj.name and 35<y<69:continue
        if 'OuterCurtainNorth' in obj.name and -46<x<-18:continue
        bank('WallWindDrift',origin,tangent,nn,length*.90,rng.uniform(.38,.88),1.45)


def front_for(b):
    name=b['name']
    if name.startswith(('Merchant','WestWard')):return 'E'
    if name.startswith(('Craft','EastWard')):return 'W'
    if name in ['SouthBarracks','SouthStableRange','WestBulkStore','EastGranary','SouthwestInn','CartersLodge'] or name.endswith('CouncilRange'):return 'N'
    return 'S'


for b in layout['buildings']:
    if b['name']=='GreatKeepComplex':continue
    x,y=b['centerBlender'];w,d=b['size'];front=front_for(b)
    for side,origin,tangent,normal,length in [('N',(x,y+d/2+.25),(1,0),(0,1),w),('W',(x-w/2-.25,y),(0,1),(-1,0),d)]:
        spans=[(-length/2,length/2)] if side!=front else [(-length/2,-2.4),(2.4,length/2)]
        for a,c in spans:
            if c-a<1:continue
            center=(origin[0]+tangent[0]*(a+c)/2,origin[1]+tangent[1]*(a+c)/2)
            if clear_route(center[0]+normal[0]*.7,center[1]+normal[1]*.7,1.1):bank('EaveSnowBuildUp',center,tangent,normal,c-a,.48,1.25)


kit.group('ENV_04_Rocky_Ground')
for i in range(280):
    x=rng.uniform(-270,270);y=rng.uniform(-260,290);r=rng.uniform(.20,1.5)
    if abs(x)<112 and abs(y)<103 or abs(x)<12 and y<0:continue
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1)
    bm.verts.ensure_lookup_table();bm.verts.index_update();points=[tuple(v.co) for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces];bm.free()
    obj=kit.mesh('FrostBrokenRock',points,faces,rockmat,('rock',i%4));obj.location=(x,y,terrain_height(x,y)+r*.18);obj.scale=(r,r*.72,r*.58);obj.rotation_euler.z=rng.random()*math.tau
    if len(obj.data.materials)==1:
        obj.data.materials.append(snow)
        for p in obj.data.polygons:
            if p.normal.z>.4 and p.center.z>.1:p.material_index=1
    if r>.7:cylinder_proxy('LandscapeRock',x,y,terrain_height(x,y)+r*.3,r*.8,r*.6)
    stats['rocks']+=1


print('ENV_STAGE_ROADS',flush=True)
kit.group('ENV_05_Mud_Slush_And_Tracks')
roadways=[([(0,-210),(0,-170),(0,-135),(0,-105),(0,-80),(0,-63)],6.3),([(-96,-55),(-70,-55),(-35,-55),(0,-55),(35,-55),(70,-55),(96,-55)],5.8),([(-12,-59),(-12,-38),(-12,-14),(-12,4),(0,15),(0,34)],5.0),([(-71,-55),(-71,-28),(-71,-4),(-71,30),(-71,77)],3.1),([(71,-55),(71,-28),(71,-4),(71,30),(71,77)],3.1)]
for ri,(points,width) in enumerate(roadways):
    patch('SlushRoadMargin',points,width+1.5,slush,.167)
    patch('WetMuddyRoad',points,width,mud,.193)
    for offset in [-.85,.85]:
        # Continuous wheel grooves follow the cart route, not a scattered noise mask.
        offset_points=[]
        for i,p in enumerate(points):
            a=Vector(points[max(0,i-1)]);b=Vector(points[min(len(points)-1,i+1)]);v=(b-a).normalized()
            offset_points.append((p[0]-v.y*offset,p[1]+v.x*offset))
        patch('CartWheelRut',offset_points,.20,rutmat,.211);stats['wheelRuts']+=1
    for a,b in zip(points,points[1:]):
        length=math.dist(a,b);count=max(1,int(length/1.2))
        tangent=Vector((b[0]-a[0],b[1]-a[1])).normalized()
        for j in range(count):
            if j%3==0:continue
            t=(j+.4)/count;offset=width*.53+.22+(j%2-.5)*.22+.14*math.sin(j*.6)
            x=a[0]+(b[0]-a[0])*t-tangent.y*offset;y=a[1]+(b[1]-a[1])*t+tangent.x*offset
            obj=kit.box('BootPrint',(x,y,.182),(.14,.29,.012),mud,math.atan2(tangent.y,tangent.x)-math.pi/2+(j%2-.5)*.12)
            stats['footprints']+=1


def barrel(x,y,z=.12,r=.48):
    # Staved barrel profile and separate iron hoops / wooden lid.
    n=16;verts=[]
    for zz,rr in [(0,r*.82),(.18,r),(.9,r),(1.12,r*.82)]:
        verts.extend([(math.cos(i*math.tau/n)*rr,math.sin(i*math.tau/n)*rr,zz) for i in range(n)])
    faces=[]
    for k in range(3):
        for i in range(n):faces.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
    faces += [tuple(reversed(range(n))),tuple(range(3*n,4*n))]
    obj=kit.mesh('SupplyBarrel',verts,faces,wood,('barrel',r));obj.location=(x,y,z)
    for zz in [.18,.86]:kit.ring('BarrelIronHoop',(x,y,z+zz),r+.015,.06,.09,iron,16)
    kit.cylinder('BarrelLid',(x,y,z+1.13),r*.79,.055,cutwood,16)
    blob('BarrelSnow',x,y,r*.78,r*.70,.10,snow,int((x+y)*100),ground=z+1.16)
    cylinder_proxy('Barrel',x,y,z+.58,r,1.16);record('barrel',x,y,r);stats['barrels']+=1


def crate(x,y,z=.12,size=1.1):
    kit.box('ProvisionCrate',(x,y,z+size/2),(size,size,size),wood)
    for zz in [z+.12,z+size-.12]:
        for yy in [y-size/2-.03,y+size/2+.03]:kit.box('CrateRim',(x,yy,zz),(size+.07,.10,.12),cutwood)
    kit.beam('CrateDiagonal',(x-size/2,y-size/2-.08,z+.1),(x+size/2,y-size/2-.08,z+size-.1),.12,cutwood)
    blob('CrateSnow',x,y,size*.47,size*.43,.08,snow,int(abs(x*y)),ground=z+size+.015)
    add_box('Crate',(x,y,z+size/2),(size,size,size));record('crate',x,y,size*.71);stats['crates']+=1


def woodpile(x,y,length=3):
    for layer,count in [(0,5),(1,4),(2,3)]:
        for i in range(count):
            yy=y+(i-(count-1)/2)*.32;zz=.29+layer*.27
            log=kit.cylinder('StackedFirewood',(x,yy,zz),.155,length,bark,10);log.rotation_euler.y=math.pi/2
            for side in [-1,1]:
                disk=kit.cylinder('LogEndGrain',(x+side*length/2,yy,zz),.142,.025,cutwood,10);disk.rotation_euler.y=math.pi/2
    blob('TimberStackSnow',x,y,length*.51,.67,.14,snow,22,ground=1.03)
    add_box('FirewoodStack',(x,y,.62),(length,1.7,1.2));record('woodpile',x,y,math.hypot(length/2,.85));stats['woodPiles']+=1


def cart(x,y,yaw=0,loaded=True):
    def p(a,b,z):return (x+math.cos(yaw)*a-math.sin(yaw)*b,y+math.sin(yaw)*a+math.cos(yaw)*b,z)
    for u in [-.85,.85]:kit.beam('CartLongitudinalRail',p(u,-1.65,.92),p(u,1.65,.92),.17,wood)
    kit.box('CartPlankBed',p(0,0,1.03),(2,3.5,.18),wood,yaw)
    for side in [-1,1]:
        for zz in [1.25,1.55,1.85]:kit.box('CartSideBoard',p(side*.99,0,zz),(.10,3.5,.19),cutwood,yaw)
        for yy in [-1.4,1.4]:kit.box('CartUpright',p(side*.98,yy,1.45),(.14,.14,1.15),wood,yaw)
        kit.beam('CartShaft',p(side*.65,-1.5,.8),p(side*.65,-3.8,.60),.12,wood)
        for yy in [-1.1,1.1]:
            wx,wy,wz=p(side*1.2,yy,.67)
            wheel=kit.ring('CartIronTyre',(wx,wy,wz),.68,.10,.13,iron,16);wheel.rotation_euler=(0,math.pi/2,yaw)
            for a in range(8):
                angle=a*math.tau/8
                kit.beam('CartWheelSpoke',p(side*1.2,yy,.67),p(side*1.2,yy+math.cos(angle)*.57,.67+math.sin(angle)*.57),.07,wood)
    if loaded:
        kit.box('CartCoveredLoad',p(0,.2,1.55),(1.6,2.3,.85),cloth,yaw)
        blob('CartLoadSnow',x,y+.2,1,1.2,.13,snow,313,ground=2.01)
    add_box('ParkedCart',(x,y-1.0,1),(2.65,5.6,2));record('cart',x,y,4.1);stats['carts']+=1


def fence(a,b):
    length=math.dist(a,b);count=max(1,round(length/2.2))
    for i in range(count+1):
        t=i/count;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
        kit.box('FencePost',(x,y,.9),(.22,.22,1.6),wood)
        kit.box('PostSnow',(x,y,1.74),(.29,.28,.10),snow)
    for z in [.55,1.25]:kit.beam('FenceRail',(*a,z),(*b,z),.13,wood)
    # The requested fences are axis-aligned and leave known gate openings.
    add_box('YardFence',((a[0]+b[0])/2,(a[1]+b[1])/2,.85),(max(.22,abs(a[0]-b[0])),max(.22,abs(a[1]-b[1])),1.7))
    stats['fenceSegments']+=1


print('ENV_STAGE_WARD_STORIES',flush=True)
kit.group('ENV_06_Trade_And_Supplies')
for x,y in [(-18,-76),(-18,-67),(18,-77),(18,-68),(-92,-48),(92,-48),(-51,27),(-52,31),(51,28),(53,32),(-78,8),(92,8)]:
    if clear_route(x,y,1):
        barrel(x,y);barrel(x+.95,y+.55)
for x,y in [(-15,-80),(16,-82),(-91,-49),(90,-49),(-91,10),(91,10),(-50,34),(53,25),(-25,34),(25,33)]:
    if clear_route(x,y,1):crate(x,y);crate(x+.25,y+.20,1.23,.85)
for x,y in [(-91,2),(92,-16),(-52,30),(53,30),(-65,-63),(-99,-82),(99,-83),(-27,37),(27,37)]:
    if clear_route(x,y,2):woodpile(x,y)
for x,y in [(-99,-69),(99,-73),(-91,7),(16,-62),(-17,-48),(49,28)]:
    if clear_route(x,y,4.2) and building_clear(x,y,1.6):cart(x,y,loaded=(x>0))
for a,b in [((-98,-20),(-98,11)),((74,12),(80,12)),((88,12),(97,12)),((-54,35),(-39,35)),((40,36),(54,36))]:fence(a,b)


def stall(x,y):
    for u in [-1.7,1.7]:
        for v in [-1.15,1.15]:kit.box('MarketStallPost',(x+u,y+v,1.65),(.12,.12,3.1),wood)
    kit.box('StallCounter',(x,y-.8,1.10),(3.6,1.0,.17),cutwood)
    vertices=[]
    for i in range(9):
        u=-1.9+i*3.8/8
        for yy,zz in [(y-1.35,2.65),(y+1.35,3.5)]:vertices.append((x+u,yy,zz+.07*math.sin(i*2.0)))
    roof=kit.mesh('WinterMarketCanvas',vertices,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(8)],cloth)
    add_box('MarketStall',(x,y,1.6),(4,2.9,3.2));record('stall',x,y,2.5)
    for u in [-.9,0,.9]:kit.box('CoveredMarketGoods',(x+u,y-.8,1.4),(.65,.6,.45),straw)
    stats['marketStalls']+=1
for x,y in [(-14,-72),(14,-73),(-16,-62),(16,-48)]:
    if clear_route(x,y,2.6) and building_clear(x,y,1.7):stall(x,y)
for x,y in [(80,8),(92,5),(-92,-17)]:
    if clear_route(x,y,1.7):
        kit.box('BoundFodderStack',(x,y,.85),(2.5,1.5,1.4),straw)
        for u in [-.7,.7]:kit.box('FodderBinding',(x+u,y,.87),(.06,1.56,1.46),wood)
        blob('FodderSnow',x,y,1.3,.8,.2,snow,404,ground=1.55);add_box('FodderStack',(x,y,.8),(2.6,1.6,1.6))


print('ENV_STAGE_FIRE_AND_BANNERS',flush=True)
kit.group('ENV_07_Torches_And_Braziers')
def flame(x,y,z,size=.5):
    for j,(material,scale) in enumerate([(amber,1),(firecore,.55)]):
        vertices=[]
        for zz,r in [(0,size*.32),(.45*size,size*.35),(1.5*size,.015)]:
            for i in range(7):
                a=i*math.tau/7;vertices.append((math.cos(a)*r*scale+zz*.12,math.sin(a)*r*scale,z+zz*scale))
        kit.mesh('LivingFlame',[(vx+x,vy+y,vz) for vx,vy,vz in vertices],[(k*7+i,k*7+(i+1)%7,(k+1)*7+(i+1)%7,(k+1)*7+i) for k in range(2) for i in range(7)],material)
    light_data=bpy.data.lights.new('ENV_TorchLight','POINT');light_data.energy=190 if size<.5 else 340;light_data.color=(1,.36,.085);light_data.shadow_soft_size=.55;light_data.use_shadow=False
    light=bpy.data.objects.new('ENV_TorchLight',light_data);scene.collection.objects.link(light);light.location=(x,y,z+.3);flames.append(light)


def torch(x,y,z=3):
    kit.beam('TorchWallBracket',(x,y+.35,z-.6),(x,y,z),.12,iron)
    kit.box('TorchBackPlate',(x,y+.38,z-.35),(.22,.10,.72),iron)
    kit.cylinder('TorchStaff',(x,y,z),.10,.9,wood,8)
    kit.ring('TorchBasket',(x,y,z+.42),.23,.07,.30,iron,8);flame(x,y,z+.48,.42);stats['torches']+=1


def brazier(x,y):
    kit.cylinder('BrazierFoot',(x,y,.28),.40,.36,iron,10)
    kit.cylinder('BrazierStem',(x,y,.65),.12,.7,iron,8)
    kit.ring('FireBasket',(x,y,1.10),.60,.08,.34,iron,12)
    kit.cylinder('CoalBed',(x,y,1.04),.53,.16,coal,12)
    for i in range(10):
        a=i*math.tau/10;kit.beam('FireBasketRib',(x+math.cos(a)*.4,y+math.sin(a)*.4,.94),(x+math.cos(a)*.6,y+math.sin(a)*.6,1.45),.045,iron)
    flame(x,y,1.15,.72);cylinder_proxy('Brazier',x,y,.72,.67,1.45);record('brazier',x,y,.7);stats['braziers']+=1
for gate in layout['gates']:
    x,y=gate['centerBlender'];r=5.7 if 'Outer' in gate['name'] else 4.8 if 'Inner' in gate['name'] else 4.2
    for sign in [-1,1]:torch(x+sign*(gate['width']/2+r-.1),y-r-.20,3.3)
for x,y,z in [(-57,-64.3,2.3),(-84,69.6,2.3),(77,13.0,2.4),(92,13.0,2.4),(-4,40.2,3),(4,40.2,3)]:torch(x,y,z)
for x,y in [(-7,4),(7,4),(-77,7),(90,7),(-5,35),(5,35)]:
    if clear_route(x,y,.75):brazier(x,y)


kit.group('ENV_08_Northern_Banners')
def banner(x,y,top,width=2.0,height=5.5):
    columns=9;rows=14;verts=[]
    for j in range(rows):
        v=j/(rows-1)
        for i in range(columns):
            u=i/(columns-1)
            verts.append((x+(u-.5)*width,y+.15*math.sin(u*math.tau*1.5+v*2)*v,top-v*height-.4*max(0,1-abs(u-.5)*3)*v**12))
    kit.mesh('WindPulledBanner',verts,[(j*columns+i,j*columns+i+1,(j+1)*columns+i+1,(j+1)*columns+i) for j in range(rows-1) for i in range(columns-1)],cloth)
    kit.beam('BannerCrossbar',(x-width*.6,y,top+.10),(x+width*.6,y,top+.10),.10,iron)
    for sign in [-1,1]:kit.beam('BannerBracket',(x+sign*width*.42,y+.5,top+.5),(x+sign*width*.42,y,top+.1),.10,iron)
    # Original angular wolf emblem, embedded as editable geometry on the cloth.
    outline=[(-.40,-.05),(-.28,.10),(-.12,.12),(-.05,.30),(.08,.40),(.12,.18),(.34,.12),(.46,.01),(.21,-.04),(.10,-.12),(.10,-.34),(-.02,-.34),(-.08,-.12),(-.25,-.10),(-.26,-.30),(-.38,-.30),(-.32,-.05)]
    emblem=[]
    for u,v in outline:
        vv=.45-v*.40;uu=u+.5
        emblem.append((x+u*width*1.25,y+.15*math.sin(uu*math.tau*1.5+vv*2)*vv-.035,top-vv*height))
    kit.mesh('OriginalWolfSigil',emblem,[tuple(range(len(emblem)))],sigil)
    stats['banners']+=1
for gate in layout['gates']:
    x,y=gate['centerBlender'];r=5.7 if 'Outer' in gate['name'] else 4.8 if 'Inner' in gate['name'] else 4.2
    for side in [-1,1]:banner(x+side*(gate['width']/2+r-.1),y-r-.35,17 if r>5 else 19 if r>4.5 else 20,2.2,5.7)
for x in [-17,17]:banner(x,37.2,29,2.2,6.0)
stats['clutterClusters']=len({(round(p['centerBlender'][0]/8),round(p['centerBlender'][1]/8)) for p in placements})


print('ENV_STAGE_ATMOSPHERE',flush=True)
# Atmosphere is separate from the portable geometry. Runtime settings reproduce
# fog/background and lights; glTF carries all prop materials and torch lights.
for obj in scene.objects:
    if obj.type=='LIGHT' and obj.data.type=='SUN':
        obj.data.energy=1.45;obj.data.color=(.70,.81,1.0);obj.data.angle=.40;obj.rotation_euler=(.90,-.35,-.6)
scene.world.use_nodes=True
background=scene.world.node_tree.nodes.get('Background');background.inputs[0].default_value=(.28,.36,.45,1);background.inputs[1].default_value=.60
atmosphere=bpy.data.collections.new('ENV_Atmosphere_Native');scene.collection.children.link(atmosphere)
old_collection=kit.collection;kit.collection=atmosphere
volume=kit.box('ColdValleyHaze',(0,80,85),(1200,1150,220),snow);kit.collection=old_collection
volume_material=bpy.data.materials.new('ENV_NativeValleyHaze');volume_material.use_nodes=True
nodes=volume_material.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');scatter=nodes.new('ShaderNodeVolumeScatter');scatter.inputs['Color'].default_value=(.62,.72,.82,1);scatter.inputs['Density'].default_value=CFG['fog_density'];scatter.inputs['Anisotropy'].default_value=.25
volume_material.node_tree.links.new(scatter.outputs['Volume'],output.inputs['Volume']);volume.data=volume.data.copy();volume.data.materials.clear();volume.data.materials.append(volume_material)
environment={'schemaVersion':1,'coordinateSystem':'glTF Y-up, metres','fog':{'type':'exp2','color':'#9caebb','density':.0018},'background':'#9caebb','hemisphere':{'sky':'#afc6dc','ground':'#343c40','intensity':1.4},'sun':{'position':[-90,150,80],'color':'#c1d8f4','intensity':1.45},'torchLightsEmbedded':True,'presets':{'overcast':{'sunIntensity':1.45,'hemisphereIntensity':1.4},'blueHour':{'sunIntensity':.12,'hemisphereIntensity':.45,'background':'#263c52'}},'nativeFog':'Blender volume is excluded from GLB; apply these runtime fog settings.'}
(OUT/'environment.json').write_text(json.dumps(environment,indent=2))


def camera(name,loc,target,lens=42):
    data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_end=2300
    return obj
cameras={
    'overview':camera('WinterValleyOverview',(252,-307,247),(0,0,7),44),
    'southern-approach':camera('SnowyApproach',(33,-151,12),(0,-92,10),38),
    'market-street':camera('InhabitedMarket',(5,-54,6.0),(-22,-73,4.5),32),
    'stable-yard':camera('StableStory',(74,-18,5.5),(88,8,3.5),29),
    'inner-courtyard':camera('NorthernCourtyard',(25,2,8),(-20,35,12),32),
    'winter-landscape':camera('PineAndMountainContext',(135,-205,24),(0,40,24),35)
}
scene.camera=cameras['overview'];scene['environment_pass']=4
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x,scene.render.resolution_y=CFG['preview_resolution'];scene.render.resolution_percentage=100
scene.render.threads_mode='FIXED';scene.render.threads=4
bpy.context.view_layer.update()
for image in bpy.data.images:
    if image.type=='IMAGE' and image.filepath:
        # Images loaded with a .blend are lazy: has_data alone can skip every
        # inherited texture. Reload the saved PNGs before packing the source.
        if not Path(bpy.path.abspath(image.filepath)).is_file():
            fallback=ROOT/'public/assets/winterfell'/image.name
            assert fallback.is_file(),f'Missing texture {image.name}'
            image.filepath=str(fallback)
        image.source='FILE';image.reload()
        assert len(image.pixels)>0,image.name
        image.pack()
layout.update({'pass':'04-environmental-storytelling','name':'Northern Fortress-Town · Winter Atmosphere Pass 04','previousTerrainMetres':layout['terrainMetres'],'terrainMetres':[size,size],'reviewScope':'Pass-03 architecture and pass-02 zoning preserved; winter landscape and ward props added.'})
(OUT/'layout.json').write_text(json.dumps(layout,indent=2));(OUT/'collision.json').write_text(json.dumps(collision,indent=2))
(OUT/'prop-placements.json').write_text(json.dumps(placements,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'winterfell_fortress_winter.blend'))
objects=list(visual.all_objects);triangles=sum(len(p.vertices)-2 for o in objects if o.type=='MESH' for p in o.data.polygons)
assert triangles<CFG['triangle_budget'],triangles
collection=bpy.data.collections.new('EnvironmentExport');scene.collection.children.link(collection)
print('ENV_STAGE_EXPORT',len(objects),triangles,flush=True)
batched=batches(objects,collection)
# Include only point lights, with the common exporter kept backwards-compatible.
def export(path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in batched+flames:obj.select_set(True)
    bpy.context.view_layer.objects.active=batched[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_cameras=False,export_lights=True)
    normalize_point_lights(path)
export(OUT/'winterfell_fortress.glb')
for obj in batched:mod=obj.modifiers.new('EnvironmentLOD1','DECIMATE');mod.ratio=.34
export(OUT/'winterfell_fortress_lod1.glb')
assert (OUT/'winterfell_fortress.glb').stat().st_size<CFG['glb_size_budget_mb']*1024**2
for obj in list(collection.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.data.collections.remove(collection)
manifest={'schemaVersion':1,'name':layout['name'],'generator':'tools/blender/environment_town.py','blenderVersion':bpy.app.version_string,'source':'artifacts/environment-pass-04/winterfell_fortress_winter.blend','scene':'winterfell_fortress.glb','lods':[{'level':0,'url':'winterfell_fortress.glb','triangles':triangles},{'level':1,'url':'winterfell_fortress_lod1.glb','decimationRatio':.34}],'modules':{},'collision':'collision.json','layout':'layout.json','environment':'environment.json','materials':sorted({m.name for o in objects if o.type=='MESH' for m in o.data.materials}),'renderMeshes':len({m.name for o in objects if o.type=='MESH' for m in o.data.materials}),'collisionProxies':len(collision['colliders']),'units':'metres','upAxis':'Y','details':previous['details'],'environmentDetails':stats,'torchLights':len(flames),'preview':'/assets/winterfell-environment/overview.png','seed':CFG['seed']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
if not args.skip_preview:
    for name,cam in cameras.items():
        print('ENV_RENDER',name,flush=True);scene.camera=cam;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    # A separate blue-hour review makes the warmth of occupied wards legible.
    for obj in scene.objects:
        if obj.type=='LIGHT' and obj.data.type=='SUN':obj.data.energy=.12
    background.inputs[0].default_value=(.08,.14,.23,1);background.inputs[1].default_value=.22
    scene.camera=cameras['southern-approach'];scene.render.filepath=str(OUT/'blue-hour.png');bpy.ops.render.render(write_still=True)
scene.camera=cameras['overview']
(SOURCE/'build-success.json').write_text(json.dumps({'blenderVersion':bpy.app.version_string,'finishedAtUnix':time.time(),'previewRendered':not args.skip_preview,'generationSeconds':round(time.time()-started,2)}))
print('ENV_COMPLETE',json.dumps(manifest),flush=True)
