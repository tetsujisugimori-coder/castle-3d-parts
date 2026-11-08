"""Compare repeat geometry and structural evidence separately from native bytes."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('first',type=Path)
parser.add_argument('second',type=Path)
parser.add_argument('--output',required=True,type=Path)
a=parser.parse_args()
if a.output.exists() or a.output.is_symlink():raise ValueError('OUTPUT_EXISTS')
load=lambda directory,name:json.loads((directory/name).read_text())
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m1=load(a.first,'manifest.json');m2=load(a.second,'manifest.json')
assert m1['status']==m2['status']=='PASS'
assert m1['application_sha256']==m2['application_sha256']
checks={name:load(a.first,name)==load(a.second,name) for name in ('freecad-audit.json','blender-audit.json','mesh-transfer.json')}
files=['input.FCStd','palisade.FCStd','palisade.step','palisade.blend','palisade.glb','mesh-transfer.json']
binary={name:{'first':hashfile(a.first/name),'second':hashfile(a.second/name),'identical':hashfile(a.first/name)==hashfile(a.second/name)} for name in files}
z1=zipfile.ZipFile(a.first/'palisade.FCStd');z2=zipfile.ZipFile(a.second/'palisade.FCStd')
changed=[name for name in z1.namelist() if z1.read(name)!=z2.read(name)]
normalize_xml=lambda b:re.sub(rb'(<Property name="LastModifiedDate".*?</Property>)',b'',b,flags=re.S)
xml_date_only=normalize_xml(z1.read('Document.xml'))==normalize_xml(z2.read('Document.xml'))
normalize_step=lambda p:re.sub(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d','TIMESTAMP',p.read_text())
step_date_only=normalize_step(a.first/'palisade.step')==normalize_step(a.second/'palisade.step')
result={'status':'PASS' if all(checks.values()) else 'FAIL','same_application_sha256':m1['application_sha256'],'originals_unchanged':m1['original_tracked_files_unchanged'] and m2['original_tracked_files_unchanged'],'geometry_and_structure_exact_json_equal':checks,'binary_hash_comparison':binary,'binary_difference_analysis':{'FCStd':{'changed_zip_entries':changed,'Document_xml_equal_except_LastModifiedDate':xml_date_only,'zip_entry_timestamps_differ':z1.infolist()[0].date_time!=z2.infolist()[0].date_time},'STEP':{'equal_after_timestamp_normalization':step_date_only},'blend':'Native blend bytes may differ between process saves (internal serialization and file metadata). Exact differing fields were not isolated. Saved/reopened object names, counts, triangles and bounds are equal; STEP-derived source mesh is byte-identical. Do not claim native byte determinism.','GLB':'See actual hash equality; binary equality is a separate result from geometry equality.'},'limits':['Headless/background execution, GUI NOT_TESTED','TechDraw omitted from changed working copies','Native blend byte differences not fully attributed','D provisional geometry, no historical dimension adoption']}
a.output.write_text(json.dumps(result,indent=2)+'\n')
assert result['status']=='PASS' and result['originals_unchanged']
print(json.dumps(result,indent=2))
