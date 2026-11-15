"""Direct public OCCT observations; flags and represented numbers are not proofs.

OCP is an isolated second OCCT build, never an in-process FreeCAD ABI bridge.
The bool* CurveOnSurface output is not recoverable from this Python binding.
"""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import traceback
import zipfile
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[3]
FIXED = 'c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a'


def sha(b): return hashlib.sha256(b).hexdigest()
def q(v): return str(Fraction(v))
def xyz(v): return [q(v.X()), q(v.Y()), q(v.Z())]
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def environment():
    import OCP
    from OCP.BRep import BRep_Tool
    libs = sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                   if '.so' in line and ('/libTK' in line or '/OCP.' in line)})
    rows=[]
    for p in libs:
        blob=Path(p).read_bytes()
        r=subprocess.run(['readelf','-d',p],capture_output=True,text=True,check=True)
        soname=[x.strip() for x in r.stdout.splitlines() if '(SONAME)' in x]
        rows.append({'path':p,'size':len(blob),'sha256':sha(blob),'elf_soname':soname})
    kernel=[r for r in rows if '/libTK' in r['path']]
    matched=bool(kernel) and all(r['path'].endswith('.so.7.8.1') and any('.so.7.8.1' in x for x in r['elf_soname']) for r in kernel)
    return {'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
            'binding_version':OCP.__version__,'distribution':importlib.metadata.version('cadquery-ocp'),
            'wheel':importlib.metadata.distribution('cadquery-ocp').read_text('WHEEL'),
            'loaded_binary_inventory':rows,'loaded_occt_version_identification':'7.8.1' if matched else 'UNKNOWN',
            'identification_basis':'loaded ELF SONAME plus versioned libraries, binding/distribution metadata; not upstream build reproducibility',
            'freecad_binary_abi_equivalence':'UNKNOWN','cross_build_numeric_equivalence':'UNKNOWN',
            'curve_on_surface_binding':BRep_Tool.CurveOnSurface_s.__doc__}


def location(s):
    t=s.Location().Transformation()
    return {'identity':s.Location().IsIdentity(),'matrix_ieee':[[q(t.Value(i,j)) for j in range(1,5)] for i in range(1,4)]}


def capture(shape, source_hash):
    from OCP.TopAbs import TopAbs_VERTEX,TopAbs_EDGE,TopAbs_WIRE,TopAbs_FACE,TopAbs_SHELL,TopAbs_SOLID
    from OCP.TopExp import TopExp,TopExp_Explorer
    from OCP.TopTools import TopTools_IndexedMapOfShape
    from OCP.TopoDS import TopoDS,TopoDS_Iterator
    from OCP.TopLoc import TopLoc_Location
    from OCP.BRep import BRep_Tool
    from OCP.BRepTools import BRepTools,BRepTools_WireExplorer
    types={'vertex':TopAbs_VERTEX,'edge':TopAbs_EDGE,'wire':TopAbs_WIRE,'face':TopAbs_FACE,'shell':TopAbs_SHELL,'solid':TopAbs_SOLID}
    casts={'vertex':TopoDS.Vertex_s,'edge':TopoDS.Edge_s,'wire':TopoDS.Wire_s,'face':TopoDS.Face_s,'shell':TopoDS.Shell_s,'solid':TopoDS.Solid_s}
    maps={};shapes={}
    for kind,typ in types.items():
        m=TopTools_IndexedMapOfShape();TopExp.MapShapes_s(shape,typ,m);maps[kind]=m
        shapes[kind]=[casts[kind](m.FindKey(i)) for i in range(1,m.Extent()+1)]
    def refs(s,k):
        out=[];ex=TopExp_Explorer(s,types[k])
        while ex.More():
            child=ex.Current();out.append({'id':maps[k].FindIndex(child),'orientation':str(child.Orientation()),'location':location(child)});ex.Next()
        return out
    def curve(c):
        if c is None:return {'type':'NULL'}
        d={'type':c.DynamicType().Name()}
        if hasattr(c,'BasisCurve'):
            d.update(basis_curve=curve(c.BasisCurve()),trim_range_ieee=[q(c.FirstParameter()),q(c.LastParameter())],basis_semantics='direct public BasisCurve; numerical representation only, not error enclosure')
        if hasattr(c,'Lin'):
            l=c.Lin();d.update(origin_ieee=xyz(l.Location()),direction_ieee=xyz(l.Direction()))
        if hasattr(c,'Location') and hasattr(c,'Direction'):
            a=c.Location();v=c.Direction();d.update(origin_uv_ieee=[q(a.X()),q(a.Y())],direction_uv_ieee=[q(v.X()),q(v.Y())])
        return d
    inventory={k:[] for k in types};uses=[]
    for k,ss in shapes.items():
      for i,s in enumerate(ss,1):
        d={'lookup_id':i,'orientation':str(s.Orientation()),'location':location(s),'closed_flag':s.Closed()}
        if k=='vertex':d['point_ieee']=xyz(BRep_Tool.Pnt_s(s))
        if k=='edge':
            d.update(vertices=refs(s,'vertex'),same_parameter_flag=BRep_Tool.SameParameter_s(s),same_range_flag=BRep_Tool.SameRange_s(s),range3d_ieee=list(map(q,BRep_Tool.Range_s(s))),curve3d=curve(BRep_Tool.Curve_s(s,0.,0.)),degenerated_flag=BRep_Tool.Degenerated_s(s))
        if k=='wire':d['edges_topological_order']=refs(s,'edge')
        if k=='face':
            surf=BRep_Tool.Surface_s(s);sd={'type':surf.DynamicType().Name(),'location_semantics':'BRep_Tool.Surface(face) may return Location-applied copy; no second transform applied'}
            if hasattr(surf,'Pln'):
                pl=surf.Pln();sd.update(origin_ieee=xyz(pl.Location()),u_ieee=xyz(pl.XAxis().Direction()),v_ieee=xyz(pl.YAxis().Direction()),normal_ieee=xyz(pl.Axis().Direction()))
            d.update(surface=sd,uv_bounds_ieee=list(map(q,BRepTools.UVBounds_s(s))),wires=refs(s,'wire'))
            raw_location=TopLoc_Location()
            raw_surface=BRep_Tool.Surface_s(s,raw_location)
            for wr in d['wires']:
                w=shapes['wire'][wr['id']-1];ex=BRepTools_WireExplorer(w,s);seq=[]
                while ex.More():
                    e=ex.Current();ei=maps['edge'].FindIndex(e);seq.append(ei)
                    pc=BRep_Tool.CurveOnSurface_s(e,s,0.,0.)
                    stored=[]
                    relative_location=e.Location().Inverted().Multiplied(raw_location)
                    for ri,rep in enumerate(e.TShape().Curves(),1):
                        if rep.IsCurveOnSurface(raw_surface,relative_location):
                            stored.append({'representation_index':ri,'type':rep.DynamicType().Name(),'pcurve':curve(rep.PCurve()),'range_ieee':[q(rep.First()),q(rep.Last())],'returned_pcurve_same_handle':rep.PCurve() is pc,'equal_geometry_copy_is_same_object':rep.PCurve().Copy() is pc,'match_basis':'public IsCurveOnSurface(raw Surface handle, edge-relative Location)'})
                    uses.append({'stored_representations_matching_face':stored,'stored_inventory_scope':'BRep_TEdge.Curves direct read, no generated representation inserted', 'face_id':i,'wire_id':wr['id'],'edge_id':ei,'wire_sequence':len(seq),'edge_orientation':str(e.Orientation()),'pcurve':curve(pc),'range2d_ieee':list(map(q,BRep_Tool.Range_s(e,s))),'is_closed_on_face':BRep_Tool.IsClosed_s(e,s),'storage_origin':'STORED' if len(stored)==1 and stored[0]['returned_pcurve_same_handle'] and not BRep_Tool.IsClosed_s(e,s) else 'UNKNOWN','storage_reason':'direct TEdge representation match plus returned curve handle identity; Python wrapper object identity (is), not geometric equality; bool* output unavailable; absence/ambiguity/closed-surface seam remains UNKNOWN','native_trim_correspondence':'UNKNOWN'})
                    ex.Next()
                wr['connected_wire_order_edge_ids']=seq
        if k=='shell':d['faces']=refs(s,'face')
        if k=='solid':d['shells']=refs(s,'shell')
        d['descriptor_sha256']=sha(canonical(d));d['source_brep_sha256']=source_hash
        d['identity_scope']='fixed source hash plus geometry/orientation/incidence descriptor; lookup_id alone is not identity'
        inventory[k].append(d)
    coverage={}
    for parent,field,child in [('edge','vertices','vertex'),('wire','edges_topological_order','edge'),('face','wires','wire'),('shell','faces','face'),('solid','shells','shell')]:
        found={r['id'] for row in inventory[parent] for r in row[field]}; expected=set(range(1,len(inventory[child])+1))
        coverage[parent+'_'+child]={'referenced':sorted(found),'all':sorted(expected),'status':'PASS' if found==expected else 'FAIL'}
    return {'inventory':inventory,'pcurve_uses':uses,'coverage':coverage,'root_orientation':str(shape.Orientation()),'root_location':location(shape),'native_material_side':'UNKNOWN','continuous_pcurve_3d_error_bound':None,'native_safety':'NOT_TESTED','flags_semantics':'stored OCCT consistency flags only, not independent continuous geometric proof'}


def native_copy_controls(shape, out, source_hash):
    """Actual isolated BRep object mutations, not altered observation JSON.

    These check observation sensitivity; they are not geometric collision tests.
    Each full mutated BRep and capture is retained for independent reexecution.
    """
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopoDS import TopoDS
    from OCP.TopLoc import TopLoc_Location
    from OCP.gp import gp_Trsf, gp_Vec
    out.mkdir(exist_ok=False)
    cases=[]
    original=capture(shape,source_hash)
    for kind in ['same_parameter_flag_false','root_orientation_reversed','root_location_translation']:
        copied=BRepBuilderAPI_Copy(shape,True,False).Shape()
        if kind=='same_parameter_flag_false':
            edge=TopoDS.Edge_s(TopExp_Explorer(copied,TopAbs_EDGE).Current())
            BRep_Builder().SameParameter(edge,False)
        elif kind=='root_orientation_reversed':copied.Reverse()
        else:
            tr=gp_Trsf();tr.SetTranslation(gp_Vec(17,0,0));copied.Location(TopLoc_Location(tr))
        p=out/(kind+'.brep');BRepTools.Write_s(copied,str(p))
        observed=capture(copied,sha(p.read_bytes()))
        if kind=='same_parameter_flag_false':
            detected=any(not e['same_parameter_flag'] for e in observed['inventory']['edge'])
        elif kind=='root_orientation_reversed':detected=observed['root_orientation']!=original['root_orientation']
        else:detected=observed['root_location']!=original['root_location']
        (out/(kind+'.json')).write_text(json.dumps(observed,indent=2)+'\n')
        cases.append({'kind':kind,'input_type':'actual copied BRep mutation via public OCCT API','mutated_brep_sha256':sha(p.read_bytes()),'expected':'observation differs, not collision FAIL','detection':'PASS' if detected else 'FAIL','native_geometric_collision':'UNKNOWN','native_safety':'NOT_TESTED'})
    assert canonical(capture(shape,source_hash))==canonical(original)
    return {'cases':cases,'original_shape_observations_unchanged':'PASS','scope':'three native-copy observation controls; not full requested fault family or continuous geometry verification'}


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    try:
        env=environment()
    except (ImportError, FileNotFoundError) as exc:
        (out/'results.json').write_text(json.dumps({'capture':'BLOCKED','reason':'OCP_OR_BINARY_INSPECTION_UNAVAILABLE','detail':str(exc),'native_real':'UNKNOWN'})+'\n');return 2
    (out/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    if env['loaded_occt_version_identification']!='7.8.1':
        (out/'results.json').write_text(json.dumps({'capture':'BLOCKED','reason':'OCCT_VERSION_UNKNOWN'}));return 2
    from OCP.TopoDS import TopoDS_Shape
    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools
    original=ROOT/'cad/stage3c/generated/assembly.FCStd';blob=original.read_bytes()
    if sha(blob)!=FIXED:raise ValueError('FIXED_FCSTD_HASH_MISMATCH')
    isolated=out/'isolated';isolated.mkdir();(isolated/'assembly.FCStd').write_bytes(blob)
    result={'fixed_fcstd_sha256':FIXED,'parts':{},'method':'direct public BRep_Tool via separately loaded OCCT7.8.1 OCP build; no FreeCAD ABI calls','native_material':'UNKNOWN','finite_real_error':'UNKNOWN','representative_native':'NOT_TESTED'}
    with zipfile.ZipFile(isolated/'assembly.FCStd') as z:
      for name in ['GATE_Bolt','GATE_BoltGuide_Left']:
        raw=z.read(name+'.Shape.brp');p=isolated/(name+'.brep');p.write_bytes(raw)
        shape=TopoDS_Shape()
        if not BRepTools.Read_s(shape,str(p),BRep_Builder()):raise ValueError('BREP_READ_FAILED')
        result['parts'][name]=capture(shape,sha(raw))
        result['parts'][name]['native_copy_controls']=native_copy_controls(shape,out/(name+'-controls'),sha(raw))
        assert p.read_bytes()==raw
    assert original.read_bytes()==blob and (isolated/'assembly.FCStd').read_bytes()==blob
    result['source_unchanged']='PASS'
    result['freecad_abi_equivalence']='UNKNOWN'
    result['continuous_error_bound']=None
    (out/'direct-capture.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'results.json').write_text(json.dumps({'capture':'PASS','scope':'observation collection only','native_real':'UNKNOWN','parts':{k:len(v['pcurve_uses']) for k,v in result['parts'].items()}},indent=2)+'\n')
    return 0


if __name__=='__main__':
    try:sys.exit(main(sys.argv[1]))
    except Exception:
        traceback.print_exc();sys.exit(1)
