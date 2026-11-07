import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {loadRecords as loadSources,validateRegister as validateSources} from './source-register.mjs';
import {validateSchema} from './observation-schema.mjs';
export const root=fileURLToPath(new URL('../',import.meta.url));
export const schema=JSON.parse(readFileSync(join(root,'observations/schema/observation.schema.json'),'utf8'));
export const hashLocation=loc=>createHash('sha256').update(JSON.stringify(loc)).digest('hex');
export const loadObservations=(dir=join(root,'observations/records'))=>readdirSync(dir).filter(x=>x.endsWith('.json')).sort().map(name=>({name,record:JSON.parse(readFileSync(join(dir,name),'utf8'))}));
const fail=(code,id)=>{throw Error(`${code} ${id}`)};
const norm=x=>x.normalize('NFKC').replace(/\s/g,'').toLowerCase();
export function validateObservations(entries,sources=loadSources()) {
 const src=new Map(validateSources(sources).map(s=>[s.id,s]));
 if(!entries.length) fail('EMPTY_REGISTER','');
 const ids=new Map(),fingerprints=new Map();
 for(const {name,record:r} of entries){
  validateSchema(r,schema);
  if(name!==`${r.id}.json`) fail('FILENAME',r.id);
  if(ids.has(r.id)) fail('DUPLICATE_ID',r.id);ids.set(r.id,r);
  const refs=new Map(),ints=new Map(r.source_interpretations.map(i=>[i.id,i]));
  for(const collection of [r.facts,r.source_interpretations,r.measurements,r.references]) if(new Set(collection.map(x=>x.id)).size!==collection.length) fail('DUPLICATE_LOCAL_ID',r.id);
  for(const ref of r.references){
   const s=src.get(ref.source_id),loc=s?.research.locations.find(x=>x.id===ref.location_id);
   if(!s||!loc) fail('SOURCE_LOCATION',r.id);
   if(!s.sites.includes(r.site)) fail('SITE_MISMATCH',r.id);
   if(ref.source_locator!==loc.locator || ref.source_location_sha256!==hashLocation(loc)) fail('LOCATOR_SNAPSHOT',r.id);
   if(ref.evidence_url!==loc.evidence_url) fail('EVIDENCE_URL',r.id);
   if(ref.source_file_sha256!==s.access.acquired_sha256) fail('FILE_HASH',r.id);
   if(ref.pdf_pages.some(p=>s.access.pdf_pages===null||p>s.access.pdf_pages)) fail('PDF_PAGE',r.id);
   // Page metadata must agree with the pinned first-layer locator; not a free-form alternative citation.
   const pdf=loc.locator.match(/PDF\s*(\d+)頁/),print=loc.locator.match(/印刷p(\d+)/);
   if(JSON.stringify(ref.pdf_pages)!==JSON.stringify(pdf?[+pdf[1]]:[])) fail('PDF_LOCATOR',r.id);
   if(JSON.stringify(ref.printed_pages)!==JSON.stringify(print?[print[1]]:[])) fail('PRINT_LOCATOR',r.id);
   const fig=loc.locator.match(/第(\d+)図/),table=loc.locator.match(/表([\d-]+)/);
   if(JSON.stringify(ref.figures)!==JSON.stringify(fig?[fig[1]]:[])) fail('FIGURE_LOCATOR',r.id);
   if(JSON.stringify(ref.tables)!==JSON.stringify(table?[table[1]]:[])) fail('TABLE_LOCATOR',r.id);
   if(ref.text_status==='checked'&&!loc.text_checked) fail('UNCHECKED_SOURCE_TEXT',r.id);
   if(ref.figure_status==='checked'&&!loc.figure_checked) fail('UNCHECKED_SOURCE_FIGURE',r.id);
   if(ref.method==='source_register_only'&&(ref.text_status==='checked'||ref.figure_status==='checked')) fail('INDIRECT_CHECK',r.id);
   if(ref.figure_status==='checked'&&(ref.method!=='pdf_text_and_page_image'||!ref.figures.length)) fail('FIGURE_METHOD',r.id);
   if(ref.method.startsWith('pdf_')&&(!ref.pdf_pages.length||!ref.source_file_sha256)) fail('PDF_METHOD',r.id);
   if(ref.method==='webpage_text'&&s.verification.acquisition!=='webpage_read') fail('WEB_METHOD',r.id);
   refs.set(ref.id,ref);
  }
  const checkRefs=(item,checked=true)=>{for(const id of item.reference_ids){const ref=refs.get(id);if(!ref)fail('LOCAL_REFERENCE',r.id);if(checked&&ref.text_status!=='checked')fail('UNCHECKED_FACT',r.id)}};
  const checked=r.verification.status==='partial_checked';
  if(checked!==r.references.some(x=>x.text_status==='checked')) fail('STATUS_CONTRADICTION',r.id);
  for(const f of r.facts){checkRefs(f,checked);if(!checked&&f.kind==='quote')fail('UNCHECKED_QUOTE',r.id)}
  for(const i of r.source_interpretations)checkRefs(i);
  for(const v of [r.position.reported_location,r.position.findspot,r.condition])if(v)checkRefs(v,checked);
  for(const v of r.original_ids){
   checkRefs(v);
   const supported=v.reference_ids.some(id=>{
    const ref=refs.get(id),text=src.get(ref.source_id).research.locations.find(x=>x.id===ref.location_id).text;
    const escaped=v.value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    if(new RegExp(`(^|[^A-Za-z0-9])${escaped}($|[^A-Za-z0-9])`).test(text))return true;
    const m=v.value.match(/^([A-Z]+)([0-9]+)$/);
    return m&&[...text.matchAll(/([A-Z]+)([0-9]+)[〜～–-]\1?([0-9]+)/g)].some(x=>x[1]===m[1]&&+m[2]>=+x[2]&&+m[2]<=+x[3]);
   });
   if(!supported)fail('UNSUPPORTED_ORIGINAL_ID',r.id);
  }
  if(r.scope==='individual'&&!r.original_ids.length)fail('UNIDENTIFIED_INDIVIDUAL',r.id);
  if(r.scope==='individual'&&r.original_ids.length!==1)fail('MULTIPLE_INDIVIDUAL_IDS',r.id);
  if(r.position.original_installation&&!ints.has(r.position.original_installation.interpretation_id)) fail('INSTALLATION_INTERPRETATION',r.id);
  for(const m of r.measurements){
   checkRefs(m);
   for(const k of ['value','lower','upper'])if(m[k]!==null&&m[k]<=0)fail('NONPOSITIVE_MEASUREMENT',r.id);
   if(m.basis==='reported'){
    const numeric=text=>[...text.matchAll(/[0-9]+(?:\.[0-9]+)?/g)].map(x=>+x[0]);
    const quoteNumbers=numeric(m.original_text);
    const sourceNumbers=m.reference_ids.flatMap(id=>{const ref=refs.get(id);return numeric(src.get(ref.source_id).research.locations.find(x=>x.id===ref.location_id).text)});
    for(const k of ['original_value','original_lower','original_upper'])if(m[k]!==null&&(!quoteNumbers.includes(m[k])||!sourceNumbers.includes(m[k])))fail('UNSUPPORTED_REPORTED_VALUE',r.id);
   }
   const range=m.statistic==='range';
   if(range?(m.value!==null||m.lower===null||m.upper===null||m.lower>m.upper):(m.value===null||m.lower!==null||m.upper!==null))fail('MEASUREMENT_SHAPE',r.id);
   if(range?(m.original_value!==null||m.original_lower===null||m.original_upper===null||m.original_lower>m.original_upper):(m.original_value===null||m.original_lower!==null||m.original_upper!==null))fail('ORIGINAL_MEASUREMENT_SHAPE',r.id);
   if((m.unit==='count')!==(m.original_unit==='count'))fail('UNIT_DIMENSION',r.id);
   const factors={mm:0.001,cm:0.01,m:1,count:1};
   for(const key of ['value','lower','upper']){
    const x=m[key],y=m[`original_${key}`];
    if(x!==null&&Math.abs(x*factors[m.unit]-y*factors[m.original_unit])>1e-10)fail('UNIT_CONVERSION',r.id);
    if(m.unit==='count'&&x!==null&&!Number.isSafeInteger(x))fail('QUANTITY_INTEGER',r.id);
   }
   if(m.basis==='measured'&&!m.method)fail('MEASUREMENT_METHOD',r.id);
   if(m.basis==='source_estimate'&&!ints.has(m.interpretation_id))fail('ESTIMATE_INTERPRETATION',r.id);
   if(m.basis!=='source_estimate'&&m.interpretation_id!==null)fail('UNEXPECTED_INTERPRETATION',r.id);
   if(r.scope==='individual'&&m.unit==='count'&&m.value!==1)fail('INDIVIDUAL_COUNT',r.id);
  }
  const fp=[norm(r.site),r.kind,r.scope,norm(r.name)].join('|');
  if(fingerprints.has(fp))fail('DUPLICATE_TARGET',r.id);fingerprints.set(fp,r.id);
 }
 for(const r of ids.values())for(const rel of r.relations){
  const target=ids.get(rel.target_id);if(!target||target.id===r.id)fail('RELATION_TARGET',r.id);
  if(rel.type!=='comparison'&&r.site!==target.site)fail('CROSS_SITE_IDENTITY',r.id);
  if(rel.type==='member_of'&&(r.scope!=='individual'||target.scope!=='collection'||r.kind!==target.kind))fail('MEMBERSHIP_SCOPE',r.id);
  if(rel.type==='member_of'){
   const a=r.original_ids[0];
   if(!a||!target.original_ids.some(x=>x.value===a.value))fail('MEMBER_IDENTIFIER',r.id);
  }
 }
 // Same source object identifier or same passage/type can denote a duplicate: require explicit candidate relation, never auto-merge/count.
 const records=[...ids.values()];
 for(let i=0;i<records.length;i++)for(let j=i+1;j<records.length;j++){
  const a=records[i],b=records[j];if(a.site!==b.site||a.kind!==b.kind)continue;
  const shared=a.references.some(x=>b.references.some(y=>x.source_id===y.source_id&&x.location_id===y.location_id));
  const identity=a.original_ids.some(x=>b.original_ids.some(y=>x.value===y.value&&x.reference_ids.some(rx=>y.reference_ids.some(ry=>a.references.find(z=>z.id===rx).source_id===b.references.find(z=>z.id===ry).source_id))));
  if((shared||identity)&&!a.relations.some(x=>x.target_id===b.id&&x.type!=='comparison')&&!b.relations.some(x=>x.target_id===a.id&&x.type!=='comparison'))fail('UNRESOLVED_DUPLICATE_CANDIDATE',`${a.id}/${b.id}`);
 }
 return records;
}
const esc=x=>String(x??'不明').replaceAll('|','\\|').replaceAll('\n',' ').replaceAll('<','&lt;').replaceAll('>','&gt;');
export function renderIndex(records){
 const lines=['# 遺構・遺物観察台帳（第2層）','',`登録 ${records.length} レコード。レコード数は遺構・遺物の総個体数ではない。報告記載の確認は歴史的真実・復元寸法の確証ではない。`,'','[手順・抽出CLI](README.md) / [設計と確認範囲](../docs/observation-register-stage2.md)','','| ID | 対象 | 城郭 | 種類 | 個別/集合 | 役割 | 確認 | 出典箇所 | 未確認数 |','| --- | --- | --- | --- | --- | --- | --- | --- | --- |'];
 for(const r of records)lines.push(`| [${r.id}](records/${r.id}.json) | ${esc(r.name)} | ${esc(r.site)} | ${r.classification}/${r.kind} | ${r.scope} | ${r.role} | ${r.verification.status} | ${r.references.map(x=>`[${x.source_id}/${x.location_id}](../sources/records/${x.source_id}.json) 本文:${x.text_status} 図:${x.figure_status}`).join('、')} | ${r.unknowns.length} |`);
 for(const r of records){lines.push('',`## ${r.id} ${esc(r.name)}`,'','### 報告・観察事項',...r.facts.map(x=>`- ${esc(x.text)} (${x.reference_ids.join(', ')})`),'','### 原報告・著者の解釈',...(r.source_interpretations.length?r.source_interpretations.map(x=>`- ${esc(x.attributed_to)}: ${esc(x.text)} (${x.reference_ids.join(', ')})`):['- 登録なし。']),'','### 記載数値',...(r.measurements.length?r.measurements.map(x=>`- ${esc(x.name)} / ${esc(x.target)}: ${x.statistic==='range'?`${x.lower}〜${x.upper}`:x.value} ${x.unit} (${x.basis}, ${x.statistic})。原記載: ${esc(x.original_text)}。範囲: ${esc(x.reported_scope)}`):['- 未確認。値を補わない。']),'','### 未確認',...r.unknowns.map(x=>`- ${esc(x)}`));}
 return lines.join('\n')+'\n';
}
export function filterRecords(records,args){
 const keys={site:r=>r.site,kind:r=>r.kind,scope:r=>r.scope,source:r=>r.references.map(x=>x.source_id),status:r=>r.verification.status,unknowns:r=>String(r.unknowns.length>0)};
 let out=records;
 for(const arg of args){if(arg==='--write')continue;const m=arg.match(/^--([^=]+)=(.+)$/);if(!m||!keys[m[1]])fail('CLI_OPTION',arg);if(m[1]==='unknowns'&&!['true','false'].includes(m[2]))fail('CLI_VALUE',arg);out=out.filter(r=>[].concat(keys[m[1]](r)).includes(m[2]));}
 return out;
}
export function run(args=process.argv.slice(2)){
 const records=validateObservations(loadObservations());const selected=filterRecords(records,args);const content=renderIndex(records),target=join(root,'observations/index.md');
 if(args.includes('--write'))writeFileSync(target,content);else if(readFileSync(target,'utf8')!==content)fail('STALE_INDEX','');
 console.log(JSON.stringify(args.some(x=>x.startsWith('--')&&x!=='--write')?selected:{status:'PASS',records:records.length,ids:records.map(x=>x.id)},null,2));
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))run();
