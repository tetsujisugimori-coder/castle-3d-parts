"""Validate actual runtime OCCT member-function interposition, not replay.

Only the original 5 fixed UV points; no added samples and no native-all-points
claim. Missing hooks, unmatched edges, or trace/existing-output disagreement
means INCOMPLETE/FAIL, never PASS.
"""
import json
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import sys

from face_region import FCSTD_SHA, D2_SHA, GUIDE_BREP_SHA, TRIM_SHA, GUIDE
from one_slice import FCSTD, CONTRACT
from verify_face0_uv import QUERIES

def digest(b):
    return sha256(b).hexdigest()

def rational(x):
    if type(x) not in (float,str,int) or isinstance(x,bool):
        raise ValueError('UNSUPPORTED_NATIVE_NUMBER')
    return F(x)

def endpoints(row):
    return frozenset(tuple(map(rational,pt)) for pt in row)

def inventory(tr):
    if (tr.get('source_fcstd_sha256') != FCSTD_SHA
            or tr.get('source_d2_sha256') != D2_SHA):
        raise ValueError('UNPINNED_TRIM_SOURCE')
    guide=tr['parts'][GUIDE]
    face=next(f for f in guide['faces'] if f['face']==0)
    if face['status']!='PASS' or len(face['wires'])!=2:
        raise ValueError('TARGET_FACE_CHANGED')
    out={}
    for wire in face['wires']:
        for use in wire['uses']:
            key=endpoints(use['directed_uv'])
            if len(key)!=2 or key in out:
                raise ValueError('NON_UNIQUE_OR_DEGENERATE_GUIDE_EDGE')
            out[key]={'edge':use['edge'],'wire':wire['wire'],
                      'role':wire['role'],'orientation':use['orientation']}
    if len(out)!=8:
        raise ValueError('EXPECTED_EIGHT_FIXED_EDGES')
    return out

def validate(base, traced, events, tr):
    result={'status':'FAIL','native_actual_interposition':'UNKNOWN',
            'native_classification_five_states':'UNKNOWN',
            'native_classifier_total_rounding_error':'UNKNOWN',
            'native_full_face_set_equality':'UNKNOWN',
            'native_material_outer':'UNKNOWN','native_void_inner':'UNKNOWN',
            'native_representative_interval':'NOT_TESTED'}
    try:
        if base!=traced or base.get('occt')!='7.8.1':
            raise ValueError('INTERPOSED_OUTPUT_NOT_IDENTICAL_TO_BASELINE')
        if base.get('sample_count')!=5 or len(base.get('samples',[]))!=5:
            raise ValueError('WRONG_NATIVE_FIVE_POINT_SET')
        by_query={}
        for i,(name,pt,expected) in enumerate(QUERIES):
            n=base['samples'][i]
            if n.get('id')!=name or tuple(map(rational,n['uv']))!=pt or n['state']!=expected:
                raise ValueError('NATIVE_FIVE_POINT_EXPECTATION_CHANGED')
            by_query[name]=[]
        inv=inventory(tr)
        if not events or len(events)>1024:
            raise ValueError('MISSING_OR_UNBOUNDED_RUNTIME_HOOK_EVENTS')
        annotated=[]
        ordinal_map={}
        for i,e in enumerate(events):
            if e.get('seq')!=i+1 or e.get('query') not in by_query or e.get('event') not in ('ray_choice','intersector','compare'):
                raise ValueError('INVALID_RUNTIME_EVENT_SEQUENCE_OR_QUERY')
            q=e['query'];kind=e['event']
            if kind=='ray_choice':
                if tuple(map(rational,e['candidate_point_uv'])) != next(p for name,p,_ in QUERIES if name==q):
                    raise ValueError('REPLAYED_OR_MISMATCHED_QUERY')
                if e.get('selected') not in (True,False):
                    raise ValueError('MISSING_ACTUAL_RAY_SELECTION_STATUS')
                if e.get('selected'):
                    ray=e['ray']
                    if tuple(map(rational,ray['origin'])) != next(p for name,p,_ in QUERIES if name==q):
                        raise ValueError('SELECTED_RAY_FROM_WRONG_QUERY')
            else:
                ordnum=e.get('face_local_edge_ordinal')
                if type(ordnum) is not int or not 1<=ordnum<=8:
                    raise ValueError('EDGE_NOT_IN_FIXED_FACE_ZERO')
                k=endpoints((e['edge_start_uv'],e['edge_end_uv']))
                if k not in inv:
                    raise ValueError('NATIVE_HOOK_EDGE_NOT_IN_STORED_PCURVE_INVENTORY')
                item=inv[k]
                if ordnum in ordinal_map and ordinal_map[ordnum]!=item['edge']:
                    raise ValueError('EDGE_ORDINAL_MAPPING_CHANGED')
                ordinal_map[ordnum]=item['edge']
                if e.get('edge_orientation') not in ('Forward','Reversed'):
                    raise ValueError('NATIVE_EDGE_ORIENTATION_UNSUPPORTED')
                if e.get('use_bbox') is not False or rational(e.get('gap_check_tolerance'))!=F('0.1'):
                    raise ValueError('CLASSIFIER_OPTIONS_DIFFER_FROM_FIXED_CASE')
                if kind=='intersector':
                    ray=e['ray']
                    if tuple(map(rational,ray['origin']))!=next(p for name,p,_ in QUERIES if name==q):
                        raise ValueError('ACTUAL_INTERSECTION_RAY_HAS_WRONG_ORIGIN')
                    if rational(e['tol_argument'])<=0:
                        raise ValueError('MISSING_INTERSECTOR_TOLERANCE')
                    if e.get('is_done') not in (True,False):
                        raise ValueError('INTERSECTION_COMPLETION_MISSING')
                    if e['is_done'] and (type(e.get('intersection_points')) is not int
                                        or type(e.get('intersection_segments')) is not int):
                        raise ValueError('INTERSECTION_COUNTS_MISSING')
                else:
                    if e.get('compare_orientation') not in ('Forward','Reversed'):
                        raise ValueError('COMPARED_EDGE_ORIENTATION_UNSUPPORTED')
                    if type(e.get('closest_index')) is not int or e.get('state_after') not in ('IN','OUT','ON','UNKNOWN'):
                        raise ValueError('INCOMPLETE_CLOSEST_INTERSECTION')
                e={**e,'global_fixed_edge':item['edge'],'wire':item['wire'],'wire_role':item['role']}
            by_query[q].append(e)
            annotated.append(e)
        records=[]
        for name,pt,expected in QUERIES:
            entries=by_query[name]
            selected=[e for e in entries if e['event']=='ray_choice' and e['selected']]
            intersection=[e for e in entries if e['event']=='intersector']
            comparisons=[e for e in entries if e['event']=='compare']
            relevant=[e for e in comparisons if e['closest_index']>0]
            if not selected or not intersection or not comparisons or len(intersection)!=len(comparisons) or not relevant:
                raise ValueError('ACTUAL_RAY_OR_CLOSEST_EDGE_NOT_CAPTURED:'+name)
            hits=[e for e in intersection if e['is_done'] and
                    e.get('intersection_points',0)+e.get('intersection_segments',0)>0]
            if not hits:
                raise ValueError('NO_ACTUAL_NATIVE_EDGE_INTERSECTION:'+name)
            records.append({
                'id':name,'uv':[str(x) for x in pt],
                'classifier_state':expected,
                'rays_selected':len(selected),'candidate_rays_total':len(entries)-len(intersection)-len(comparisons),
                'edge_calls':len(intersection),'hit_events':len(hits),
                'edge_use_sequence':[e['global_fixed_edge'] for e in intersection],
                'closest_edge_sequence':[e['global_fixed_edge'] for e in relevant],
                'selected_rays':[e['ray'] for e in selected],
                'closest_transitions':[{'edge':e['global_fixed_edge'],'state_after':e['state_after'],
                                       'closest_index':e['closest_index']} for e in relevant],
            })
        return {**result,'status':'PASS','native_actual_interposition':'PASS',
                'native_classification_five_states':'PASS',
                'fixed_face_edge_inventory':len(inv),
                'observed_distinct_edge_count':len(ordinal_map),
                'instrumented_events':len(annotated),
                'five_points':records,
                'events':annotated,
                'scope':'actual linked OCCT 7.8.1 runtime member-function call trace, NOT numerical proof of all-point equality'}
    except (KeyError,ValueError,TypeError,StopIteration,IndexError,ZeroDivisionError) as e:
        return {**result,'reason':str(e)}

def main(base_file,raw_file,events_file,trim_file,hook_file,output):
    output.mkdir(parents=True,exist_ok=False)
    if digest(FCSTD.read_bytes())!=FCSTD_SHA or digest(CONTRACT.read_bytes())!=D2_SHA:
        raise ValueError('PINNED_SOURCE_CHANGED')
    raw=base_file.read_bytes(),raw_file.read_bytes(),events_file.read_bytes(),trim_file.read_bytes()
    if digest(raw[3])!=TRIM_SHA:
        raise ValueError('UNCHANGED_TRIM_PROVENANCE_MISMATCH')
    with __import__('zipfile').ZipFile(FCSTD) as z:
        if digest(z.read(GUIDE+'.Shape.brp'))!=GUIDE_BREP_SHA:
            raise ValueError('PINNED_GUIDE_BREP_CHANGED')
    try:
        ev=[json.loads(line) for line in raw[2].decode('utf-8').splitlines()]
        assessment=validate(json.loads(raw[0]),json.loads(raw[1]),ev,json.loads(raw[3]))
    except (ValueError,UnicodeError,KeyError) as e:
        assessment={'status':'FAIL','reason':type(e).__name__+': '+str(e),
                    'native_actual_interposition':'UNKNOWN',
                    'native_classifier_total_rounding_error':'UNKNOWN',
                    'native_full_face_set_equality':'UNKNOWN',
                    'native_representative_interval':'NOT_TESTED'}
    assessment.update({'schema':'d5d-face0-actual-occt-branch-trace-v1',
                       'inputs_sha256':{name:digest(data) for name,data in
                                       zip(('native_baseline','native_interposed','hook_events','trim'),raw)},
                       'hook_binary_sha256':digest(hook_file.read_bytes())})
    (output/'trace-report.json').write_text(json.dumps(assessment,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return 0 if assessment['status']=='PASS' else 2

if __name__=='__main__':
    if len(sys.argv)!=7:
        raise SystemExit('usage: verify_face0_trace.py BASELINE TRACED EVENTS TRIM HOOK SO OUTPUT_DIR')
    sys.exit(main(*(Path(p) for p in sys.argv[1:])))
