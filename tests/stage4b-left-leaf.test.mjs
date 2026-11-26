import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {loadAssembly,saveAssembly} from '../assembly/stage4a/contract.mjs';
import {checkGlbNodes,inspectGlb,verifyGlbBytes} from '../assembly/stage4a/glb-scene.mjs';
import {validateFixedLeaf} from '../assembly/stage4b/fixed-leaf.mjs';

const base='cad/stage4b/west-gate-left';
const get=p=>readFileSync(new URL('../'+p,import.meta.url));
const json=p=>JSON.parse(get(p));
const c=json('assembly/stage4b/catalog.json');
const a=json('assembly/stage4b/example.json');
const board='YAM-WEST-LEFT-BOARD',rail='YAM-WEST-LEFT-RAIL';
test('two definitions, eight instances, v2 round trip retains exact catalog',async()=>{
 assert.deepEqual(c.definitions.map(d=>d.id),[board,rail]);
 assert.deepEqual(a.instances.map(i=>i.definition_id),[...Array(6).fill(board),rail,rail]);
 assert.equal(new Set(a.instances.map(i=>i.id)).size,8);
 assert.deepEqual(await loadAssembly(c,await saveAssembly(c,a)),a);
 await validateFixedLeaf(c,JSON.stringify(a));
});
for(const [name,mutation,why] of [
 ['missing board',x=>x.instances.splice(1,1),/count/],
 ['wrong registered definition',x=>x.instances[2].definition_id=rail,/occurrence/],
 ['millimetre gap fault',x=>x.instances[2].translation_m[0]+=.001,/placement/],
 ['rail moved into board',x=>x.instances[6].translation_m[1]-=.001,/placement/],
 ['orientation change',x=>x.instances[2].yaw_quarters=1,/occurrence/],
 ['missing definition',x=>x.instances[2].definition_id='unknown',/definition/],
 ['tampered catalog hash',x=>x.catalog_sha256='0'.repeat(64),/SHA/],
])test('fixed example rejects '+name,async()=>{
 const x=structuredClone(a);mutation(x);await assert.rejects(validateFixedLeaf(c,JSON.stringify(x)),why);
});
test('checked public assets, fixed merged mesh and distinct reused glTF meshes',async()=>{
 for(const d of [...c.definitions,{
  upstream_id:'YAM-WEST-LEFT-LEAF',revision:'D0',pose:null,subset:null,
  manifest:base+'/west-gate-left-leaf.manifest.json',glb:base+'/west-gate-left-leaf.glb',nodes:['B01','B02','B03','B04','B05','B06','R01','R02'],
 }]){
  const m=json(d.manifest),b=get(d.glb),bytes=b.buffer.slice(b.byteOffset,b.byteOffset+b.length);
  d.glb_sha256??=m.files.glb.sha256;
  await verifyGlbBytes(bytes,d.glb_sha256);
  const g=inspectGlb(bytes);checkGlbNodes(d,m,g);
  if(g.nodes.length===8){
   assert.equal(g.meshes.length,2);
   assert.equal(new Set(g.nodes.filter(n=>n.name.startsWith('B')).map(n=>n.mesh)).size,1);
   assert.equal(new Set(g.nodes.filter(n=>n.name.startsWith('R')).map(n=>n.mesh)).size,1);
  }
  b[b.length-1]^=1;await assert.rejects(verifyGlbBytes(bytes.slice(0,bytes.byteLength-1),d.glb_sha256),/SHA/);
 }
});
test('prototype inputs unchanged, metadata refresh deterministic',()=>{
 for(const [p,want] of [
  [base+'/west-gate-board-draft.FCStd','c7ab631138477a20923d324992540c8ffdc729fdc37e5eafc876ab2e8833e3f8'],
  [base+'/west-gate-board-draft.step','d1c9f112caa949c296d0b133c422f497f2b21f77f724aaa78fb7c1fbb642de8e'],
  ['blender/stage4b/west-gate-board-draft.blend','3fcd0ea524b4764b113dcad800992d1ee7e9567dbae65b11f151f79ab589bd68'],
 ])assert.equal(createHash('sha256').update(get(p)).digest('hex'),want);
 execFileSync(process.execPath,['scripts/stage4b/build-catalog.mjs','--check']);
});

test('canvas check rejects a blank image even when bulky, and accepts a highly compressed gate raster',async()=>{
 const {deflateSync,crc32}=await import('node:zlib');
 const {assertLeafPixels}=await import('../scripts/stage4b/png.mjs');
 const make=(draw,level)=>{
  const chunk=(type,b)=>{
   const c=Buffer.alloc(12+b.length);c.writeUInt32BE(b.length);c.write(type,4);b.copy(c,8);
   c.writeUInt32BE(crc32(c.subarray(4,-4)),c.length-4);return c;
  };
  const w=100,h=110,stride=w*3+1,header=Buffer.alloc(13),raw=Buffer.alloc(h*stride);
  header.writeUInt32BE(w);header.writeUInt32BE(h,4);header[8]=8;header[9]=2;
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
   const b=draw&&x>=35&&x<64&&y>=15&&y<95?[130,78,35]:[195,204,183];
   raw.set(b,y*stride+1+x*3);
  }
  return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',deflateSync(raw,{level})),chunk('IEND',Buffer.alloc(0))]);
 };
 const good=make(true,9),bad=make(false,0);
 assert(good.length<5000);assert(bad.length>5000);
 assert.equal(assertLeafPixels(good).woodPixels,29*80);
 assert.throws(()=>assertLeafPixels(bad),/rendered surface not found/);
});
