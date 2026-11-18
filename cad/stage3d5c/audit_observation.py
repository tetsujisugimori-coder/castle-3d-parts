"""Fixed observation comparison and semantic negative controls, not safety proof.

Reference must be freshly extracted from pinned original bytes, not supplied by
an untrusted observation. Compare full descriptors and every incidence. The
result certifies no generic CAD geometry: it is this fixed observation contract.
"""
import copy,hashlib,json
from collections import Counter
from fractions import Fraction as Q
from proof_contract import line_plane_identity

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def signature(row):return hashlib.sha256(canonical({k:v for k,v in row.items() if k!='identity'})).hexdigest()

def audit(candidate, reference):
    reasons=[]
    try:
        if candidate['source_brep_sha256']!=reference['source_brep_sha256']:reasons.append('FIXED_BREP_BINDING')
        t,r=candidate['topology'],reference['topology']
        for k in ('vertices','edges','wires','faces','shells','solids'):
            if len(t[k])!=len(r[k]):reasons.append('MISSING_OR_EXCESS_'+k.upper())
            for row in t[k]:
                if row['identity']['source_brep_sha256']!=candidate['source_brep_sha256'] or signature(row)!=row['identity']['descriptor_sha256']:
                    reasons.append('DESCRIPTOR_CONTENT_MISMATCH')
        vi={i for e in t['edges'] for i in e['vertex_ids']}
        eu=Counter(i for w in t['wires'] for i in w['ordered_edge_ids'])
        wu=Counter(i for f in t['faces'] for i in f['wire_ids'])
        fu=Counter(i for s in t['shells'] for i in s['face_ids'])
        su=Counter(i for s in t['solids'] for i in s['shell_ids'])
        if vi!=set(range(len(t['vertices']))) or set(eu)!=set(range(len(t['edges']))) or any(x!=2 for x in eu.values()) or set(wu)!=set(range(len(t['wires']))) or any(x!=1 for x in wu.values()) or set(fu)!=set(range(len(t['faces']))) or any(x!=1 for x in fu.values()) or set(su)!=set(range(len(t['shells']))) or any(x!=1 for x in su.values()):
            reasons.append('UNCOVERED_OR_DUPLICATED_TOPOLOGY')
        for f in t['faces']:
            expected=[(wi,ei,j) for wi in f['wire_ids'] for j,ei in enumerate(t['wires'][wi]['ordered_edge_ids'])]
            actual=[(u['wire_id'],u['edge_id'],u['order']) for u in f['pcurve_uses']]
            if actual!=expected:reasons.append('PCURVE_USE_INVENTORY')
            for u in f['pcurve_uses']:
                pc=u['pcurve'];e=t['edges'][u['edge_id']]['curve3d'];s=f['surface_frame_ieee']
                if pc is None:reasons.append('MISSING_PCURVE');continue
                case={'curve_type':e['type'],'pcurve_type':'Line2d' if pc['type'] in ('Line2d','Line2dSegment') else pc['type'],
                    'surface_type':f['surface_type'],'c0':e['origin_mm_ieee'],'c1':e['direction_ieee'],
                    'p0':pc['origin_uv_ieee'],'p1':pc['direction_uv_ieee'],
                    'origin':s['origin_mm'],'u_axis':s['u'],'v_axis':s['v'],'range':pc['use_parameter_range_ieee']}
                result=line_plane_identity(case)
                if result['status']!='PASS':reasons.append(result.get('reason','UNSUPPORTED'))
                if pc['use_parameter_range_ieee']!=e['parameter_range_ieee']:reasons.append('RANGE_MISMATCH')
                if u['edge_descriptor_sha256']!=t['edges'][u['edge_id']]['identity']['descriptor_sha256']:reasons.append('EDGE_USE_IDENTITY')
        # Geometry and orientations must match the independently pinned extraction,
        # not merely a rewritten self-consistent family of descriptors.
        for k in ('vertices','edges','wires','faces','shells','solids'):
            for a,b in zip(t[k],r[k]):
                if a.get('orientation')!=b.get('orientation'):reasons.append('ORIENTATION_CHANGED')
                if a.get('placement_ieee')!=b.get('placement_ieee'):reasons.append('LOCATION_CHANGED')
                if canonical(a)!=canonical(b):reasons.append('FIXED_DESCRIPTOR_OR_INCIDENCE_CHANGED')
        if t['shape_orientation']!=r['shape_orientation']:reasons.append('MATERIAL_ORIENTATION_CHANGED')
        if t['shape_placement_ieee']!=r['shape_placement_ieee']:reasons.append('LOCATION_CHANGED')
        if canonical(t)!=canonical(r):reasons.append('FIXED_OBSERVATION_CHANGED')
    except (KeyError,IndexError,TypeError,ValueError,ZeroDivisionError) as e:
        reasons.append('MALFORMED_OBSERVATION:'+type(e).__name__)
    return {'status':'FAIL' if reasons else 'PASS','reasons':sorted(set(reasons)),
            'scope':'fixed native-derived observation contract only',
            'real_geometry_collision':'UNKNOWN','material_outer':'UNKNOWN','void_inner':'UNKNOWN'}

def controls(record):
    rows=[]
    def check(id,c,reason=None):
        result=audit(c,record);expected='PASS' if reason is None else 'FAIL'
        rows.append({'id':id,'scope':'mutated observation only; not mutated CAD or actual collision',
          'reference_brep_sha256':record['source_brep_sha256'],'input':c,'expected_status':expected,'expected_reason':reason,'actual':result})
        if result['status']!=expected or (reason and reason not in result['reasons']):raise AssertionError(id)
    check('normal',copy.deepcopy(record))
    for k in ('vertices','edges','wires','faces','shells','solids'):
        c=copy.deepcopy(record);c['topology'][k].pop();check('missing-'+k,c,'MISSING_OR_EXCESS_'+k.upper())
        c=copy.deepcopy(record);c['topology'][k].append(copy.deepcopy(c['topology'][k][-1]));check('unreferenced-extra-'+k,c,'MISSING_OR_EXCESS_'+k.upper())
    for k in ('faces','wires'):
        c=copy.deepcopy(record);row=c['topology'][k][0];row['orientation']='Reversed' if row['orientation']=='Forward' else 'Forward';check('reversed-'+k,c,'ORIENTATION_CHANGED')
    c=copy.deepcopy(record);c['topology']['shape_orientation']='Reversed';check('material-side-reverse',c,'MATERIAL_ORIENTATION_CHANGED')
    for key in ('origin_uv_ieee','direction_uv_ieee'):
        c=copy.deepcopy(record);pc=c['topology']['faces'][0]['pcurve_uses'][0]['pcurve'];pc[key][0]=str(Q(pc[key][0])+1);check('pcurve-'+key,c,'PCURVE_SURFACE_3D_INCONSISTENCY')
    c=copy.deepcopy(record);s=c['topology']['faces'][0]['surface_frame_ieee'];s['origin_mm'][0]=str(Q(s['origin_mm'][0])+1);check('surface-shift',c,'PCURVE_SURFACE_3D_INCONSISTENCY')
    c=copy.deepcopy(record);c['topology']['faces'][0]['pcurve_uses'].pop();check('missing-pcurve-use',c,'PCURVE_USE_INVENTORY')
    # Derive the guide opening endpoints through face inner-wire incidence,
    # never through an arbitrary ordinal. These remain observation mutations.
    t=record['topology']
    inner={wi for f in t['faces'] for wi,role in zip(f['wire_ids'],f['wire_roles']) if role=='inner'}
    vids={vi for wi in inner for ei in t['wires'][wi]['ordered_edge_ids'] for vi in t['edges'][ei]['vertex_ids']}
    if vids:
        center={axis:sum((Q(t['vertices'][i]['point_mm_ieee'][axis]) for i in vids),Q(0))/len(vids) for axis in (1,2)}
        for label,scale,shift in [('opening-enlarged',Q(11,10),Q(0)),('opening-shrunk',Q(9,10),Q(0)),('opening-shifted',Q(1),Q(2))]:
            c=copy.deepcopy(record)
            for i in vids:
                p=c['topology']['vertices'][i]['point_mm_ieee']
                for axis in (1,2):p[axis]=str(center[axis]+(Q(p[axis])-center[axis])*scale+shift)
            check(label+'-endpoint-observation',c,'FIXED_DESCRIPTOR_OR_INCIDENCE_CHANGED')
    c=copy.deepcopy(record);c['topology']['shape_placement_ieee'][3]=str(Q(c['topology']['shape_placement_ieee'][3])*2);check('double-location',c,'LOCATION_CHANGED')
    # Repeat a geometric corruption with all row self-hashes recalculated.
    c=copy.deepcopy(record);c['topology']['vertices'][0]['point_mm_ieee'][0]='99999'
    for k in ('vertices','edges','wires','faces','shells','solids'):
        for row in c['topology'][k]:row['identity']['descriptor_sha256']=signature(row)
    check('self-rehashed-geometry-not-trusted',c,'FIXED_DESCRIPTOR_OR_INCIDENCE_CHANGED')
    return rows
