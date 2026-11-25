import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createWorkshopController,nextPlacement,translationFromFields,portOptions} from '../assembly/stage4a/workshop-ui.mjs';

const data=async name=>JSON.parse(await readFile(new URL('../assembly/stage4a/'+name,import.meta.url),'utf8'));
const catalog=await data('catalog.json'),example=await data('example.json'),raw=JSON.stringify(example);
const add=()=>nextPlacement(example,'PAL-U01');
const fixture=({prepare=async a=>a,publish=()=>{}}={})=>createWorkshopController({catalog,prepare,publish});

test('UI placement picks unused id and distinct initial x',()=>{
  const a=structuredClone(example);
  a.instances.push({...a.instances[0],id:'P1'});
  const op=nextPlacement(a,'PAL-U01');
  assert.equal(op.id,'P2');assert.equal(op.definition_id,'PAL-U01');
  assert.ok(Math.abs(op.translation_m[0]-9.525)<=1e-9);
  a.instances[0].translation_m[0]=9999;
  assert.throws(()=>nextPlacement(a,'PAL-U01'),/上限/);
});
test('coordinate inputs accept finite signed decimals; reject blank, nonfinite and out-of-range',()=>{
  assert.deepEqual(translationFromFields(['-3.525','0','1.25']),[-3.525,0,1.25]);
  for(const v of ['', '  ','Infinity','NaN','10001','-10001'])
    assert.throws(()=>translationFromFields([v,'0','0']),/座標/);
  assert.throws(()=>translationFromFields(['1','2']),/座標/);
});
test('port choices preserve identity and occupied ports',()=>{
  const ports=portOptions(catalog,example);
  assert.equal(ports.length,6);assert.equal(ports.filter(p=>p.occupied).length,4);
  assert.deepEqual(ports.filter(p=>!p.occupied).map(p=>p.endpoint),[
    {instance_id:'F01',port:'left'},{instance_id:'F02',port:'right'}
  ]);
  const a=structuredClone(example);
  a.connections=a.connections.map(c=>({a:{port:c.a.port,instance_id:c.a.instance_id},b:{port:c.b.port,instance_id:c.b.instance_id}}));
  assert.deepEqual(portOptions(catalog,a),ports);
});
test('controller initializes, edits, publishes then saves v2',async()=>{
  let published;
  const c=fixture({publish:(view,a)=>{assert.deepEqual(view,a);published=a}});
  assert.equal(c.snapshot(),null);
  await c.load(raw);
  assert.deepEqual(c.snapshot(),example);
  const next=await c.edit(add());
  assert.equal(next.instances.length,4);assert.deepEqual(published,next);
  assert.deepEqual(JSON.parse(await c.save()),next);
  next.instances.pop();assert.equal(c.snapshot().instances.length,4);
});
test('invalid JSON and invalid connected edit never prepare or publish',async()=>{
  let prepared=0,published=0;
  const c=fixture({prepare:async a=>{prepared++;return a},publish:()=>published++});
  await c.load(raw);
  await assert.rejects(c.load('{"schema_version":1}'));
  await assert.rejects(c.edit({kind:'move',id:'F01',translation_m:[0,0,0]}),/misaligned/);
  assert.equal(prepared,1);assert.equal(published,1);
  assert.deepEqual(c.snapshot(),example);
});
test('failed GLB preparation retains previous design and does not publish',async()=>{
  let published=0,fail=false;
  const c=fixture({prepare:async a=>{if(fail)throw Error('asset failure');return a},publish:()=>published++});
  await c.load(raw);fail=true;
  await assert.rejects(c.edit(add()),/asset failure/);
  assert.equal(published,1);assert.deepEqual(c.snapshot(),example);
  fail=false;assert.equal((await c.edit(add())).instances.length,4);
});
test('failed synchronous scene publication does not commit design',async()=>{
  let fail=false,visible=null;
  const c=fixture({publish:(_,a)=>{if(fail)throw Error('render failure');visible=a}});
  await c.load(raw);fail=true;
  await assert.rejects(c.edit(add()),/render failure/);
  assert.deepEqual(c.snapshot(),example);assert.deepEqual(visible,example);
});
test('overlapping edits are refused; first operation is preserved',async()=>{
  let release,entered;
  const wait=new Promise(r=>release=r),start=new Promise(r=>entered=r);
  let hold=false;
  const c=fixture({prepare:async a=>{if(hold){entered();await wait}return a}});
  await c.load(raw);hold=true;
  const pending=c.edit(add());await start;
  assert.equal(c.busy,true);
  await assert.rejects(c.load(raw),/operation in progress/);
  assert.throws(()=>c.save(),/not ready/);
  release();await pending;
  assert.equal(c.busy,false);assert.equal(c.snapshot().instances.length,4);
});
test('context-loss stop rejects in-flight preparation and all later edits',async()=>{
  let release,entered,hold=false,published=0;
  const wait=new Promise(r=>release=r),start=new Promise(r=>entered=r);
  const c=fixture({prepare:async a=>{if(hold){entered();await wait}return a},publish:()=>published++});
  await c.load(raw);hold=true;
  const pending=c.edit(add());await start;c.stop();release();
  await assert.rejects(pending,/stopped/);
  await assert.rejects(c.load(raw),/stopped/);
  assert.equal(published,1);assert.deepEqual(c.snapshot(),example);
});
test('initial prepare failure leaves no valid design and permits retry',async()=>{
  let fail=true;
  const c=fixture({prepare:async a=>{if(fail)throw Error('asset failure');return a}});
  await assert.rejects(c.load(raw),/asset failure/);
  assert.equal(c.snapshot(),null);
  fail=false;await c.load(raw);assert.deepEqual(c.snapshot(),example);
});
