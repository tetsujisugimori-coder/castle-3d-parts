import {transition,validateLock} from './contract.mjs';

// Document-local history. Only validated states are stored; saved snapshots never
// import undo/redo entries. Animation frames may be grouped into one operation.
export function createStateHistory(model, initial={angle:0,bolt:0}) {
 const m=structuredClone(model);validateLock(m);
 const copy=s=>({angle:s.angle,bolt:s.bolt});
 const valid=s=>{if(!s||Object.keys(s).sort().join(',')!=='angle,bolt')throw Error('Invalid state keys');transition(m,s,{type:'angle',value:s.angle});return copy(s)};
 const same=(a,b)=>a.angle===b.angle&&a.bolt===b.bolt;
 let state=valid(initial),past=[],future=[],gesture=null;
 function end(){if(gesture&&!same(state,gesture)){past.push(copy(gesture));future=[]}gesture=null;return copy(state)}
 return {
  get state(){return copy(state)},
  get canUndo(){return past.length>0||!!gesture&&!same(state,gesture)},
  get canRedo(){return future.length>0&&(!gesture||same(state,gesture))},
  begin(){end();gesture=copy(state)},end,
  apply(action){const next=valid(transition(m,state,action));if(same(next,state))return copy(state);if(!gesture){past.push(copy(state));future=[]}state=next;return copy(state)},
  undo(){end();if(!past.length)return copy(state);const next=valid(past.at(-1));future.push(copy(state));past.pop();state=next;return copy(state)},
  redo(){end();if(!future.length)return copy(state);const next=valid(future.at(-1));past.push(copy(state));future.pop();state=next;return copy(state)},
  serialize(){return JSON.stringify({schema_version:1,state:valid(state)})},
  inspect(){return {state:copy(state),past:past.map(copy),future:future.map(copy),gesture:gesture&&copy(gesture)}}
 };
}

export function restoreStateHistory(model,text){
 const saved=JSON.parse(text);
 if(!saved||Object.keys(saved).sort().join(',')!=='schema_version,state'||saved.schema_version!==1)throw Error('Unsupported saved state; history is not persistent');
 return createStateHistory(model,saved.state);
}
