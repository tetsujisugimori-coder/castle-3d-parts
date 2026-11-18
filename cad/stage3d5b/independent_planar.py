"""Separate-reviewer reference route; not an independent CAD kernel execution.

Fixture generation follows stock-minus-open-rectangular-hole algebra; no
candidate geometry factory is imported. Affine reference enumerates every
coefficient/domain endpoint instead of calling candidate interval operations.
Shared Fraction, schema, semantics and candidate comparison calls are disclosed.
"""
from fractions import Fraction as Q
from pathlib import Path
import argparse,copy,hashlib,itertools,json,sys

def rectangle(axis,c,a0,a1,b0,b1,sign):
    a,b=(axis+1)%3,(axis+2)%3
    points=[]
    for u,v in [(a0,b0),(a1,b0),(a1,b1),(a0,b1)]:
        p=[0,0,0];p[axis]=c;p[a]=u;p[b]=v;points.append([str(x) for x in p])
    return points if sign>0 else points[::-1]

def fixture():
    faces=[]
    def face(label,axis,c,aa,bb,sign,hole=None):
        wires=[{'id':label+'-outer','role':'outer','curve_type':'Line',
                'vertices':rectangle(axis,c,*aa,*bb,sign)}]
        if hole is not None:
            wires.append({'id':label+'-inner','role':'inner','curve_type':'Line',
                          'vertices':rectangle(axis,c,*hole[0],*hole[1],-sign)})
        faces.append({'id':label,'surface':'Plane','axis':axis,'coordinate':str(c),
                      'normal_sign':sign,'wires':wires})
    face('xmin',0,0,(0,4),(0,6),-1,((1,3),(2,4)))
    face('xmax',0,2,(0,4),(0,6),1,((1,3),(2,4)))
    face('ymin',1,0,(0,6),(0,2),-1)
    face('ymax',1,4,(0,6),(0,2),1)
    face('zmin',2,0,(0,2),(0,4),-1)
    face('zmax',2,6,(0,2),(0,4),1)
    face('hole-ymin',1,1,(2,4),(0,2),1)
    face('hole-ymax',1,3,(2,4),(0,2),-1)
    face('hole-zmin',2,2,(0,2),(1,3),1)
    face('hole-zmax',2,4,(0,2),(1,3),-1)
    return {'schema':'rectilinear-boundary-v1','unit':'m','faces':faces}

def independent_cells():
    # Formula: x in[0,2], y in[0,4], z in[0,6], NOT(y in(1,3) AND z in(2,4)).
    # Atomic material closed boxes; their shared boundaries are material.
    return [[str(x) for x in (0,y0,z0,2,y1,z1)]
            for y0,y1 in [(0,1),(1,3),(3,4)]
            for z0,z1 in [(0,2),(2,4),(4,6)]
            if not (y0==1 and z0==2)]

def mutate(base):
    def one(label,fn):
        d=copy.deepcopy(base);fn(d);return label,d
    def reverse_face(d):
        d['faces'][0]['normal_sign']*=-1
        for w in d['faces'][0]['wires']:w['vertices'].reverse()
    def invert_all(d):
        for f in d['faces']:
            f['normal_sign']*=-1
            for w in f['wires']:w['vertices'].reverse()
    return [
        one('missing-face',lambda d:d['faces'].pop()),
        one('missing-inner-trim',lambda d:d['faces'][0]['wires'].pop()),
        one('orientation-reversed-with-consistent-winding',reverse_face),
        one('material-void-inverted',invert_all),
        one('unsupported-curve',lambda d:d['faces'][0]['wires'][0].update(curve_type='BSplineCurve')),
        one('unsupported-surface',lambda d:d['faces'][0].update(surface='Cylinder')),
        one('duplicate-face',lambda d:d['faces'].append(copy.deepcopy(d['faces'][0]))),
        one('zero-edge',lambda d:d['faces'][0]['wires'][0]['vertices'].insert(1,d['faces'][0]['wires'][0]['vertices'][0])),
        one('nonplanar-vertex',lambda d:d['faces'][0]['wires'][0]['vertices'][0].__setitem__(0,'1/1000')),
        one('wrong-unit',lambda d:d.update(unit='mm')),
        one('open-wire',lambda d:d['faces'][0]['wires'][0]['vertices'].pop()),
        one('hole-winding-reversed',lambda d:d['faces'][0]['wires'][1]['vertices'].reverse()),
    ]

def deform(base,mapping):
    d=copy.deepcopy(base)
    for f in d['faces']:
        if f['axis']==1:f['coordinate']=mapping.get(f['coordinate'],f['coordinate'])
        for w in f['wires']:
            for p in w['vertices']:p[1]=mapping.get(p[1],p[1])
    return d

def cavity(base):
    d=copy.deepcopy(base);d['faces']=d['faces'][:6]
    for f in d['faces']:f['wires']=f['wires'][:1]
    intervals=[('1/2','3/2'),('1','3'),('2','4')]
    for a in range(3):
        u,v=(a+1)%3,(a+2)%3
        for c,s in [(intervals[a][0],1),(intervals[a][1],-1)]:
            ident='cavity-'+str(a)+'-'+str(s)
            points=rectangle(a,c,*intervals[u],*intervals[v],s)
            d['faces'].append({'id':ident,'surface':'Plane','axis':a,'coordinate':c,'normal_sign':s,
                              'wires':[{'id':ident+'wire','role':'outer','curve_type':'Line','vertices':points}]})
    return d

def topology_fixture():
    d=fixture();vertices=[];edges=[];wires=[];faces=[]
    def vertex(p):
        mm=[str(Q(x)*1000) for x in p]
        ids=[i for i,v in enumerate(vertices) if v['point_mm_ieee']==mm]
        if ids:return ids[0]
        vertices.append({'point_mm_ieee':mm});return len(vertices)-1
    def edge(a,b):
        for i,e in enumerate(edges):
            if set(e['vertex_ids'])=={a,b}:return i
        edges.append({'vertex_ids':[a,b],'curve_type':'Line','degenerated_observed':False});return len(edges)-1
    for f in d['faces']:
        wis=[];fed=[];fvs=[]
        for w in f['wires']:
            vs=[vertex(p) for p in w['vertices']];es=[edge(a,b) for a,b in zip(vs,vs[1:]+vs[:1])]
            wis.append(len(wires));wires.append({'closed_observed':True,'ordered_vertex_ids':vs,'ordered_edge_ids':es})
            fed.extend(es);fvs.extend(vs)
        norm=['0']*3;norm[f['axis']]=str(f['normal_sign']);position=['0']*3;position[f['axis']]=str(Q(f['coordinate'])*1000)
        faces.append({'surface_type':'Plane','normal_ieee':norm,'position_mm_ieee':position,'wire_ids':wis,'wire_roles':[w['role'] for w in f['wires']],
                      'edge_ids':list(set(fed)),'vertex_ids':list(set(fvs))})
    return {'vertices':vertices,'edges':edges,'wires':wires,'faces':faces,'all_edges_used':True,'all_vertices_used':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True)
    ap.add_argument('--candidate-dir',type=Path,default=Path(__file__).resolve().parent);args=ap.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(args.candidate_dir.resolve()))
    import planar_contract as m
    import transform_bounds as t
    import planar_native as adapter
    rows=[]
    def check(ident,input_,expected,fn):
        result=fn();actual=result.get('boundary_math',{}).get('status',result.get('candidate_status',result.get('status','NO_STATUS')))
        ok=actual==expected if expected!='REJECT_OR_UNKNOWN' else actual in ('FAIL','UNKNOWN')
        row={'id':ident,'input':input_,'expected':expected,'actual':actual,'comparison_pass':ok,'result':result};rows.append(row)
        return result
    base=fixture()
    proof=check('normal-boundary-analytic-rectangular-opening',base,'PASS',lambda:m.verify_boundary(base))
    got=sorted([list(map(Q,b)) for b in proof['exact_material_cells_m']]);exp=sorted([list(map(Q,b)) for b in independent_cells()])
    assert got==exp and proof['atomic_material_cell_count']==8
    volume=sum((b[3]-b[0])*(b[4]-b[1])*(b[5]-b[2]) for b in got);assert volume==40
    for label,d in mutate(base):check(label,d,'FAIL',lambda d=d:m.verify_boundary(d))
    for label,mapping,expected in [('hole-enlarged',{'1':'1/2','3':'7/2'},'FAIL'),('hole-shrunk',{'1':'3/2','3':'5/2'},'PASS'),('hole-shifted',{'1':'3/2','3':'7/2'},'FAIL')]:
        model=deform(base,mapping)
        check(label+'-valid-boundary',model,'PASS',lambda model=model:m.verify_boundary(model))
        check(label+'-A-subset-M',{'source':base,'model':model},expected,lambda model=model:m.compare_material(base,model))
    delta=Q(1,10**12)
    for label,ylo,expected in [('void-through-query',Q(3,2),'PASS'),('wall-contact',Q(1),'FAIL'),('microseparation',Q(1)+delta,'PASS'),('microintrusion',Q(1)-delta,'FAIL')]:
        b=list(map(str,[-1,ylo,Q(5,2),3,Q(5,2),Q(7,2)]));check(label,b,expected,lambda b=b:m.certify_void_box(base,b))
    cav=cavity(base);check('disconnected-boundary-internal-cavity',cav,'FAIL',lambda:m.verify_boundary(cav))
    identity=[1,0,0,0,0,1,0,0,0,0,1,0]
    actual=identity.copy();actual[0]=['999/1000','1001/1000'];actual[3]=['-1/10','1/5'];actual[5]=['99/100','101/100'];actual[7]=['1/100','3/100']
    domain=[['-2','3'],['-5','-1'],['0','4']]
    ar=check('asymmetric-affine-error',{'actual':actual,'nominal':identity,'domain':domain},'PASS',lambda:t.affine_error(actual,identity,domain))
    # Separate reference: enumerate multilinear extrema at all coefficient and domain endpoints.
    row_ranges=[]
    for i in range(3):
        coeff=[]
        for j in range(4):
            v=actual[4*i+j];v=[Q(v),Q(v)] if not isinstance(v,list) else list(map(Q,v));coeff.append([a-Q(identity[4*i+j]) for a in v])
        vals=[sum(cs[j]*x[j] for j in range(3))+cs[3] for cs in itertools.product(*coeff) for x in itertools.product(*[list(map(Q,v)) for v in domain])]
        row_ranges.append([min(vals),max(vals)])
    independent_error=sum(max(abs(a),abs(b)) for a,b in row_ranges);assert Q(ar['error_m'])==independent_error
    for x in [['-1001/1000','-999/1000'],['-1/3','2/7']]:
        rounded=t.round_enclosure(x,'1/100');assert rounded.lo<=Q(x[0]) and rounded.hi>=Q(x[1])
        rows.append({'id':'round-'+x[0],'input':x,'quantum':'1/100','expected':'OUTWARD','actual':'OUTWARD','comparison_pass':True,'result':rounded.json()})
    top=topology_fixture();boxes=[['0','0','0','2','4','6']]
    check('adapter-normal-synthetic-topology',top,'PASS',lambda:adapter.assess(top,boxes))
    for label,key,row in [('unreferenced-vertex','vertices',{'point_mm_ieee':['9000']*3}),('unreferenced-edge','edges',{'vertex_ids':[0,1],'curve_type':'Line','degenerated_observed':False}),('unreferenced-wire','wires',copy.deepcopy(top['wires'][0]))]:
        bad=copy.deepcopy(top);bad[key].append(row);check('adapter-'+label,bad,'REJECT_OR_UNKNOWN',lambda bad=bad:adapter.assess(bad,boxes))
    report={'scope':'independent synthetic analytic reference and observation-adapter fault audit',
      'shared':['Python Fraction','schema','closed-material/open-void semantics','candidate functions called for comparisons'],
      'independent':['analytic stock-minus-rectangular-hole fixture and exact8cells/volume40','full mutation inputs','affine coefficient/domain endpoint enumeration'],
      'not_independent':['same Python runtime','native input extraction and FreeCAD kernel NOT_TESTED by this reviewer'],
      'normal_volume_m3':str(volume),'reference_cells_m':independent_cells(),
      'affine_reference_row_ranges':[[str(a),str(b)] for a,b in row_ranges],'affine_reference_error_m':str(independent_error),
      'case_count':len(rows),'all_comparisons_pass':all(r['comparison_pass'] for r in rows),'rows':rows,
      'source_sha256':{name:hashlib.sha256((args.candidate_dir/name).read_bytes()).hexdigest() for name in ['planar_contract.py','transform_bounds.py','planar_native.py','planar_document.py']},
      'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'real_brep_inclusion':'UNKNOWN','finite_real_error':'UNKNOWN','independent_kernel_rerun':'NOT_TESTED'}
    (args.output_dir/'independent-planar.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'case_count':len(rows),'all_comparisons_pass':report['all_comparisons_pass'],'failed_ids':[r['id'] for r in rows if not r['comparison_pass']]}))
    if not report['all_comparisons_pass']:raise SystemExit(1)

if __name__=='__main__':main()
