import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {catalogSha256,loadAssembly,saveAssembly,worldPort} from '../assembly/stage4a/contract.mjs';
import {checkGlbNodes,inspectGlb} from '../assembly/stage4a/glb-scene.mjs';
import {modelPose,poseDocument,poses} from '../assembly/stage4b-wave2/poses.mjs';
const base='assembly/stage4b-wave2/';
const json=p=>JSON.parse(readFileSync(p));
const design=json(base+'design.json'),catalog=json(base+'catalog.json'),old=json('assembly/stage4b/catalog.json'),left=json('assembly/stage4b/example.json');
const raw=p=>modelPose(catalog,design,left,p);
const digest=p=>createHash('sha256').update(readFileSync(p)).digest('hex');

test('D0 definitions unchanged; three reusable D1 canonical parts and read-only assets',()=>{
 assert.deepEqual(catalog.definitions.slice(0,2),old.definitions);
 const defs=catalog.definitions.slice(2);
 assert.deepEqual(defs.map(d=>d.id),['YAM-WEST-POST','YAM-WEST-BEARING','YAM-WEST-PIVOT']);
 for(const d of defs){
  const m=json(d.manifest);
  assert.deepEqual(Object.keys(m.files).sort(),['blender','cad','glb','step']);
  for(const f of Object.values(m.files))assert.equal(digest(f.repository_path),f.sha256);
  assert.equal(digest(d.glb),d.glb_sha256);
  const glb=readFileSync(d.glb);
  assert.equal(checkGlbNodes(d,m,inspectGlb(glb.buffer.slice(glb.byteOffset,glb.byteOffset+glb.byteLength))).length,1);
 }
});

const xyz=r=>r.translation_m.map(x=>Math.round(x*1000));
const face=(g,side,which)=>g.instances.find(r=>r.id===side+'-'+which);
const leftExpected={
 closed:{board:[-1805,0,20],rail:[-1870,130,420],pin:0},
 open:{board:[-1800,395,20],rail:[-1930,330,420],pin:1}
};
const rightExpected={
 closed:{board:[1535,0,20],rail:[20,130,420],pin:2,q:0},
 open:{board:[1800,665,20],rail:[1930,2180,420],pin:1,q:3}
};
const status={closed:[false,false],left:[true,false],right:[false,true],both:[true,true]};
for(const [pose,[l,r]] of Object.entries(status))test('independent fixed coordinates and v2 save/load: '+pose,async()=>{
 const g=raw(pose);
 assert.equal(g.instances.length,26);assert.equal(g.connections.length,8);
 assert.deepEqual(Object.fromEntries(catalog.definitions.map(d=>[d.id,g.instances.filter(i=>i.definition_id===d.id).length])),{
 'YAM-WEST-LEFT-BOARD':12,'YAM-WEST-LEFT-RAIL':4,'YAM-WEST-POST':2,'YAM-WEST-BEARING':4,'YAM-WEST-PIVOT':4});
 for(const [side,open,expect] of [['L',l,leftExpected],['R',r,rightExpected]]){
  const x=side==='L'?-1:1,e=expect[open?'open':'closed'];
  assert.deepEqual(xyz(face(g,side,'B01')),e.board);assert.deepEqual(xyz(face(g,side,'R01')),e.rail);
  assert.equal(face(g,side,'B06').yaw_quarters,open?(x<0?1:3):0);
  assert.equal(face(g,side,'pin-0').yaw_quarters,e.pin);
  assert.deepEqual(xyz(face(g,side,'post')),[x*2300,200,0]);
  for(const h of [0,1]){
   const b=face(g,side,'bearing-'+h),p=face(g,side,'pin-'+h);
   assert.deepEqual(xyz(b),[x*2000,200,[400,2100][h]]);assert.deepEqual(xyz(p),xyz(b));
   assert.deepEqual(worldPort(catalog,b,'axis').point_m,worldPort(catalog,p,'axis').point_m);
  }
 }
 const saved=await poseDocument(catalog,design,left,pose);
 const restored=await loadAssembly(catalog,saved);
 assert.equal(restored.catalog_commit,design.baseline);
 assert.equal(restored.catalog_sha256,await catalogSha256(catalog));
 assert.deepEqual(restored.instances,g.instances);
 assert.deepEqual(restored.connections,g.connections);
 assert.deepEqual(JSON.parse(await saveAssembly(catalog,restored)),JSON.parse(saved));
 if(pose==='closed')assert.equal(saved,readFileSync(base+'example.json','utf8'));
});

test('independent local test of seam, floor and bounded swing gap',()=>{
 const c=raw('closed');
 const l=face(c,'L','R01'),r=face(c,'R','R01');
 assert.equal(xyz(r)[0]-(xyz(l)[0]+1850),40);
 for(const i of c.instances.filter(i=>i.definition_id.endsWith('BOARD')))assert.equal(xyz(i)[2],20);
 // Coordinates from fixed closed pose transformed to the pivot frame. Project
 // both leaf envelopes for independent 0–90° samples; not a solid proof.
 let gap=Infinity,post=Infinity;
 for(let i=0;i<=90;i++){
  const a=i*Math.PI/180;
  const lo=130*Math.cos(a)-100*Math.sin(a);
  const board=1915*Math.cos(a)+200*Math.sin(a);
  const rail=1980*Math.cos(a)+70*Math.sin(a);
  gap=Math.min(gap,4000-2*Math.max(board,rail));
  post=Math.min(post,lo+150);
 }
 assert(gap>37&&gap<40);assert(post>=50);
 assert.equal(design.bearing_bore_radius-design.pin_radius,2);
 assert.equal(design.arm_base_z-design.bearing_height,10);
 // Bracket reach exceeds the post stand-off; alternate dimensions are rejected.
 assert.equal(design.parts['YAM-WEST-BEARING'].bounds_mm[0],-150);
});

test('part- and side-only observation configurations',async()=>{
 for(const k of ['post','bearing','pivot','inspect-left','inspect-right']){
  const a=await loadAssembly(catalog,await poseDocument(catalog,design,left,k));
  assert.equal(a.instances.length,k.startsWith('inspect-')?13:1);
  assert.equal(a.connections.length,k.startsWith('inspect-')?4:0);
 }
 await assert.rejects(poseDocument(catalog,design,left,'__proto__'),/unknown/);
 assert.deepEqual(Object.keys(poses),['closed','left','right','both']);
});

for(const [n,mut,re] of [
 ['bad part',a=>a.instances[0].definition_id='BRANCH-INCOMPATIBLE',/definition/],
 ['bad rev',a=>a.instances[0].revision='D0',/revision/],
 ['changed support',a=>a.instances.find(x=>x.id==='L-bearing-0').translation_m[0]+=.004,/ports/],
 ['bad port',a=>a.connections[0].a.port='unknown',/port/],
 ['duplicated connection',a=>a.connections.push(a.connections[0]),/connected/],
 ['bad catalog',a=>a.catalog_sha256='f'.repeat(64),/SHA/],
])test('negative control: '+n,async()=>{
 const value=JSON.parse(await poseDocument(catalog,design,left,'closed'));mut(value);
 await assert.rejects(loadAssembly(catalog,JSON.stringify(value)),re);
});
