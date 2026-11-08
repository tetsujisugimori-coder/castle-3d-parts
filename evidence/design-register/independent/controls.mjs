const {load,validate,cadRead}=await import(process.env.REVIEW_MODULE || '../../../scripts/design-register.mjs');
const cases=[
 ['initial_reason_rewritten',r=>{r[0].data.reason='歴史上確定したため正式採用。'}],
 ['initial_author_rewritten',r=>{r[0].data.author='別の判断担当者'}],
 ['initial_time_rewritten',r=>{r[0].data.created_at='2020-01-01T00:00:00Z'}],
 ['history_bypass_via_argument',r=>{r.shift()}]
];
const results=cases.map(([name,mutate])=>{const r=structuredClone(load());mutate(r);try{if(name==='history_bypass_via_argument')validate(r,{decisions:{}});else validate(r);return {name,rejected:false,error:null}}catch(e){return {name,rejected:true,error:e.message}}});
const r=structuredClone(load());r[0].data.reason='変更履歴なしに初版を改変';try{cadRead(r);results.push({name:'reader_accepts_rewritten_history',rejected:false})}catch(e){results.push({name:'reader_accepts_rewritten_history',rejected:true,error:e.message})}
console.log(JSON.stringify(results,null,2));process.exitCode=results.every(r=>r.rejected)?0:1;
