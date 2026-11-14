"""Stage3C native CI orchestration with strict named STEP identity.
Preserved original generators remain in Git history; current source hashes are verified.

Run inside the Debian trixie native CI job, after installing FreeCAD/Blender.
This is a batch software test, never manual GUI or physical-Safari evidence.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CORE = {'build.py', 'state.py', 'native_test.py', 'blender.py', 'collision.py',
        'run.py', 'legacy.py', 'finalize.py', 'check.py', 'check_test.py', 'spec.json'}
HISTORY = {'history.py', 'history_test.py', 'history_native_test.py', 'history_parity_test.py'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def portable(repo, generated):
    checker = load_module(repo/'cad/stage3c/check.py', 'native_portable_checker')
    assert checker.SOURCES == CORE | HISTORY, 'Native source contract must explicitly cover core plus history'
    manifest = json.loads((generated/'manifest.json').read_text())
    expected = CORE | HISTORY
    assert set(manifest['source_hashes']) == expected, 'Unexpected/missing native source file'
    assert all(digest(repo/'cad/stage3c'/f) == h for f,h in manifest['source_hashes'].items())
    # check.py declares the same strict core+history set. No runtime weakening.
    # check() verifies every source hash and artifact hash; no manifest rewrite.
    assert checker.SOURCES == expected
    result = checker.check(generated)
    result['scope'] = 'Portable validation of newly regenerated artifacts; native execution recorded separately'
    result['source_contract'] = {'core_generators': sorted(CORE), 'runtime_history_tests': sorted(HISTORY),
                                 'all_declared_hashes_verified': True,
                                 'checker_contract': 'Explicit CORE11 plus HISTORY4 in checked source',
                                 'manifest_source_hashes_modified': False}
    return result

def compare_saved_semantics(repo, generated):
    previous=json.loads((repo/'cad/stage3c/generated/collision.json').read_text())
    current=json.loads((generated/'collision.json').read_text())
    max_distance_error=0.0;max_overlap_error=0.0;pairs=0
    for group in ['samples','bolt_samples','fixed_pairs']:
        if group=='fixed_pairs':
            batches=[(previous[group],current[group])]
        else:
            assert len(previous[group])==len(current[group])
            batches=[]
            for old,new in zip(previous[group],current[group]):
                assert old['angle_degrees']==new['angle_degrees'] and old['bolt_m']==new['bolt_m']
                batches.append((old['pairs'],new['pairs']))
        for old,new in batches:
            key=lambda row:tuple(sorted([row['a'],row['b']]))
            aa={key(row):row for row in old};bb={key(row):row for row in new}
            assert aa.keys()==bb.keys()
            for pair in aa:
                a=aa[pair];b=bb[pair]
                de=abs(a['distance_m']-b['distance_m']);ve=abs(a['overlap_mm3']-b['overlap_mm3'])
                assert de<1e-7 and ve<=.0001,(group,pair,de,ve)
                assert a['contact']==b['contact'],(group,pair,a['contact'],b['contact'])
                max_distance_error=max(max_distance_error,de);max_overlap_error=max(max_overlap_error,ve);pairs+=1
    return {'status':'PASS','pair_measurements':pairs,'maximum_distance_difference_m':max_distance_error,'maximum_overlap_difference_mm3':max_overlap_error,'same_pair_sample_classification':True,'byte_identity_not_required':True,'continuous_path':'UNKNOWN'}

def native_cad(repo, generated, evidence):
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    import FreeCAD as A
    import FreeCADGui as G
    import Part
    import Import
    G.showMainWindow()
    import TechDrawGui
    sys.path.insert(0, str(repo/'cad/stage3c'))
    from state import load_document, validate_document, transition
    spec = json.loads((repo/'cad/stage3c/spec.json').read_text())
    baseline = load_document(repo/'cad/stage3c/generated/assembly.FCStd', 'PreservedReference')
    doc = load_document(generated/'assembly.FCStd', 'RegeneratedReadback')
    for d in [baseline, doc]:
        for o in d.Objects:
            if 'KeepUpdated' in o.PropertiesList:
                o.KeepUpdated = False
        d.recompute()
        validate_document(d)
    ids = spec['part_ids']
    assert len(ids) == 23 and len(set(ids)) == 23
    assert {o.PartID for o in doc.Objects if 'PartID' in o.PropertiesList} == set(ids)
    semantic = []
    for name in ids:
        a = baseline.getObject(name).Shape
        b = doc.getObject(name).Shape
        assert a.isValid() and b.isValid() and len(a.Solids)==len(b.Solids)==1
        delta = a.cut(b).Volume + b.cut(a).Volume
        assert delta < .01, (name, 'symmetric_difference_mm3', delta)
        semantic.append({'id':name,'symmetric_difference_mm3':delta,'volume_mm3':b.Volume})
    # STEP importer identity is required; no silent pairing merely by file order.
    step = A.newDocument('SeparateProcessStepReadback')
    Import.insert(str(generated/'assembly.step'), step.Name)
    step.recompute()
    shaped = [o for o in step.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
    inventory=[{'name':o.Name,'label':o.Label,'type_id':o.TypeId,'solids':len(o.Shape.Solids),'valid':o.Shape.isValid(),'volume_mm3':o.Shape.Volume} for o in shaped]
    save(evidence/'step-import-inventory.json',inventory)
    assert all(o.Shape.isValid() and len(o.Shape.Solids)>0 for o in shaped), ('STEP invalid/open shape',inventory)
    imported=[o for o in shaped if len(o.Shape.Solids)==1]
    aggregates=[o for o in shaped if len(o.Shape.Solids)>1]
    assert len(imported)==23, ('STEP leaf count',inventory)
    assert {o.Label for o in imported}==set(ids) and len({o.Label for o in imported})==23, ('STEP exact PartID labels',inventory)
    assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in imported), 'STEP valid single solids'
    assembled=Part.makeCompound([o.Shape for o in imported])
    aggregate_rows=[]
    for aggregate in aggregates:
        assert aggregate.Label not in ids and aggregate.Name not in ids, ('STEP aggregate uses reserved PartID',inventory)
        assert len(aggregate.Shape.Solids)==23, ('STEP incomplete aggregate',inventory)
        delta=aggregate.Shape.cut(assembled).Volume+assembled.cut(aggregate.Shape).Volume
        assert delta<.01,('STEP aggregate differs from exact 23 leaves',aggregate.Label,delta)
        aggregate_rows.append({'name':aggregate.Name,'label':aggregate.Label,'solids':23,'symmetric_difference_mm3':delta})
    step_rows=[]
    for name in ids:
        matches=[o for o in imported if o.Label==name]
        assert len(matches)==1, (name,'STEP identity',[(o.Name,o.Label) for o in imported])
        a=doc.getObject(name).Shape;b=matches[0].Shape
        delta=a.cut(b).Volume+b.cut(a).Volume
        assert delta<.01,(name,'STEP symmetric difference',delta)
        step_rows.append({'id':name,'symmetric_difference_mm3':delta})
    A.closeDocument(step.Name)
    A.setActiveDocument(doc.Name)
    # Actual TechDraw edge measurements after live parameter changes.
    dimension_rows=[]
    for length,width,height,gap in [(900,20,40,1),(880,18,35,.5),(900,22,45,2)]:
        lock=doc.getObject('LockMechanism')
        lock.BoltLength=length;lock.BoltWidth=width;lock.BoltHeight=height;lock.GuideGap=gap
        doc.recompute()
        names=['BoltLengthDimension','BoltWidthDimension','BoltHeightDimension']
        for page in ['LockBoltPage','LockPositionsPage']:
            G.activeDocument().getObject(page).show()
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            for k in names:doc.getObject(k).touch()
            doc.recompute();app.processEvents();time.sleep(.05)
            values=[doc.getObject(k).getRawValue() for k in names]
            if all(abs(a-b)<1e-5 for a,b in zip(values,[length,width,height])):break
        assert all(abs(a-b)<1e-5 for a,b in zip(values,[length,width,height])),values
        for name in ['GATE_BoltGuide_LeftBore','GATE_BoltGuide_RightBore','GATE_BoltReceiverBore']:
            bore=doc.getObject(name)
            assert abs(bore.Width.Value-(width+2*gap))<1e-6
            assert abs(bore.Height.Value-(height+2*gap))<1e-6
        dimension_rows.append({'length_mm':length,'width_mm':width,'height_mm':height,'gap_mm':gap,'native_dimensions_mm':values})
    lock=doc.getObject('LockMechanism')
    lock.BoltLength=900;lock.BoltWidth=20;lock.BoltHeight=40;lock.GuideGap=1;doc.recompute()
    transition(doc,0,.07)
    doc.saveAs(str(evidence/'separate-reopen-state.FCStd'))
    result={'status':'PASS','FreeCAD':A.Version(),'parts':23,'separate_process_fcstd_reopen':True,
            'separate_process_step_reopen':True,'semantic_reference_comparison':semantic,'step_comparison':step_rows,'step_import_inventory':inventory,'step_aggregate_comparison':aggregate_rows,
            'native_dimension_variants':dimension_rows,'saved_state':{'angle_degrees':0,'bolt_m':.07},
            'continuous_path':'UNKNOWN','manual_gui':'NOT_TESTED','physical_strength':'NOT_TESTED'}
    save(evidence/'native-independent-readback.json',result)
    A.closeDocument(doc.Name);A.closeDocument(baseline.Name)
    print('Separate-process CAD/STEP/TechDraw semantic readback PASS',flush=True)
    # Match preserved generator process termination strategy, after closing docs.
    sys.stdout.flush();sys.stderr.flush();os._exit(0)

def native_state_reopen(repo, evidence):
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    import FreeCAD as A
    import FreeCADGui as G
    G.showMainWindow()
    sys.path.insert(0,str(repo/'cad/stage3c'))
    from state import load_document,validate_document
    doc=load_document(evidence/'separate-reopen-state.FCStd','ThirdProcessReadback')
    validate_document(doc)
    assert doc.Mechanism.Angle.Value==0 and doc.LockMechanism.BoltPosition.Value==70
    assert abs(doc.GATE_Bolt.Shape.BoundBox.XMin-(-400+70))<1e-5
    save(evidence/'third-process-state.json',{'status':'PASS','FreeCAD':A.Version(),'state':{'angle_degrees':0,'bolt_m':.07},'actual_bolt_xmin_mm':doc.GATE_Bolt.Shape.BoundBox.XMin})
    A.closeDocument(doc.Name)
    sys.stdout.flush();sys.stderr.flush();os._exit(0)

def native_history(repo, generated, evidence, reopen):
    # TechDraw-bearing documents need a QApplication/Gui bootstrap even though
    # this is an offscreen batch test. Do not claim manual GUI operation.
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    import FreeCAD as A
    import FreeCADGui as G
    import runpy
    G.showMainWindow()
    sys.path.insert(0,str(repo/'cad/stage3c'))
    script=repo/'cad/stage3c/history_native_test.py'
    source=evidence/'history/history-result.FCStd' if reopen else generated/'assembly.FCStd'
    output=evidence/'history-reopen' if reopen else evidence/'history'
    sys.argv=[str(script),str(source),str(output)]+(['--reopen-only'] if reopen else [])
    try:
        runpy.run_path(str(script),run_name='__main__')
    except SystemExit as exit_status:
        if exit_status.code not in (None,0):raise
    # Destruction order of Python/Qt/FreeCAD singletons can abort at process exit.
    # Close all documents and flush the actual successful test output first,
    # then use the preserved generator's explicit successful termination model.
    for name in list(A.listDocuments()):A.closeDocument(name)
    app.processEvents()
    sys.stdout.flush();sys.stderr.flush();os._exit(0)

def native_blender(repo, generated, evidence, kind):
    import bpy
    from mathutils import Vector
    import math
    source=json.loads((generated/'mesh-transfer.json').read_text())
    mesh_validator=load_module(repo/'scripts/stage3c-mesh-integrity.py','stage3c_mesh_integrity')
    pivot=Vector(source['pivot_m'])
    if kind=='blend':bpy.ops.wm.open_mainfile(filepath=str(generated/'assembly.blend'))
    else:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(generated/'assembly.glb'))
    poses=[(1,0,0),(31,0,.14),(61,0,0),(106,45,0),(151,90,0),(241,0,0)]
    assert {o.name for o in bpy.data.objects if o.type=='MESH'}=={e['id'] for e in source['objects']}
    rows=[]
    for frame,angle,bolt in poses:
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        c=math.cos(math.radians(angle));s=math.sin(math.radians(angle))
        max_error=0;mesh_rows=[]
        for part in source['objects']:
            obj=bpy.data.objects.get(part['id']);assert obj and obj.get('part_id')==part['id']
            expected_parent='BoltSlide' if part['movement']=='bolt' else 'GatePivot' if part['moving'] else None
            assert (obj.parent.name if obj.parent else None)==expected_parent
            target=[]
            for x,y,z in part['vertices_m']:
                if part['moving']:
                    dx=x-pivot.x+(bolt if part['movement']=='bolt' else 0);dy=y-pivot.y
                    x=pivot.x+dx*c-dy*s;y=pivot.y+dx*s+dy*c
                target.append((x,y,z))
            vs=[obj.matrix_world@v.co for v in obj.data.vertices]
            obj.data.calc_loop_triangles()
            actual_faces=[list(triangle.vertices) for triangle in obj.data.loop_triangles]
            mesh_counts=mesh_validator.compare_mesh(target,part['faces'],[list(v) for v in vs],actual_faces,tolerance=1e-5)
            mesh_rows.append({'id':part['id'],'status':'PASS',**mesh_counts})
            expected=[min(v[i] for v in target) for i in range(3)]+[max(v[i] for v in target) for i in range(3)]
            actual=[min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)]
            error=max(abs(a-b) for a,b in zip(expected,actual));assert error<1e-5,(part['id'],frame,error)
            max_error=max(max_error,error)
        assert len(mesh_rows)==23
        rows.append({'frame':frame,'angle_degrees':angle,'bolt_m':bolt,'parts':23,'maximum_bounds_error_m':max_error,'vertex_triangle_comparison':'PASS','mesh_comparisons':mesh_rows})
    save(evidence/('separate-process-'+kind+'.json'),{'status':'PASS','Blender':bpy.app.version_string,'format':kind,'separate_process_reopen':True,'poses':rows,'vertex_triangle_object_pose_comparisons':sum(len(row['mesh_comparisons']) for row in rows),'mesh_validator_sha256':digest(repo/'scripts/stage3c-mesh-integrity.py'),'manual_gui':'NOT_TESTED'})

def orchestrate(args):
    repo=args.repo.resolve();evidence=args.evidence.resolve()
    if evidence.exists():raise SystemExit('Refusing existing evidence output directory')
    evidence.mkdir(parents=True)
    runtime=evidence/'runtime';runtime.mkdir()
    cache=runtime/'cache';cache.mkdir()
    generated=evidence/'regenerated'
    env=os.environ.copy();env.update({'TMPDIR':str(runtime),'TMP':str(runtime),'TEMP':str(runtime),'XDG_CACHE_HOME':str(cache),'QT_QPA_PLATFORM':'offscreen'})
    freecadlib='/usr/lib/freecad-python3/lib'
    env['PYTHONPATH']=os.pathsep.join([freecadlib,str(repo/'cad/stage3c'),env.get('PYTHONPATH','')])
    env['LD_LIBRARY_PATH']=os.pathsep.join([freecadlib,env.get('LD_LIBRARY_PATH','')])
    records=[]
    def command(name,argv,timeout=2400):
        start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        error=None;exit_code=None
        try:
            with (evidence/(name+'.log')).open('wb') as log:
                proc=subprocess.run(argv,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
                exit_code=proc.returncode
        except subprocess.TimeoutExpired:
            error='TIMEOUT after '+str(timeout)+' seconds'
        records.append({'name':name,'argv':argv,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':exit_code,'error':error,'log_sha256':digest(evidence/(name+'.log'))})
        save(evidence/'commands.json',records)
        if error or exit_code:raise RuntimeError(name+' failed: '+str(error or exit_code)+'; see original log')
    wrapper=Path(__file__).resolve()
    base=['/usr/bin/python3',str(wrapper),'--repo',str(repo),'--evidence',str(evidence)]
    try:
        command('versions',['/usr/bin/python3','-c','import sys,FreeCAD; print(sys.version); print(FreeCAD.Version())'],120)
        command('regenerate',['/usr/bin/python3',str(repo/'cad/stage3c/run.py'),str(generated)])
        save(evidence/'portable-regenerated.json',portable(repo,generated))
        save(evidence/'saved-collision-semantic-comparison.json',compare_saved_semantics(repo,generated))
        command('cad-independent-readback',base+['--child','cad'],600)
        command('state-third-process',base+['--child','state'],180)
        command('native-history',base+['--child','history'],600)
        command('native-history-reopen',base+['--child','history-reopen'],300)
        for kind in ['blend','glb']:
            command('separate-process-'+kind,['blender','-b','-t','1','--python-exit-code','1','--python',str(wrapper),'--','--repo',str(repo),'--evidence',str(evidence),'--child',kind],600)
        binary_comparison=[]
        for name in ['assembly.FCStd','assembly.step','assembly.blend','assembly.glb']:
            binary_comparison.append({'path':name,'saved_sha256':digest(repo/'cad/stage3c/generated'/name),'regenerated_sha256':digest(generated/name),'byte_identical':digest(repo/'cad/stage3c/generated'/name)==digest(generated/name),'semantic_comparison':'PASS; independent native/STEP/Blender readback reports'})
        save(evidence/'native-summary.json',{'status':'PASS','scope':'batch native generation and separate-process reopen, not manual GUI','commands':len(records),'binary_comparison':binary_comparison,'continuous_path':'UNKNOWN','physical_strength':'NOT_TESTED','historical_certainty':'UNKNOWN'})
    except Exception as error:
        save(evidence/'native-summary.json',{'status':'FAIL','error':str(error),'native_acceptance':'HOLD','commands_completed':len(records)})
        raise

if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    parser=argparse.ArgumentParser();parser.add_argument('--repo',required=True,type=Path);parser.add_argument('--evidence',required=True,type=Path);parser.add_argument('--child',choices=['cad','state','blend','glb','history','history-reopen'])
    args=parser.parse_args(argv)
    if args.child:
        generated=args.evidence/'regenerated'
        if args.child=='cad':native_cad(args.repo,generated,args.evidence)
        elif args.child=='state':native_state_reopen(args.repo,args.evidence)
        elif args.child in ['history','history-reopen']:native_history(args.repo,generated,args.evidence,args.child=='history-reopen')
        else:native_blender(args.repo,generated,args.evidence,args.child)
    else:orchestrate(args)
