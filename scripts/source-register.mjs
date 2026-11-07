import {readFileSync, readdirSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve, join} from 'node:path';
export const root = fileURLToPath(new URL('../', import.meta.url));
export const schema = JSON.parse(readFileSync(join(root, 'sources/schema/source.schema.json'), 'utf8'));
const keywords = new Set(['$schema','$id','title','type','const','enum','properties','required','additionalProperties','items','minItems','uniqueItems','minLength','pattern','minimum','maximum','format']);
const plain = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const canonical = x => Array.isArray(x) ? '['+x.map(canonical).join(',')+']' : plain(x) ? '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}' : JSON.stringify(x);
export function validateSupportedSchema(spec) {
  if (!plain(spec)) throw Error('SCHEMA_OBJECT');
  for (const key of Object.keys(spec)) if (!keywords.has(key)) throw Error(`SCHEMA_UNSUPPORTED ${key}`);
  if ('$schema' in spec && spec.$schema !== 'https://json-schema.org/draft/2020-12/schema') throw Error('SCHEMA_DIALECT');
  for (const key of ['$id','title','pattern']) if (key in spec && typeof spec[key]!=='string') throw Error(`SCHEMA_VALUE ${key}`);
  if (spec.pattern) new RegExp(spec.pattern);
  if ('type' in spec && (![].concat(spec.type).length || ![].concat(spec.type).every(x=>['null','array','object','integer','string','boolean'].includes(x)))) throw Error('SCHEMA_TYPE');
  if ('format' in spec && !['uri','date'].includes(spec.format)) throw Error('SCHEMA_FORMAT');
  for (const key of ['additionalProperties','uniqueItems']) if (key in spec && typeof spec[key]!=='boolean') throw Error(`SCHEMA_VALUE ${key}`);
  for (const key of ['minItems','minLength']) if (key in spec && (!Number.isSafeInteger(spec[key]) || spec[key]<0)) throw Error(`SCHEMA_VALUE ${key}`);
  for (const key of ['minimum','maximum']) if (key in spec && !Number.isFinite(spec[key])) throw Error(`SCHEMA_VALUE ${key}`);
  if ('required' in spec && (!Array.isArray(spec.required) || !spec.required.every(x=>typeof x==='string'))) throw Error('SCHEMA_VALUE required');
  if ('enum' in spec && (!Array.isArray(spec.enum) || !spec.enum.length || !spec.enum.every(x=>x===null || ['string','number','boolean'].includes(typeof x)))) throw Error('SCHEMA_VALUE enum');
  if ('const' in spec && spec.const!==null && !['string','number','boolean'].includes(typeof spec.const)) throw Error('SCHEMA_VALUE const');
  if ('properties' in spec && !plain(spec.properties)) throw Error('SCHEMA_VALUE properties');
  for (const child of Object.values(spec.properties ?? {})) validateSupportedSchema(child);
  if ('items' in spec) validateSupportedSchema(spec.items);
}
export function validateSchema(value, spec = schema, path = '$', nested = false) {
  if (!nested) validateSupportedSchema(spec);
  const fail = code => {throw Error(`${code} ${path}`)};
  if ('const' in spec && value !== spec.const) fail('CONST');
  if (spec.type) {
    const types = [].concat(spec.type);
    const matches = t => t === 'null' ? value === null : t === 'array' ? Array.isArray(value) : t === 'object' ? value !== null && !Array.isArray(value) && typeof value === 'object' : t === 'integer' ? Number.isSafeInteger(value) : typeof value === t;
    if (!types.some(matches)) fail('TYPE');
  }
  if (spec.enum && !spec.enum.includes(value)) fail('ENUM');
  if (typeof value === 'string') {
    if (spec.minLength && value.trim().length < spec.minLength) fail('EMPTY');
    if (spec.pattern && !new RegExp(spec.pattern).test(value)) fail('PATTERN');
    if (spec.format === 'uri') { try { const u = new URL(value); if (!['http:','https:'].includes(u.protocol) || u.username || u.password || /\s/.test(value)) fail('URL'); } catch {fail('URL')} }
    if (spec.format === 'date' && (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0,10) !== value)) fail('DATE');
    if (spec.format && !['uri','date'].includes(spec.format)) fail('SCHEMA_FORMAT');
  }
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) fail('NUMBER');
    if (spec.minimum !== undefined && value < spec.minimum) fail('MINIMUM');
    if (spec.maximum !== undefined && value > spec.maximum) fail('MAXIMUM');
  }
  if (Array.isArray(value)) {
    if (spec.minItems && value.length < spec.minItems) fail('MIN_ITEMS');
    if (spec.uniqueItems && new Set(value.map(canonical)).size !== value.length) fail('DUPLICATE_ITEM');
    value.forEach((x,i) => validateSchema(x,spec.items,`${path}[${i}]`,true));
  } else if (value !== null && typeof value === 'object') {
    for (const k of spec.required ?? []) if (!Object.hasOwn(value,k)) fail(`MISSING:${k}`);
    for (const k of Object.keys(value)) {
      if (!Object.hasOwn(spec.properties ?? {}, k)) {if (spec.additionalProperties === false) fail(`EXTRA:${k}`)}
      else validateSchema(value[k],spec.properties[k],`${path}.${k}`,true);
    }
  }
}
export function loadRecords(dir = join(root,'sources/records')) {
  return readdirSync(dir).filter(x=>x.endsWith('.json')).sort().map(name=>({name,record:JSON.parse(readFileSync(join(dir,name),'utf8'))}));
}
export function validateRegister(entries) {
  if (!entries.length) throw Error('EMPTY_REGISTER');
  const ids=new Set(), fingerprints=new Set(), identifiers=new Map();
  const norm=x=>String(x??'').normalize('NFKC').toLowerCase().replace(/[\s:：・―－-]/g,'');
  for (const {name,record:r} of entries) {
    validateSchema(r);
    if (name !== `${r.id}.json`) throw Error(`FILENAME ${name}`);
    if (ids.has(r.id)) throw Error(`DUPLICATE_ID ${r.id}`); ids.add(r.id);
    const fp=[r.title,r.bibliography.publisher,r.bibliography.publication_year,r.bibliography.volume,r.bibliography.edition].map(norm).join('|');
    if (fingerprints.has(fp)) throw Error(`DUPLICATE_BIBLIOGRAPHY ${r.id}`); fingerprints.add(fp);
    // A set-level catalogue ID can legitimately describe separate volumes. Volume/edition scope it.
    for (const x of r.bibliography.identifiers) {
      const key=(x.scheme==='NCID-set' ? [x.scheme,x.value,r.bibliography.volume,r.bibliography.edition] : [x.scheme,x.value]).map(norm).join('|');
      if (identifiers.has(key)) throw Error(`DUPLICATE_IDENTIFIER ${r.id}`); identifiers.set(key,r.id);
    }
    const successful = r.access.checks.filter(x=>x.outcome!=='failed');
    if (r.verification.acquisition==='webpage_read' && !successful.some(x=>x.outcome==='read' && x.url===r.access.official_url)) throw Error(`WEB_ACCESS_EVIDENCE ${r.id}`);
    if (r.verification.bibliography !== 'unverified' && !successful.some(x=>r.bibliography.evidence_urls.includes(x.url))) throw Error(`BIBLIOGRAPHY_EVIDENCE ${r.id}`);
    if (r.verification.acquisition==='catalog_only' && !successful.some(x=>x.outcome==='catalog_read')) throw Error(`CATALOG_EVIDENCE ${r.id}`);
    if (r.bibliography.publication_date) {
      const d=r.bibliography.publication_date;
      if (r.bibliography.publication_year!==null && Number(d.slice(0,4))!==r.bibliography.publication_year) throw Error(`PUBLICATION_DATE ${r.id}`);
      if (d.length===10 && (!Number.isFinite(Date.parse(d)) || new Date(d).toISOString().slice(0,10)!==d)) throw Error(`PUBLICATION_DATE ${r.id}`);
    }
    for (const x of r.bibliography.identifiers) {
      const pattern={DOI:/^10\.[0-9]{4,9}\/\S+$/, NDL:/^[0-9]{9}$/, JPNO:/^[0-9]{8}$/, NCID:/^[A-Z]{2}[0-9]{8}$/, 'NCID-set':/^[A-Z]{2}[0-9]{8}$/}[x.scheme];
      if (pattern && !pattern.test(x.value)) throw Error(`IDENTIFIER_FORMAT ${r.id}`);
    }
    const locs=r.research.locations;
    if (new Set(locs.map(x=>x.id)).size!==locs.length) throw Error(`DUPLICATE_LOCATOR ${r.id}`);
    if (r.verification.acquisition === 'full_file_acquired' && (!r.access.acquired_sha256 || !r.access.pdf_pages || !r.access.checks.some(x=>x.outcome==='downloaded' && x.url===r.access.pdf_url))) throw Error(`ACQUISITION_EVIDENCE ${r.id}`);
    for(const loc of locs) if ((loc.text_checked || loc.figure_checked) && !successful.some(x=>['read','downloaded'].includes(x.outcome) && x.url===loc.evidence_url)) throw Error(`PASSAGE_ACCESS_EVIDENCE ${r.id}`);
    if (r.verification.acquisition !== 'full_file_acquired' && (r.access.acquired_sha256!==null || r.access.pdf_pages!==null)) throw Error(`ACQUISITION_CONTRADICTION ${r.id}`);
    if (['catalog_only','unavailable'].includes(r.verification.acquisition) && (r.verification.text!=='not_checked'|| !['not_checked','not_applicable'].includes(r.verification.figures))) throw Error(`VERIFICATION_CONTRADICTION ${r.id}`);
    if (r.verification.text !== 'not_checked' && !locs.some(x=>x.text_checked)) throw Error(`TEXT_EVIDENCE ${r.id}`);
    if (r.verification.figures==='partial_checked' && !locs.some(x=>x.figure_checked)) throw Error(`FIGURE_EVIDENCE ${r.id}`);
    if (r.verification.text==='not_checked' && locs.some(x=>x.text_checked)) throw Error(`TEXT_CONTRADICTION ${r.id}`);
    if (['not_checked','not_applicable'].includes(r.verification.figures) && locs.some(x=>x.figure_checked)) throw Error(`FIGURE_CONTRADICTION ${r.id}`);
    for (const x of locs) if ((x.kind==='quote'||x.kind==='summary') && !x.text_checked) throw Error(`UNCHECKED_PASSAGE ${r.id}`);
  }
  for (const {record:r} of entries) for (const id of r.research.related_source_ids) if (!ids.has(id)||id===r.id) throw Error(`RELATED_ID ${r.id}:${id}`);
  return entries.map(x=>x.record);
}
const esc = v=>String(v??'不明').replaceAll('|','\\|').replaceAll('\n',' ');
export function renderIndex(records) {
  const out=['# 城郭研究史料台帳','',`登録 ${records.length} 件。書誌・入手・本文・図版の判定は独立。本文の部分確認は全文照合ではない。`, '', '[登録規約](README.md) / [検証・残件](../docs/source-register-stage1.md)','', '| ID | 名称 | 城郭・遺跡 | 種別 | 年 | 巻・版 | PDF | 書誌 | 入手 | 本文 | 図版 |','| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |'];
  for(const r of records) out.push(`| [${r.id}](records/${r.id}.json) | ${esc(r.title)} | ${r.sites.map(esc).join('、')} | ${r.source_type} | ${esc(r.bibliography.publication_year)} | ${esc([r.bibliography.volume,r.bibliography.edition].filter(Boolean).join(' / ')||null)} | ${r.access.pdf_url?'[公開リンク]('+r.access.pdf_url+')':'未確認'} | ${r.verification.bibliography} | ${r.verification.acquisition} | ${r.verification.text} | ${r.verification.figures} |`);
  out.push('','## 城郭・遺跡別','');
  for(const site of [...new Set(records.flatMap(r=>r.sites))].sort()) out.push(`- ${esc(site)}: ${records.filter(r=>r.sites.includes(site)).map(r=>`[${r.id}](records/${r.id}.json)`).join('、')}`);
  out.push('','## 原資料未入手','');
  for(const r of records.filter(r=>['catalog_only','unavailable'].includes(r.verification.acquisition))) out.push(`- [${r.id} ${esc(r.title)}](records/${r.id}.json): ${esc(r.access.other_methods.join(' / '))}`);
  out.push('','## 本文・図版の残る確認','');
  for(const r of records) out.push(`- ${r.id}: ${r.research.unknowns.map(esc).join(' / ')}`);
  return out.join('\n')+'\n';
}
export function run(args = process.argv.slice(2)) {
  const records=validateRegister(loadRecords()); const content=renderIndex(records); const target=join(root,'sources/index.md');
  if(args.includes('--write')) writeFileSync(target,content);
  else if(readFileSync(target,'utf8')!==content) throw Error('STALE_INDEX');
  const siteArg=args.find(x=>x.startsWith('--site='));
  if(siteArg) console.log(JSON.stringify(records.filter(r=>r.sites.includes(siteArg.slice(7))),null,2));
  else console.log(JSON.stringify({status:'PASS',records:records.length,ids:records.map(x=>x.id),mode:args.includes('--write')?'generate':'check'}));
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) run();
