"""Pass 02: fortress-town spatial massing. Reuses the existing material/mesh kit.
No prop dressing, texture refinements, or changes to the shipped prototype.
"""
import math
import random
from contextlib import contextmanager
import bpy


def build(api):
    box, cylinder, roof = (api[key] for key in ['box','cylinder','roof'])
    wall, tower, crenels = (api[key] for key in ['wall_run','tower','crenels'])
    stone, trim, wood, snow, ground, dirt = (api[key] for key in ['stone','trim','wood','snow','ground','dirt'])
    visual = api['visual']
    buildings, courts, zones, gates = [], [], [], []

    @contextmanager
    def zone(name):
        print('LAYOUT_ZONE_BEGIN', name, flush=True)
        before = set(visual.all_objects)
        collection = bpy.data.collections.new('ZONE_' + name)
        visual.children.link(collection)
        yield
        for obj in set(visual.all_objects) - before:
            collection.objects.link(obj)
            if obj.name in visual.objects: visual.objects.unlink(obj)
            obj['zone'] = name
        print('LAYOUT_ZONE_COMPLETE', name, len(collection.objects), flush=True)

    def court(name, x, y, w, d, kind='service'):
        box(name+'_Court',(x,y,.015),(w,d,.13),dirt if kind=='service' else trim)
        courts.append({'name':name,'centerBlender':[x,y],'size':[w,d],'function':kind})

    def road(name,x,y,w,d):
        box(name,(x,y,.095),(w,d,.10),dirt)

    def building(name,x,y,w,d,h=6,kind='timber'):
        box(name+'_Foundation',(x,y,.5),(w+.5,d+.5,1),stone,.05)
        box(name+'_Mass',(x,y,h/2+.65),(w,d,h),wood if kind=='timber' else stone,.06,collide=True)
        roof(name+'_Roof',x,y,h+.7,w+1,d+1,min(5.8,w*.38))
        buildings.append({'name':name,'centerBlender':[x,y],'size':[w,d],'height':h,'type':kind})

    def ring(name,x0,x1,y0,y1,h,gate_x,gap):
        wall(name+'West',(x0), (y0+y1)/2,y1-y0,'y',h)
        wall(name+'East',(x1), (y0+y1)/2,y1-y0,'y',h)
        wall(name+'North',(x0+x1)/2,y1,x1-x0,'x',h)
        for a,b in [(x0,gate_x-gap/2),(gate_x+gap/2,x1)]:
            wall(name+'South',(a+b)/2,y0,b-a,'x',h)

    def gate(name,x,y,gap,shaft_radius,shaft_height,clearance=8):
        offset=gap/2+shaft_radius-.1
        for side in [-1,1]:tower(name+'_Tower',x+side*offset,y,shaft_radius,shaft_height)
        box(name+'_Bridge',(x,y,clearance+3.2),(gap+2,7.5,6.4),stone,.08,collide=True)
        for yy in [y-3.75,y+3.75]:crenels(x,yy,clearance+7,gap+2)
        for side in [-1,1]:box(name+'_OpenGate',(x+side*(gap/2+.2),y+2.3,3.6),(.28,6.8,7.2),wood,.03,collide=True)
        gates.append({'name':name,'centerBlender':[x,y],'width':gap,'clearance':clearance})

    with zone('00_Snowy_Hinterland'):
        box('TownFrozenTerrain',(0,0,-.7),(480,480,1.3),ground)
        box('TownSnowField',(0,0,-.065),(478,478,.12),snow)
        # Low ridges and dispersed pine groups establish a larger setting without
        # overwhelming the settlement silhouette or revisiting material detail.
        for i in range(24):
            a=i*math.tau/24
            x=math.cos(a)*random.uniform(188,220);y=math.sin(a)*random.uniform(188,220)
            r=random.uniform(18,31);h=random.uniform(18,43)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,0))
            ob=api['relocate'](bpy.context.object,'SnowRidge',snow);ob.scale=(r,r*.85,h)
        for i in range(170):
            x=random.uniform(-205,205);y=random.uniform(-205,205)
            if abs(x)<119 and abs(y)<110 or abs(x)<13 and y<0:continue
            h=random.uniform(6,13)
            cylinder('HinterlandPineTrunk',(x,y,h*.25),.22,h*.5,wood,6)
            for k in range(2):
                bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=h*(.24-k*.07),radius2=0,depth=h*.65,location=(x,y,h*(.43+k*.26)))
                api['relocate'](bpy.context.object,'HinterlandSnowPine',snow)
        for i in range(75):
            x=random.uniform(-160,160);y=random.uniform(-150,150)
            if abs(x)<111 and abs(y)<102:continue
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,-.05))
            ob=api['relocate'](bpy.context.object,'TownSnowBank',snow);ob.scale=(random.uniform(3,8),random.uniform(2,6),random.uniform(.3,1.3))

    with zone('01_Outer_Defences'):
        box('TownWardGround',(0,0,-.01),(204,184,.13),ground)
        ring('OuterCurtain',-104,104,-94,94,10,0,14)
        for x in [-104,104]:
            for y in [-94,94]:tower('OuterCornerTower',x,y,5.5,18)
            for y in [-48,0,48]:tower('OuterFlankingTower',x,y,4.6,16)
        for x in [-53,0,53]:tower('NorthOuterTower',x,94,4.6,17)
        for x in [-58,58]:tower('SouthOuterTower',x,-94,4.6,17)
        gate('OuterGatehouse',0,-94,14,5.7,20,8.5)

    with zone('02_Trade_And_Arrival_Ward'):
        court('ArrivalMarket',0,-62,42,32,'market / public arrival')
        road('SouthApproach',0,-123,12,62)
        road('ArrivalSpine',0,-77,12,34)
        road('MarketToInnerGate',-12,-41,10,36)
        road('MarketCrossStreet',0,-55,181,7)
        # Paired rows frame the market while its centre remains an open square.
        for x in [-35,33]:
            for i,y in enumerate([-83,-68,-37]):
                building(('MerchantHouse' if x<0 else 'CraftWorkshop')+str(i),x,y,14,13,6.5)
        building('SouthwestInn',-57,-76,20,19,8,'stone')
        building('CartersLodge',57,-77,18,18,6)
        building('WestBakehouse',-55,-38,15,15,6)
        building('EastWorkshop',55,-37,15,15,6)

    with zone('03_West_Military_Ward'):
        court('MusterAndTraining',-84,-5,27,33,'military / drill')
        building('SouthBarracks',-84,-35,22,20,7.5,'stone')
        building('NorthBarracks',-84,28,22,20,7.5,'stone')
        building('OfficerBarracks',-84,55,21,17,8,'stone')
        building('Quartermaster',-84,77,22,12,6.5)
        road('WestWardLane',-71,12,4,126)
        zones.append({'name':'Military ward','centerBlender':[-84,15],'purpose':'Barracks, muster ground and quartermaster; separate from public arrival.'})

    with zone('04_East_Stable_Ward'):
        court('StableExerciseYard',84,-5,25,34,'stable / exercise')
        building('SouthStableRange',84,-36,22,22,5.8)
        building('NorthStableRange',84,31,22,30,6.5)
        building('FodderBarn',84,66,22,17,8)
        box('StableYardEastBoundary',(97,-5,.9),(.28,34,1.8),wood,collide=True)
        # Leave a ten-metre west entry aligned to the service lane.
        for y in [-16,6]:box('StableYardWestBoundary',(74,y,.9),(.28,12,1.8),wood,collide=True)
        road('EastWardLane',71,12,4,126)
        zones.append({'name':'Stable ward','centerBlender':[84,10],'purpose':'Long stable ranges face a dedicated exercise yard; fodder stored to the north.'})

    with zone('05_Bulk_Storage'):
        building('WestBulkStore',-84,-73,22,24,8,'stone')
        building('EastGranary',84,-73,22,24,10,'stone')
        court('WestUnloadingYard',-83,-52,25,10)
        court('EastUnloadingYard',83,-52,25,10)
        road('NorthServiceCircuit',0,87,195,6)
        zones.append({'name':'Storage and receiving','centerBlender':[0,-76],'purpose':'Bulk stores sit near the outer gate and cross street, before inner security.'})

    with zone('06_Inner_Defences'):
        ring('InnerCurtain',-64,64,-25,80,13,-12,12)
        for x in [-64,64]:
            for y in [-25,80]:tower('InnerCornerTower',x,y,4.8,22,True)
            tower('InnerFlankingTower',x,30,4.1,20)
        gate('InnerGatehouse',-12,-25,12,4.8,23,8)

    with zone('07_Protected_Inner_Ward'):
        court('GreatAssemblyCourt',0,4,67,39,'ceremonial / inner assembly')
        road('InnerCeremonialLane',-12,0,10,42)
        road('CitadelApproach',0,15,10,22)
        court('WestResidentialCourt',-46,29,22,14,'residential')
        court('EastHouseholdCourt',47,29,22,14,'household / domestic')
        for side in [-1,1]:
            for i,y in enumerate([-9,14,44,66]):
                building(('WestWardHouse' if side<0 else 'EastWardHouse')+str(i),side*47,y,15,14,7 if i<2 else 8,'stone' if i==3 else 'timber')
        building('WestCouncilRange',-24,-10,13,12,9,'stone')
        building('EastCouncilRange',24,-10,13,12,9,'stone')
        road('WestInnerLane',-35,31,5,91)
        road('EastInnerLane',35,31,5,91)
        zones.append({'name':'Protected inner ward','centerBlender':[0,4],'purpose':'Large assembly court with household and residential side courts, entered through an offset gate.'})

    with zone('08_Citadel_And_Great_Keep'):
        ring('CitadelCurtain',-32,32,25,74,16,0,10)
        gate('CitadelGatehouse',0,25,10,4.2,25,8)
        court('KeepForecourt',0,34,44,15,'citadel / keep forecourt')
        # Strong stepped silhouette: broad lower keep, tall upper donjon, and
        # four independent corner masses rather than a single oversized house.
        box('GreatKeepLower',(0,55,13),(30,27,26),stone,.15,collide=True)
        box('GreatKeepPlinth',(0,55,1),(32,29,2),trim,.10)
        box('GreatKeepUpper',(0,57,34),(19,18,16),stone,.12,collide=True)
        box('GreatKeepUpperTerrace',(0,57,42.1),(19,18,.2),snow)
        for y in [48,66]:crenels(0,y,42.7,19)
        for x in [-9.5,9.5]:crenels(x,57,42.7,18,'y')
        for x in [-17,17]:
            for y in [42,68]:tower('GreatKeepCorner',x,y,4.4,34,True)
        for x in [-24,24]:building('KeepSideHall',x,55,10,22,15,'stone')
        buildings.append({'name':'GreatKeepComplex','centerBlender':[0,55],'size':[58,40],'height':43.4,'type':'stepped keep / four corner towers'})
        zones.append({'name':'Great Keep citadel','centerBlender':[0,55],'purpose':'Third defensible enclosure and keep forecourt; 43 m donjon dominates all surrounding roofs.'})

    # Shared metadata lets the exporter and review checks use this exact layout.
    info={
        'pass':'02-layout-massing','name':'Northern Fortress-Town · Layout Pass 02',
        'footprintMetres':[208,188],'prototypeFootprintMetres':[76,64],
        'footprintAreaMultiplier':round(208*188/(76*64),2),
        'terrainMetres':[480,480],'defensiveRings':3,'maximumKeepHeightMetres':43.4,
        'buildingCount':len(buildings),'buildings':buildings,'courtyards':courts,'zones':zones,'gates':gates,
        'routes':[
            {'name':'Gate-to-keep route','pointsBlender':[[0,-130],[0,-63],[-12,-55],[-12,4],[0,15],[0,34]],'minimumIntendedWidth':6},
            {'name':'Military supply access','pointsBlender':[[0,-62],[0,-55],[-71,-55],[-71,-5],[-84,-5]],'minimumIntendedWidth':4},
            {'name':'Stable supply access','pointsBlender':[[0,-62],[0,-55],[71,-55],[71,-5],[84,-5]],'minimumIntendedWidth':4}
        ],
        'spawn':[0,1.92,125],'bounds':[-230,230,-230,230],
        'overviewCamera':[252,-307,247],'overviewTarget':[0,0,7],
        'reviewScope':'Intermediate layout and scale. Existing material kit reused unchanged. No new tiny props or texture polish. Building interiors remain closed.'
    }
    api['layout_info'].update(info)
