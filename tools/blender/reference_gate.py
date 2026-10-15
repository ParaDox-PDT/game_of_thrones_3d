"""Solid masonry shoulders above the gate vault, up to its upper chamber."""
import math

def dimensions(width,height):
    bottom=max(height-4.3,5.6+width/2+.70)
    return bottom,height+.9-bottom

def spandrels(kit,material,x,y,z,width,height):
    top,_=dimensions(width,height);radius=width/2+.65
    for j in range(24):
        a=-width/2+j*width/24;b=a+width/24
        za=5.6+math.sqrt(max(0,radius*radius-a*a));zb=5.6+math.sqrt(max(0,radius*radius-b*b))
        vertices=[]
        for depth in [-4.02,4.02]:vertices.extend([(x+a,y+depth,z+za),(x+b,y+depth,z+zb),(x+b,y+depth,z+top),(x+a,y+depth,z+top)])
        kit.mesh('VaultMasonrySpandrel',vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material)
