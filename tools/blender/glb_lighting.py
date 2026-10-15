"""Normalize native Blender light power for the supplied realtime lighting rig.
Only standard KHR_lights_punctual JSON is changed; geometry remains untouched.
"""
import json
import struct
from pathlib import Path


def normalize_point_lights(path,scale=.012,range_metres=18):
    path=Path(path);raw=path.read_bytes()
    assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
    length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4E4F534A
    data=json.loads(raw[20:20+length])
    extras=data['asset'].setdefault('extras',{})
    if extras.get('northernTorchNormalization')==scale:return
    lights=data.get('extensions',{}).get('KHR_lights_punctual',{}).get('lights',[])
    for light in lights:
        if light['type']=='point':
            light['intensity']=light.get('intensity',1)*scale
            light['range']=range_metres
    extras['northernTorchNormalization']=scale
    encoded=json.dumps(data,separators=(',',':')).encode('utf-8')
    encoded+=b' '*((-len(encoded))%4)
    rest=raw[20+length:]
    total=20+len(encoded)+len(rest)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+rest)
