"""Reusable facade, masonry arch and roof geometry for the reference rebuild."""
import math
from mathutils import Vector

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
        if False:  # Closed doors use the building foundation; no floating threshold stairs.
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
                vx=near[0]+(vx-near[0])*.64;vy=near[1]+(vy-near[1])*.64;vz=maxz+(vz-maxz)*.64
            cap.append((vx,vy,vz+.075))
        eaves=sorted([q for q in p if q[2]==z],key=lambda q:q[1]);ridges=sorted([q for q in p if q[2]==maxz],key=lambda q:q[1])
        if len(eaves)==2 and len(ridges)==2:
            vv=[];ff=[];count=max(5,round(d/1.4));phase=sum(ord(c) for c in name)*.17
            for j in range(count+1):
                t=j/count;edge=.60+.08*math.sin(j*.8+phase)+.035*math.sin(j*2.1+phase)
                r=tuple(ridges[0][k]*(1-t)+ridges[1][k]*t for k in range(3));e=tuple(eaves[0][k]*(1-t)+eaves[1][k]*t for k in range(3))
                vv.extend([(r[0],r[1],r[2]+.08),(r[0]+(e[0]-r[0])*edge,r[1]+(e[1]-r[1])*edge,r[2]+(e[2]-r[2])*edge+.08)])
            ff=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(count)]
            kit.mesh(name+'_WindScouredRoofSnow',vv,ff,snow)
        else:quad(name+'_SnowCap',cap,snow,.045)
    for xx in [x-w/2,x+w/2]:kit.box(name+'_EavesFascia',(xx,y,z-.04),(.16,d+.2,.28),wood)
    kit.box(name+'_Ridge',(x,y,z+h+.06),(.22,d if style!='hipped' else d*.46,.18),trim)
    if style=='clerestory':
        kit.box(name+'_RidgeVentBody',(x,y,z+h+.45),(1.8,d*.60,.9),wood)
        for side in [-1,1]:
            for zz in [z+h+.2,z+h+.45,z+h+.7]:kit.box(name+'_VentLouvre',(x+side*.94,y,zz),(.10,d*.62,.10),dark)
        roof(name+'_VentRoof',x,y,z+h+.9,2.3,d*.66,.7,'gable',mat)
