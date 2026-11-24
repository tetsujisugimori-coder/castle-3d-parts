import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {validateAssembly,worldPort,placeAtPort,saveAssembly,loadAssembly,rotate} from "../assembly/stage4a/contract.mjs";
const read=p=>readFileSync(new URL("../"+p,import.meta.url));
const json=p=>JSON.parse(read(p));
const c=json("assembly/stage4a/catalog.json"),a=json("assembly/stage4a/example.json"),d=json("assembly/stage4a/yamanaka-demand.json");
const clone=()=>structuredClone(a);
test("fixed manifests, subset, actual GLB bytes and port face centres",()=>{
 for(const p of c.definitions){
  const m=json(p.manifest);assert.equal(m.assembly_id,p.upstream_id);
  assert.equal(m.revision,p.pose??p.revision);assert.equal(m.basis,"D");
  const nodes=m.parts.filter(n=>p.subset===null||n.unit_id===p.subset);
  assert.deepEqual(nodes.map(n=>n.glb_node).sort(),[...p.nodes].sort());
  assert.equal(m.files.glb.sha256,p.glb_sha256);
  assert.equal(createHash("sha256").update(read(p.glb)).digest("hex"),p.glb_sha256);
  for(const side of ["left","right"]){
   const member=p.subset?"U01_Rail_002":"GATE_Connector_"+(side==="left"?"Left":"Right");
   const b=nodes.find(n=>n.id===member).bounds_m, port=p.ports[side];
   const expected=[b[side==="left"?0:3],(b[1]+b[4])/2,(b[2]+b[5])/2];
   expected.forEach((v,i)=>assert.ok(Math.abs(v-port.point_m[i])<1e-12));
   assert.deepEqual(port.outward,[side==="left"?-1:1,0,0]);
  }
 }
});
test("reference assembly matches existing static audit, not whole PAL assembly",()=>{
 const audit=json("cad/stage3a/generated/connection-audit.json");
 assert.equal(audit.static_only,true);
 const rows=audit.rows.find(r=>r.pose==="B0").connections;
 assert.deepEqual(a.instances[0].translation_m,rows.find(r=>r.side==="left").translation_m);
 assert.deepEqual(a.instances[2].translation_m,rows.find(r=>r.side==="right").translation_m);
 assert.deepEqual(validateAssembly(c,a),{status:"ANCHOR_ALIGNMENT_ONLY",instances:3,connections:2});
 assert.equal(a.instances[0].definition_id,a.instances[2].definition_id);
});
test("snap and round trip",()=>{
 const left=placeAtPort(c,a.instances[1],"left",a.instances[0],"right");
 assert.ok(Math.abs(left.translation_m[0]+3.525)<1e-12);
 assert.deepEqual(loadAssembly(c,saveAssembly(c,a)),a);
 const r=clone();for(const i of r.instances){i.translation_m=rotate(i.translation_m,1);i.yaw_quarters=1}
 assert.equal(validateAssembly(c,r).connections,2);
 assert.deepEqual(worldPort(c,r.instances[1],"right").outward,[0,1,0]);
});
const faults=[
 ["wrong units",x=>x.unit="mm"],["wrong frame",x=>x.frame="Y-up"],["wrong basis",x=>x.basis="A"],["wrong catalog",x=>x.catalog_commit="other"],
 ["duplicate id",x=>x.instances[2].id="F01"],["unknown definition",x=>x.instances[0].definition_id="missing"],["wrong revision",x=>x.instances[0].revision="B1"],["pose mismatch",x=>x.instances[1].pose="B1"],["nonfinite",x=>x.instances[0].translation_m[0]=Infinity],["scale",x=>x.instances[0].scale=2],["bad rotation",x=>x.instances[0].yaw_quarters=0.5],["gap",x=>x.instances[0].translation_m[0]-=.001],["overlap",x=>x.instances[0].translation_m[0]+=.001],["bad direction",x=>x.instances[0].yaw_quarters=2],["unknown port",x=>x.connections[0].a.port="missing"],["missing instance",x=>x.connections[0].a.instance_id="lost"],["duplicate port",x=>x.connections.push(structuredClone(x.connections[0]))],["self",x=>x.connections[0].b.instance_id="F01"],["forged safety",x=>x.status="PASS"],["prototype name",x=>x.connections[0].a.port="constructor"]
];
for(const [name,mutate] of faults)test("reject "+name,()=>{const x=clone();mutate(x);assert.throws(()=>validateAssembly(c,x))});
test("reject invalid save without changing valid fixture",()=>{assert.throws(()=>loadAssembly(c,"{"));assert.throws(()=>loadAssembly(c,JSON.stringify({...a,unit:"mm"})));assert.equal(validateAssembly(c,a).connections,2)});
test("demand IDs, priority, unknown historical claims and no placement authorization",()=>{
 assert.equal(d.site,"山中城");assert.equal(d.library_commit,c.baseline_commit);
 assert.equal(d.items.length,10);assert.equal(new Set(d.items.map(x=>x.id)).size,10);
 assert.deepEqual(d.items.map(x=>x.priority),[1,1,1,1,1,2,2,2,3,4]);
 for(const x of d.items){assert.equal(x.historical_form,"UNKNOWN");assert.equal(x.historical_dimensions,"UNKNOWN");assert.equal(x.placement,"NOT_AUTHORIZED");assert.ok(x.source_refs.length>0);assert.ok(x.source_refs.every(s=>s.startsWith("https://github.com/tetsujisugimori-coder/")))}
});
