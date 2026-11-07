// CI/local evidence capture. Failure is never converted to PASS; old evidence is not overwritten.
import {mkdirSync,readFileSync,writeFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const dir=process.argv[2];if(!dir||existsSync(dir))throw Error('NEW_OUTPUT_DIRECTORY_REQUIRED');mkdirSync(dir,{recursive:true});
const git=(...args)=>{const r=spawnSync('git',args,{encoding:'utf8'});if(r.status!==0)throw Error(r.stderr);return r.stdout.trim()};
const files=git('ls-files','-z').split('\0').filter(Boolean);
const manifest=Object.fromEntries(files.map(p=>[p,createHash('sha256').update(readFileSync(p)).digest('hex')]));
const result={started_at:new Date().toISOString(),head:git('rev-parse','HEAD'),tree:git('rev-parse','HEAD^{tree}'),dirty:git('status','--porcelain'),node:process.version,platform:process.platform,source_sha256:manifest,commands:[],scope:'Software structure/provenance checks, not archaeological proof; no browser or physical device run'};
for(const args of [['scripts/source-register.mjs'],['scripts/observation-register.mjs'],['--test'],['scripts/build-site.mjs']]){
 const r=spawnSync(process.execPath,args,{encoding:'utf8',maxBuffer:16*1024*1024});const name=`command-${result.commands.length+1}`;
 writeFileSync(join(dir,`${name}.stdout.txt`),r.stdout??'');writeFileSync(join(dir,`${name}.stderr.txt`),r.stderr??'');
 result.commands.push({args,exit_code:r.status,signal:r.signal,error:r.error?.message??null,stdout_sha256:createHash('sha256').update(r.stdout??'').digest('hex'),stderr_sha256:createHash('sha256').update(r.stderr??'').digest('hex')});
}
result.finished_at=new Date().toISOString();result.status=result.commands.every(x=>x.exit_code===0&&!x.error)?'PASS':'FAIL';
writeFileSync(join(dir,'result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,head:result.head,tree:result.tree,output:dir}));if(result.status!=='PASS')process.exitCode=1;
