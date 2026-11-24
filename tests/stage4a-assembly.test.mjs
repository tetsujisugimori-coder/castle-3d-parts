import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {catalogSha256,validateAssembly,worldPort,placeAtPort,saveAssembly,loadAssembly,rotate} from "../assembly/stage4a/contract.mjs";
import {parseUniqueJson} from "../assembly/stage4a/json-data.mjs";
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
test("reference assembly matches existing static audit, not whole PAL assembly",async()=>{
 const audit=json("cad/stage3a/generated/connection-audit.json");
 assert.equal(audit.static_only,true);
 const rows=audit.rows.find(r=>r.pose==="B0").connections;
 assert.deepEqual(a.instances[0].translation_m,rows.find(r=>r.side==="left").translation_m);
 assert.deepEqual(a.instances[2].translation_m,rows.find(r=>r.side==="right").translation_m);
 assert.deepEqual(await validateAssembly(c,a),{status:"ANCHOR_ALIGNMENT_ONLY",instances:3,connections:2});
 assert.equal(a.instances[0].definition_id,a.instances[2].definition_id);
});
test("snap and round trip",async()=>{
 const left=placeAtPort(c,a.instances[1],"left",a.instances[0],"right");
 assert.ok(Math.abs(left.translation_m[0]+3.525)<1e-12);
 assert.deepEqual(await loadAssembly(c,await saveAssembly(c,a)),a);
 const r=clone();for(const i of r.instances){i.translation_m=rotate(i.translation_m,1);i.yaw_quarters=1}
 assert.equal((await validateAssembly(c,r)).connections,2);
 assert.deepEqual(worldPort(c,r.instances[1],"right").outward,[0,1,0]);
});
const faults=[
 ["wrong units",x=>x.unit="mm"],["wrong frame",x=>x.frame="Y-up"],["wrong basis",x=>x.basis="A"],["wrong catalog",x=>x.catalog_commit="other"],
 ["duplicate id",x=>x.instances[2].id="F01"],["unknown definition",x=>x.instances[0].definition_id="missing"],["wrong revision",x=>x.instances[0].revision="B1"],["pose mismatch",x=>x.instances[1].pose="B1"],["nonfinite",x=>x.instances[0].translation_m[0]=Infinity],["scale",x=>x.instances[0].scale=2],["bad rotation",x=>x.instances[0].yaw_quarters=0.5],["gap",x=>x.instances[0].translation_m[0]-=.001],["overlap",x=>x.instances[0].translation_m[0]+=.001],["bad direction",x=>x.instances[0].yaw_quarters=2],["unknown port",x=>x.connections[0].a.port="missing"],["missing instance",x=>x.connections[0].a.instance_id="lost"],["duplicate port",x=>x.connections.push(structuredClone(x.connections[0]))],["self",x=>x.connections[0].b.instance_id="F01"],["forged safety",x=>x.status="PASS"],["prototype name",x=>x.connections[0].a.port="constructor"]
];
for(const [name,mutate] of faults)test("reject "+name,async()=>{const x=clone();mutate(x);await assert.rejects(validateAssembly(c,x))});
test("reject invalid save without changing valid fixture",async()=>{
 await assert.rejects(loadAssembly(c,"{"),SyntaxError);
 await assert.rejects(loadAssembly(c,JSON.stringify({...a,unit:"mm"})),/invalid assembly header/);
 assert.equal((await validateAssembly(c,a)).connections,2);
});
test("demand IDs, priority, unknown historical claims and no placement authorization",()=>{
 assert.equal(d.site,"山中城");assert.equal(d.library_commit,c.baseline_commit);
 assert.equal(d.items.length,10);assert.equal(new Set(d.items.map(x=>x.id)).size,10);
 assert.deepEqual(d.items.map(x=>x.priority),[1,1,1,1,1,2,2,2,3,4]);
 for(const x of d.items){assert.equal(x.historical_form,"UNKNOWN");assert.equal(x.historical_dimensions,"UNKNOWN");assert.equal(x.placement,"NOT_AUTHORIZED");assert.ok(x.source_refs.length>0);assert.ok(x.source_refs.every(s=>s.startsWith("https://github.com/tetsujisugimori-coder/")))}
});

test("v2 catalog digest matches independent SHA-256 of canonical UTF-8",async()=>{
 const sample=JSON.parse('{"2":2,"10":10,"𝄞":["源",-0,1.00,"\\r\\n"],"a":{"z":false,"a":null}}');
 const canonical='{"10":10,"2":2,"a":{"a":null,"z":false},"𝄞":["源",0,1,"\\r\\n"]}';
 assert.equal(await catalogSha256(sample),createHash("sha256").update(canonical,"utf8").digest("hex"));
 assert.equal(await catalogSha256(c),a.catalog_sha256);
 const reverseKeys=value=>Array.isArray(value)?value.map(reverseKeys):
   value&&typeof value==="object"?Object.fromEntries(Object.entries(value).reverse()
     .map(([key,item])=>[key,reverseKeys(item)])):value;
 assert.deepEqual(await loadAssembly(reverseKeys(c),await saveAssembly(c,a)),a);
});

const catalogFaults=[
 ["port height and paths, with the original commit",x=>{
   for(const d of x.definitions)for(const port of Object.values(d.ports))port.point_m[2]+=.1;
   x.definitions[0].manifest="different.json";
   x.definitions[0].glb="different.glb";
 }],
 ["port direction",x=>x.definitions[0].ports.right.outward[0]=-1],
 ["part ID",x=>x.definitions[0].id="PAL-U99"],
 ["part revision",x=>x.definitions[0].revision="B1"],
 ["part pose",x=>x.definitions[1].pose="B1"],
 ["unit",x=>x.unit="mm"],
 ["coordinate frame",x=>x.frame="Y-up"],
 ["GLB reference",x=>x.definitions[0].glb="other.glb"],
 ["GLB hash",x=>x.definitions[0].glb_sha256="0".repeat(64)],
 ["GLB nodes",x=>x.definitions[0].nodes[0]="U02_Post_001"],
 ["node order",x=>x.definitions[0].nodes.reverse()],
 ["catalog self-claimed digest",x=>x.catalog_sha256=a.catalog_sha256],
];
for(const [name,mutate] of catalogFaults)test("reject changed catalog "+name,async()=>{
 const saved=await saveAssembly(c,a);
 const changed=structuredClone(c);
 mutate(changed);
 assert.equal(changed.baseline_commit,c.baseline_commit);
 await assert.rejects(loadAssembly(changed,saved),/catalog SHA-256 mismatch/);
 await assert.rejects(saveAssembly(changed,a),/catalog SHA-256 mismatch/);
});

test("reject legacy, unknown and missing or tampered fingerprint on persisted input",async()=>{
 const missing=clone();
 delete missing.catalog_sha256;
 for(const [input,error] of [
   [missing,/missing or invalid catalog_sha256/],
   [{...missing,schema_version:1},/unsupported assembly schema/],
   [{...a,schema_version:3},/unsupported assembly schema/],
   [{...a,catalog_sha256:"a".repeat(64)},/catalog SHA-256 mismatch/],
   [{...a,catalog_sha256:"0".repeat(63)+"\n"},/missing or invalid catalog_sha256/],
   [{...a,catalog_sha256:"g".repeat(64)},/missing or invalid catalog_sha256/],
   [{...a,catalog_sha256:null},/missing or invalid catalog_sha256/],
 ])await assert.rejects(loadAssembly(c,JSON.stringify(input)),error);
 await assert.rejects(saveAssembly(c,{...missing,schema_version:1}),/unsupported assembly schema/);
 assert.deepEqual(await loadAssembly(c,await saveAssembly(c,missing)),a);
 assert.equal(Object.hasOwn(missing,"catalog_sha256"),false);
});

test("catalog and design are snapshotted before digest yields",async()=>{
 const catalog=structuredClone(c);
 const design=clone();
 const pending=saveAssembly(catalog,design);
 catalog.definitions[0].ports.right.point_m[2]+=.1;
 design.instances[0].translation_m[0]=0;
 assert.deepEqual(await loadAssembly(c,await pending),a);
 const loading=loadAssembly(catalog,await saveAssembly(c,a));
 catalog.definitions[0].ports.right.point_m[2]=c.definitions[0].ports.right.point_m[2];
 await assert.rejects(loading,/catalog SHA-256 mismatch/);
});

const badCoordinates=[
 ["three empty slots",()=>Array(3)],
 ["one empty slot",()=>[0,,0]],
 ["undefined",()=>[0,undefined,0]],
 ["null",()=>[0,null,0]],
 ["NaN",()=>[0,NaN,0]],
 ["Infinity",()=>[0,Infinity,0]],
 ["negative Infinity",()=>[0,-Infinity,0]],
 ["numeric string",()=>[0,"1",0]],
 ["short",()=>[0,0]],
 ["long",()=>[0,0,0,0]],
 ["inherited slot",()=>{
   const value=[0,,0];
   Object.setPrototypeOf(value,[0,1,0]);
   return value;
 }],
 ["nested",()=>[0,[1],0]],
];
for(const [name,coordinates] of badCoordinates)test("reject invalid coordinates "+name,async()=>{
 const input=clone();
 input.instances=[input.instances[0]];
 input.connections=[];
 const value=coordinates();
 input.instances[0].translation_m=value;
 const before=Object.getOwnPropertyDescriptors(value);
 await assert.rejects(saveAssembly(c,input),/JSON|instance/);
 assert.throws(()=>rotate(value,0),/invalid vector/);
 assert.equal(input.instances[0].translation_m,value);
 assert.deepEqual(Object.getOwnPropertyDescriptors(value),before);
});

test("reject holes and non-data properties outside coordinate arrays",async()=>{
 for(const property of ["instances","connections"]){
   const input=clone();
   delete input[property][0];
   await assert.rejects(saveAssembly(c,input),/dense JSON array/);
 }
 const input=clone();
 Object.defineProperty(input,"toJSON",{get(){throw new Error("getter should not run")},enumerable:true});
 await assert.rejects(saveAssembly(c,input),/expected own JSON data property/);
 const editedCatalog=structuredClone(c);
 editedCatalog.definitions[0].nodes[0]=undefined;
 await assert.rejects(loadAssembly(editedCatalog,JSON.stringify(a)),/expected finite, acyclic JSON data/);
});

test("single and rotated connected arrangements survive repeated save/load",async()=>{
 const single={...clone(),instances:[{...a.instances[0],translation_m:[-0,1e-9,10000]}],connections:[]};
 const rotated=clone();
 for(const placement of rotated.instances){
   placement.translation_m=rotate(placement.translation_m,3);
   placement.yaw_quarters=3;
 }
 for(const design of [single,rotated]){
   const first=await saveAssembly(c,design);
   let value=await loadAssembly(c,first);
   assert.deepEqual(value,JSON.parse(JSON.stringify(design)));
   for(let index=0;index<3;index++){
     assert.equal(await saveAssembly(c,value),first);
     value=await loadAssembly(c,first);
   }
 }
});

test("duplicate keys rejected per object after decoding Unicode escapes",async()=>{
 const saved=await saveAssembly(c,a);
 for(const text of [
   saved.replace('"unit": "m"', '"unit": "mm", "unit": "m"'),
   saved.replace('"unit": "m"', '"\\u0075nit": "m", "unit": "m"'),
   saved.replace('"yaw_quarters": 0', '"yaw_quarters": 1, "yaw_quarters": 0'),
 ])await assert.rejects(loadAssembly(c,text),/duplicate JSON key/);
 const separateObjects=[{k:'quote " [ ] { } , : \\',u:1},{k:true}];
 assert.deepEqual(parseUniqueJson(JSON.stringify(separateObjects)),separateObjects);
 assert.deepEqual(await loadAssembly(c,saved),a);
});
