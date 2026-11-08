import {mkdirSync,writeFileSync,readFileSync,readdirSync} from 'node:fs';
import {execFileSync,spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {join} from 'node:path';
const out=process.argv[2]||'verification-evidence';mkdirSync(out,{recursive:true});
const sha=x=>createHash('sha256').update(x).digest('hex');
const manifest={head:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),tree:execFileSync('git',['rev-parse','HEAD^{tree}'],{encoding:'utf8'}).trim(),started_at:new Date().toISOString(),node:process.version,commands:[],files:{}};
for(const args of [['--test',...readdirSync('tests').filter(x=>x.endsWith('.test.mjs')).map(x=>'tests/'+x)],['scripts/verification-register.mjs'],['scripts/verification-register.mjs','search','OBS-0002'],['scripts/design-register.mjs'],['scripts/build-site.mjs']]){const x=spawnSync('node',args,{encoding:'utf8'}),log=`command-${manifest.commands.length+1}.log`,body=(x.stdout||'')+(x.stderr||'');writeFileSync(join(out,log),body);manifest.commands.push({args,exit:x.status,signal:x.signal,log,sha256:sha(body)});}
for(const p of execFileSync('git',['ls-files'],{encoding:'utf8'}).trim().split('\n'))manifest.files[p]=sha(readFileSync(p));manifest.completed_at=new Date().toISOString();writeFileSync(join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');if(manifest.commands.some(x=>x.exit!==0))process.exitCode=1;
