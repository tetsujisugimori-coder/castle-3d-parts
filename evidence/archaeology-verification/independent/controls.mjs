import {load,validate} from './scripts/verification-register.mjs';
const outputs=[];
for(const [name,mutate] of [
 ['duplicate_OBS_missing_OBS2',r=>{let d=structuredClone(r[0].data);d.id=r[1].data.id;r[1].data=d;}],
 ['overwrite_original_summary',r=>{r[0].data.summary='発掘で高さ2mの木柵柱5本を確認した';}],
 ['same_revision_different_reason',r=>{r[0].data.change_reason='別の結論へ変更';}],
 ]){const r=structuredClone(load());mutate(r);try{validate(r);outputs.push({name,accepted:true});}catch(e){outputs.push({name,accepted:false,error:e.message});}}
console.log(JSON.stringify(outputs,null,2));
