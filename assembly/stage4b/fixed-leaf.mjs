import {loadAssembly} from '../stage4a/contract.mjs';

/** Strict fixed-example contract. User-edited workshop designs still use the generic v2 contract. */
export async function validateFixedLeaf(catalog,text){
 const a=await loadAssembly(catalog,text);
 if(a.instances.length!==8||a.connections.length!==0)throw Error('wrong fixed occurrence/contact count');
 const byId=new Map(a.instances.map(i=>[i.id,i]));
 const expected=[
  ...Array.from({length:6},(_,i)=>['B0'+(i+1),'BOARD',[i*290,0,0]]),
  ['R01','RAIL',[-65,130,400]],['R02','RAIL',[-65,130,2100]],
 ];
 for(const [id,kind,at] of expected){
  const i=byId.get(id);
  if(!i||i.definition_id!=='YAM-WEST-LEFT-'+kind||i.revision!=='D0'||i.pose!==null||i.yaw_quarters!==0)
   throw Error('wrong fixed occurrence: '+id);
  if(at.some((mm,k)=>i.translation_m[k]!==mm/1000))throw Error('wrong fixed placement: '+id);
 }
 return a;
}
