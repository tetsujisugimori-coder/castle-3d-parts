// UI transaction boundary: validate -> prepare GLB -> synchronous publish -> commit.
import {loadAssembly,saveAssembly} from './contract.mjs';
import {canonicalJson} from './json-data.mjs';
import {editAssembly} from './workshop.mjs';
const clone=x=>JSON.parse(canonicalJson(x));
const check=(ok,msg)=>{if(!ok)throw Error(msg)};
export const MAX_IMPORT_BYTES=4_000_000;

export function nextPlacement(assembly,definitionId){
  let n=1;
  const ids=new Set(assembly.instances.map(i=>i.id));
  while(ids.has('P'+n))n++;
  const x=Math.max(0,...assembly.instances.map(i=>i.translation_m[0]))+6;
  check(x<=10000,'新規配置の座標上限です。既存部品を移動してください。');
  return {kind:'add',id:'P'+n,definition_id:definitionId,translation_m:[x,0,0],yaw_quarters:0};
}
export function translationFromFields(values){
  check(Array.isArray(values)&&values.length===3&&values.every(v=>
    typeof v==='string'&&v.trim()!==''&&Number.isFinite(Number(v))&&Math.abs(Number(v))<=10000),
    'X・Y・Zに有効なメートル座標を入力してください。');
  return values.map(Number);
}
export function portOptions(catalog,assembly){
  return assembly.instances.flatMap(i=>{
    const d=catalog.definitions.find(d=>d.id===i.definition_id);
    check(d,'unknown definition');
    return Object.keys(d.ports).map(port=>{
      const endpoint={instance_id:i.id,port};
      // Key order must not affect occupancy.
      const occupied=assembly.connections.some(c=>[c.a,c.b].some(e=>e.instance_id===i.id&&e.port===port));
      return {endpoint,key:JSON.stringify(endpoint),occupied};
    });
  });
}
export function createWorkshopController({catalog,prepare,publish}){
  const c=clone(catalog);
  let current=null,busy=false,stopped=false;
  const snapshot=()=>current?clone(current):null;
  async function apply(produce){
    check(!stopped,'workshop stopped');
    check(!busy,'operation in progress');
    busy=true;
    try{
      const next=await produce();
      check(!stopped,'workshop stopped');
      const staged=await prepare(clone(next));
      check(!stopped,'workshop stopped');
      // publish is synchronous. It must restore the previous view if it throws.
      publish(staged,clone(next));
      current=next;
      return snapshot();
    }finally{busy=false;}
  }
  return {
    snapshot,
    get busy(){return busy;},
    stop(){stopped=true;},
    load(text){return apply(()=>loadAssembly(c,text));},
    edit(command){
      const op=clone(command);
      return apply(()=>{check(current,'design not loaded');return editAssembly(c,current,op);});
    },
    save(){
      check(!stopped&&!busy&&current,'design not ready');
      return saveAssembly(c,snapshot());
    }
  };
}
