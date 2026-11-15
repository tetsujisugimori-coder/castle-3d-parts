"""Fixed exact-model boundary report. Not an imported-CAD certificate."""
import hashlib,json,sys
from pathlib import Path
from boundary import from_boxes,verify_boundary,verify_void,enclose,pair_relation
from bridge import ROOT,sources
sys.path.insert(0,str(ROOT/'cad/stage3d2'))
from proof import verify
def build_report():
    c=json.loads((ROOT/'cad/stage3d2/contract.json').read_text())
    identity=sources()
    a=from_boxes([c['moving_box']]);b=from_boxes(c['obstacle_boxes'])
    analytical=verify(c,'9e8bb54754f2ce8ff0623bc5a2676788f22ec2154f4da98c66939eaae0b287a2',identity)
    report={'schema':1,'sources':identity,'scope':'exact analytical rational boundary; NO BRep conversion',
            'parts':c['parts'],'unit':'mm','coordinate_frame':'D2 analytical world','door_degrees':0,'travel_mm':[0,140],
            'boundaries':{'bolt':a,'guide':b},'verified':{'bolt':verify_boundary(a),'guide':verify_boundary(b)},
            'guide_outer':enclose(b,'1/10'),
            'hole_inner':verify_void(b,['-201','-1159/10','9991/10','-179','-941/10','10409/10']),
            'whole_stock_limitation':{'reason':'Whole stock fills through-hole; overlap is not actual CAD collision FAIL',
               'relation':pair_relation(a,from_boxes([['-200','-130','990','-180','0','1050']]))},
            'analytical':analytical,'analytical_counts':{s:sum(r['status']==s for r in analytical['intervals']) for s in ['PASS','FAIL','UNKNOWN']},
            'cad_counts':{'PASS':0,'FAIL':0,'UNKNOWN':128},
            'cad_connection':'UNKNOWN: exact rational boundary has no certified relation to floating-point trimmed BRep',
            'real_object_guarantee':'NOT_TESTED'}
    if report['analytical_counts']!={'PASS':128,'FAIL':0,'UNKNOWN':0}:raise AssertionError('D2_REGRESSION')
    return report

if __name__=='__main__':
    out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise ValueError('EVIDENCE_ALREADY_EXISTS')
    report=build_report()
    out.write_text(json.dumps(report,indent=2));print(json.dumps({'analytical':report['analytical_counts'],'CAD':report['cad_counts']}))
