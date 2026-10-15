"""Image A driven Winterfell reconstruction. Metres; Blender +Y is north.
Builds independent district collections and GLBs, with local district origins.
"""
import argparse, json, math, random, sys, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--skip-preview',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);ROOT=Path(args.root)
OUT=ROOT/'public/assets/winterfell-reference';ART=ROOT/'artifacts/reference-pass-05'
OUT.mkdir(parents=True,exist_ok=True);ART.mkdir(parents=True,exist_ok=True)
sys.stdout=open(ART/'generation.log','w',encoding='utf-8',buffering=1);sys.stderr=sys.stdout
sys.path.insert(0,str(Path(__file__).parent))
from architecture_kit import Kit,batches
from reference_materials import materials
import reference_architecture as arch
from reference_gate import dimensions as gate_dimensions,spandrels as gate_spandrels
from glb_lighting import normalize_point_lights
PLAN=json.loads((Path(__file__).parent/'reference-layout.json').read_text());R=random.Random(PLAN['seed']);started=time.time()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
root=bpy.data.collections.new('WINTERFELL_REFERENCE');scene.collection.children.link(root)
kit=Kit(root);M=materials(OUT);modules={};buildings=[];props=[];lights=[];stats={'windows':0,'doors':0,'roofVariants':{},'buildings':0,'towers':0,'trees':0,'barrels':0,'carts':0,'snowBanks':0}
collision={'schemaVersion':2,'units':'metres','floor':3,'capsule':{'radius':.36,'height':1.8,'stepHeight':.3},'bounds':[-510,510,-510,510],'colliders':[],'walkableSurfaces':[]}
for key,value in {'kit':kit,'stats':stats,'collision':collision,'stone':M['Stone'],'trim':M['Trim'],'wood':M['Timber'],'metal':M['Iron'],'plaster':M['Plaster'],'slate':M['Slate'],'snow':M['Snow'],'dark':M['Dark']}.items():setattr(arch,key,value)

def group(name,center=(0,0)):
    if name not in modules:
        c=bpy.data.collections.new('WF5_'+name);root.children.link(c);modules[name]={'collection':c,'origin':center}
    kit.collection=modules[name]['collection'];return kit.collection

def box(name,p,size,mat='Stone',yaw=0):return kit.box(name,p,size,M[mat] if isinstance(mat,str) else mat,yaw)
def cyl(name,p,r,h,mat='Stone',n=40):return kit.cylinder(name,p,r,h,M[mat] if isinstance(mat,str) else mat,n)
def beam(name,a,b,w=.16,mat='Timber'):return kit.beam(name,a,b,w,M[mat])
def proxy(name,x,y,z,w,d,h,yaw=0):collision['colliders'].append({'name':name,'type':'box','center':[x,z,-y],'size':[w,h,d],'yaw':yaw})
def diskproxy(name,x,y,z,r,h):collision['colliders'].append({'name':name,'type':'cylinder','center':[x,z,-y],'radius':r,'height':h})
def segdist(x,y,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy or 1)))
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
def inside(x,y,poly):
    result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result
def riverdist(x,y):return min(segdist(x,y,a,b) for a,b in zip(PLAN['river'],PLAN['river'][1:]))
def ground(x,y):
    base=3+.006*y+.45*math.sin(x/73)*math.cos(y/91)
    outside=max(0,max(abs(x)-175,abs(y)-190))
    rough=min(1,outside/55)*(2.2*math.sin(x/29)*math.sin(y/43)+1.2*math.sin((x+y)/18))
    # Incised river banks meet the water plane at -2 m.
    rd=riverdist(x,y);cut=11*max(0,min(1,(32-rd)/13))
    pool=math.sqrt(((x-117)/10)**2+((y+24)/7)**2)
    return base+rough-cut-(1.2*max(0,1-pool)**.35 if pool<1 else 0)
def floorheight(x,y):
    h=ground(x,y)
    if abs(x)<6.5 and -310<y<-217:
        if y<-285:h=max(h,ground(0,-310)+(3.4-ground(0,-310))*(y+310)/25)
        elif y<-234:h=3.4
        else:h=max(h,3.4+(ground(0,-217)-3.4)*(y+234)/17)
    return h
def clearroad(x,y,r=0):return all(segdist(x,y,a,b)>road['width']/2+r+1 for road in PLAN['roads'] for a,b in zip(road['points'],road['points'][1:]))
def clearbuilding(x,y,r=0):
    for b in buildings:
        dx=x-b['center'][0];dy=y-b['center'][1];c=math.cos(b['yaw']);s=math.sin(b['yaw'])
        if abs(dx*c+dy*s)<b['size'][0]/2+r and abs(-dx*s+dy*c)<b['size'][1]/2+r:return False
    return True

def blob(name,x,y,rx,ry,h,mat='Snow',z=None,n=16):
    vertices=[(0,0,h)];rr=random.Random(round(x*17+y*19))
    for scale,zz in [(.5,h*.76),(.86,h*.26),(1,0)]:
        for i in range(n):
            a=i*math.tau/n;v=rr.uniform(.88,1.12);vertices.append((math.cos(a)*rx*scale*v,math.sin(a)*ry*scale*v,zz))
    faces=[(0,1+i,1+(i+1)%n) for i in range(n)]
    for k in range(2):faces.extend([(1+k*n+i,1+k*n+(i+1)%n,1+(k+1)*n+(i+1)%n,1+(k+1)*n+i) for i in range(n)])
    o=kit.mesh(name,vertices,faces,M[mat]);o.location=(x,y,ground(x,y) if z is None else z)
    for p in o.data.polygons:p.use_smooth=True
    return o

def ground_patch(name,x,y,rx,ry,mat):
    n=24;vertices=[];faces=[]
    for j in range(n+1):
        for i in range(n+1):
            xx=x-rx+i*rx*2/n;yy=y-ry+j*ry*2/n
            vertices.append((xx,yy,ground(xx,yy)+.20))
    for j in range(n):
        for i in range(n):
            xx=(i+.5)/n*2-1;yy=(j+.5)/n*2-1
            if xx*xx+yy*yy < .87+.1*math.sin(i*1.1+j*.7):
                k=j*(n+1)+i;faces.append((k,k+1,k+n+2,k+n+1))
    obj=kit.mesh(name,vertices,faces,M[mat])
    for p in obj.data.polygons:p.use_smooth=True
    return obj

def ribbon(name,points,width,mat,offset=.04,water=False):
    samples=[]
    for a,b in zip(points,points[1:]):
        for j in range(max(2,math.ceil(math.dist(a,b)/2))):
            t=j/max(2,math.ceil(math.dist(a,b)/2));samples.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
    samples.append(points[-1]);vertices=[]
    for i,(x,y) in enumerate(samples):
        a=Vector(samples[max(0,i-1)]);b=Vector(samples[min(len(samples)-1,i+1)]);v=(b-a).normalized()
        w=width*(1+.06*math.sin(i*.78)+.025*math.sin(i*1.91))
        for s in [-1,1]:
            xx=x-v.y*w*s/2;yy=y+v.x*w*s/2;zz=-2 if water else floorheight(xx,yy)
            vertices.append((xx,yy,zz+offset))
    o=kit.mesh(name,vertices,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(samples)-1)],M[mat])
    for p in o.data.polygons:p.use_smooth=True
    return o

print('STAGE terrain',flush=True);group('terrain')
step=6;half=540;n=181
verts=[(x*step-half,y*step-half,ground(x*step-half,y*step-half)) for y in range(n) for x in range(n)]
terrain=kit.mesh('SculptedNorthernGround',verts,[(y*n+x,y*n+x+1,(y+1)*n+x+1,(y+1)*n+x) for y in range(n-1) for x in range(n-1)],M['Snow'])
for p in terrain.data.polygons:p.use_smooth=True
collision['terrainHeightField']={'origin':[-half,-half],'step':step,'columns':n,'rows':n,'surfaceOffset':.08,'heights':[floorheight(x*step-half,-(z*step-half)) for z in range(n) for x in range(n)]}
collision['spawn']=[0,floorheight(0,-306)+1.88,306]
group('river',(-190,-20));ribbon('WinterfellRiver',PLAN['river'],42,'Water',0,True)
for a,b in zip(PLAN['river'],PLAN['river'][1:]):
    count=max(1,int(math.dist(a,b)/9))
    for i in range(count):
        t=(i+.5)/count;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
        if abs(x)>24 or not(-290<y<-222):diskproxy('DeepRiver',x,y,-1.4,13,4)
        for side in [-1,1]:
            tx=(b[0]-a[0]);ty=b[1]-a[1];ll=math.hypot(tx,ty);xx=x-ty/ll*side*24;yy=y+tx/ll*side*24
            xx+=R.uniform(-5,5);yy+=R.uniform(-5,5)
            blob('RiverBankRock',xx,yy,R.uniform(2,5),R.uniform(1.8,4),R.uniform(1,3),'Rock',n=20)
            if i%3==0:blob('RiverBankSnow',xx+.3,yy,3,2,.45,'Snow',z=ground(xx,yy)+1.4)
        if i%3==0:ribbon('RiverFoam',[(x-3+R.random()*4,y),(x-1,y-2),(x+R.random()*2,y-5)],R.uniform(.08,.2),'Foam',.055,True)
group('roads')
for i,road in enumerate(PLAN['roads']):
    ribbon(road['name']+'_slushyEdges',road['points'],road['width']+2.2,'Slush',.025+i*.002)
    ribbon(road['name']+'_wornSurface',road['points'],road['width'],'Earth',.065+i*.002)
    if road['width']>5:
        for sign in [-1,1]:ribbon('TrafficRut',[(x+sign*1.15,y) for x,y in road['points']],.27,'Mud',.11+i*.002)

def turn_objects(objs,x,y,yaw):
    if not yaw:return
    bpy.context.view_layer.update()
    matrix=Matrix.Translation((x,y,0))@Matrix.Rotation(yaw,4,'Z')@Matrix.Translation((-x,-y,0))
    for o in objs:o.matrix_world=matrix@o.matrix_world

def building(name,x,y,w,d,h,yaw=0,kind='house',style='gable',chimney=True):
    z=ground(x,y);before=set(kit.collection.objects)
    box(name+'_BatteredFoundation',(x,y,z+.15),(w+.65,d+.65,1.15),'Stone')
    box(name+'_Core',(x,y,z+h/2),(w-1.2,d-1.2,h),'Stone')
    timber=kind in ['house','stable','service'];field=M['Plaster'] if timber else M['Stone']
    for side,origin,tangent,normal,width in [('S',(x,y-d/2),(1,0),(0,-1),w),('N',(x,y+d/2),(1,0),(0,1),w),('W',(x-w/2,y),(0,1),(-1,0),d),('E',(x+w/2,y),(0,1),(1,0),d)]:
        openings=[];front=side=='S';dw=3.5 if kind in ['stable','store'] else 2
        if front:openings.append({'u':0,'w':dw,'bottom':z+.25,'top':z+3.5,'door':True,'arch':not timber})
        levels=[2.3] if h<7 else [2.6,6] if h<12 else list(range(3,int(h-1),4))
        count=max(2,int(width/4.8))
        for zz in levels:
            for k in range(count):
                u=-width/2+(k+1)*width/(count+1)
                if front and zz<4 and abs(u)<dw*.7+1:continue
                openings.append({'u':u,'w':.8 if kind=='store' else 1.05,'bottom':z+zz,'top':min(z+zz+1.8,z+h-.3),'arch':not timber})
        arch.facade(name+'_'+side,origin,tangent,normal,width,z,h,field,openings,timber)
        if not timber:
            for u in [-width/2+.6,width/2-.6]:
                for zz in range(1,int(h),2):arch.local_box('Quoin',origin,tangent,normal,u,.07,z+zz,(1.0,.22,.55),M['Trim'])
    rh=min(8.5,w*.45);roofmat=M['Shingle'] if kind=='service' else M['Slate']
    arch.roof(name,x,y,z+h+.1,w+1.3,d+1.2,rh,style,roofmat)
    if kind in ['hall','keep']:
        for sy in [-1,1]:
            for i in range(max(3,int(d/6))):
                yy=y-d/2+(i+.5)*d/max(3,int(d/6))
                box('SteppedStoneButtress',(x+sy*(w/2+.55),yy,z+h*.38),(1.1,1.35,h*.76),'Stone')
                box('ButtressWeathering',(x+sy*(w/2+.55),yy,z+h*.76),(1.3,1.55,.28),'Trim')
    if chimney:
        cx=x+w*.24;cy=y+d*.22;cz=z+h+rh*.6
        box('HearthStack',(cx,cy,cz+1.8),(1.05,1.3,3.6),'Stone')
        box('ChimneyCoping',(cx,cy,cz+3.6),(1.45,1.65,.3),'Trim')
        box('SootDarkFlue',(cx,cy,cz+3.77),(.7,.9,.06),'Dark')
    if h>=7 and w>10 and kind not in ['stable','store']:
        for sy in [-1,1]:
            xx=x+sy*w*.3;yy=y-d*.12;zz=z+h+rh*.40
            box('DormerHousing',(xx,yy,zz+.7),(2.1,2.4,1.4),'Timber')
            arch.roof('Dormer',xx,yy,zz+1.35,2.7,2.8,1.1,'gable',M['Slate'])
            box('DormerWindow',(xx+sy*1.06,yy,zz+.7),(.04,1.2,1.0),'Dark')
    new=set(kit.collection.objects)-before;turn_objects(new,x,y,yaw)
    proxy(name,x,y,z+h/2,w,d,h,yaw)
    buildings.append({'name':name,'module':next(k for k,v in modules.items() if v['collection']==kit.collection),'center':[x,y],'size':[w,d],'yaw':yaw,'height':h,'ground':z});stats['buildings']+=1

def tower(name,x,y,r=7,h=23,roof=False):
    z=ground(x,y);n=96;windowlevels=list(range(5,int(h-4),5))
    def radius_at(zz):return r*(1.02-.02*(zz-2)/max(1,h-5))
    profile=sorted([(0,r*1.16),(.8,r*1.16),(2,r*1.02),(h-3,r),(h-2.2,r*1.10),(h-.8,r*1.10)]+[(zz+dz,radius_at(zz+dz)) for zz in windowlevels for dz in [-.72,.72]])
    vertices=[(rr*math.cos(i*math.tau/n),rr*math.sin(i*math.tau/n),zz) for zz,rr in profile for i in range(n)]
    faces=[tuple(reversed(range(n)))]+[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for k in range(len(profile)-1) for i in range(n) if not (i%12==1 and any(abs((profile[k][0]+profile[k+1][0])/2-zz)<.71 for zz in windowlevels))]+[tuple(range((len(profile)-1)*n,len(profile)*n))]
    obj=kit.mesh(name+'_BatteredDrum',vertices,faces,M['Stone']);obj.location=(x,y,z)
    for p in obj.data.polygons:p.use_smooth=len(p.vertices)==4
    uv=obj.data.uv_layers.active
    for p in obj.data.polygons:
        for li in p.loop_indices:
            co=obj.data.vertices[obj.data.loops[li].vertex_index].co;uv.data[li].uv=(math.atan2(co.y,co.x)*r/3,co.z/3)
    for zz,rr in [(1.6,r*1.03),(h*.5,r+.08),(h-2.1,r*1.12)]:kit.ring('DrumStringCourse',(x,y,z+zz),rr,.18,.22,M['Trim'],64)
    cyl('TowerWalkDeck',(x,y,z+h-.65),r*1.07,.22,'Earth',64)
    kit.ring('CrenellatedParapet',(x,y,z+h),r*1.10,.7,1.5,M['Stone'],64)
    count=max(12,round(r*2.7))
    for i in range(count):
        a=i*math.tau/count;xx=x+math.cos(a)*r*1.065;yy=y+math.sin(a)*r*1.065
        box('TowerMerlon',(xx,yy,z+h+1.35),(.8,1.25,1.45),'Stone',a)
        box('MerlonSnow',(xx,yy,z+h+2.11),(.88,1.32,.12),'Snow',a)
        box('MachicolationCorbel',(x+math.cos(a)*r*1.04,y+math.sin(a)*r*1.04,z+h-2.2),(.65,.65,.9),'Trim',a)
    for zz in windowlevels:
        for i in range(8):
            a=(i*12+1.5)*math.tau/n;rr=radius_at(zz);ww=rr*math.tau/n
            xx=x+math.cos(a)*(rr-.22);yy=y+math.sin(a)*(rr-.22)
            box('RecessedArrowLoop',(xx,yy,z+zz),(.035,ww+.16,1.5),'Dark',a)
            xx=x+math.cos(a)*(rr+.01);yy=y+math.sin(a)*(rr+.01)
            box('ArrowLoopSill',(xx,yy,z+zz-.8),(.5,ww+.36,.17),'Trim',a)
            box('ArrowLoopLintel',(xx,yy,z+zz+.8),(.48,ww+.36,.17),'Trim',a)
            for side in [-1,1]:box('DeepArrowLoopJamb',(xx-math.sin(a)*side*(ww/2+.07),yy+math.cos(a)*side*(ww/2+.07),z+zz),(.5,.14,1.5),'Trim',a)
    if roof:
        # Tall roofed turret, rather than a flat cylinder cap.
        verts=[(x+math.cos(i*math.tau/48)*r*.83,y+math.sin(i*math.tau/48)*r*.83,z+h+.5) for i in range(48)]+[(x,y,z+h+r*1.5)]
        kit.mesh('SteepTurretRoof',verts,[(i,(i+1)%48,48) for i in range(48)],M['Slate'])
    diskproxy(name,x,y,z+h/2,r*1.03,h);stats['towers']+=1

def wall_run(a,b,h=14,thick=3.3,gaps=()):
    d=Vector(b)-Vector(a);length=d.length;t=d.normalized();yaw=math.atan2(t.y,t.x);normal=(-t.y,t.x)
    intervals=[(0,length)]
    for g in gaps:
        gx,gy=g['center']
        if segdist(gx,gy,a,b)>3.5:continue
        u=(gx-a[0])*t.x+(gy-a[1])*t.y;lo=u-g['width']/2;hi=u+g['width']/2
        intervals=[piece for l,r in intervals for piece in [(l,min(r,lo)),(max(l,hi),r)] if piece[1]-piece[0]>.1]
    for lo,hi in intervals:
        count=max(1,math.ceil((hi-lo)/7))
        for i in range(count):
            u=lo+(hi-lo)*(i+.5)/count;w=(hi-lo)/count;x=a[0]+t.x*u;y=a[1]+t.y*u;z=ground(x,y)
            box('CurtainMasonry',(x,y,z+h/2),(w+.03,thick,h),'Stone',yaw)
            box('BatteredFooting',(x,y,z+.6),(w+.1,thick+.65,1.4),'Trim',yaw)
            box('CurtainCoping',(x,y,z+h+.08),(w+.09,thick+.25,.25),'Trim',yaw)
            for side in [-1,1]:
                xx=x+normal[0]*side*(thick/2+.02);yy=y+normal[1]*side*(thick/2+.02)
                box('WallStringCourse',(xx,yy,z+h*.6),(w,.16,.22),'Trim',yaw)
                stair_gap=side==-1 and any(math.dist((x,y),p)<4 for p in [(-93.2,30.5),(-156.1,111)])
                if not stair_gap:box('WallParapet',(xx,yy,z+h+.55),(w,.48,.9),'Stone',yaw)
                box('Buttress',(xx+normal[0]*side*.3,yy+normal[1]*side*.3,z+h*.34),(.8,.85,h*.68),'Stone',yaw)
            for j in range(max(2,round(w/1.85))):
                uu=-w/2+(j+.5)*w/max(2,round(w/1.85));xx=x+t.x*uu;yy=y+t.y*uu
                for side in [-1,1]:
                    px=xx+normal[0]*side*thick*.43;py=yy+normal[1]*side*thick*.43
                    if side==-1 and any(math.dist((px,py),p)<2.5 for p in [(-92,30.5),(-154.5,111)]):continue
                    box('CurtainMerlon',(px,py,z+h+1.30),(1.0,.65,1.3),'Stone',yaw)
                    box('WallSnowCap',(px,py,z+h+2),(1.08,.73,.13),'Snow',yaw)
            ca=[a[0]+t.x*(lo+(hi-lo)*i/count),a[1]+t.y*(lo+(hi-lo)*i/count)]
            cb=[a[0]+t.x*(lo+(hi-lo)*(i+1)/count),a[1]+t.y*(lo+(hi-lo)*(i+1)/count)]
            collision['colliders'].append({'name':'CurtainWall','type':'wall','a':[ca[0],-ca[1]],'b':[cb[0],-cb[1]],'width':thick,'center':[x,z+h/2,-y],'height':h})
            # Polygon wall walks are represented by thin supported OBB surfaces.
            collision['walkableSurfaces'].append({'name':'CurtainWalk','center':[x,-y],'size':[w,thick],'yaw':yaw,'height':z+h+.22})

def enclosure(points,h,thick,gaps=()):
    for a,b in zip(points,points[1:]+points[:1]):wall_run(a,b,h,thick,gaps)

def gate(g,small=False):
    x,y=g['center'];z=ground(x,y);w=g['width'];h=g['height'];r=3.7 if small else 7.4
    for sign in [-1,1]:tower(g['label']+'_GuardTower',x+sign*(w/2+r-.5),y,r,h+7 if not small else h+4)
    chamber_bottom,chamber_height=gate_dimensions(w,h)
    box('GatehouseUpperChamber',(x,y,z+chamber_bottom+chamber_height/2),(w+2,8,chamber_height),'Stone')
    gate_spandrels(kit,M['Stone'],x,y,z,w,h)
    # True vaulted opening through the gate, with two rings of voussoirs.
    for yy in [y-4.15,y+4.15]:arch.arch('GateArch',(x,yy),(1,0),(0,-1),0,z,w,5.6,M['Trim'],.65,.65)
    for sign in [-1,1]:box('GateRecessJamb',(x+sign*(w/2+.4),y,z+3),(1.0,8,6),'Stone')
    for yy in [y-3.6,y+3.6]:
        for u in range(-int(w/2)+1,int(w/2)):
            box('RaisedPortcullisBar',(x+u*.9,yy,z+9),(.11,.12,3.4),'Iron')
        for zz in [8,9.2,10.4]:box('PortcullisTie',(x,yy,z+zz),(w,.13,.12),'Iron')
    arch.roof('GatehouseRoof',x,y,z+h+.95,w+2.8,9.5,2.8,'gable',M['Slate'])
    proxy('GatehouseOverhead',x,y,z+chamber_bottom+chamber_height/2,w+2,8,chamber_height)
    for sign in [-1,1]:
        # Doors stand against the inner jamb, leaving the central passage open.
        box('OpenOakGateLeaf',(x+sign*(w/2-.12),y+1,z+3),(.22,5.5,6),'Timber')

print('STAGE fortifications',flush=True);group('outer_walls')
outergates=PLAN['gates'][:2]+[{'center':[-166.5,-37],'width':5}]
enclosure(PLAN['outerWall'],15,3.8,outergates)
for i,(x,y) in enumerate(PLAN['outerWall']):
    if any(math.dist((x,y),g['center'])<28 for g in PLAN['gates'][:2]):continue
    tower('PerimeterTower',x,y,8.4 if i in [0,1,2,7,10,11] else 4.2,24 if i in [0,1,2,7,10,11] else 18)
group('gatehouses')
for g in PLAN['gates'][:2]:gate(g)
group('inner_walls',(-10,3));enclosure(PLAN['keepWall'],10.2,2.5,PLAN['gates'][2:])
for x,y in PLAN['keepWall']:
    if min(math.dist((x,y),g['center']) for g in PLAN['gates'][2:])>16:tower('InnerWardTurret',x,y,3.3,14)
for g in PLAN['gates'][2:]:gate(g,True)

print('STAGE central keep',flush=True);group('keep',(-18,4))
building('KeepMainRange',-19,8,49,48,25,kind='keep',chimney=False)
building('KeepSouthernRange',-15,-17,18,53,16,math.pi/2,kind='keep',chimney=False)
for x,y,r,h in [(-48,-12,11.5,39),(18,-12,10.5,37),(-45,34,9.7,43),(20,37,10.2,45),(-22,12,10.5,49)]:tower('GreatKeepDrum',x,y,r,h)
for x,y in [(-6,-35),(9,-35)]:box('KeepEntryButtress',(x,y,ground(x,y)+4),(2.3,3,8),'Stone')

print('STAGE districts',flush=True);group('stables',(-110,105))
for values in [('WestStableRange',-137,105,12,56,6.4),('NorthStableRange',-111,133,12,55,6.8),('EastStableRange',-80,106,11,46,6.1)]:
    name,x,y,w,d,h=values;building(name,x,y,w,d,h,math.pi/2 if 'North' in name else .015,kind='stable',style='clerestory',chimney=False)
building('StableLodge',-139,68,11,13,7,kind='house')
group('guest_houses',(91,111))
for i,(x,y,w,d,angle) in enumerate([(53,128,15,19,-.13),(84,131,17,23,.08),(115,112,16,22,-.18),(49,100,14,18,.12),(79,93,15,21,.02),(116,77,16,22,.20)]):building('GuestHouse'+str(i),x,y,w,d,8.5+i%2,angle,style='hipped' if i%3==0 else 'gable')
group('storehouses',(-126,8))
for i,(x,y) in enumerate([(-130,43),(-127,13),(-127,-15)]):building('Storehouse'+str(i),x,y,14,31,7.3,math.pi/2+.025*i,kind='store',chimney=False)
building('WarehouseOffice',-147,-48,11,16,7,kind='service')
group('kitchens',(-90,-105))
building('KitchenRange',-91,-100,18,40,8.5,-.10,kind='service')
building('Bakehouse',-120,-88,14,20,7.6,.12,kind='service')
building('Scullery',-75,-124,11,17,6.2,.05,kind='service')
for x,y in [(-120,-104),(-113,-105)]:blob('StoneBakeOven',x,y,2.4,2.7,3,'Stone');box('OvenMouth',(x,y-2.4,ground(x,y)+1),(.9,.2,1.1),'Dark')
group('great_hall',(-13,-111));building('GreatHall',-13,-111,25,63,13,math.pi/2,kind='hall',style='clerestory')
for x in [-43,17]:tower('HallStairTurret',x,-111,3.7,21,True)
group('family_quarters',(91,-114))
building('FamilyNorthRange',87,-88,13,53,9.8,math.pi/2+.035)
building('FamilyWestRange',58,-113,12,37,9.2,-.02)
building('FamilyEastRange',116,-115,14,42,10.4,.06)
building('FamilySouthLodge',102,-139,12,23,7.5,math.pi/2,style='hipped')
group('maesters_towers',(150,-109))
for x,y,r,h in [(151,-85,5.2,31),(151,-111,6.1,38),(151,-137,5.0,29)]:tower('MaestersTower',x,y,r,h,True)
building('MaestersGallery',151,-111,5.5,54,12,kind='hall',chimney=False)
group('mill',(-181,-25));building('RiverMill',-181,-25,15,22,8.7,.015,kind='service')
wheel=kit.ring('MillWaterwheel',(-195,-25,.5),5.2,.55,1.9,M['Timber'],48);wheel.rotation_euler.y=math.pi/2
for i in range(20):
    a=i*math.tau/20;y=-25+math.cos(a)*4.9;z=.5+math.sin(a)*4.9
    o=box('WaterwheelPaddle',(-195,y,z),(2.5,1.2,.22),'Timber');o.rotation_euler.x=a
    beam('WheelSpoke',(-196,-25,.5),(-196,y,z),.25)
beam('MillAxle',(-198,-25,.5),(-182,-25,.5),.55)
group('service_buildings')
for i,(x,y,w,d,ang) in enumerate([(-143,-119,11,20,-.08),(-118,-158,13,18,-.3),(-73,-161,12,16,.15),(-46,-167,11,13,-.1),(38,-162,10,14,.12),(137,-48,12,17,.25),(160,56,11,13,.1),(-59,148,10,14,-.18),(-135,151,11,17,1.25)]):building('ServiceWorkshop'+str(i),x,y,w,d,5.7,ang,kind='service',chimney=i%2==0)

print('STAGE bridges and stairs',flush=True);group('bridges')
for y0,y1 in [(-310,-285),(-285,-234),(-234,-217)]:
    points=[(0,y0),(0,y1)];ribbon('SouthBridgeDeck',points,12,'Stone',.13)
    count=max(2,int((y1-y0)/2))
    for i in range(count):
        yy=y0+(y1-y0)*(i+.5)/count;z=floorheight(0,yy)
        for side in [-1,1]:box('BridgeParapet',(side*6.4,yy,z+.7),(.8,(y1-y0)/count+.02,1.3),'Stone')
    if y0==-285:
        for yy in [-280,-263,-246]:
            for side in [-1,1]:box('BridgePier',(side*4.8,yy,-1.1),(2.7,3.8,9),'Stone')
        for yy in [-280,-263]:
            for side in [-1,1]:arch.arch('BridgeArch',(side*6.2,yy+8.5),(0,1),(side,0),0,-2.2,13,1.8,M['Stone'],.85,1)
group('defensive_access')
# Stair beside the northwestern inner wall. Treads rise at 0.25 m to a supported landing.
for index,(x,y,length,height,yaw) in enumerate([(-88,15,31,10.2,0),(-149,90,42,15,0)]):
    z=ground(x,y);height=ground(-93.2 if index==0 else -156.1,y+length/2)+height+.24-z;steps=round(height/.25);run=length/steps
    for i in range(steps):
        lx=0;ly=-length/2+(i+.5)*run;xx=x-math.sin(yaw)*ly;yy=y+math.cos(yaw)*ly;top=z+(i+1)*height/steps
        box('WallAccessTread',(xx,yy,(top+z)/2),(2.3,run+.015,top-z),'Stone',yaw)
        collision['walkableSurfaces'].append({'name':'WallAccessTread','center':[xx,-yy],'size':[2.3,run+.02],'yaw':yaw,'height':top})
    for side in [-1,1]:beam('StairGuardRail',(x+side*1.2,y-length/2,z+1),(x+side*1.2,y+length/2,z+height+1),.13)
    box('WallStairLanding',(x-2,y+length/2,z+height-.2),(6.3,3,.4),'Stone')
    collision['walkableSurfaces'].append({'name':'WallStairLanding','center':[x-2,-y-length/2],'size':[6.3,3],'yaw':0,'height':z+height})

print('STAGE structures complete',stats,flush=True)

def fence(name,points,height=1.5):
    for a,b in zip(points,points[1:]):
        count=max(1,math.ceil(math.dist(a,b)/3));posts=[]
        for j in range(count+1):
            t=j/count;x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t;z=ground(x,y)
            box(name+'Post',(x,y,z+height/2),(.19,.19,height),'Timber');posts.append((x,y,z))
        for p,q in zip(posts,posts[1:]):
            for dz in [.55,height-.12]:beam(name+'Rail',(p[0],p[1],p[2]+dz),(q[0],q[1],q[2]+dz),.12)

def barrel(x,y,scale=1):
    z=ground(x,y);n=16;verts=[]
    for zz,r in [(0,.4),(.15,.46),(.65,.51),(1.15,.46),(1.3,.4)]:
        verts.extend([(x+math.cos(i*math.tau/n)*r*scale,y+math.sin(i*math.tau/n)*r*scale,z+zz*scale) for i in range(n)])
    faces=[tuple(reversed(range(n))),tuple(range(4*n,5*n))]+[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for k in range(4) for i in range(n)]
    kit.mesh('CooperedBarrel',verts,faces,M['Timber'])
    for zz,r in [(.22,.485),(1.08,.485)]:kit.ring('IronBarrelHoop',(x,y,z+zz*scale),r*scale,.035,.08*scale,M['Iron'],24)
    stats['barrels']+=1

def cart(x,y,yaw=0):
    z=ground(x,y);before=set(kit.collection.objects)
    for i in range(6):box('CartBedPlank',(x-1+i*.4,y,z+1),(.38,3.1,.15),'Timber')
    for side in [-1,1]:
        for h in [1.3,1.65,2.0]:box('CartSideboard',(x+side*1.17,y,z+h),(.12,3.2,.25),'Timber')
        for yy in [-1.3,1.3]:box('CartUpright',(x+side*1.2,y+yy,z+1.5),(.15,.16,1.25),'Timber')
        for yy in [-.95,.95]:
            o=kit.ring('CartWheel',(x+side*1.5,y+yy,z+.8),.79,.12,.15,M['Timber'],24);o.rotation_euler.y=math.pi/2
            for j in range(10):
                a=j*math.tau/10;beam('WheelSpoke',(x+side*1.5,y+yy,z+.8),(x+side*1.5,y+yy+math.cos(a)*.71,z+.8+math.sin(a)*.71),.065)
        beam('CartShaft',(x+side*.8,y-1.5,z+1),(x+side*.8,y-4,z+.65),.12)
    turn_objects(set(kit.collection.objects)-before,x,y,yaw);proxy('Cart',x,y,z+1.2,2.7,3.4,2.4,yaw);stats['carts']+=1

def woodpile(x,y):
    z=ground(x,y)
    for row,count in [(0,5),(1,4),(2,3)]:
        for k in range(count):
            o=cyl('SplitFirewood',(x+(k-(count-1)/2)*.39,y,z+.22+row*.34),.2,2.0,'Timber',10);o.rotation_euler.x=math.pi/2
    box('LogPileSnow',(x,y,z+1.12),(1.2,1.8,.12),'Snow')

def torch(x,y,height=2.5):
    z=ground(x,y);beam('TorchPost',(x,y,z),(x,y,z+height),.13)
    cyl('IronBrazier',(x,y,z+height),.28,.32,'Iron',12)
    blob('Embers',x,y,.22,.22,.45,'Ember',z=z+height+.12,n=8)
    data=bpy.data.lights.new('TorchWarmth','POINT');data.energy=160;data.color=(1,.39,.13);data.shadow_soft_size=.3
    o=bpy.data.objects.new('TorchWarmth',data);kit.collection.objects.link(o);o.location=(x,y,z+height+.5);lights.append(o)

def banner(x,y,z,width=2,height=4):
    beam('BannerPole',(x,y,z),(x,y,z+height+.6),.11)
    vertices=[]
    for j in range(9):
        for i in range(5):vertices.append((x+i*width/4,y+math.sin(i*.9+j*.45)*.15,z+height-j*height/8*.75))
    kit.mesh('NorthernWoolBanner',vertices,[(j*5+i,j*5+i+1,(j+1)*5+i+1,(j+1)*5+i) for j in range(8) for i in range(4)],M['Cloth'])
    # Simple pale heraldic stripe is geometry, so it remains visible in the GLB.
    beam('BannerPaleDevice',(x+width*.48,y-.18,z+height*.85),(x+width*.48,y-.18,z+height*.43),width*.12,'Snow')

print('STAGE lived-in yards',flush=True)
group('training_yard',(-17,110))
# Training wear is blended into the landscape texture, without an overlay seam.
for pts in [[(-52,77),(-52,143),(18,143),(18,77)],[(-52,77),(-26,77)],[(-8,77),(18,77)]]:fence('TrainingPalisade',pts,1.6)
for x in [-38,-24,-10,4]:
    y=133;z=ground(x,y);beam('TargetFrame',(x,y,z),(x,y,z+2.1),.16)
    o=cyl('StrawArcheryTarget',(x,y-.15,z+1.7),.72,.20,'Fodder',32);o.rotation_euler.x=math.pi/2
    o=kit.ring('TargetRing',(x,y-.27,z+1.7),.42,.09,.025,M['Cloth'],32);o.rotation_euler.x=math.pi/2
for x,y in [(-37,94),(-13,95),(6,114),(-28,115)]:
    z=ground(x,y);beam('QuintainPost',(x,y,z),(x,y,z+2),.16);beam('QuintainCrossbar',(x-1,y,z+1.7),(x+1,y,z+1.7),.14)
    box('PracticeShield',(x+.8,y,z+1.35),(.55,.18,.8),'Timber')
fence('WeaponRack',[(-48,84),(-48,97)],1.7)
for y in range(85,97,2):beam('PracticeSpear',(-47.5,y,ground(-47.5,y)),(-47.8,y,ground(-47.8,y)+2.8),.055)
for module,clusters in {
    'stables':[(-128,86),(-93,122),(-88,86)],'storehouses':[(-109,36),(-146,30),(-110,-22)],
    'kitchens':[(-105,-111),(-117,-73),(-69,-114)],'guest_houses':[(62,118),(102,92)],
    'family_quarters':[(75,-106),(103,-127)],'keep':[(-70,-20),(49,30)],
    'service_buildings':[(-129,-142),(45,-153),(128,-37)]}.items():
    group(module)
    for i,(x,y) in enumerate(clusters):
        for j in range(4):barrel(x+j%2*1.1,y+j//2*1.1,R.uniform(.8,1.15))
        woodpile(x+3,y);box('SupplyCrate',(x+3,y+3,ground(x+3,y+3)+.6),(1.4,1.1,1.2),'Timber')
        if i==0:cart(x-4 if module=='storehouses' else x+5,y-5,R.uniform(-.5,.5))
group('stables')
for y in [86,103,119]:
    fence('HitchingRail',[(-126,y),(-117,y)],1.4)
    box('StoneWaterTrough',(-117,y+3,ground(-117,y+3)+.45),(3,1.3,.9),'Stone')
    box('TroughWater',(-117,y+3,ground(-117,y+3)+.92),(2.6,.95,.03),'Water')
for x,y in [(-92,126),(-89,126),(-86,126)]:blob('HayBale',x,y,1.2,1.4,1.5,'Fodder')
group('great_hall')
for x,y in [(-36,-132),(9,-132)]:
    z=ground(x,y);box('CourtyardBench',(x,y,z+.55),(4,.7,.18),'Timber')
    for dx in [-1.5,1.5]:box('BenchSupport',(x+dx,y,z+.25),(.3,.6,.5),'Stone')
cyl('CourtyardWell',(-15,-149,ground(-15,-149)+.6),2.4,1.2,'Stone',48)
cyl('WellOpening',(-15,-149,ground(-15,-149)+1.22),1.7,.03,'Dark',48)
group('family_quarters')
for x in [76,85,94]:
    for y in [-109,-120]:
        box('KitchenGardenBed',(x,y,ground(x,y)+.12),(5,7,.25),'Earth')
        fence('GardenWattle',[(x-2.6,y-3.6),(x+2.6,y-3.6),(x+2.6,y+3.6),(x-2.6,y+3.6),(x-2.6,y-3.6)],.65)
group('gatehouses')
for x,y in [(-8,-177),(8,-177),(-8,162),(8,162)]:torch(x,y,3)
for x,y,z in [(-14,-188,27),(14,-188,27),(-14,172,27),(14,172,27)]:banner(x,y,z)
group('inner_walls')
for x,y in [(-6,-64),(7,-64),(-17,64),(-3,64)]:torch(x,y)
group('keep')
for x,y in [(-40,-32),(23,-30)]:torch(x,y,3)
banner(-48,-12,ground(-48,-12)+42,3,5)
group('bridges')
for yy in range(-309,-217,2):
    for side in [-1,1]:proxy('BridgeParapet',side*6.4,yy,floorheight(0,yy)+.7,.8,2.1,1.3)
# Exact analytic bridge surface supplements the coarser landscape heightfield.
for yy in range(-310,-217):
    collision['walkableSurfaces'].append({'name':'BridgeDeck','center':[0,-yy-.5],'size':[12,1.02],'yaw':0,'height':floorheight(0,yy+.5)+.13})

print('STAGE godswood',flush=True);group('godswood',(120,0))
enclosure(PLAN['godswoodWall'],7.2,1.8,[{'center':[110,-54],'width':6}])
for x,y in PLAN['godswoodWall'][1:-1]:tower('GodswoodBoundaryTurret',x,y,2.6,10)
pondx,pondy=117,-24
blob('SacredPool',pondx,pondy,9.7,6.8,.02,'Water',z=ground(pondx,pondy)+1.08,n=64)
for i in range(28):
    a=i*math.tau/28;xx=pondx+math.cos(a)*10.7;yy=pondy+math.sin(a)*7.5
    blob('PoolRimBoulder',xx,yy,R.uniform(.7,1.5),R.uniform(.6,1.2),R.uniform(.5,1.2),'Rock',n=12)

def limb(name,points,radii,material='Bark',n=8):
    source=points;source_radii=radii;points=[];radii=[]
    for k in range(len(source)-1):
        a=Vector(source[max(0,k-1)]);b=Vector(source[k]);c=Vector(source[k+1]);d=Vector(source[min(len(source)-1,k+2)])
        subdivisions=1 if name=='PineBough' else 4
        for j in range(subdivisions):
            t=j/subdivisions;points.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
            radii.append(source_radii[k]*(1-t)+source_radii[k+1]*t)
    points.append(source[-1]);radii.append(source_radii[-1])
    verts=[]
    for i,p in enumerate(points):
        tangent=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])).normalized()
        u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
        for j in range(n):verts.append(tuple(Vector(p)+(u*math.cos(j*math.tau/n)+v*math.sin(j*math.tau/n))*radii[i]))
    faces=[tuple(reversed(range(n))),tuple(range((len(points)-1)*n,len(points)*n))]+[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for k in range(len(points)-1) for i in range(n)]
    obj=kit.mesh(name,verts,faces,M[material])
    for p in obj.data.polygons:p.use_smooth=True
    uv=obj.data.uv_layers.active
    for p in obj.data.polygons:
        for li in p.loop_indices:
            vi=obj.data.loops[li].vertex_index;uv.data[li].uv=((vi%n)/n*max(.5,radii[0]*3),vi//n*.22)
    return obj

def bare_tree(x,y,height=12,sacred=False):
    z=ground(x,y);mat='PaleBark' if sacred else 'Bark';r=height*.055
    limb('AncientWeirwood' if sacred else 'WinterOak',[(x,y,z),(x+.4,y-.2,z+height*.3),(x-.8,y+.3,z+height*.67),(x-.3,y,z+height)],[r*1.6,r,r*.58,.08],mat,14)
    for i in range(9 if sacred else 6):
        a=i*2.399+R.random()*.3;start=z+height*(.28+.05*i);reach=height*R.uniform(.33,.61)
        ex=x+math.cos(a)*reach;ey=y+math.sin(a)*reach;ez=start+height*.4
        points=[(x,y,start),(x+math.cos(a+.2)*reach*.4,y+math.sin(a+.2)*reach*.4,start+height*.19),(ex,ey,ez)]
        limb('GnarledBough',points,[r*.55,r*.28,.06],mat)
        for j in [-1,1]:
            tx=ex+math.cos(a+j*.6)*reach*.4;ty=ey+math.sin(a+j*.6)*reach*.4;tz=ez+height*.13
            limb('BareTwigs',[points[1],(ex,ey,ez),(tx,ty,tz)],[r*.2,.08,.018],mat,6)
            if sacred:
                # Sparse individual leaf planes preserve the branching silhouette.
                vv=[];ff=[]
                for leaf in range(160):
                    px=tx+R.gauss(0,2.1);py=ty+R.gauss(0,2.1);pz=tz+R.gauss(0,.7);size=R.uniform(.12,.26);k=len(vv);a=R.random()*math.tau
                    for dx,dy,dz in [(-1,0,0),(-.5,-.42,.06),(.3,-.46,.08),(1,0,0),(.3,.46,-.05),(-.5,.42,-.04)]:vv.append((px+size*(dx*math.cos(a)-dy*math.sin(a)),py+size*(dx*math.sin(a)+dy*math.cos(a)),pz+dz))
                    ff.append(tuple(range(k,k+6)))
                kit.mesh('CrimsonLeaves',vv,ff,M['RedLeaves'])
    if sacred:
        for i in range(9):
            a=i*math.tau/9;limb('ExposedSacredRoot',[(x,y,z+.7),(x+math.cos(a)*3,y+math.sin(a)*3,z+.18),(x+math.cos(a)*5,y+math.sin(a)*5,ground(x+math.cos(a)*5,y+math.sin(a)*5)+.1)],[.8,.38,.06],mat)
    diskproxy('TreeTrunk',x,y,z+height/2,r,height);stats['trees']+=1

bare_tree(120,4,23,True)
for i in range(48):
    x=R.uniform(86,153);y=R.uniform(-37,43)
    if math.dist((x,y),(120,4))>15 and math.dist((x,y),(117,-24))>13 and clearroad(x,y,2) and segdist(x,y,(143,-30),(120,4))>4:bare_tree(x,y,R.uniform(7,14))

print('STAGE landscape and snow',flush=True);group('landscape')
# Reusable branch-and-needle sprays: no solid cone tree silhouettes.
def pine(x,y,h):
    z=ground(x,y);cyl('PineTrunk',(x,y,z+h*.48),h*.027,h*.96,'Bark',12)
    vv=[];ff=[];sv=[];sf=[]
    for tier in range(9):
        hh=h*(.16+tier*.087);reach=h*(.26-tier*.024)
        for j in range(7):
            a=j*math.tau/7+tier*.57+R.uniform(-.15,.15);ex=x+math.cos(a)*reach;ey=y+math.sin(a)*reach;ez=z+hh-R.uniform(.1,.5)
            limb('PineBough',[(x,y,z+hh),(ex,ey,ez)],[.075,.014],'Bark',5)
            for twig in range(4):
                t=(twig+1)/4;px=x+(ex-x)*t;py=y+(ey-y)*t;wid=reach*.24*(1-t*.45);k=len(vv)
                # Raised, lobed sprays make a broken silhouette at every level.
                vv.extend([(px-math.sin(a)*wid,py+math.cos(a)*wid,ez+.06),(px+math.cos(a)*.45,py+math.sin(a)*.45,ez+.28),(px+math.sin(a)*wid,py-math.cos(a)*wid,ez+.06),(px-math.cos(a)*.35,py-math.sin(a)*.35,ez+.16)])
                ff.append((k,k+1,k+2,k+3))
                if (j+tier+twig)%3!=0:
                    k=len(sv);sv.extend([(px-math.sin(a)*wid*.8,py+math.cos(a)*wid*.8,ez+.10),(px+math.cos(a)*.3,py+math.sin(a)*.3,ez+.34),(px+math.sin(a)*wid*.8,py-math.cos(a)*wid*.8,ez+.10),(px-math.cos(a)*.2,py-math.sin(a)*.2,ez+.23)]);sf.append((k,k+1,k+2,k+3))
    kit.mesh('PineNeedleSprays',vv,ff,M['Needles']);kit.mesh('SnowOnBoughs',sv,sf,M['Snow']);stats['trees']+=1

for i in range(660):
    x=R.uniform(-370,370);y=R.uniform(-360,390)
    if inside(x,y,PLAN['outerWall']) or riverdist(x,y)<34 or not clearroad(x,y,8) or abs(x)<16 and y<-180:continue
    pine(x,y,R.uniform(9,19))
for i in range(380):
    x=R.uniform(-290,290);y=R.uniform(-290,300)
    if not clearroad(x,y,2) or not clearbuilding(x,y,2) or riverdist(x,y)<19:continue
    if inside(x,y,PLAN['outerWall']) and R.random()<.82:continue
    rx=R.uniform(.5,3);ry=R.uniform(.5,2.7);h=R.uniform(.3,1.8)
    blob('GlacialBoulder',x,y,rx,ry,h,'Rock',n=20);blob('RockSnowCap',x+.1,y,rx*.7,ry*.7,h*.15,'Snow',z=ground(x,y)+h*.83,n=16)
group('snow_accumulation')
for b in buildings:
    x,y=b['center'];w,d=b['size'];a=b['yaw'];c=math.cos(a);s=math.sin(a)
    for j in range(7):
        lx=R.uniform(-w/2,w/2);ly=R.choice([-1,1])*(d/2+.7);xx=x+lx*c-ly*s;yy=y+lx*s+ly*c
        if clearroad(xx,yy,.8):blob('LeewardSnowdrift',xx,yy,R.uniform(1,2.8),R.uniform(.6,1.4),R.uniform(.2,.65));stats['snowBanks']+=1
for i in range(210):
    x=R.uniform(-174,174);y=R.uniform(-181,169)
    if inside(x,y,PLAN['outerWall']) and clearroad(x,y,1.4) and clearbuilding(x,y,1.7):blob('WindblownSnow',x,y,R.uniform(1,3),R.uniform(.7,2),R.uniform(.10,.35));stats['snowBanks']+=1
# Low, continuous mountain ridges, with many irregular rounded peaks.
group('distant_ridges')
for ridge in range(3):
    verts=[];rows=12;cols=65
    for j in range(rows):
        for i in range(cols):
            x=-800+i*25;y=410+ridge*105+j*14
            profile=math.sin(math.pi*j/(rows-1))**.8
            height=(42+ridge*22+20*math.sin(i*.31+ridge)+14*math.sin(i*.79+ridge*.9))*profile
            verts.append((x,y,height-3))
    o=kit.mesh('NorthernMountainRidge',verts,[(j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i) for j in range(rows-1) for i in range(cols-1)],M['Snow'])
    for p in o.data.polygons:p.use_smooth=True

print('STAGE terrain surface',flush=True)
# A unique landscape texture breaks snow cover around routes and working yards.
N=2048;gy,gx=np.mgrid[0:N,0:N].astype(np.float32);gx=gx/(N-1)*1080-540;gy=gy/(N-1)*1080-540
rng=np.random.default_rng(1926);noise=np.zeros((N,N),dtype=np.float32)
for cells,weight in [(17,.42),(43,.27),(109,.19),(277,.12)]:
    field=rng.random((cells,cells),dtype=np.float32);fx=(gx+540)/1080*cells;fy=(gy+540)/1080*cells
    ix=fx.astype(int);iy=fy.astype(int);tx=fx-ix;ty=fy-iy;tx=tx*tx*(3-2*tx);ty=ty*ty*(3-2*ty)
    noise+=((field[iy%cells,ix%cells]*(1-tx)+field[iy%cells,(ix+1)%cells]*tx)*(1-ty)+(field[(iy+1)%cells,ix%cells]*(1-tx)+field[(iy+1)%cells,(ix+1)%cells]*tx)*ty)*weight
wear=np.zeros_like(noise)
for road in PLAN['roads']:
    for a,b in zip(road['points'],road['points'][1:]):
        dx=b[0]-a[0];dy=b[1]-a[1];t=np.clip(((gx-a[0])*dx+(gy-a[1])*dy)/(dx*dx+dy*dy or 1),0,1)
        dist=np.sqrt((gx-a[0]-t*dx)**2+(gy-a[1]-t*dy)**2)
        wear=np.maximum(wear,np.exp(-dist**2/(road['width']+5)**2))
for b in buildings:
    x,y=b['center'];c=math.cos(b['yaw']);s=math.sin(b['yaw']);dx=gx-x;dy=gy-y
    dist=np.maximum(np.abs(dx*c+dy*s)-b['size'][0]/2,np.abs(-dx*s+dy*c)-b['size'][1]/2)
    wear=np.maximum(wear,np.exp(-np.maximum(0,dist)**2/35)*.75)
wood=np.exp(-(((gx-120)/32)**2+((gy-2)/45)**2))* .7
wear=np.maximum(wear,wood)
wear=np.maximum(wear,np.exp(-(((gx+17)/29)**4+((gy-109)/29)**4))*.6)
mix=np.clip((noise-.47)*2.8+wear*.62,0,.85)
rgb=np.array([.76,.80,.81])[None,None,:]*(1-mix[:,:,None])+np.array([.34,.33,.29])[None,None,:]*mix[:,:,None]
rgb*=.96+noise[:,:,None]*.08
im=bpy.data.images.new('R5_LandscapeSnowWear',N,N);im.pixels.foreach_set(np.concatenate([rgb,np.ones((N,N,1))],axis=-1).astype(np.float32).ravel());im.filepath_raw=str(OUT/'LandscapeSnowWear.png');im.file_format='PNG';im.save();im.pack()
landmat=M['Snow'].copy();landmat.name='R5_LandscapeSnowWear';nodes=landmat.node_tree.nodes;links=landmat.node_tree.links
base=next(node for node in nodes if node.type=='TEX_IMAGE' and node.image.name.endswith('_base'));base.image=im
uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map='LandscapeUV';links.new(uvnode.outputs['UV'],base.inputs['Vector'])
terrain.data.materials.clear();terrain.data.materials.append(landmat)
uv=terrain.data.uv_layers.new(name='LandscapeUV')
for li,loop in enumerate(terrain.data.loops):
    co=terrain.data.vertices[loop.vertex_index].co;uv.data[li].uv=((co.x+540)/1080,(co.y+540)/1080)
# The terrain has its own second UV set, so preserve it directly at export.
del gx,gy,noise,wear,wood,mix,rgb,field,fx,fy,ix,iy,tx,ty,dist

print('STAGE bevels',flush=True)
# Bevel unique box meshes once; linked details share the finished geometry.
for key,mesh in list(kit.cache.items()):
    if key[0]!='box':continue
    width=min(.045,min(key[1])*.12)
    if width<.008:continue
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.bevel(bm,geom=list(bm.edges),offset=width,segments=1,affect='EDGES')
    bm.to_mesh(mesh);bm.free();mesh.update()
    uv=mesh.uv_layers.active
    for p in mesh.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
        for li in p.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]/3,co[axes[1]]/3)

print('STAGE lighting and cameras',flush=True)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1600;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.43,.51,.61,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.45
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.35
lightdata=bpy.data.lights.new('ColdOvercastSun','SUN');lightdata.energy=2.3;lightdata.angle=math.radians(18);lightdata.color=(.86,.91,1)
sun=bpy.data.objects.new('ColdOvercastSun',lightdata);root.objects.link(sun);sun.rotation_euler=(math.radians(28),math.radians(-24),math.radians(-32))
for name,pos,power,size in [('CloudSoftbox',(30,-150,250),1800000,450),('NorthernSkyFill',(-250,180,210),950000,400)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=(.83,.9,1)
    ob=bpy.data.objects.new(name,data);root.objects.link(ob);ob.location=pos;ob.rotation_euler=(-Vector(pos)).to_track_quat('-Z','Y').to_euler()
cameras={}
def camera(name,pos,target,scale=None,lens=42):
    data=bpy.data.cameras.new(name);data.clip_end=4000;data.lens=lens
    if scale:data.type='ORTHO';data.ortho_scale=scale
    ob=bpy.data.objects.new(name,data);root.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler();cameras[name]=ob;return ob
camera('01_reference_overview',(0,-470,720),(0,-20,6),540)
camera('02_top_down',(0,-20,850),(0,-20,0),485)
camera('03_south_gate',(35,-279,20),(0,-181,18),lens=35)
camera('04_keep',(-68,-69,15),(-12,9,29),lens=26)
camera('05_godswood',(143,-30,9),(120,4,15),lens=30)
camera('06_training_yard',(-30,78,7),(-15,125,9),lens=24)
camera('07_river_mill',(-245,-63,16),(-179,-24,10),lens=34)
camera('08_great_hall',(32,-154,10),(-13,-110,13),lens=30)
scene.camera=cameras['01_reference_overview'];bpy.context.view_layer.update()
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=4000;area.spaces.active.shading.type='MATERIAL'
scene['reference']='Image A.png supplied by user; artistic layout interpretation, not a surveyed plan.'
scene['pass']=5;scene['north_axis']='Blender +Y; glTF -Z'
for o in root.all_objects:
    if o.type=='MESH':o.name=o.name.replace('D3_','WF5_');o['detail_pass']=5
blend=ART/'winterfell_reference.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

print('STAGE modular exports',flush=True)
manifest={'schemaVersion':1,'name':'Winterfell — Image A reconstruction','units':'metres','north':'-Z','modules':[],'districts':PLAN['districts'],'stats':stats,'layout':{'outerWall':PLAN['outerWall'],'keepWall':PLAN['keepWall'],'roads':PLAN['roads']},'views':{}}
for name,ob in cameras.items():
    # Three.js receives the same positions with the Blender Z-up transform.
    direction=ob.rotation_euler.to_quaternion()@Vector((0,0,-1));target=ob.location+direction*100
    manifest['views'][name]={'position':[ob.location.x,ob.location.z,-ob.location.y],'target':[target.x,target.z,-target.y]}
for name,record in modules.items():
    print('EXPORT',name,flush=True);collection=bpy.data.collections.new('TEMP_EXPORT');scene.collection.children.link(collection)
    if name=='terrain':
        duplicate=terrain.copy();duplicate.data=terrain.data.copy();collection.objects.link(duplicate);objs=[duplicate]
    else:objs=batches(list(record['collection'].objects),collection)
    ox,oy=record['origin']
    for ob in objs:ob.location=(-ox,-oy,0)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objs:ob.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    path=OUT/(name+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
    triangles=sum(len(p.vertices)-2 for o in objs for p in o.data.polygons)
    manifest['modules'].append({'id':name,'url':'/assets/winterfell-reference/'+path.name,'position':[ox,0,-oy],'bytes':path.stat().st_size,'triangles':triangles,'meshes':len(objs)})
    for ob in objs:
        mesh=ob.data;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
    bpy.data.collections.remove(collection)
manifest['stats']['triangles']=sum(m['triangles'] for m in manifest['modules'])
manifest['stats']['exportBytes']=sum(m['bytes'] for m in manifest['modules'])
manifest['stats']['sourceObjects']=len(root.all_objects)
manifest['torches']=[{'position':[o.location.x,o.location.z,-o.location.y],'color':'#ff7833','intensity':35,'distance':13} for o in lights]
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(OUT/'collision.json').write_text(json.dumps(collision,separators=(',',':')),encoding='utf-8')
(OUT/'environment.json').write_text(json.dumps({'background':'#9baab7','fog':{'density':.00065},'hemisphere':{'sky':'#d6e4ee','ground':'#646361','intensity':1.25},'sun':{'color':'#e4efff','intensity':2.2}},indent=2))
(ART/'buildings.json').write_text(json.dumps(buildings,indent=2))
(ART/'layout-analysis.json').write_text(json.dumps(PLAN,indent=2))
if not args.skip_preview:
    for name,ob in cameras.items():
        print('RENDER',name,flush=True);scene.camera=ob;scene.render.filepath=str(ART/(name+'.png'));bpy.ops.render.render(write_still=True)
scene.camera=cameras['01_reference_overview']
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
(ART/'build-success.json').write_text(json.dumps({'ok':True,'blender':bpy.app.version_string,'elapsedSeconds':round(time.time()-started),'blend':str(blend),'modules':len(modules),'stats':stats},indent=2))
print('DONE',stats,flush=True)
