import struct,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[3]/'cad/stage2c/generated'
results=[]
for rev in ['B0','B1','B2']:
 p=root/rev;b=(p/'assembly.glb').read_bytes();magic,version,length=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and length==len(b)
 size,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a;j=json.loads(b[20:20+size]);manifest=json.loads((p/'link-manifest.json').read_text());nodes={n['name']:n for n in j['nodes'] if 'mesh' in n};assert len(nodes)==14
 for part in manifest['parts']:
  n=nodes[part['glb_node']];assert n.get('matrix') is None and n.get('rotation',[0,0,0,1])==[0,0,0,1]
  pos=j['accessors'][j['meshes'][n['mesh']]['primitives'][0]['attributes']['POSITION']];t=n.get('translation',[0,0,0]);s=n.get('scale',[1,1,1]);lo=[pos['min'][i]*s[i]+t[i] for i in range(3)];hi=[pos['max'][i]*s[i]+t[i] for i in range(3)]
  # Blender GLTF exporter maps Z-up coordinates into Y-up: (x,z,-y).
  actual=[lo[0],-hi[2],lo[1],hi[0],-lo[2],hi[1]]
  assert all(abs(x-y)<1e-5 for x,y in zip(actual,part['bounds_m'])),(part['id'],actual,part['bounds_m'])
 results.append({'revision':rev,'glb_parts':len(nodes),'accessor_bounds_vs_cad_manifest':'PASS'})
print(json.dumps(results,indent=2))
