// Stage 4-A: fixed GLB reference geometry; never a CAD safety certificate.
import {loadAssembly,worldPort,rotate} from './contract.mjs';
import {canonicalJson,parseUniqueJson} from './json-data.mjs';
import {displayPlacement} from './workshop.mjs';

const check=(ok,message)=>{if(!ok)throw Error(message)};
const equalNames=(a,b)=>a.length===b.length && new Set(a).size===a.length &&
  new Set(b).size===b.length && a.every(n=>b.includes(n));
const close=(a,b,tol)=>a.length===b.length && a.every((v,i)=>Number.isFinite(v)&&
  Number.isFinite(b[i])&&Math.abs(v-b[i])<=tol);
export const DISPLAY_BOUNDS_TOLERANCE_M=1e-4;
export const toDisplay=([x,y,z])=>[x,z,y===0?0:-y];
export function displayBounds(b) {
  return [b[0],b[2],-b[4],b[3],b[5],-b[1]];
}
export function placedBounds(b,i) {
  const corners=[];
  for(const x of [b[0],b[3]])for(const y of [b[1],b[4]])for(const z of [b[2],b[5]]){
    corners.push(toDisplay(rotate([x,y,z],i.yaw_quarters).map((v,k)=>v+i.translation_m[k])));
  }
  return [...[0,1,2].map(k=>Math.min(...corners.map(v=>v[k]))),
    ...[0,1,2].map(k=>Math.max(...corners.map(v=>v[k])))];
}
export function checkAssetManifest(d,m) {
  check(m?.schema_version===1 && m.assembly_id===d.upstream_id &&
    m.revision===(d.pose??d.revision) && m.basis==='D' &&
    m.cad_eligibility==='reference_only','manifest identity mismatch');
  check(d.pose===null || m.pose_angle_degrees===0,'unexpected gate pose');
  check(m.files?.glb?.path===d.glb.split('/').at(-1) &&
    m.files.glb.sha256===d.glb_sha256,'manifest GLB mismatch');
  check(Array.isArray(m.parts)&&m.parts.length>0,'manifest parts missing');
  const all=m.parts.map(p=>p.glb_node);
  check(all.every(n=>typeof n==='string'&&n.length>0)&&new Set(all).size===all.length,'duplicate or invalid manifest node');
  for(const p of m.parts)check(Array.isArray(p.bounds_m)&&p.bounds_m.length===6&&
    p.bounds_m.every(Number.isFinite)&&[0,1,2].every(k=>p.bounds_m[k]<=p.bounds_m[k+3]),'manifest bounds invalid');
  const selected=m.parts.filter(p=>d.subset===null||p.unit_id===d.subset);
  check(equalNames(selected.map(p=>p.glb_node),d.nodes),'manifest subset mismatch');
  return selected;
}
export async function verifyGlbBytes(bytes,expected) {
  check(bytes instanceof ArrayBuffer,'expected GLB ArrayBuffer');
  const hex=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),
    b=>b.toString(16).padStart(2,'0')).join('');
  check(hex===expected,'GLB SHA-256 mismatch');
  return hex;
}
export function inspectGlb(bytes) {
  check(bytes instanceof ArrayBuffer&&bytes.byteLength>=20,'truncated GLB');
  const v=new DataView(bytes);
  check(v.getUint32(0,true)===0x46546c67&&v.getUint32(4,true)===2&&
    v.getUint32(8,true)===bytes.byteLength,'invalid GLB header');
  const length=v.getUint32(12,true);
  check(length>0&&length%4===0&&20+length+8<=bytes.byteLength&&
    v.getUint32(16,true)===0x4e4f534a,'invalid GLB JSON chunk');
  const j=parseUniqueJson(new TextDecoder('utf-8',{fatal:true}).decode(new Uint8Array(bytes,20,length)));
  check(j.asset?.version==='2.0'&&Array.isArray(j.buffers)&&j.buffers.length===1&&
    !Object.hasOwn(j.buffers[0],'uri')&&!(j.images?.length)&&
    !(j.extensionsRequired?.length)&&!(j.extensionsUsed?.length)&&
    !(j.animations?.length)&&!(j.skins?.length),'unsupported/external GLB resource');
  const bin=20+length, binLength=v.getUint32(bin,true);
  check(v.getUint32(bin+4,true)===0x004e4942&&bin+8+binLength===bytes.byteLength&&
    Number.isInteger(j.buffers[0].byteLength)&&j.buffers[0].byteLength>=0&&
    binLength>=j.buffers[0].byteLength&&binLength-j.buffers[0].byteLength<=3,'invalid GLB BIN chunk');
  return j;
}
export function checkGlbNodes(d,m,j) {
  const selected=checkAssetManifest(d,m);
  const nodes=j.nodes??[], roots=j.scenes?.[j.scene??0]?.nodes??[];
  check(Array.isArray(nodes)&&Array.isArray(roots)&&roots.length===nodes.length&&
    new Set(roots).size===nodes.length&&roots.every(k=>Number.isInteger(k)&&k>=0&&k<nodes.length),
    'expected fixed flat GLB scene');
  check(equalNames(nodes.map(n=>n.name),m.parts.map(p=>p.glb_node)),'GLB node set mismatch');
  const revision=d.pose===null?d.revision:d.upstream_id+'/'+d.pose;
  for(const n of nodes)check(Number.isInteger(n.mesh)&&j.meshes?.[n.mesh]&&
    !(n.children?.length)&&!Object.hasOwn(n,'skin')&&n.extras?.assembly_revision===revision&&
    n.extras?.basis==='D'&&n.extras?.cad_eligibility==='reference_only','GLB node identity mismatch');
  return selected;
}
const boxArray=b=>[...b.min.toArray(),...b.max.toArray()];
const boundsMatch=(a,b)=>close(a,b,DISPLAY_BOUNDS_TOLERANCE_M);

// Dependencies supplied by the existing pinned Three.js import map.
// Cached templates own geometry/materials; instances share immutable geometry
// and material resources, but have separate Object3D transforms.
// Consumers must not mutate or dispose shared resources.
export function createGlbAssembler({THREE,GLTFLoader,catalog,root,fetcher=globalThis.fetch}) {
  const c=JSON.parse(canonicalJson(catalog)), base=new URL(root);
  const pending=new Map(), sources=new Set();
  let disposed=false;
  function release(source){
    const geometries=new Set(),materials=new Set();
    source.traverse(o=>{
      if(o.geometry)geometries.add(o.geometry);
      for(const m of o.material?(Array.isArray(o.material)?o.material:[o.material]):[])materials.add(m);
    });
    for(const g of geometries)g.dispose();
    for(const m of materials)m.dispose();
  }
  function dispose(){
    if(disposed)return;
    disposed=true;pending.clear();
    for(const source of sources)release(source);
    sources.clear();
  }
  const url=path=>new URL(path,base).href;
  async function fetchBytes(path) {
    const r=await fetcher(url(path));
    check(r.ok,'asset HTTP '+r.status+' '+path);
    return r.arrayBuffer();
  }
  async function loadTemplate(d) {
    const [manifestBytes,bytes]=await Promise.all([fetchBytes(d.manifest),fetchBytes(d.glb)]);
    const manifest=parseUniqueJson(new TextDecoder('utf-8',{fatal:true}).decode(manifestBytes));
    await verifyGlbBytes(bytes,d.glb_sha256);
    const selected=checkGlbNodes(d,manifest,inspectGlb(bytes));
    const gltf=await new GLTFLoader().parseAsync(bytes,'');
    const source=gltf.scene, meshes=new Map();
    if(disposed){release(source);throw Error('assembler disposed');}
    try {
    source.updateMatrixWorld(true);
    source.traverse(o=>{
      if(!o.isMesh)return;
      check(!meshes.has(o.name),'duplicate loaded mesh');
      meshes.set(o.name,o);
    });
    check(equalNames([...meshes.keys()],manifest.parts.map(p=>p.glb_node)),'loaded mesh set mismatch');
    const revision=d.pose===null?d.revision:d.upstream_id+'/'+d.pose;
    for(const p of manifest.parts) {
      const mesh=meshes.get(p.glb_node);
      check(mesh.children.length===0&&mesh.userData.assembly_revision===revision&&
        mesh.userData.basis==='D'&&mesh.userData.cad_eligibility==='reference_only','loaded mesh identity mismatch');
      check(boundsMatch(boxArray(new THREE.Box3().setFromObject(mesh,true)),displayBounds(p.bounds_m)),
        'loaded mesh bounds mismatch: '+p.glb_node);
    }
    sources.add(source);
    return selected.map(p=>({part:p,source:meshes.get(p.glb_node)}));
    }catch(error){release(source);throw error;}
  }
  function template(d) {
    if(!pending.has(d.id)){
      const job=loadTemplate(d);
      pending.set(d.id,job);
      job.catch(()=>{if(pending.get(d.id)===job)pending.delete(d.id)});
    }
    return pending.get(d.id);
  }
  async function prepare(input) {
    check(!disposed,'assembler disposed');
    const a=await loadAssembly(c,canonicalJson(input));
    const definitions=new Map(c.definitions.map(d=>[d.id,d]));
    const ids=[...new Set(a.instances.map(i=>i.definition_id))];
    const templates=new Map(await Promise.all(ids.map(async id=>[id,await template(definitions.get(id))])));
    check(!disposed,'assembler disposed');
    const group=new THREE.Group(), instances=new Map(), ports=new Map(), rows=[];
    group.name='stage4a-assembly';
    for(const i of a.instances) {
      const g=new THREE.Group(), placement=displayPlacement(i);
      g.name=i.id; g.userData.instance_id=i.id;
      g.position.fromArray(placement.position);g.rotation.y=placement.yaw;
      for(const {part,source} of templates.get(i.definition_id)){
        const mesh=source.clone(false);
        // Preserve the original GLB world transform when extracting a node.
        mesh.matrixAutoUpdate=false;mesh.matrix.copy(source.matrixWorld);
        mesh.matrixWorldNeedsUpdate=true;g.add(mesh);
      }
      group.add(g);instances.set(i.id,g);
      const d=definitions.get(i.definition_id);
      for(const [name,p] of Object.entries(d.ports)){
        const origin=new THREE.Vector3(...toDisplay(p.point_m));
        const outward=new THREE.Vector3(...toDisplay(p.outward));
        ports.set(JSON.stringify([i.id,name]),{origin,outward,group:g,
          expected:worldPort(c,i,name)});
      }
    }
    group.updateMatrixWorld(true);
    for(const i of a.instances){
      const g=instances.get(i.id), t=templates.get(i.definition_id);
      for(let k=0;k<t.length;k++){
        const mesh=g.children[k], part=t[k].part;
        const actual=boxArray(new THREE.Box3().setFromObject(mesh,true));
        const expected=placedBounds(part.bounds_m,i);
        check(boundsMatch(actual,expected),'placed mesh bounds mismatch: '+i.id+'/'+mesh.name);
        rows.push({instance_id:i.id,node:mesh.name,actual,expected});
      }
    }
    const portRows=new Map();
    for(const [key,p] of ports) {
      const point=p.origin.clone().applyMatrix4(p.group.matrixWorld).toArray();
      const outward=p.outward.clone().transformDirection(p.group.matrixWorld).toArray();
      check(close(point,toDisplay(p.expected.point_m),1e-9)&&
        close(outward,toDisplay(p.expected.outward),1e-9),'display port mismatch');
      portRows.set(key,{point,outward});
    }
    const connectionRows=a.connections.map(({a,b})=>{
      const p=portRows.get(JSON.stringify([a.instance_id,a.port]));
      const q=portRows.get(JSON.stringify([b.instance_id,b.port]));
      check(close(p.point,q.point,1e-9)&&close(p.outward,q.outward.map(v=>-v),1e-9),'display connection mismatch');
      return {a,b,point:p.point};
    });
    // Nothing is attached to a live scene until the caller accepts this result.
    return {group,instances,rows,portRows,connectionRows,status:'ANCHOR_ALIGNMENT_ONLY'};
  }
  // Call only after all consumer groups have been detached from live scenes.
  return {prepare,dispose};
}
