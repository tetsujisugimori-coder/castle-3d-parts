/** Explicit demonstration decisions, not historical adoption or production approval. */
import {snapshot,part,trace,propose,decide,application,preserve,writeNew,ROOT,BASE,hash,evidenceDiff} from './research-cad.mjs';
import {readFileSync,mkdirSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
const out=resolve(process.argv[2]??'evidence/stage2a/demo');
if(existsSync(out))throw Error('OUTPUT_EXISTS');mkdirSync(out,{recursive:true});
const s=snapshot(ROOT,BASE),p=part(),baseHashes=Object.fromEntries(p.artifacts.map(a=>[a.path,hash(readFileSync(resolve(ROOT,a.path)))]));
const c=propose(s,s,[{parameter:'post_height',proposed_value:2.2,unit:'m'}],'統合試験専用D値。史料の寸法・史実採用ではない。');
const meta={actor:'八兵衛（Stage 2-A 試作D統合試験）',at:'2026-11-08T12:15:00Z',reason:'依頼された実証ケース用。作業コピーのみ2.0mから2.2mへ変更。史実認定ではない。'};
const approved=decide(c,'approved',{...meta,id:'DEC-WORK-DEMO-0001'});
writeNew(resolve(out,'snapshot.json'),s);writeNew(resolve(out,'proposed.json'),c);writeNew(resolve(out,'approved.json'),approved);writeNew(resolve(out,'application.json'),application(approved));
const rejected=decide(c,'rejected',{...meta,id:'DEC-WORK-DEMO-0002',reason:'却下時の原本非変更を検証する試験。'}),deferred=decide(c,'deferred',{...meta,id:'DEC-WORK-DEMO-0003',reason:'保留時の原本非変更を検証する試験。'});
writeNew(resolve(out,'rejected.json'),rejected);writeNew(resolve(out,'deferred.json'),deferred);
const simulated=structuredClone(s);const h=simulated.records.find(r=>r.id==='HYP-0001');h.data.status='withdrawn';h.sha256=hash(JSON.stringify(h.data));
const report={scope:'integration_demo_only',basis:'D',formal_cad_adoption:false,cases:{case1:{status:'PASS',trace:trace(s,'site/cad/palisade.glb')},case2:{status:'PASS',simulation:true,note:'合成HYP撤回を差分検出関数へ入力。実研究台帳を改変せず、承認・適用APIには使用しない。',changes:evidenceDiff(s,simulated)},case3:{status:'READY_FOR_REAL_RUN',application:'application.json'},case4:{status:'NOT_TESTED',note:'cad-regenerate.pyの実結果を別manifestに記録'},case5:{status:'NOT_TESTED',note:'2回の実生成結果を別comparisonに記録'},case6:{status:'PASS',states:[rejected.status,deferred.status],hashes_unchanged:baseHashes}},original_files_preserved:preserve()};
for(const [path,sha]of Object.entries(baseHashes))if(hash(readFileSync(resolve(ROOT,path)))!==sha)throw Error('ORIGINAL_CHANGED');
writeNew(resolve(out,'cases.json'),report);
console.log(out);
