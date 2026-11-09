export const REVISIONS=['B0','B1','B2'];
export const VIEWS=['front','side','top'];
const ID=/^[A-Za-z][A-Za-z0-9_.:-]*$/;
const isID=value=>typeof value==='string'&&ID.test(value);
const HASH=/^[a-f0-9]{64}$/;
const assert=(yes,message)=>{if(!yes)throw Error(message)};
const unique=(xs,label)=>assert(new Set(xs).size===xs.length,`${label}: duplicate`);
export function validateManifest(m,revision){
 assert(m?.schema_version===1&&m.revision===revision&&REVISIONS.includes(revision),'revision/schema mismatch');
 assert(m.basis==='D'&&m.cad_eligibility==='reference_only','research classification mismatch');
 assert(typeof m.assembly_id==='string'&&isID(m.assembly_id),'assembly ID missing');
 for(const [key,name]of[['glb','assembly.glb'],['svg','drawing.svg']])assert(m.files?.[key]?.path===name&&HASH.test(m.files[key].sha256),'file contract invalid: '+key);
 assert(Array.isArray(m.parts)&&m.parts.length===14,'14 component instances required');unique(m.parts.map(p=>p.id),'part ID');unique(m.parts.map(p=>p.glb_node),'node ID');
 const ids=new Set(m.parts.map(p=>p.id)),svg=[];
 assert(Array.isArray(m.dimensions)&&m.dimensions.length>0,'dimensions missing');unique(m.dimensions.map(d=>d.id),'dimension ID');
 const dimensions=new Map(m.dimensions.map(d=>[d.id,d]));
 for(const d of m.dimensions){assert(isID(d.id)&&typeof d.label==='string'&&Number.isFinite(d.value_m)&&d.value_m>0&&['true','projected'].includes(d.kind),'invalid dimension');assert(Array.isArray(d.part_ids)&&d.part_ids.every(id=>ids.has(id)),'dimension part reference missing')}
 for(const p of m.parts){assert(isID(p.id)&&isID(p.unit_id)&&isID(p.glb_node)&&typeof p.label==='string'&&typeof p.freecad_object==='string','invalid part');assert(Array.isArray(p.bounds_m)&&p.bounds_m.length===6&&p.bounds_m.every(Number.isFinite)&&p.bounds_m.slice(0,3).every((v,i)=>v<p.bounds_m[i+3]),'invalid part bounds');assert(Array.isArray(p.dimension_ids)&&p.dimension_ids.length>0&&p.dimension_ids.every(id=>dimensions.has(id)),'dimension reference missing');for(const view of VIEWS){assert(isID(p.svg_ids?.[view]),'SVG ID missing');svg.push(p.svg_ids[view])}assert(Array.isArray(p.research_refs),'research references missing');for(const r of p.research_refs)assert(isID(r.id)&&typeof r.path==='string'&&/^(research|sources|observations|design)\/[A-Za-z0-9_./-]+\.(json|md)$/.test(r.path)&&!r.path.includes('..'),'unsafe research path')}
 unique(svg,'SVG ID');assert(typeof m.source_commit==='string'&&/^[a-f0-9]{40}$/.test(m.source_commit),'source commit missing');assert(m.previous_revision===(revision==='B0'?null:revision==='B1'?'B0':'B1'),'parent revision mismatch');assert(Array.isArray(m.changes),'changes missing');for(const c of m.changes)assert(dimensions.has(c.dimension_id)&&Number.isFinite(c.before_m)&&Number.isFinite(c.after_m)&&c.after_m===dimensions.get(c.dimension_id).value_m,'invalid change');return m;
}
export async function verifyHash(bytes,expected){const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');assert(actual===expected,'asset SHA256 mismatch');return actual}
// Parse detached XML, reject active content, then import only an explicit SVG subset.
export function sanitizeDrawing(text,manifest,doc=document){
 assert(!/<!DOCTYPE|<!ENTITY/i.test(text),'DTD/entity forbidden');
 const xml=new DOMParser().parseFromString(text,'image/svg+xml');assert(!xml.querySelector('parsererror'),'malformed SVG');const root=xml.documentElement;assert(root.localName==='svg'&&root.namespaceURI==='http://www.w3.org/2000/svg'&&root.getAttribute('data-revision')===manifest.revision,'SVG revision mismatch');
 const tags=new Set(['svg','g','path','line','polyline','polygon','rect','circle','ellipse','text','tspan','title','desc','defs','marker']);
 const attrs=new Set(['id','x','y','x1','y1','x2','y2','cx','cy','r','rx','ry','width','height','viewBox','preserveAspectRatio','d','points','transform','fill','fill-rule','stroke','stroke-width','stroke-linecap','stroke-linejoin','stroke-dasharray','opacity','fill-opacity','stroke-opacity','font-size','font-family','font-weight','text-anchor','dominant-baseline','dx','dy','markerWidth','markerHeight','refX','refY','orient','markerUnits','data-revision','data-view','data-part-id','data-dimension-id','data-value-m','data-kind','data-unit','version','xmlns','xmlns:xlink']);
 const styles=new Set(['fill','fill-rule','fill-opacity','stroke','stroke-width','stroke-linecap','stroke-linejoin','stroke-dasharray','stroke-opacity','opacity','font-size','font-family','font-weight','text-anchor','dominant-baseline']);
 const ids=new Set();
 for(const e of [root,...root.querySelectorAll('*')]){assert(tags.has(e.localName)&&e.namespaceURI===root.namespaceURI,'SVG element forbidden: '+e.localName);for(const a of [...e.attributes]){assert(!/^on/i.test(a.name)&&!/(?:url\s*\(|javascript:|data:|https?:|\/\/|expression\s*\()/i.test(a.value)||['xmlns','xmlns:xlink'].includes(a.name),'SVG external/active attribute');if(a.name==='style'){assert(!/[\\@]/.test(a.value),'SVG escaped style forbidden');for(const rule of a.value.split(';').filter(x=>x.trim())){const split=rule.indexOf(':');assert(split>0&&styles.has(rule.slice(0,split).trim()),'SVG style forbidden')}}else assert(attrs.has(a.name),'SVG attribute forbidden: '+a.name)}if(e.id){assert(!ids.has(e.id),'SVG duplicate ID');ids.add(e.id)}}
 for(const view of VIEWS){assert(root.querySelectorAll(`[data-view="${view}"]`).length===1,'SVG view missing/duplicate');for(const p of manifest.parts){const matches=[...root.querySelectorAll('[id]')].filter(e=>e.id===p.svg_ids[view]);assert(matches.length===1&&matches[0].getAttribute('data-part-id')===p.id&&matches[0].closest('[data-view]')?.getAttribute('data-view')===view,'SVG part mapping mismatch')}}
 assert(root.querySelectorAll('[data-part-id]').length===manifest.parts.length*3,'SVG unexpected part mapping count');
 for(const d of manifest.dimensions){const elements=[...root.querySelectorAll('[data-dimension-id]')].filter(e=>e.getAttribute('data-dimension-id')===d.id);assert(elements.length===1&&elements[0].hasAttribute('data-value-m')&&Number(elements[0].getAttribute('data-value-m'))===d.value_m&&elements[0].getAttribute('data-kind')===d.kind,'SVG dimension mismatch')}
 assert(root.querySelectorAll('[data-dimension-id]').length===manifest.dimensions.length,'SVG unknown dimensions');
 for(const e of root.querySelectorAll('[data-part-id]'))assert(manifest.parts.some(p=>p.id===e.getAttribute('data-part-id')),'SVG unknown part');
 return doc.importNode(root,true);
}
export function validateMeshes(manifest,meshes){
 assert(meshes.length===manifest.parts.length,'GLB count mismatch');unique(meshes.map(m=>m.name),'GLB node');for(const p of manifest.parts){const o=meshes.find(o=>o.name===p.glb_node);assert(o&&o.revision===manifest.revision&&o.basis==='D'&&o.eligibility==='reference_only','GLB identity mismatch');assert(o.bounds_m.length===6&&o.bounds_m.every((v,i)=>Number.isFinite(v)&&Math.abs(v-p.bounds_m[i])<1e-4),'GLB geometry mismatch')}
 return true;
}
