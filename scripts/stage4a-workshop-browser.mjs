// Candidate browser test, not a CI or physical Safari result.
import {createServer} from 'node:http';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,extname,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';

const out=resolve(process.env.STAGE4A_OUT||'stage4a-ui-evidence');
mkdirSync(out,{recursive:true});
const root=resolve('.');
const allow=['previews/stage4a/','assembly/stage4a/','cad/stage2c/generated/B0/','cad/stage3a/generated/B0/'];
const mime={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.css':'text/css','.glb':'model/gltf-binary'};
const server=createServer((req,res)=>{
  try{
    const path=decodeURIComponent(new URL(req.url,'http://local').pathname).replace(/^\//,'');
    if(!allow.some(p=>path.startsWith(p)))throw Error('outside preview');
    const p=resolve(root,path);
    if(!p.startsWith(root+sep)||!allow.some(a=>p.startsWith(resolve(root,a)+sep)))throw Error('escape');
    res.setHeader('Content-Type',mime[extname(p)]||'application/octet-stream');
    res.end(readFileSync(p));
  }catch{res.statusCode=404;res.end('missing')}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base='http://127.0.0.1:'+server.address().port+'/previews/stage4a/workshop.html';
const rows=[];
const engines=process.env.STAGE4A_ENGINE?[process.env.STAGE4A_ENGINE]:['chromium','webkit'];
const threeRoot=resolve(process.env.THREE_ROOT||'/tmp/castle2d-pw/node_modules/three');
const original=JSON.parse(readFileSync('assembly/stage4a/example.json','utf8'));
const key=(id,port)=>JSON.stringify({instance_id:id,port});
const ready=p=>p.waitForSelector('#status[data-state=ready]',{timeout:30000});
const error=p=>p.waitForSelector('#status[data-state=error]',{timeout:30000});
const click=async(p,id,ok=true)=>{await p.locator('#'+id).click();await (ok?ready(p):error(p))};
async function save(p){await click(p,'save');return JSON.parse(await p.locator('#json').inputValue())}
async function dependencies(c){
  await c.route('https://cdn.jsdelivr.net/npm/three@0.180.0/**',r=>{
    const path=resolve(threeRoot,r.request().url().split('/three@0.180.0/')[1]);
    if(!path.startsWith(threeRoot+sep))return r.abort();
    return r.fulfill({path,contentType:'text/javascript'});
  });
}
async function initial(p){await p.goto(base,{waitUntil:'domcontentloaded'});await ready(p);assert.equal(await p.locator('#viewport canvas').count(),1);assert.equal(await p.locator('#instance option').count(),3);assert.match(await p.locator('#summary').textContent(),/21.*2/)}
async function normal(p,row){
  await initial(p);
  assert.deepEqual(await save(p),original);
  await p.selectOption('#instance','F01');await p.locator('#x').fill('-4');
  await click(p,'move',false);assert.deepEqual(await save(p),original);
  await click(p,'add');
  const id=await p.locator('#instance').inputValue();
  assert.equal(id,'P1');
  await p.locator('#x').fill('8');await p.locator('#y').fill('2');await p.locator('#z').fill('0');
  await click(p,'move');await click(p,'right');
  let s=await save(p);
  assert.equal(s.instances.length,4);
  assert.deepEqual(s.instances.find(i=>i.id===id).translation_m,[8,2,0]);
  assert.equal(s.instances.find(i=>i.id===id).yaw_quarters,1);
  assert.deepEqual(s.instances.slice(0,3),original.instances);
  await click(p,'left');
  await p.selectOption('#port-a',key('F02','right'));await p.selectOption('#port-b',key(id,'left'));
  await click(p,'connect',false);await click(p,'align');
  s=await save(p);assert.equal(s.connections.length,3);
  assert.ok(Math.abs(s.instances.find(i=>i.id===id).translation_m[0]-8.475)<=1e-9);
  const connection=await p.locator('#connection option').evaluateAll(os=>os.map(o=>o.value).filter(Boolean).find(v=>JSON.parse(v).b.instance_id==='P1'));
  await p.selectOption('#connection',connection);await click(p,'disconnect');
  await p.selectOption('#instance',id);await click(p,'remove');
  assert.deepEqual(await save(p),original);
  await p.locator('#json').fill('{"schema_version":1}');await click(p,'load',false);
  assert.deepEqual(await save(p),original);
  await p.locator('#file').setInputFiles({name:'design.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(s))});
  await click(p,'load-file');assert.deepEqual(await save(p),s);
  await click(p,'example');assert.deepEqual(await save(p),original);
  for(const id of ['fit','turn','zoom','zoom-out'])await p.locator('#'+id).click();
  await p.selectOption('#instance','F01');
  await p.locator('#instance').focus();await p.keyboard.press('ArrowDown');
  assert.equal(await p.locator('#instance').inputValue(),'G01');
  assert.match(await p.locator('#selection').textContent(),/^G01 /);
  assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'horizontal overflow');
  row.checks=['initial actual GLB load','connected edit rejection','add/move/rotate','align/reject/disconnect/remove','v2 JSON and file load','view buttons and keyboard','responsive width'];
}
let fatal;
try{
  const {chromium,webkit}=await import(pathToFileURL(process.env.PW_MODULE||'/tmp/castle2d-pw/node_modules/playwright/index.mjs').href);
  for(const engine of engines){
    const b=await({chromium,webkit}[engine]).launch({headless:true,args:engine==='chromium'?['--no-sandbox','--enable-unsafe-swiftshader']:[]});
    try{
      for(const width of [375,390,765,1280])for(const motion of ['no-preference','reduce']){
        const id=engine+'-'+width+'-'+motion,row={engine,width,motion,status:'FAIL',checks:[],errors:[]};
        const c=await b.newContext({viewport:{width,height:900},reducedMotion:motion});
        try{
          await dependencies(c);const p=await c.newPage();p.on('pageerror',e=>row.errors.push(e.message));
          await c.tracing.start({screenshots:true,snapshots:true});
          try{await normal(p,row);assert.deepEqual(row.errors,[]);await p.screenshot({path:resolve(out,id+'.png'),fullPage:true});row.status='PASS'}
          catch(e){row.error=e.stack;await p.screenshot({path:resolve(out,'FAIL-'+id+'.png'),fullPage:true}).catch(()=>{})}
          finally{await c.tracing.stop({path:resolve(out,id+'.zip')})}
        }catch(e){row.error=e.stack}
        finally{rows.push(row);await c.close()}
      }
      for(const fault of ['missing-glb','wrong-glb']){
        const row={engine,fault,status:'FAIL'},c=await b.newContext();
        try{
          await dependencies(c);
          await c.route('**/cad/stage3a/generated/B0/assembly.glb',r=>r.fulfill(fault==='missing-glb'?{status:404,body:'missing'}:{status:200,body:Buffer.from([0,1,2,3])}));
          const p=await c.newPage();await p.goto(base,{waitUntil:'domcontentloaded'});await error(p);
          assert.equal(await p.locator('#add').isDisabled(),true);
          assert.match(await p.locator('#summary').textContent(),/—/);
          row.status='PASS';
        }catch(e){row.error=e.stack}finally{rows.push(row);await c.close()}
      }
    }finally{await b.close()}
  }
}catch(e){fatal=e.stack}
finally{
  server.close();
  writeFileSync(resolve(out,'results.json'),JSON.stringify({
    head:execFileSync('git',['rev-parse','HEAD']).toString().trim(),
    tree:execFileSync('git',['rev-parse','HEAD^{tree}']).toString().trim(),
    expected:10*engines.length,rows,fatal:fatal??null,physical_iphone:'NOT_TESTED'
  },null,2));
  if(fatal||rows.length!==10*engines.length||rows.some(r=>r.status!=='PASS'))process.exitCode=1;
}
