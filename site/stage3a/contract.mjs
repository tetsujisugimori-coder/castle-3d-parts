// Gate poses are NOT fence revisions. Reuse the reviewed SVG, hash and mesh guards.
export {verifyHash,sanitizeDrawing,VIEWS} from '../stage2c/contract.mjs';
import{validateMeshes as legacyMeshes}from'../stage2c/contract.mjs';
export function validateMeshes(m,meshes){return legacyMeshes({...m,revision:m.assembly_id+'/'+m.revision},meshes)}
const check=(v,s)=>{if(!v)throw Error(s)};
const id=v=>typeof v==='string'&&/^[A-Za-z][A-Za-z0-9_.:-]*$/.test(v);
const unique=a=>new Set(a).size===a.length;
export function validateManifest(m,pose){
 check(m?.schema_version===1&&m.revision===pose&&['B0','B1','B2'].includes(pose),'gate pose/schema mismatch');
 check(m.basis==='D'&&m.cad_eligibility==='reference_only'&&/^gate/i.test(m.assembly_id),'gate classification/namespace');
 check(/^[a-f0-9]{40}$/.test(m.source_commit),'source commit');
 check(m.previous_revision===null&&Array.isArray(m.changes)&&m.changes.length===0,'poses are not revisions');
 for(const [k,f]of[['glb','assembly.glb'],['svg','drawing.svg']])check(m.files?.[k]?.path===f&&/^[a-f0-9]{64}$/.test(m.files[k].sha256),'file hash/path');
 check(Array.isArray(m.parts)&&m.parts.length===7&&unique(m.parts.map(p=>p.id))&&unique(m.parts.map(p=>p.glb_node)),'part count/identity');
 check(Array.isArray(m.dimensions)&&m.dimensions.length>0&&unique(m.dimensions.map(d=>d.id)),'dimensions');
 check(JSON.stringify([...m.parts.map(p=>p.id)].sort())===JSON.stringify(['GATE_Post_Left','GATE_Post_Right','GATE_Beam','GATE_Door','GATE_Axis','GATE_Connector_Left','GATE_Connector_Right'].sort()),'gate part set');
 const ids=new Set(m.parts.map(p=>p.id)),dims=new Map(m.dimensions.map(d=>[d.id,d])),svg=[];
 for(const d of m.dimensions)check(id(d.id)&&typeof d.label==='string'&&Number.isFinite(d.value_m)&&d.value_m>0&&d.kind==='true'&&Array.isArray(d.part_ids)&&d.part_ids.length>0&&unique(d.part_ids)&&d.part_ids.every(x=>ids.has(x)),'dimension value/reference');
 for(const p of m.parts){
 check(id(p.id)&&id(p.unit_id)&&id(p.glb_node)&&typeof p.freecad_object==='string'&&typeof p.label==='string','part schema');
 check(Array.isArray(p.bounds_m)&&p.bounds_m.length===6&&p.bounds_m.every(Number.isFinite)&&p.bounds_m.slice(0,3).every((v,i)=>v<p.bounds_m[i+3]),'part bounds');
 check(Array.isArray(p.dimension_ids)&&p.dimension_ids.length>0&&unique(p.dimension_ids)&&p.dimension_ids.every(x=>dims.has(x)&&dims.get(x).part_ids.includes(p.id))&&m.dimensions.filter(d=>d.part_ids.includes(p.id)).every(d=>p.dimension_ids.includes(d.id)),'dimension mapping');
 for(const v of['front','side','top']){check(id(p.svg_ids?.[v]),'SVG mapping');svg.push(p.svg_ids[v])}
 check(Array.isArray(p.research_refs)&&p.research_refs.length>0,'research references');
 for(const r of p.research_refs)check(id(r.id)&&(r.path==='cad/stage3a/spec.json'||/^(research|sources|observations|design)\/[A-Za-z0-9_./-]+\.(json|md)$/.test(r.path))&&!r.path.includes('..'),'research path');
 }
 check(unique(svg),'duplicate SVG identity');return m;
}
export function validateRevisionPair(){throw Error('Gate poses have no revision ancestry')}
