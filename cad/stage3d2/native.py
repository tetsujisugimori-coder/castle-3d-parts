"""Read-only correspondence observations. Not a CAD/analytic equality certificate."""
import json,sys,hashlib,os
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/lib/freecad/lib'])
import FreeCAD as A
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'cad/stage3c'))
from state import load_document,transition
c=json.loads(Path(__file__).with_name('contract.json').read_text());out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
source=ROOT/'cad/stage3c/generated/assembly.FCStd';before=hashlib.sha256(source.read_bytes()).hexdigest();assert before==c['sources']['cad/stage3c/generated/assembly.FCStd']
d=load_document(source)
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
ids=sorted(o.PartID for o in d.Objects if 'PartID' in o.PropertiesList);assert len(ids)==23
rows=[]
def bounds(s):return [getattr(s.BoundBox,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]
for mm in (0,70,140):
 transition(d,0,mm/1000);a=d.getObject('GATE_Bolt');b=d.getObject('GATE_BoltGuide_Left')
 rows.append({'bolt_mm':mm,'door_degrees':0,'bolt_bounds_mm':bounds(a.Shape),'guide_bounds_mm':bounds(b.Shape),'bolt_type':a.TypeId,'guide_type':b.TypeId,'bolt_volume_mm3':a.Shape.Volume,'guide_volume_mm3':b.Shape.Volume,'distance_mm_observed':a.Shape.distToShape(b.Shape)[0],'overlap_mm3_observed':a.Shape.common(b.Shape).Volume,'valid_solids_observed':[a.Shape.isValid(),b.Shape.isValid()],'correspondence':'UNKNOWN','reason':'sampled topology/bounds/distance do not prove exact BRep set equality or an absolute error bound'})
A.closeDocument(d.Name);assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(out/'native.json').write_text(json.dumps({'source_sha256':before,'source_unchanged':True,'part_ids':ids,'samples':rows,'actual_shape_correspondence':'UNKNOWN','actual_CAD_distance_error':'UNKNOWN','actual_CAD_motion_enclosure':'UNKNOWN','scope':'read-only observations of fixed representative, not dense sampling proof','FreeCAD':A.Version()},indent=2));print('NATIVE OBSERVATIONS COMPLETE; CAD GUARANTEES UNKNOWN',flush=True);os._exit(0)
