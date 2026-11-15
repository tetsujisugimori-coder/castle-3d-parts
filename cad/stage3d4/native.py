"""Read actual BRep trims and topology without saving original. All numbers are observations."""
import hashlib,json,os,sys
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/lib/freecad/lib'])
import FreeCAD as A
import Part
from bridge import ROOT,PARTS,sources,assess
sys.path.insert(0,str(ROOT/'cad/stage3c'))
from state import load_document,transition

def point(v):return [v.x,v.y,v.z]
def describe(s):
    faces=[]
    for f in s.Faces:
        wires=[]
        for w in f.Wires:
            wires.append({'orientation':w.Orientation,'closed':w.isClosed(),'edges':[
                {'curve':type(e.Curve).__name__,'orientation':e.Orientation,
                 'vertices':[point(v.Point) for v in e.Vertexes], 'length_observed':e.Length,
                 'tolerance_observed':e.getTolerance(1)} for e in w.OrderedEdges]})
        faces.append({'surface':type(f.Surface).__name__,'orientation':f.Orientation,'wires':wires,
                      'normal_observed':point(f.normalAt(0,0)),'area_observed':f.Area})
    return {'brep_sha256':hashlib.sha256(s.exportBrepToString().encode()).hexdigest(),
            'placement':str(s.Placement),'valid':s.isValid(),'closed':s.isClosed(),
            'solids':len(s.Solids),'shells':len(s.Shells),'solid_orientations':[x.Orientation for x in s.Solids],
            'shell_orientations':[x.Orientation for x in s.Shells],'faces':faces,
            'bounds_observed':[getattr(s.BoundBox,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']],
            'tolerance_observed':s.getTolerance(1)}

def main(out):
    out.mkdir(parents=True,exist_ok=False);before=sources()
    d=load_document(ROOT/'cad/stage3c/generated/assembly.FCStd')
    for o in d.Objects:
        if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
    transition(d,0,0)
    originals={n:d.getObject(n).Shape.copy() for n in PARTS}
    def record(shapes):return {'sources':before,'unit':'mm','frame':'FreeCAD world','door_degrees':0,'travel_mm':[0,140],
                               'parts':{n:describe(s) for n,s in shapes.items()}}
    data=record(originals);(out/'original.json').write_text(json.dumps(data,indent=2));rows=[{'case':'original','input':data,'assessment':assess(data)}]
    for n,s in originals.items():(out/(n+'.brep')).write_text(s.exportBrepToString())
    b,g=PARTS
    def stage(name):(out/'progress.txt').open('a').write(name+'\n')
    stage('before-mutations')
    expanded=Part.makeBox(900,24,40,A.Vector(-400,-117,1000))
    stage('expanded')
    shrunk=originals[g].fuse(Part.makeBox(20,2,42,A.Vector(-200,-116,999)))
    stage('shrunk')
    shift=originals[b].copy();shift.translate(A.Vector(0,1,0))
    stage('shift')
    reverse=originals[b].copy();reverse.reverse()
    stage('reverse')
    opened=Part.makeShell(originals[b].Faces[:-1])
    stage('opened')
    curved=Part.makeCylinder(10,40,A.Vector(-400,-115,1000))
    stage('curved')
    extra=originals[b].fuse(Part.makeBox(1,1,1,A.Vector(0,0,0)))
    stage('extra')
    for case,n,s in [('bolt_enlarged',b,expanded),('hole_shrunk',g,shrunk),('placement_shift',b,shift),
                     ('orientation_reversed',b,reverse),('missing_face_open_shell',b,opened),
                     ('unsupported_curved',b,curved),('extra_solid',b,extra)]:
        stage(case)
        changed=dict(originals);changed[n]=s;r=record(changed);v=assess(r)
        identity_changed=r['parts'][n]['brep_sha256']!=data['parts'][n]['brep_sha256']
        if not identity_changed or v['cad_intervals']['PASS']!=0:raise AssertionError(case)
        rows.append({'case':case,'kind':'real FreeCAD isolated in-memory mutation','input':r,'assessment':v,'BRep_changed':identity_changed,'fixed_observation_match':'REJECTED_BREP_CHANGED'})
        (out/(case+'.brep')).write_text(s.exportBrepToString())
    A.closeDocument(d.Name)
    after=sources()
    if after!=before:raise AssertionError('ORIGINAL_CHANGED')
    report={'schema':1,'FreeCAD':A.Version(),'OCC':getattr(Part,'OCC_VERSION','UNKNOWN'),'sources_before':before,'sources_after':after,
            'rows':rows,'warning':'Topology/kernel results and floats are observations, not certified BRep semantics or containment.',
            'cad_intervals':{'PASS':0,'FAIL':0,'UNKNOWN':128}}
    (out/'native.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('Native original + 7 isolated mutations recorded; CAD128 UNKNOWN',flush=True)
if __name__=='__main__':
    try:main(Path(sys.argv[1]))
    except BaseException:
        import traceback
        error=traceback.format_exc();Path(sys.argv[1]).joinpath('error.txt').write_text(error);os.write(2,error.encode())
        os._exit(1)
    os._exit(0)
