// Execute preserved browser contracts with platform-safe paths and Chromium sandbox.
// The exact adapted module, input hashes and built asset hashes are retained.
import {readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync, openSync, closeSync} from 'node:fs';
import {resolve, join, dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync, spawnSync} from 'node:child_process';

const [stage] = process.argv.slice(2);
if (!['stage3c','stage3b','stage3a','stage2d'].includes(stage)) throw Error('Unsupported browser contract');
const envName = stage.toUpperCase() + '_OUT';
if (!process.env[envName] || !process.env.PW_MODULE || !process.env.THREE_DIR) throw Error('Set output, PW_MODULE and THREE_DIR explicitly');
const out = resolve(process.env[envName]);
if (existsSync(out)) throw Error('Use a new browser evidence directory; originals are not overwritten');
mkdirSync(out, {recursive:true});
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const input = `scripts/${stage}-browser.mjs`;
let code = readFileSync(input, 'utf8');
const original = digest(code);
// Keep the original assertions and matrix. Only adapt dependencies, serving and launch.
code = code.replace("resolve,extname}", "resolve,extname,relative,isAbsolute}");
code = code.replaceAll("!p.startsWith(root+'/')", "(relative(root,p).startsWith('..')||isAbsolute(relative(root,p)))");
code = code.replaceAll("resolve('/tmp/castle2d-pw/node_modules/three',", "resolve(process.env.THREE_DIR,");
code = code.replaceAll("resolve('/tmp/castle2d-pw/node_modules/three/build/three.module.js')", "resolve(process.env.THREE_DIR,'build/three.module.js')");
code = code.replaceAll("['--no-sandbox','--enable-unsafe-swiftshader']", "['--enable-unsafe-swiftshader']");
// Playwright otherwise disables Chromium's sandbox by default even without that arg.
code = code.replaceAll(".launch({headless:true,", ".launch({chromiumSandbox:true,headless:true,");
code = code.replaceAll(".launch({headless:true}", ".launch({chromiumSandbox:true,headless:true}");
if (code.includes('--no-sandbox')) throw Error('Unadapted sandbox-disabling launch');
if (stage==='stage3c') {
  const historyChecks=`
await angle(p,0);
await p.locator('#lock').click();
const lockedPose=await p.locator('#pose-audit').textContent();
assert.equal(Number(await p.locator('#bolt-value').getAttribute('data-position')),.14);
await p.locator('#undo-state').click();assert.equal(Number(await p.locator('#bolt-value').getAttribute('data-position')),0);
await p.locator('#redo-state').click();assert.equal(await p.locator('#pose-audit').textContent(),lockedPose);
await p.locator('#open').click();assert.equal(await p.locator('#operation-reason').getAttribute('data-rejected'),'true');assert.equal(await p.locator('#pose-audit').textContent(),lockedPose);
await p.locator('#unlock').click();const unlockedPose=await p.locator('#pose-audit').textContent();
await p.locator('#undo-state').click();assert.equal(await p.locator('#pose-audit').textContent(),lockedPose);
await p.locator('#redo-state').click();assert.equal(await p.locator('#pose-audit').textContent(),unlockedPose);
await p.locator('#open').click();await p.waitForFunction(()=>Number(document.querySelector('#angle-value').dataset.angle)===90);
await p.locator('#undo-state').click();assert.equal(Number(await p.locator('#angle-value').getAttribute('data-angle')),0,'animated open is one operation');
await p.locator('#redo-state').click();assert.equal(Number(await p.locator('#angle-value').getAttribute('data-angle')),90);
await p.locator('#undo-state').click();await angle(p,45);assert(await p.locator('#redo-state').isDisabled(),'new state discards redo');
await p.locator('#undo-state').click();assert.equal(Number(await p.locator('#angle-value').getAttribute('data-angle')),0);
await p.locator('#redo-state').click();assert.equal(Number(await p.locator('#angle-value').getAttribute('data-angle')),45);
await p.reload();await p.waitForSelector('#status[data-loaded=true]');assert.equal(Number(await p.locator('#angle-value').getAttribute('data-angle')),0);assert.equal(Number(await p.locator('#bolt-value').getAttribute('data-position')),0);assert(await p.locator('#undo-state').isDisabled());assert(await p.locator('#redo-state').isDisabled());
row.checks.push('state Undo/Redo: lock, unlock, animated door, rejection, branch, reload and actual mesh bounds');
`;
  const historyAnchor="await p.locator('[data-pose=\"45\"]').click();await p.locator('#reset-view').click();";
  if(!code.includes(historyAnchor))throw Error('Stage3C history test anchor changed');
  code=code.replace(historyAnchor,historyChecks+historyAnchor);
  code=code.replace("assert(await p.locator('#open').isDisabled());row.status='PASS'", "assert(await p.locator('#open').isDisabled());row.rejection=await p.locator('#status').textContent();row.status='PASS'");

  code = code.replace("await p.locator('#reset-view').click();", "const beforeReset=await p.locator('#pose-audit').textContent();await p.locator('#reset-view').click();assert.equal(await p.locator('#pose-audit').textContent(),beforeReset,'camera Reset preserves mechanism state');");
  code = code.replace("const row={engine,fault,status:'FAIL'}", "const row={engine,fault,expected:'reject corrupted input and disable controls',status:'FAIL'}");
  code = code.replace("const p=await c.newPage(),bad=structuredClone(m);", "const p=await c.newPage();await c.tracing.start({screenshots:true,snapshots:true});const bad=structuredClone(m);");
  code = code.replace("rows.push(row);console.log(JSON.stringify(row));await c.close()}await b.close()", "await p.screenshot({path:`${out}/${engine}-fault-${fault}.png`,fullPage:true});await c.tracing.stop({path:`${out}/${engine}-fault-${fault}.zip`});rows.push(row);console.log(JSON.stringify(row));await c.close()}await b.close()");
}
// Legacy regressions retain their fixed normal matrix and add raw fault evidence.
if(stage==='stage3b') {
  function replaceOnce(before,after){if(!code.includes(before))throw Error('Stage3B contract changed: '+before.slice(0,90));code=code.replace(before,after)}
  replaceOnce("await p.goto(base+'stage3b/');await p.waitForSelector('#status[data-loaded=true]');", "await p.goto(base+'stage3b/');await p.waitForSelector('#status[data-loaded=true]');assert.equal(await p.locator('#bolt,#lock,#unlock,#lock-state,#undo-state,#redo-state').count(),0,'legacy Stage3B has no locking/history controls');");
  replaceOnce("row.checks.push('pause, reverse, reduced motion, resize');", "row.checks.push('pause, reverse, reduced motion, resize');await angle(p,45);await p.locator('#open').click();if(motion!=='reduce')assert.equal(await p.locator('#motion-state').getAttribute('data-running'),'true','hidden fault starts during active motion');else assert.equal(Number(await p.locator('#angle-value').getAttribute('data-angle')),90);await p.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});try{document.dispatchEvent(new Event('visibilitychange'))}finally{delete document.hidden}});assert.equal(await p.locator('#motion-state').getAttribute('data-running'),'false');assert.equal(await p.locator('#motion-state').getAttribute('data-reason'),'hidden');const hiddenAngle=await p.locator('#angle-value').getAttribute('data-angle');await p.waitForTimeout(120);assert.equal(await p.locator('#angle-value').getAttribute('data-angle'),hiddenAngle);row.checks.push('simulated visibilitychange/hidden stops without pose drift; physical tab lifecycle NOT_TESTED');");
  replaceOnce("await p.locator('#reset-view').click();await p.screenshot", "const mechanismBeforeCamera=await p.locator('#pose-audit').textContent();await p.locator('#reset-view').click();const resetCanvas=await p.locator('#viewport canvas').screenshot();await p.locator('#front').click();assert.notDeepEqual(await p.locator('#viewport canvas').screenshot(),resetCanvas,'front viewpoint changes rendered image');await p.locator('#reset-view').click();assert.deepEqual(await p.locator('#viewport canvas').screenshot(),resetCanvas,'camera reset restores rendered viewpoint');assert.equal(await p.locator('#pose-audit').textContent(),mechanismBeforeCamera,'camera reset leaves mechanism unchanged');row.checks.push('camera reset image restoration and no lock-mode mixing');await p.screenshot");
  replaceOnce("'projection-index','projection-hash']", "'projection-index','projection-hash','lost-context']");
  replaceOnce("await p.goto(base+'stage3b/');await p.waitForSelector('#status[data-error=true]');", "await p.goto(base+'stage3b/');if(fault==='lost-context'){await p.waitForSelector('#status[data-loaded=true]');await p.evaluate(()=>document.querySelector('canvas').dispatchEvent(new Event('webglcontextlost',{cancelable:true})))}await p.waitForSelector('#status[data-error=true]');");
  replaceOnce("const p=await c.newPage(),bad=structuredClone(m);", "const p=await c.newPage();await c.tracing.start({screenshots:true,snapshots:true});const bad=structuredClone(m);");
  replaceOnce("rows.push(row);console.log(JSON.stringify(row));await c.close()}await b.close()", "await p.screenshot({path:`${out}/${engine}-fault-${fault}.png`,fullPage:true});await c.tracing.stop({path:`${out}/${engine}-fault-${fault}.zip`});rows.push(row);console.log(JSON.stringify(row));await c.close()}await b.close()");
  code=code.replaceAll('21*engines.length','22*engines.length');
}
if(stage==='stage3a') {
  const before="const p=await c.newPage(),row={engine,fault,status:'FAIL'};try{";
  if(!code.includes(before))throw Error('Stage3A fault contract changed');
  code=code.replace(before,"const p=await c.newPage(),row={engine,fault,status:'FAIL'};await c.tracing.start({screenshots:true,snapshots:true});try{");
  const tail="catch(e){row.error=e.message}rows.push(row);console.log(JSON.stringify(row));await c.close()}";
  if(!code.includes(tail))throw Error('Stage3A fault close changed');
  code=code.replace(tail,"catch(e){row.error=e.message}await p.screenshot({path:`${out}/${engine}-fault-${fault}.png`,fullPage:true});await c.tracing.stop({path:`${out}/${engine}-fault-${fault}.zip`});rows.push(row);console.log(JSON.stringify(row));await c.close()}");
}

if (stage==='stage2d') {
  const researchReady="await p.goto(base+'research-cad/');await p.waitForSelector('#status');";
  if(!code.includes(researchReady))throw Error('Stage2D linked research viewer readiness contract changed');
  code=code.replace(researchReady,"await p.goto(base+'research-cad/');await p.waitForSelector('#status[data-loaded=true]');await p.waitForLoadState('networkidle');");

  // A pending held navigation can block the next action's prechecks. Inject the
  // race only in the fault control; normal selectOption coverage stays intact.
  const oldHelper="async function changeRevision(p,rev){await Promise.all([p.waitForEvent('framenavigated',f=>f===p.mainFrame()),p.selectOption('#revision',rev,{noWaitAfter:true})])}";
  const newHelper="async function changeRevisionDuringHeldResponse(p,rev){await Promise.all([p.waitForURL(u=>u.searchParams.get('revision')===rev,{waitUntil:'commit',timeout:30000}),p.locator('#revision').evaluate((el,value)=>{el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}))},rev)])}";
  if(!code.includes(oldHelper))throw Error('Stage2D navigation contract changed; review adaptation');
  code=newHelper+"\nasync function _bounded(p,label){let timer;try{return await Promise.race([p,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(label)),30000)})])}finally{clearTimeout(timer)}}\n"+code;
  const oldRace="await changeRevision(p,'B1');await began;await changeRevision(p,'B2');await ready(p,'B2');release();";
  if(!code.includes(oldRace))throw Error('Stage2D stale-response contract changed; review adaptation');
  code=code.replace(oldRace, "try{await changeRevisionDuringHeldResponse(p,'B1');await _bounded(began,'B1 held request not observed');await changeRevisionDuringHeldResponse(p,'B2');await ready(p,'B2')}finally{release()}");
  code=code.replace("const p=await c.newPage(),r={engine:name,fault,status:'FAIL'};try{", "const p=await c.newPage(),r={engine:name,fault,status:'FAIL'};await c.tracing.start({screenshots:true,snapshots:true});console.log(JSON.stringify({engine:name,fault,phase:'start'}));try{");
  const tail="rows.push(r);console.log(JSON.stringify(r));await c.close()}";
  if(!code.includes(tail))throw Error('Stage2D fault close changed');
  code=code.replace(tail,"await p.screenshot({path:`${out}/${name}-fault-${fault}.png`,fullPage:true});await c.tracing.stop({path:`${out}/${name}-fault-${fault}.zip`});rows.push(r);console.log(JSON.stringify(r));await c.close()}");
}
const buildAudit = `
const _buildFiles={};
function _walkBuild(dir){for(const e of _readBuildDir(dir,{withFileTypes:true})){const p=resolve(dir,e.name);if(e.isDirectory())_walkBuild(p);else _buildFiles[relative(resolve('dist'),p).replaceAll('\\\\','/')]=createHash('sha256').update(readFileSync(p)).digest('hex')}}
_walkBuild(resolve('dist'));writeFileSync(resolve(out,'build-hashes.json'),JSON.stringify(_buildFiles,null,2));
`;
code = "import {readdirSync as _readBuildDir} from 'node:fs';\n" + code.replace("const root=resolve('dist')", buildAudit + "\nconst root=resolve('dist')");
const executed = join(out,'executed-contract.mjs');
writeFileSync(executed,code);
const files = [...new Set([...execFileSync('git',['ls-files','-z']).toString().split('\0'),...execFileSync('git',['ls-files','--others','--exclude-standard','-z']).toString().split('\0')])].filter(Boolean);
const sources = Object.fromEntries(files.filter(p=>!p.startsWith('evidence/')).map(p=>[p,digest(readFileSync(p))]));
const dependencies={playwright:JSON.parse(readFileSync(resolve(dirname(process.env.PW_MODULE),'package.json'))).version,three:JSON.parse(readFileSync(resolve(process.env.THREE_DIR,'package.json'))).version};
const record = {stage,command:`node scripts/stage3c-browser-runtime.mjs ${stage}`,head:execFileSync('git',['rev-parse','HEAD']).toString().trim(),tree:execFileSync('git',['show','-s','--format=%T','HEAD']).toString().trim(),working_tree:execFileSync('git',['status','--porcelain']).toString(),original_contract_sha256:original,executed_contract_sha256:digest(code),runtime_sha256:digest(readFileSync('scripts/stage3c-browser-runtime.mjs')),sources,platform:process.platform,node:process.version,dependencies,sandbox:'chromiumSandbox:true; no --no-sandbox',started_at:new Date().toISOString()};
writeFileSync(join(out,'execution.json'),JSON.stringify(record,null,2));
const stdoutFd=openSync(join(out,'stdout.log'),'wx'),stderrFd=openSync(join(out,'stderr.log'),'wx');
let run;
try {run=spawnSync(process.execPath,[executed],{env:process.env,stdio:['ignore',stdoutFd,stderrFd]});}
finally {closeSync(stdoutFd);closeSync(stderrFd);}
Object.assign(record,{ended_at:new Date().toISOString(),exit_code:run.status,signal:run.signal,error:run.error?.message});
writeFileSync(join(out,'execution.json'),JSON.stringify(record,null,2));
const evidenceHashes={};
for(const entry of readdirSync(out,{withFileTypes:true}))if(entry.isFile()&&entry.name!=='sha256.json')evidenceHashes[entry.name]=digest(readFileSync(join(out,entry.name)));
writeFileSync(join(out,'sha256.json'),JSON.stringify(evidenceHashes,null,2));
console.log(JSON.stringify({stage,exit_code:run.status,signal:run.signal,error:run.error?.message}));
process.exitCode=run.status===0?0:1;
