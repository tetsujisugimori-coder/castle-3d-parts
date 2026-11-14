import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createStateHistory, restoreStateHistory} from '../site/stage3c/history.mjs';
const model=JSON.parse(readFileSync('cad/stage3c/generated/manifest.json'));
const pose=(angle,bolt)=>({angle,bolt});
test('lock, unlock and door operations reverse and replay exact states',()=>{
 const h=createStateHistory(model);const states=[pose(0,.07),pose(0,.14),pose(0,0),pose(45,0),pose(90,0)];
 for(const s of states)h.apply({type:s.bolt!==h.state.bolt?'bolt':'angle',value:s.bolt!==h.state.bolt?s.bolt:s.angle});
 for(const s of [...states.slice(0,-1).reverse(),pose(0,0)])assert.deepEqual(h.undo(),s);
 for(const s of states)assert.deepEqual(h.redo(),s);
});
test('rejected operations and no-op retain state, past and future',()=>{
 const h=createStateHistory(model);h.apply({type:'angle',value:45});h.undo();
 for(const action of [{type:'angle',value:NaN},{type:'angle',value:91},{type:'bolt',value:-1},{type:'bolt',value:true},{type:'reset',value:0}]){
  const before=h.inspect();assert.throws(()=>h.apply(action));assert.deepEqual(h.inspect(),before);
 }
 h.apply({type:'angle',value:0});assert.deepEqual(h.redo(),pose(45,0));
 h.apply({type:'bolt',value:0});const before=h.inspect();assert.throws(()=>h.apply({type:'bolt',value:.14}));assert.deepEqual(h.inspect(),before);
});
test('partial and locked bolt forbid door movement without consuming history',()=>{
 for(const bolt of [.001,.07,.14]){const h=createStateHistory(model);h.apply({type:'bolt',value:bolt});const before=h.inspect();assert.throws(()=>h.apply({type:'angle',value:.1}));assert.deepEqual(h.inspect(),before)}
});
test('new operation after undo drops redo; returned objects cannot poison stacks',()=>{
 const h=createStateHistory(model);h.apply({type:'angle',value:45});h.undo();h.apply({type:'bolt',value:.14});assert.equal(h.canRedo,false);assert.deepEqual(h.redo(),pose(0,.14));
 const external=h.state;external.angle=90;const audit=h.inspect();audit.past[0].bolt=999;assert.deepEqual(h.state,pose(0,.14));assert.deepEqual(h.undo(),pose(0,0));
});
test('100 undo redo cycles preserve geometry state contract',()=>{
 const h=createStateHistory(model);h.apply({type:'bolt',value:.14});for(let i=0;i<100;i++){assert.deepEqual(h.undo(),pose(0,0));assert.deepEqual(h.redo(),pose(0,.14))}
});
test('snapshot stores validated state, reopen starts with empty history',()=>{
 const h=createStateHistory(model);h.apply({type:'bolt',value:.14});const saved=h.serialize();const loaded=restoreStateHistory(model,saved);
 assert.deepEqual(loaded.state,h.state);assert.equal(loaded.canUndo,false);assert.equal(loaded.canRedo,false);assert.deepEqual(loaded.undo(),h.state);
 for(const state of [pose(45,.14),pose(91,0),pose(0,-1),pose(true,0)])assert.throws(()=>restoreStateHistory(model,JSON.stringify({schema_version:1,state})));
 assert.throws(()=>restoreStateHistory(model,JSON.stringify({schema_version:1,state:pose(0,0),past:[pose(45,.14)]})));
 assert.throws(()=>restoreStateHistory(model,'not json'));
});
test('initial invalid and mutable model contracts fail closed',()=>{
 assert.throws(()=>createStateHistory(model,pose(45,.14)));const m=structuredClone(model),h=createStateHistory(m);m.bolt.lock_m=999;assert.throws(()=>h.apply({type:'bolt',value:999}));assert.deepEqual(h.state,pose(0,0));
});
