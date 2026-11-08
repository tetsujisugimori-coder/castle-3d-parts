import {ROOT,preserve,validateCandidate,verifyExecution,hash,part,BASE} from './research-cad.mjs';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {execFileSync} from 'node:child_process';
const out=resolve(process.argv[2]??'/tmp/research-cad-evidence');mkdirSync(out,{recursive:true});const reports=[];
for(const name of ['proposed','approved','rejected','deferred','applied']){const c=JSON.parse(readFileSync(resolve(ROOT,`evidence/stage2a/demo/${name}.json`)));validateCandidate(c,ROOT,true);reports.push({name,id:c.id,sha256:c.sha256,status:c.status});}
const applied=JSON.parse(readFileSync(resolve(ROOT,'evidence/stage2a/demo/applied.json'))),proof=applied.events.at(-1).manifest;const run=verifyExecution(applied,proof);
const source=execFileSync('git',['ls-files','-z'],{cwd:ROOT}).toString().split('\0').filter(Boolean);const hashes=Object.fromEntries(source.map(p=>[p,hash(readFileSync(resolve(ROOT,p)))]));
const result={status:'PASS',base:BASE,head:execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT}).toString().trim(),preserved:preserve(),candidates:reports,actual_run_manifest:proof,actual_software:{freecad:run.freecad.software,blender:run.blender.version},note:'This CI verifies committed real-run artifacts. It does not itself execute FreeCAD or Blender.',source_hashes:hashes};
writeFileSync(resolve(out,'verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,preserved:result.preserved,candidates:reports.length}));
