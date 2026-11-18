"""Document observations exclusively in a byte-identical isolated FCStd copy.

Recompute here is deliberately separate from read-only BRep member extraction.
No Document is saved. Finite represented-coefficient comparisons do not enclose
the geometric real or establish all-state equivalence.
"""
from fractions import Fraction as F
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
import native


def represented_matrix(matrix):
    values = [F(x) for x in matrix]
    # Convert translations mm -> m exactly after lifting the binary doubles.
    return [str(x/1000 if i%4 == 3 else x) for i, x in enumerate(values[:12])]


def snapshot(doc):
    result = {}
    for name in native.PARTS:
        o = doc.getObject(name)
        if o is None: raise ValueError('DOCUMENT_OBJECT_MISSING:'+name)
        parent = o.getParentGeoFeatureGroup()
        chain, seen = [], set()
        while parent is not None:
            if parent.Name in seen: raise ValueError('PARENT_CYCLE')
            seen.add(parent.Name)
            chain.append({'object_id':parent.Name, 'placement':native.placement(parent.Placement)})
            parent = parent.getParentGeoFeatureGroup()
        result[name] = {'object_id':o.Name, 'type_id':o.TypeId,
                        'part_id':getattr(o, 'PartID', None),
                        'object_placement':native.placement(o.Placement),
                        'global_placement':native.placement(o.getGlobalPlacement()),
                        'parent_chain_nearest_first':chain,
                        'expression_engine':list(o.ExpressionEngine),
                        'in_list_ids':[x.Name for x in o.InList],
                        'state':list(o.State), 'shape':native.describe(o.Shape)}
    return result


def main(out):
    sys.path.extend(['/usr/lib/freecad-python3/lib', '/usr/lib/freecad/lib'])
    import FreeCAD as A
    import Part
    from transform_bounds import affine_error, combined_error, ERROR_COMPONENTS, chain, IDENTITY
    sys.path.insert(0, str(native.ROOT/'cad/stage3c'))
    from state import transition
    out.mkdir(parents=True, exist_ok=False)
    original = native.FCSTD.read_bytes()
    if native.digest(original) != native.FCSTD_PIN: raise ValueError('PINNED_INPUT_MISMATCH')
    work = out/'isolated'; work.mkdir()
    copy = work/'assembly.FCStd'; copy.write_bytes(original)
    transient = work/'transient'; transient.mkdir()
    doc = A.newDocument('D5BPlanarIsolated')
    try:
        doc.TransientDir = str(transient.resolve())+'/'
        doc.FileName = str(copy.resolve())
        doc.restore()
        # Disable drawing updates only in the isolated in-memory Document.
        for obj in doc.Objects:
            if 'KeepUpdated' in obj.PropertiesList: obj.KeepUpdated = False
        before = snapshot(doc)
        doc.recompute()
        after = snapshot(doc)
        cases, comparisons, declared_paths = [], [], []
        for mm in (0,70,140):
            transition(doc, 0, mm/1000)
            snap = snapshot(doc)
            for name in native.PARTS:
                base = before[name]['shape']['shape_placement_observed']['matrix_observed']
                observed = snap[name]['shape']['shape_placement_observed']['matrix_observed']
                # Test the explicit serialized-Shape path and faults relative
                # to this declared inventory. Its world-frame semantics remain
                # unproved; no XML or parent transform is silently injected.
                expected_ids=['serialized-location','mm-to-m']
                location={'id':expected_ids[0],'from_frame':'stored-local','to_frame':'stored-located',
                          'from_unit':'mm','to_unit':'mm','matrix':[str(F(x)) for x in observed[:12]]}
                scale={'id':expected_ids[1],'from_frame':'stored-located','to_frame':'represented-m',
                       'from_unit':'mm','to_unit':'m','matrix':[str(F(x,1000)) for x in IDENTITY]}
                paths=[('normal',[location,scale]),('location-missing',[scale]),
                       ('location-twice',[location,location,scale])]
                wrong=dict(scale);wrong['matrix']=list(IDENTITY)
                paths.append(('wrong-unit-scale',[location,wrong]))
                declared_paths.append({'object_id':name,'travel_mm':mm,
                    'expected_path_inventory':expected_ids,'inventory_origin':'explicit extraction rule, NOT independently certified Document/world path',
                    'cases':[{'id':label,'input':entries,'expected':'PASS' if label=='normal' else 'FAIL',
                              'result':chain(entries,expected_ids,'stored-local','represented-m')} for label,entries in paths],
                    'world_equivalence':'UNKNOWN'})
                for item in declared_paths[-1]['cases']:
                    if item['result']['status'] != item['expected']:
                        raise AssertionError('DECLARED_PATH_CONTROL:'+item['id'])
                nominal = represented_matrix(base)
                if name == native.PARTS[0]: nominal[3] = str(F(nominal[3])+F(mm,1000))
                identity = [1,0,0,0,1,0,0,0,1]
                if [F(base[4*i+j]) for i in range(3) for j in range(3)] != identity:
                    comparisons.append({'object_id':name,'travel_mm':mm,'status':'UNKNOWN',
                                        'reason':'nonidentity-baseline-needs-certified-inverse-domain'})
                    continue
                # Domain covers the finite observed vertices relative to their
                # stored Shape Location. This remains an observed domain.
                verts = [p for f in before[name]['shape']['faces'] for p in f['vertices_mm_observed']]
                base_t = before[name]['shape']['shape_placement_observed']['base_mm_observed']
                domain = [[str(min(F(p[j])-F(base_t[j]) for p in verts)/1000),
                           str(max(F(p[j])-F(base_t[j]) for p in verts)/1000)] for j in range(3)]
                c = affine_error(represented_matrix(observed), nominal, domain)
                comparisons.append({'object_id':name, 'travel_mm':mm, 'reference_travel_mm':0,
                                    'nominal_matrix_m':nominal, 'observed_represented_matrix_m':represented_matrix(observed),
                                    'domain_m':domain, 'represented_matrix_difference':c,
                                    'status':'UNKNOWN', 'scope':'exact difference of stored coefficients only; real-state equivalence unproved'})
            cases.append({'door_degrees':0,'travel_mm':mm,'parts':snap,
                          'scope':'isolated Document recompute observation, no continuous proof'})
        result = {'schema':'isolated-document-placement-v1', 'FreeCAD':A.Version(),'OCCT':Part.OCC_VERSION,
                  'source_sha256':native.FCSTD_PIN, 'isolated_copy_before_sha256':native.digest(original),
                  'restored_before_explicit_recompute':before,'after_explicit_recompute':after,
                  'states':cases,'represented_matrix_comparisons':comparisons,
                  'declared_path_controls':declared_paths,
                  'placement_rule':'raw Shape import includes serialized Location once; Document owns object/parent placement; never apply XML to an already located Shape',
                  'real_error_components':combined_error({key:None for key in ERROR_COMPONENTS}),
                  'finite_unit_conversion':'exact mathematical mm/1000, not geometric-real provenance',
                  'real_world_equivalence':'UNKNOWN', 'all_state_equivalence':'UNKNOWN',
                  'continuous_motion':'NOT_TESTED','document_saved':False,'original_document_opened':False}
        if copy.read_bytes() != original or native.FCSTD.read_bytes() != original:
            raise AssertionError('SOURCE_OR_ISOLATED_FILE_CHANGED')
        result['original_and_copy_after_sha256'] = native.digest(original)
        (out/'document.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print('Isolated Document state observations recorded; geometric-real placement error UNKNOWN',flush=True)
    finally:
        A.closeDocument(doc.Name)


if __name__ == '__main__':
    try: main(Path(sys.argv[1]))
    except BaseException:
        os.write(2,traceback.format_exc().encode());os._exit(1)
    os._exit(0)
