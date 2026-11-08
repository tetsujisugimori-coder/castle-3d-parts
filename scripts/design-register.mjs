import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {validateSchema} from './observation-schema.mjs';
export const root=fileURLToPath(new URL('../',import.meta.url));
const read=p=>JSON.parse(readFileSync(root+p,'utf8'));
export const digest=x=>createHash('sha256').update(x).digest('hex');
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const fail=c=>{throw Error(c)};
export const load=()=>readdirSync(root+'design/decisions').filter(p=>p.endsWith('.json')).sort().map(p=>({path:p,data:read('design/decisions/'+p)}));
const schema=read('design/schema/decision.schema.json');
const concepts={post_height:['m','height'],post_width:['m','post_width'],post_center_spacing:['m','spacing'],post_count:['count','count'],rail_levels:['count','rails'],cross_section:['description',null],arrangement:['description',null]};
export function validate(rows=load()){
 if(arguments.length>1)fail('BASELINE_OVERRIDE_FORBIDDEN');
 const baseline=read('design/baseline.json');
 const initialPins={"DEC-0001-r1.json": "136b500a89d3829088dc44ed254f4507f4ecadae0d295b4ef024c61e0a7fe6bb", "DEC-0002-r1.json": "df08021ddc590fcfe41c870895f048b5484fd70d60dfd518386f464322c768cf"};
 if(!same(baseline.decisions,initialPins))fail('INITIAL_MANIFEST_CHANGED');
 const catalog=read('catalog/wooden-palisade-v0.json'),keys=new Map();
 for(const row of rows){validateSchema(row.data,schema);const d=row.data,key=`${d.id}-r${d.revision}.json`;if(row.path!==key)fail('FILENAME');if(keys.has(key))fail('DUPLICATE_REVISION');keys.set(key,d)}
 // Immutable original decisions remain present. Later revisions are separate files.
 for(const [path,sha] of Object.entries(baseline.decisions)){if(!keys.has(path))fail('HISTORY_LOST');if(digest(readFileSync(root+'design/decisions/'+path))!==sha)fail('HISTORY_MUTATED')}
 for(const {data:d} of rows){
  if(!Number.isFinite(Date.parse(d.created_at))||!/[Z]|[+-]\d\d:\d\d$/.test(d.created_at))fail('DATE');
  if(d.cad.eligibility!=='reference_only'||d.cad.write_allowed)fail('CAD_WRITE_FORBIDDEN');
  const h=d.hypothesis;if(!/^HYP-\d{4}$/.test(h.id)||h.path!==`research/hypotheses/${h.id}.json`)fail('HYP_REFERENCE');
  let raw;try{raw=execFileSync('git',['show',`${h.commit}:${h.path}`],{cwd:root,stdio:['ignore','pipe','pipe']})}catch{fail('HYP_FIXED_COMMIT_UNAVAILABLE')}
  if(digest(raw)!==h.sha256)fail('HYP_HASH');const hyp=JSON.parse(raw);if(hyp.id!==h.id||hyp.revision!==h.revision)fail('HYP_REVISION');
  if(d.site!==hyp.target_site||d.part_id!==catalog.id)fail('TARGET');
  const claim=x=>x.observation_id+'/'+x.item_kind+'/'+x.item_id;
  if(!same(d.support,hyp.support.map(claim))||!same(d.counterevidence,hyp.counterevidence.map(claim)))fail('EVIDENCE_SUBSTITUTION');
  if(!same(d.competitors,hyp.competing_hypotheses))fail('COMPETITOR');
  if(!same(d.unknowns,[...hyp.unknowns,...hyp.adverse_information]))fail('UNKNOWN_LOSS');
  if(d.status==='adopted'&&hyp.status!=='partly_supported')fail('UNSUPPORTED_ADOPTION');
  if(d.status==='rejected'&&!hyp.counterevidence.length)fail('UNSUPPORTED_REJECTION');
  if(d.revision===1){if(d.previous!==null||d.change_evidence.length)fail('INITIAL_HISTORY')}else{
   const previous=`${d.id}-r${d.revision-1}.json`,old=keys.get(previous);if(d.previous!==previous||!old)fail('PREVIOUS_REVISION');
   if(d.created_at<old.created_at||d.reason===old.reason)fail('REVISION_REASON');
   if(d.status!==old.status){const valid=d.status==='rejected'?d.counterevidence:d.support;if(!d.change_evidence.length||d.change_evidence.some(e=>!valid.includes(e)))fail('CHANGE_EVIDENCE')}
  }
  if(d.parameters.length!==Object.keys(concepts).length||new Set(d.parameters.map(p=>p.name)).size!==d.parameters.length)fail('PARAMETER_SET');
  for(const p of d.parameters){const def=concepts[p.name];if(!def||p.unit!==def[0]||p.measurement_target!==p.name)fail('MEASUREMENT_CONCEPT');if(p.application_site!==d.site)fail('PARAMETER_SITE');
   // Stage 4 establishes a reference-only contract. Real A/B/C numeric use needs a separately reviewed extraction contract.
   if(p.historical_value!==null||p.hypothesis_value!==null)fail('UNCONFIRMED_VALUE');
   if(p.basis!=='D')fail('BASIS_PROMOTION');const expected=def[1]?catalog.dimensions_m[def[1]]:null;
   if(p.prototype_value!==expected)fail('PROTOTYPE_VALUE');
   if(p.evidence_id!==(def[1]?`catalog/wooden-palisade-v0.json#/dimensions_m/${def[1]}`:'none'))fail('PARAMETER_EVIDENCE');
   if(p.confirmation!==(expected===null?'unknown':'prototype_only'))fail('CONFIRMATION_PROMOTION');
  }
 }
 for(const [path] of Object.entries(baseline.decisions)){if(!same(keys.get(path),read('design/decisions/'+path)))fail('HISTORY_INPUT_MUTATED')}
 return rows;
}
export function preserve(){const base=process.env.PR_BASE_SHA;if(base){if(!/^[a-f0-9]{40}$/.test(base))fail('PR_BASE_INVALID');const paths=execFileSync('git',['ls-tree','-r','--name-only',base,'--','design/decisions'],{cwd:root,encoding:'utf8'}).trim().split('\n').filter(Boolean);for(const p of paths){let current;try{current=readFileSync(root+p)}catch{fail('PR_HISTORY_LOST '+p)}if(!current.equals(execFileSync('git',['show',`${base}:${p}`],{cwd:root})))fail('PR_HISTORY_CHANGED '+p)}}const b=read('design/baseline.json');for(const [path,sha] of Object.entries(b.files)){if(digest(readFileSync(root+path))!==sha)fail('BASELINE_CHANGED '+path);const original=execFileSync('git',['show',`${b.commit}:${path}`],{cwd:root});if(digest(original)!==sha)fail('BASELINE_FORGED '+path)}return Object.keys(b.files).length}
export function cadRead(rows=load()){return validate(rows).map(({data:d})=>({decision_id:d.id,revision:d.revision,hypothesis:d.hypothesis,eligibility:'reference_only',write_allowed:false,parameters:d.parameters}))}
export function search(rows,filters={}){return validate(rows).filter(({data:d})=>(!filters.site||d.site===filters.site)&&(!filters.part||d.part_id===filters.part)&&(!filters.hypothesis||d.hypothesis.id===filters.hypothesis)&&(!filters.status||d.status===filters.status))}
export function render(rows=load()){return '# 設計判断・CAD根拠台帳\n\nJSON正本から生成。採用判断は史実の確定ではない。正式CAD書込み不可。\n\n'+validate(rows).map(({data:d})=>`## ${d.id} revision ${d.revision}\n${d.site} / ${d.part_id} / ${d.status}\n${d.reason}\n仮説: ${d.hypothesis.id} revision ${d.hypothesis.revision} / SHA256 ${d.hypothesis.sha256}\n固定commit: ${d.hypothesis.commit}\n支持: ${d.support.join(', ')}\n反証: ${d.counterevidence.join(', ')||'登録なし（反証不存在の証明ではない）'}\n競合: ${d.competitors.join(', ')}\n旧判断: ${d.previous??'初版'}\n\n`+d.parameters.map(p=>`- ${p.name}: 史料=null / 仮説=null / 試作D=${p.prototype_value??'未設定'} ${p.unit} / ${p.evidence_id}`).join('\n')+'\n\n未確認:\n'+d.unknowns.map(x=>'- '+x).join('\n')).join('\n\n')+'\n'}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){try{const args=process.argv.slice(2);if(args[0]==='generate'&&args.length===1){writeFileSync(root+'design/index.md',render());writeFileSync(root+'design/cad-reference.json',JSON.stringify(cadRead(),null,2)+'\n')}else if(args[0]==='search'){const f={};for(let i=1;i<args.length;i+=2){if(!['--site','--part','--hypothesis','--status'].includes(args[i])||!args[i+1])fail('CLI_ARGUMENT');f[args[i].slice(2)]=args[i+1]}console.log(JSON.stringify(search(load(),f),null,2))}else if(!args.length){validate();preserve();if(readFileSync(root+'design/index.md','utf8')!==render()||readFileSync(root+'design/cad-reference.json','utf8')!==JSON.stringify(cadRead(),null,2)+'\n')fail('GENERATED_DRIFT');console.log('PASS')}else fail('CLI_ARGUMENT')}catch(e){console.error(e.message);process.exitCode=1}}
