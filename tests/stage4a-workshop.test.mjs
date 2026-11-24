import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {editAssembly,createWorkshopSession,displayPlacement} from '../assembly/stage4a/workshop.mjs';
import {worldPort,loadAssembly,saveAssembly} from '../assembly/stage4a/contract.mjs';

const data = name => readFile(new URL('../assembly/stage4a/'+name,import.meta.url),'utf8').then(JSON.parse);
const c = await data('catalog.json'), example = await data('example.json');
const a = {instance_id:'F01',port:'right'}, b = {instance_id:'G01',port:'left'};
const add = (id='F03') => ({kind:'add',id,definition_id:'PAL-U01',translation_m:[10,0,0],yaw_quarters:0});
const disconnect = s => editAssembly(c,s,{kind:'disconnect',a,b});
const edit = (s,op) => editAssembly(c,s,op);

test('representative 3 placements / 2 connections and no mutation',async()=>{
  const s = await edit(example,add());
  assert.equal(s.instances.length,4);
  assert.equal(s.connections.length,2);
  assert.equal(s.instances[3].revision,'B0');
  assert.equal(example.instances.length,3);
  assert.deepEqual(s.instances.slice(0,3),example.instances);
});
test('same part instances independently editable',async()=>{
  const s = await edit(await edit(example,add()),{kind:'move',id:'F03',translation_m:[12,2,1]});
  assert.deepEqual(s.instances[3].translation_m,[12,2,1]);
  assert.deepEqual(s.instances[0],example.instances[0]);
  assert.deepEqual(s.instances[2],example.instances[2]);
});
test('coordinate conversion and positive CAD yaw',()=>{
  assert.deepEqual(displayPlacement({translation_m:[2,3,4],yaw_quarters:1}),{position:[2,4,-3],yaw:Math.PI/2});
  assert.deepEqual(displayPlacement(example.instances[0]),{position:[-3.525,0,0],yaw:0});
});
test('reject connected displacement',async()=>{
  await assert.rejects(edit(example,{kind:'move',id:'F01',translation_m:[0,0,0]}),/misaligned/);
});
test('reject connected rotation',async()=>{
  await assert.rejects(edit(example,{kind:'rotate',id:'F01',yaw_quarters:1}),/misaligned/);
});
test('disconnect reverse endpoints then rotate and move',async()=>{
  let s = await edit(example,{kind:'disconnect',a:b,b:a});
  s = await edit(s,{kind:'rotate',id:'F01',yaw_quarters:1});
  s = await edit(s,{kind:'move',id:'F01',translation_m:[2,3,4]});
  assert.equal(s.connections.length,1);
  assert.equal(s.instances[0].yaw_quarters,1);
  assert.deepEqual(s.instances[0].translation_m,[2,3,4]);
});
test('reject deleting connected part, allow disconnected deletion',async()=>{
  await assert.rejects(edit(example,{kind:'remove',id:'F01'}),/disconnect/);
  const s = await edit(await disconnect(example),{kind:'remove',id:'F01'});
  assert.equal(s.instances.length,2);
});
test('reject duplicate id and unknown part',async()=>{
  await assert.rejects(edit(example,add('F01')),/duplicate/);
  await assert.rejects(edit(example,{...add(),definition_id:'unknown'}),/unknown/);
});
test('reject invalid transform and extra field',async()=>{
  await assert.rejects(edit(example,{...add(),yaw_quarters:4}));
  await assert.rejects(edit(example,{...add(),translation_m:[0,0,10001]}));
  await assert.rejects(edit(example,{...add(),scale:2}),/fields/);
});
test('reconnect aligned ports',async()=>{
  const s = await edit(await disconnect(example),{kind:'connect',a,b});
  assert.equal(s.connections.length,2);
});
test('align-connect moves only disconnected part and exact anchors coincide',async()=>{
  let s = await disconnect(example);
  s = await edit(s,{kind:'move',id:'F01',translation_m:[-20,1,1]});
  s = await edit(s,{kind:'align-connect',a:b,b:a});
  assert.deepEqual(s.instances[0].translation_m,[-3.525,0,0]);
  const p=worldPort(c,s.instances[0],'right').point_m;
  const q=worldPort(c,s.instances[1],'left').point_m;
  assert.ok(p.every((v,i)=>Math.abs(v-q[i])<=1e-9));
  assert.deepEqual(s.instances[1],example.instances[1]);
});
test('reject occupied ports, incompatible direction and missing connection',async()=>{
  await assert.rejects(edit(example,{kind:'connect',a,b}),/already connected/);
  await assert.rejects(edit(example,{kind:'align-connect',a,b}),/disconnected/);
  await assert.rejects(edit(await disconnect(example),{kind:'disconnect',a,b}),/unknown connection/);
  const s=await disconnect(example);
  await assert.rejects(edit(s,{kind:'align-connect',a:b,b:{instance_id:'F01',port:'left'}}),/incompatible/);
});
test('edited v2 design round trips',async()=>{
  const s=await edit(example,add());
  assert.deepEqual(await loadAssembly(c,await saveAssembly(c,s)),s);
});
test('invalid load and asset preparation failure retain last valid state',async()=>{
  const session=createWorkshopSession(c,example);
  await session.ready;
  await assert.rejects(session.load('{"schema_version":1}'));
  await assert.rejects(session.edit(add(),async()=>{throw Error('asset missing');}),/asset missing/);
  assert.deepEqual(session.snapshot(),example);
});
test('delayed older preparation cannot overwrite new successful request',async()=>{
  const session=createWorkshopSession(c,example);
  await session.ready;
  let release,entered;
  const waiting=new Promise(r=>release=r), start=new Promise(r=>entered=r);
  const old=session.edit(add('OLD'),async()=>{entered();await waiting;return 'old';});
  await start;
  const fresh=await session.edit(add('NEW'),async()=> 'new');
  release();
  assert.equal(fresh.status,'APPLIED');
  assert.equal(fresh.staged,'new');
  assert.equal((await old).status,'STALE');
  assert.equal(session.snapshot().instances.at(-1).id,'NEW');
});
test('stale failed load cannot change state; save snapshots are independent',async()=>{
  const session=createWorkshopSession(c,example);
  await session.ready;
  let release,entered;
  const waiting=new Promise(r=>release=r), start=new Promise(r=>entered=r);
  const old=session.edit(add('OLD'),async()=>{entered();await waiting;throw Error('late');});
  await start;
  await session.edit(add('NEW'));
  release();
  assert.equal((await old).status,'STALE');
  const s=session.snapshot();s.instances.pop();
  assert.equal((await loadAssembly(c,await session.save())).instances.length,4);
});
