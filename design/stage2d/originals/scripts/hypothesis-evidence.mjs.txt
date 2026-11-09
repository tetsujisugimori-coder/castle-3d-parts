// Capture actual commands, nonzero exits, fixed source hashes and immutable-history checks.
import {mkdirSync,existsSync,readFileSync,writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';import {createHash} from 'node:crypto';import {join} from 'node:path';
import {canonical} from './hypothesis-register.mjs';
const out=process.argv[2];if(!out||existsSync(out))throw Error('NEW_OUTPUT_DIRECTORY_REQUIRED');mkdirSync(out,{recursive:true});
const run=(cmd,args)=>spawnSync(cmd,args,{encoding:'utf8',maxBuffer:32*1024*1024});
const git=(...args)=>{const r=run('git',args);if(r.status!==0)throw Error(r.stderr);return r.stdout.trim()};
const sha=b=>createHash('sha256').update(b).digest('hex');
const files=git('ls-files','-z').split('\0').filter(Boolean);
const result={started_at:new Date().toISOString(),head:git('rev-parse','HEAD'),tree:git('rev-parse','HEAD^{tree}'),node:process.version,platform:process.platform,commands:[],preservation:null,source_sha256:Object.fromEntries(files.map(f=>[f,sha(readFileSync(f))])),scope:'Software/reference validation; not archaeological proof; no physical device, CAD, or browser testing'};
const baseline=JSON.parse(readFileSync('research/baseline.json','utf8'));
try {
 const entries=git('ls-tree','-r',baseline.commit).split('\n').filter(Boolean).map(l=>{const m=l.match(/^\d+ blob ([a-f0-9]+)\t(.*)$/);if(!m)throw Error('BASE_TREE_ENTRY');return [m[2],m[1]]});
 if(canonical(Object.fromEntries(entries))!==canonical(baseline.files))throw Error('BASELINE_MANIFEST_MISMATCH');
 for(const [p,h] of entries){const b=readFileSync(p);if(createHash('sha1').update(`blob ${b.length}\0`).update(b).digest('hex')!==h)throw Error(`BASELINE_CHANGED ${p}`)}
 const base=process.env.PR_BASE_SHA;
 if(base){if(!/^[a-f0-9]{40}$/.test(base))throw Error('BASE_SHA');const tree=git('ls-tree','-r','--name-only',base);if(tree.split('\n').includes('research/history/records.json')){const old=JSON.parse(git('show',`${base}:research/history/records.json`)),now=JSON.parse(readFileSync('research/history/records.json','utf8'));for(const r of old)if(!now.some(x=>canonical(x)===canonical(r)))throw Error('HISTORY_CHANGED_OR_REMOVED')}}
 result.preservation={status:'PASS',baseline_commit:baseline.commit,files:entries.length,pr_base:base??null};
}catch(e){result.preservation={status:'FAIL',error:e.message}}
for(const args of [['scripts/source-register.mjs'],['scripts/observation-register.mjs'],['scripts/hypothesis-register.mjs'],['--test'],['scripts/hypothesis-red-green.mjs'],['scripts/build-site.mjs']]){
 const r=run(process.execPath,args),n=`command-${result.commands.length+1}`;writeFileSync(join(out,n+'.stdout.txt'),r.stdout??'');writeFileSync(join(out,n+'.stderr.txt'),r.stderr??'');result.commands.push({args,exit_code:r.status,signal:r.signal,error:r.error?.message??null,stdout_sha256:sha(r.stdout??''),stderr_sha256:sha(r.stderr??'')});
}
result.status=result.preservation.status==='PASS'&&result.commands.length===6&&result.commands.every(x=>x.exit_code===0&&!x.error)?'PASS':'FAIL';result.finished_at=new Date().toISOString();
writeFileSync(join(out,'result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,head:result.head,tree:result.tree}));if(result.status!=='PASS')process.exitCode=1;
