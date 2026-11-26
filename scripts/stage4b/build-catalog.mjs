import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {saveAssembly} from '../../assembly/stage4a/contract.mjs';

const base='cad/stage4b/west-gate-left';
const spec=JSON.parse(readFileSync(base+'/spec.json'));
const mode=process.argv[2];
if(!['--generate','--check'].includes(mode))throw Error('choose --generate or --check');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
function file(path,value){
 const s=(typeof value==='string'?value:JSON.stringify(value,null,2)+'\n');
 if(mode==='--check'){
  if(s!==readFileSync(path,'utf8'))throw Error('metadata drift: '+path);
 }else writeFileSync(path,s);
}
const assets=(stem,assembly_id,parts)=>{
 const glb=base+'/'+stem+'.glb';
 const manifest=base+'/'+stem+'.manifest.json',glb_sha256=hash(glb);
 file(manifest,{schema_version:1,assembly_id,revision:spec.revision,basis:'D',cad_eligibility:'reference_only',
  unit:'m',frame:spec.frame,parts,files:{glb:{path:stem+'.glb',sha256:glb_sha256}}});
 return {manifest,glb,glb_sha256};
};
const toM=mm=>mm.map(v=>v/1000);
const bounds=(name,lo,key)=>({
 glb_node:name,bounds_m:toM([...lo,...lo.map((v,i)=>v+spec.definitions[key].size_mm[i])]),
});
const definitions=Object.entries(spec.definitions).map(([id,d])=>{
 const board=id.endsWith('BOARD');
 return {id,upstream_id:id,revision:spec.revision,pose:null,subset:null,basis:'D',eligibility:'reference_only',
  label:board?'左門扉の板材（D0）':'左門扉の横桟（D0）',nodes:[d.node],ports:{},
  ...assets(board?'west-gate-board-web':d.stem,id,[bounds(d.node,[0,0,0],id)])};
});
assets('west-gate-left-leaf',spec.assembly_id,spec.instances.map(r=>bounds(r.id,r.at_mm,r.source)));
const catalog={schema_version:1,basis:'D',frame:spec.frame,unit:'m',
 baseline_commit:'8dcd835523c4de68f2f39e8cc5ea078c712a358d',
 definitions,limits:{historical:'UNKNOWN',physical_strength:'NOT_TESTED',continuous_motion:'UNKNOWN',joinery:'UNKNOWN',
 connection:'NO_CERTIFIED_PORTS',model:'STATIC_REFERENCE_ONLY'}};
const assembly={schema_version:2,basis:'D',frame:spec.frame,unit:'m',catalog_commit:catalog.baseline_commit,
 instances:spec.instances.map(r=>({id:r.id,definition_id:r.source,revision:spec.revision,pose:null,translation_m:toM(r.at_mm),yaw_quarters:0})),
 connections:[]};
file('assembly/stage4b/catalog.json',catalog);
file('assembly/stage4b/example.json',await saveAssembly(catalog,assembly));
