"""Lightweight linked-mesh construction and glTF batching for architecture passes."""
import math
import bpy
from mathutils import Vector


class Kit:
    def __init__(self, parent):
        self.parent=parent
        self.collection=parent
        self.cache={}

    def group(self,name):
        collection=bpy.data.collections.new('DETAIL_'+name)
        self.parent.children.link(collection)
        self.collection=collection
        return collection

    def mesh(self,name,vertices,faces,material,cache_key=None,smooth=False):
        key=cache_key
        if key is not None and key in self.cache:
            data=self.cache[key]
        else:
            data=bpy.data.meshes.new(name)
            data.from_pydata(vertices,[],faces);data.materials.append(material);data.update()
            uv=data.uv_layers.new(name='UVMap')
            for p in data.polygons:
                axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
                for li in p.loop_indices:
                    co=data.vertices[data.loops[li].vertex_index].co
                    uv.data[li].uv=(co[axes[0]]/3,co[axes[1]]/3)
                p.use_smooth=smooth and abs(p.normal.z)<.8
            if smooth:
                normals=[]
                for p in data.polygons:
                    for li in p.loop_indices:
                        co=data.vertices[data.loops[li].vertex_index].co
                        radial=Vector((co.x,co.y,0)).normalized()
                        dot=p.normal.dot(radial)
                        normals.append(tuple(radial*(1 if dot>0 else -1)) if abs(dot)>.85 else tuple(p.normal))
                data.normals_split_custom_set(normals)
            if key is not None:self.cache[key]=data
        obj=bpy.data.objects.new('D3_'+name,data);self.collection.objects.link(obj)
        obj['detail_pass']=3
        return obj

    def box(self,name,loc,size,mat,yaw=0):
        x,y,z=(s/2 for s in size)
        vertices=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        obj=self.mesh(name,vertices,faces,mat,('box',tuple(round(s,4) for s in size),mat.name))
        obj.location=loc;obj.rotation_euler.z=yaw
        return obj

    def beam(self,name,a,b,width,mat):
        delta=Vector(b)-Vector(a)
        obj=self.box(name,(Vector(a)+Vector(b))/2,(width,width,delta.length),mat)
        obj.rotation_mode='QUATERNION';obj.rotation_quaternion=delta.to_track_quat('Z','Y')
        return obj

    def cylinder(self,name,loc,r,h,mat,n=32):
        vertices=[(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for z in [-h/2,h/2] for i in range(n)]
        faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        obj=self.mesh(name,vertices,faces,mat,('cylinder',r,h,mat.name,n),smooth=True);obj.location=loc
        return obj

    def ring(self,name,loc,r,thickness,h,mat,n=48):
        vertices=[];faces=[]
        for i in range(n):
            a=i*math.tau/n;b=(i+1)*math.tau/n
            index=len(vertices)
            vertices += [(rr*math.cos(t),rr*math.sin(t),zz) for zz in [-h/2,h/2] for rr,t in [(r,a),(r,b),(r-thickness,b),(r-thickness,a)]]
            faces += [tuple(index+j for j in p) for p in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(2,3,7,6)]]
        obj=self.mesh(name,vertices,faces,mat,('ring',r,thickness,h,mat.name,n));obj.location=loc
        return obj


def batches(objects,collection):
    buckets={}
    for obj in objects:
        if obj.type!='MESH':continue
        matrix=obj.matrix_world
        normal_matrix=matrix.to_3x3().inverted().transposed()
        for poly in obj.data.polygons:
            mat=obj.data.materials[poly.material_index]
            bucket=buckets.setdefault(mat.name,{'v':[],'f':[],'uv':[],'normals':[],'mat':mat})
            indices=[]
            for li in poly.loop_indices:
                vi=obj.data.loops[li].vertex_index
                indices.append(len(bucket['v']));bucket['v'].append(tuple(matrix@obj.data.vertices[vi].co))
                bucket['uv'].append(tuple(obj.data.uv_layers.active.data[li].uv))
                bucket['normals'].append(tuple((normal_matrix@obj.data.corner_normals[li].vector).normalized()))
            bucket['f'].append(indices)
    result=[]
    for name,b in buckets.items():
        data=bpy.data.meshes.new('EXPORT_'+name);data.from_pydata(b['v'],[],b['f']);data.materials.append(b['mat']);data.update()
        uv=data.uv_layers.new(name='UVMap')
        for p in data.polygons:
            p.use_smooth=True
            for li in p.loop_indices:uv.data[li].uv=b['uv'][data.loops[li].vertex_index]
        data.normals_split_custom_set(b['normals'])
        obj=bpy.data.objects.new('ENV_'+name,data);collection.objects.link(obj)
        obj.modifiers.new('Triangulate','TRIANGULATE');result.append(obj)
    return result


def export_glb(path,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
