"""Deterministic tileable PBR images, embedded in every portable district GLB."""
import bpy
import numpy as np


def materials(folder):
    n=512
    y,x=np.mgrid[0:n,0:n].astype(float);u=x/n;v=y/n
    rng=np.random.default_rng(1505)
    grain=rng.random((n,n))-.5
    noise=grain*.16
    # Periodic bilinear fractal noise avoids the visible sinusoidal checker pattern.
    for cells,weight in [(5,.40),(13,.22),(37,.12),(97,.08)]:
        field=rng.random((cells,cells))-.5;fx=u*cells;fy=v*cells
        ix=fx.astype(int);iy=fy.astype(int);tx=fx-ix;ty=fy-iy
        tx=tx*tx*(3-2*tx);ty=ty*ty*(3-2*ty)
        noise+=((field[iy%cells,ix%cells]*(1-tx)+field[iy%cells,(ix+1)%cells]*tx)*(1-ty)+(field[(iy+1)%cells,ix%cells]*(1-tx)+field[(iy+1)%cells,(ix+1)%cells]*tx)*ty)*weight
    result={}
    specs={
      'Stone':((.27,.29,.30),'stone',.89),
      'Trim':((.38,.38,.36),'stone',.88),
      'Timber':((.19,.135,.087),'wood',.85),
      'Slate':((.12,.155,.17),'roof',.77),
      'Shingle':((.23,.195,.15),'roof',.90),
      'Snow':((.78,.83,.85),'snow',.86),
      'Earth':((.235,.215,.185),'earth',.83),
      'Mud':((.15,.125,.092),'earth',.58),
      'Slush':((.47,.49,.47),'earth',.67),
      'Rock':((.24,.27,.27),'rock',.93),
      'Plaster':((.48,.46,.40),'rock',.95),
      'Bark':((.19,.15,.105),'wood',.95),
      'PaleBark':((.64,.65,.59),'wood',.94),
      'Iron':((.065,.077,.08),'rock',.52),
      'Cloth':((.12,.165,.18),'cloth',.97),
      'Water':((.045,.12,.145),'water',.22),
    }
    for name,(color,kind,rough) in specs.items():
        h=.5+noise*.18;ao=np.ones((n,n));variation=1+noise*.20
        if kind=='stone':
            row=np.floor(y/64).astype(int);xx=(x+(row%2)*53+9*np.sin(row*1.7))%128
            yy=y%64
            mortar=(np.minimum(xx,128-xx)<2.3+noise*1.6)|(np.minimum(yy,64-yy)<2.2+noise)
            blocks=(np.sin(np.floor((x+(row%2)*53)/128)*41.7+row*19.31)*.5+.5)
            variation=.90+blocks*.19+noise*.22
            h=np.where(mortar,.15,.66+noise*.12);ao=np.where(mortar,.65,1)
            variation=np.where(mortar,.64,variation)
        elif kind=='wood':
            lines=np.sin(u*6.283*39+np.sin(v*6.283*2)*2.4)
            seams=(x%128<3)
            h=.55+lines*.075+noise*.12;variation=.88+lines*.12+noise*.26
            h=np.where(seams,.18,h);ao=np.where(seams,.66,1)
        elif kind=='roof':
            row=np.floor(y/48).astype(int);xx=(x+row%2*32)%64;yy=y%48
            seam=(xx<2)|(yy<3)
            h=np.where(seam,.15,.35+yy/90+noise*.08)
            variation=np.where(seam,.5,.87+np.sin(row*15.3+np.floor(xx/64)*6.8)*.08+noise*.20)
            ao=np.where(seam,.65,1)
        elif kind=='snow':
            variation=1+noise*.045;h=.5+noise*.035
        elif kind=='cloth':
            h=.5+np.sin(x*3.14159)*np.cos(y*3.14159)*.03+noise*.03
        elif kind=='water':
            h=.5+np.sin(u*6.283*7+np.sin(v*6.283*3))* .11+noise*.06
            variation=.9+noise*.24
        elif kind=='earth':
            h=.5+noise*.25+grain*.12;variation=.9+noise*.5
        rgb=np.clip(np.array(color)[None,None,:]*variation[:,:,None],0,1)
        dx=np.roll(h,-1,axis=1)-np.roll(h,1,axis=1)
        dy=np.roll(h,-1,axis=0)-np.roll(h,1,axis=0)
        normal=np.stack([-dx*2.5,-dy*2.5,np.ones_like(h)],axis=-1)
        normal=normal/np.linalg.norm(normal,axis=-1)[:,:,None]*.5+.5
        orm=np.stack([ao,np.clip(rough+noise*.12,.12,1),np.full_like(h,.75 if name=='Iron' else 0)],axis=-1)
        images=[]
        for suffix,pixels in [('base',rgb),('normal',normal),('orm',orm)]:
            rgba=np.concatenate([pixels,np.ones((n,n,1))],axis=-1).astype(np.float32)
            im=bpy.data.images.new('R5_'+name+'_'+suffix,n,n)
            if suffix!='base':im.colorspace_settings.name='Non-Color'
            im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(folder/(name+'_'+suffix+'.png'));im.file_format='PNG';im.save();im.pack();images.append(im)
        m=bpy.data.materials.new('R5_'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
        nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes.get('Principled BSDF')
        p.inputs['Roughness'].default_value=rough
        for suffix,im in zip(['base','normal','orm'],images):
            tex=nodes.new('ShaderNodeTexImage');tex.image=im
            if suffix=='base':links.new(tex.outputs['Color'],p.inputs['Base Color'])
            elif suffix=='normal':
                nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65 if kind=='stone' else .28
                links.new(tex.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],p.inputs['Normal'])
            else:
                sep=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],sep.inputs['Color'])
                links.new(sep.outputs['Green'],p.inputs['Roughness']);links.new(sep.outputs['Blue'],p.inputs['Metallic'])
        result[name]=m
    for name,color,emission in [('Dark',(.016,.023,.024),0),('WarmWindow',(.36,.19,.07),.3),('Needles',(.035,.075,.054),0),('RedLeaves',(.24,.035,.025),0),('Fodder',(.32,.27,.14),0),('Ember',(1,.28,.045),3),('Foam',(.55,.66,.68),0)]:
        m=bpy.data.materials.new('R5_'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.87
        if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
        result[name]=m
    return result
