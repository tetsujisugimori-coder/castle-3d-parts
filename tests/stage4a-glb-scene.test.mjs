import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {checkAssetManifest,inspectGlb,verifyGlbBytes,checkGlbNodes,displayBounds,placedBounds,
  toDisplay,DISPLAY_BOUNDS_TOLERANCE_M} from '../assembly/stage4a/glb-scene.mjs';
import {worldPort,rotate} from '../assembly/stage4a/contract.mjs';

const read=p=>readFile(new URL('../'+p,import.meta.url));
const json=async p=>JSON.parse(await read(p));
const c=await json('assembly/stage4a/catalog.json');
const example=await json('assembly/stage4a/example.json');
const fixtures=await Promise.all(c.definitions.map(async d=>{
  const data=await read(d.glb);
  return {d,m:await json(d.manifest),bytes:data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength)};
}));
const close=(actual,expected,tol=DISPLAY_BOUNDS_TOLERANCE_M)=>{
  assert.equal(actual.length,expected.length);
  actual.forEach((v,k)=>assert.ok(Number.isFinite(v)&&Math.abs(v-expected[k])<=tol,
    'coordinate '+k+': '+v+' != '+expected[k]));
};
// Independent CPU inspection of actual float32 POSITION bytes, not glTF min/max metadata.
// This fixed-fixture oracle intentionally rejects unsupported hierarchy and transforms.
function vertices(bytes,j,node){
  for(const key of ['matrix','translation','rotation','scale','children'])assert.ok(!Object.hasOwn(node,key));
  const view=new DataView(bytes),start=28+view.getUint32(12,true),result=[];
  for(const primitive of j.meshes[node.mesh].primitives){
    const a=j.accessors[primitive.attributes.POSITION],b=j.bufferViews[a.bufferView];
    assert.equal(a.componentType,5126);assert.equal(a.type,'VEC3');
    assert.ok(!a.sparse&&!a.normalized);assert.equal(b.buffer,0);
    const stride=b.byteStride??12,offset=(b.byteOffset??0)+(a.byteOffset??0);
    assert.ok(a.count>0&&stride>=12);
    assert.ok((a.byteOffset??0)+(a.count-1)*stride+12<=b.byteLength);
    assert.ok(offset+(a.count-1)*stride+12<=j.buffers[0].byteLength);
    for(let k=0;k<a.count;k++)result.push([0,4,8].map(n=>view.getFloat32(start+offset+k*stride+n,true)));
  }
  return result;
}
function bounds(points){
  return [...[0,1,2].map(k=>Math.min(...points.map(p=>p[k]))),
    ...[0,1,2].map(k=>Math.max(...points.map(p=>p[k])))];
}
function transform(p,i){
  // Independent positive Y-up yaw in display coordinates.
  const [x,y,z]=p, t=toDisplay(i.translation_m);
  const q=[[x,y,z],[z,y,-x],[-x,y,-z],[-z,y,x]][i.yaw_quarters];
  return q.map((v,k)=>v+t[k]);
}
for(const {d,m,bytes} of fixtures){
  test(d.id+' actual GLB digest, node identity and vertex bounds',async()=>{
    assert.equal(await verifyGlbBytes(bytes,d.glb_sha256),d.glb_sha256);
    const j=inspectGlb(bytes),selected=checkGlbNodes(d,m,j);
    assert.equal(selected.length,7);
    assert.equal(j.nodes.length,d.subset===null?7:14);
    assert.deepEqual(selected.map(p=>p.glb_node).sort(),[...d.nodes].sort());
    assert.ok(selected.every(p=>!p.glb_node.startsWith('U02_')));
    for(const p of m.parts){
      const node=j.nodes.find(n=>n.name===p.glb_node);
      close(bounds(vertices(bytes,j,node)),displayBounds(p.bounds_m));
    }
  });
  test(d.id+' actual position bytes agree with four quarter turns',()=>{
    const j=inspectGlb(bytes);
    for(const p of checkGlbNodes(d,m,j)){
      const points=vertices(bytes,j,j.nodes.find(n=>n.name===p.glb_node));
      for(let q=0;q<4;q++){
        const i={translation_m:[2,3,4],yaw_quarters:q};
        close(bounds(points.map(v=>transform(v,i))),placedBounds(p.bounds_m,i));
      }
    }
  });
  test(d.id+' rejects altered bytes, truncated GLB and wrong manifest',async()=>{
    const changed=bytes.slice(0);new Uint8Array(changed)[changed.byteLength-1]^=1;
    await assert.rejects(verifyGlbBytes(changed,d.glb_sha256),/SHA-256 mismatch/);
    assert.throws(()=>inspectGlb(bytes.slice(0,19)),/truncated/);
    assert.throws(()=>inspectGlb(bytes.slice(0,-4)),/header/);
    const wrong=structuredClone(m);wrong.files.glb.sha256='0'.repeat(64);
    assert.throws(()=>checkAssetManifest(d,wrong),/GLB mismatch/);
  });
  test(d.id+' rejects wrong node set, duplicate, extras and manifest subset',()=>{
    const j=inspectGlb(bytes);
    const wrong=structuredClone(j);wrong.nodes[0].name='unexpected';
    assert.throws(()=>checkGlbNodes(d,m,wrong),/node set/);
    const duplicate=structuredClone(j);duplicate.nodes[1].name=duplicate.nodes[0].name;
    assert.throws(()=>checkGlbNodes(d,m,duplicate),/node set/);
    const metadata=structuredClone(j);metadata.nodes[0].extras.assembly_revision='B9';
    assert.throws(()=>checkGlbNodes(d,m,metadata),/identity/);
    const manifest=structuredClone(m);manifest.parts.splice(0,1);
    assert.throws(()=>checkAssetManifest(d,manifest),/subset/);
  });
}
test('reference arrangement uses exactly 21 actual meshes; no U02 copies',()=>{
  const rows=[];
  for(const i of example.instances){
    const {d,m,bytes}=fixtures.find(f=>f.d.id===i.definition_id);
    const j=inspectGlb(bytes);
    for(const p of checkGlbNodes(d,m,j)){
      const node=j.nodes.find(n=>n.name===p.glb_node);
      const actual=bounds(vertices(bytes,j,node).map(v=>transform(v,i)));
      close(actual,placedBounds(p.bounds_m,i));
      rows.push({id:i.id,name:p.glb_node,actual});
    }
  }
  assert.equal(rows.length,21);
  assert.equal(rows.filter(r=>r.name.startsWith('U02_')).length,0);
  assert.equal(new Set(rows.map(r=>r.id+'/'+r.name)).size,21);
  close(bounds(rows.flatMap(r=>[r.actual.slice(0,3),r.actual.slice(3)])),
    [-6,0,-.075,6,2.35,.174]);
  const left=rows.find(r=>r.id==='F01'&&r.name==='U01_Post_001');
  const right=rows.find(r=>r.id==='F02'&&r.name==='U01_Post_001');
  close(right.actual.map((v,k)=>v-left.actual[k]),[7.05,0,0,7.05,0,0]);
});
test('two display anchors coincide for all four global orientations',()=>{
  for(let q=0;q<4;q++){
    const a=structuredClone(example);
    for(const i of a.instances){i.translation_m=rotate(i.translation_m,q);i.yaw_quarters=q}
    for(const connection of a.connections){
      const port=e=>{
        const i=a.instances.find(i=>i.id===e.instance_id),d=c.definitions.find(d=>d.id===i.definition_id);
        const p=d.ports[e.port],expected=worldPort(c,i,e.port);
        const actual=transform(toDisplay(p.point_m),i);
        close(actual,toDisplay(expected.point_m),1e-9);
        return actual;
      };
      close(port(connection.a),port(connection.b),1e-9);
    }
  }
});
