// Stage 4-A: static reference assembly only. No geometry or historical certification.
const assert=(ok,msg)=>{if(!ok)throw new Error(msg)};
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const obj=o=>o!==null&&typeof o==="object"&&!Array.isArray(o);
const keys=(o,ks)=>obj(o)&&Object.keys(o).length===ks.length&&ks.every(k=>own(o,k));
const id=s=>typeof s==="string"&&/^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(s);
const vec=v=>Array.isArray(v)&&v.length===3&&v.every(n=>Number.isFinite(n)&&Math.abs(n)<=10000);
const EPS=1e-9;
const close=(a,b)=>a.every((v,i)=>Math.abs(v-b[i])<=EPS);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const neg=a=>a.map(v=>-v);
export function rotate(v,q){
  assert(vec(v)&&Number.isInteger(q)&&q>=0&&q<=3,"invalid vector/rotation");
  const [x,y,z]=v;
  return [[x,y,z],[-y,x,z],[-x,-y,z],[y,-x,z]][q];
}
function def(c,i){
  const d=c.definitions.find(d=>d.id===i.definition_id);
  assert(d&&d.revision===i.revision&&d.pose===i.pose,"unknown definition/revision/pose");
  return d;
}
function checkInstance(c,i){
  assert(keys(i,["id","definition_id","revision","pose","translation_m","yaw_quarters"])&&id(i.id)&&vec(i.translation_m)&&Number.isInteger(i.yaw_quarters)&&i.yaw_quarters>=0&&i.yaw_quarters<=3,"invalid instance");
  def(c,i);
}
export function worldPort(c,i,p){
  checkInstance(c,i);
  const d=def(c,i);
  assert(typeof p==="string"&&own(d.ports,p),"unknown port");
  const port=d.ports[p];
  return {point_m:add(rotate(port.point_m,i.yaw_quarters),i.translation_m),outward:rotate(port.outward,i.yaw_quarters),type:port.type};
}
// Trusted catalog is the fixed, version-controlled catalog, not imported with a save.
export function validateAssembly(c,a){
  assert(keys(a,["schema_version","unit","frame","basis","catalog_commit","instances","connections"])&&a.schema_version===1&&a.unit===c.unit&&a.frame===c.frame&&a.basis==="D"&&a.catalog_commit===c.baseline_commit,"invalid assembly header");
  assert(Array.isArray(a.instances)&&a.instances.length>0&&a.instances.length<=1000&&Array.isArray(a.connections)&&a.connections.length<=2000,"invalid assembly counts");
  const instances=new Map();
  for(const i of a.instances){checkInstance(c,i);assert(!instances.has(i.id),"duplicate instance");instances.set(i.id,i)}
  const used=new Set();
  function endpoint(e){
    assert(keys(e,["instance_id","port"])&&instances.has(e.instance_id),"invalid endpoint");
    const p=worldPort(c,instances.get(e.instance_id),e.port);
    const k=JSON.stringify([e.instance_id,e.port]);
    assert(!used.has(k),"port already connected");used.add(k);return p;
  }
  for(const c0 of a.connections){
    assert(keys(c0,["a","b"])&&c0.a?.instance_id!==c0.b?.instance_id,"invalid/self connection");
    const p=endpoint(c0.a),q=endpoint(c0.b);
    assert(p.type===q.type&&close(p.point_m,q.point_m)&&close(p.outward,neg(q.outward)),"incompatible/misaligned ports");
  }
  return {status:"ANCHOR_ALIGNMENT_ONLY",instances:a.instances.length,connections:a.connections.length};
}
export function placeAtPort(c,fixed,fixedPort,moving,movingPort){
  const a=worldPort(c,fixed,fixedPort);
  const origin={...moving,translation_m:[0,0,0]};
  const b=worldPort(c,origin,movingPort);
  assert(fixed.id!==moving.id&&a.type===b.type&&close(a.outward,neg(b.outward)),"incompatible placement");
  const result={...origin,translation_m:sub(a.point_m,b.point_m)};
  checkInstance(c,result);return result;
}
export function saveAssembly(c,a){validateAssembly(c,a);return JSON.stringify(a,null,2)+"\n"}
export function loadAssembly(c,s){assert(typeof s==="string"&&s.length<=1000000,"invalid save size");const a=JSON.parse(s);validateAssembly(c,a);return a}
