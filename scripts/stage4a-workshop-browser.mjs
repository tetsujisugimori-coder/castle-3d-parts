// Workshop browser suite for desktop input and Playwright touch emulation.
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
const touchProbes=[];
const engines=process.env.STAGE4A_ENGINE?[process.env.STAGE4A_ENGINE]:['chromium','webkit'];
const threeRoot=resolve(process.env.THREE_ROOT||'/tmp/castle2d-pw/node_modules/three');
const original=JSON.parse(readFileSync('assembly/stage4a/example.json','utf8'));
const key=(id,port)=>JSON.stringify({instance_id:id,port});
const ready=p=>p.waitForSelector('#status[data-state=ready]',{timeout:30000});
const error=p=>p.waitForSelector('#status[data-state=error]',{timeout:30000});
const click=async(p,id,ok=true)=>{await p.locator('#'+id).click();await (ok?ready(p):error(p))};
async function save(p){await click(p,'save');return JSON.parse(await p.locator('#json').inputValue())}
async function pasteDesign(page,design){
  const input=page.locator('#json');
  const text=JSON.stringify(design);
  await input.evaluate(element=>{
    delete element.dataset.trustedPaste;
    element.addEventListener('paste',event=>{
      if(event.isTrusted)element.dataset.trustedPaste=event.clipboardData.getData('text/plain');
    },{once:true});
  });
  await input.fill(text);
  await input.press('ControlOrMeta+a');
  await input.press('ControlOrMeta+c');
  await input.fill('');
  await input.press('ControlOrMeta+v');
  await page.waitForFunction(expected=>document.getElementById('json').dataset.trustedPaste===expected,text);
  assert.equal(await input.inputValue(),text);
}
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
  await pasteDesign(p,s);await click(p,'load');assert.deepEqual(await save(p),s);
  await click(p,'example');assert.deepEqual(await save(p),original);
  await p.locator('#file').setInputFiles({name:'design.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(s))});
  await click(p,'load-file');assert.deepEqual(await save(p),s);
  await click(p,'example');assert.deepEqual(await save(p),original);
  for(const id of ['fit','turn','zoom','zoom-out'])await p.locator('#'+id).click();
  await p.selectOption('#instance','F01');
  await p.locator('#instance').focus();await p.keyboard.press('ArrowDown');
  assert.equal(await p.locator('#instance').inputValue(),'G01');
  assert.match(await p.locator('#selection').textContent(),/^G01 /);
  const [download]=await Promise.all([p.waitForEvent('download'),p.locator('#download').click()]);
  await ready(p);
  assert.equal(await download.failure(),null);
  assert.equal(download.suggestedFilename(),'castle-assembly-v2.json');
  const bytes=readFileSync(await download.path());
  assert.deepEqual(bytes,Buffer.from(await p.locator('#json').inputValue(),'utf8'));
  assert.deepEqual(JSON.parse(bytes.toString('utf8')),original);
  await p.selectOption('#instance','F01');
  await p.locator('#fit').click();
  const canvas=p.locator('#viewport canvas');await canvas.scrollIntoViewIfNeeded();
  const box=await canvas.boundingBox();assert.ok(box);
  await p.mouse.click(box.x+box.width/2,box.y+box.height/2);
  await p.waitForFunction(()=>document.querySelector('#instance').value==='G01');
  assert.match(await p.locator('#selection').textContent(),/^G01 /);
  assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'horizontal overflow');
  row.checks=['initial actual GLB load','connected edit rejection','add/move/rotate','align/reject/disconnect/remove','v2 JSON paste and file load','download byte equality','3D mouse selection','view buttons and exact keyboard selection','responsive width'];
}
async function observeTouchInput(page){
  return page.evaluate(()=>{
    window.__stage4aTouch=[];
    for(const type of ['pointerdown','pointerup','touchstart','touchend']){
      document.addEventListener(type,event=>{
        const target=event.target.closest?.('button')?.id||event.target.tagName;
        window.__stage4aTouch.push({
          target,type,isTrusted:event.isTrusted,pointerType:event.pointerType??null,
          changedTouches:event.changedTouches?.length??null
        });
      },true);
    }
    return {maxTouchPoints:navigator.maxTouchPoints,coarsePointer:matchMedia('(pointer:coarse)').matches};
  });
}
const readTouchInput=page=>page.evaluate(()=>window.__stage4aTouch.splice(0));
function requireTrustedTap(events,target){
  const received=events.filter(e=>e.target===target&&e.isTrusted);
  for(const type of ['pointerdown','pointerup']){
    assert.ok(received.some(e=>e.type===type&&e.pointerType==='touch'),target+': missing trusted touch '+type);
  }
  for(const type of ['touchstart','touchend']){
    assert.ok(received.some(e=>e.type===type&&e.changedTouches>0),target+': missing trusted '+type);
  }
}
async function probeTouchInput(browser,engine){
  for(const hasTouch of [false,true]){
    const row={engine,version:browser.version(),hasTouch,status:'FAIL'};
    touchProbes.push(row);
    const context=await browser.newContext({hasTouch});
    try{
      const page=await context.newPage();
      await page.setContent('<button id="probe" style="width:120px;height:100px">Touch probe</button>');
      row.capabilities=await observeTouchInput(page);
      if(hasTouch){
        await page.touchscreen.tap(50,50);
      }else{
        await assert.rejects(page.touchscreen.tap(50,50),/hasTouch must be enabled/);
      }
      row.tapEvents=await readTouchInput(page);
      if(hasTouch)requireTrustedTap(row.tapEvents,'probe');
      else assert.deepEqual(row.tapEvents,[]);
      await page.mouse.click(50,50);
      row.mouseEvents=await readTouchInput(page);
      for(const type of ['pointerdown','pointerup']){
        assert.ok(row.mouseEvents.some(e=>e.type===type&&e.target==='probe'&&e.isTrusted&&e.pointerType==='mouse'));
      }
      assert.ok(row.mouseEvents.every(e=>e.pointerType==='mouse'));
      row.status='PASS';
    }catch(error){
      row.error=error.stack;
    }finally{await context.close()}
  }
}
async function touchNormal(p,row){
  await initial(p);
  // WebKit WPE can report zero while delivering native emulated touch input.
  // The observed events and resulting editor state are the acceptance criteria.
  row.capabilities=await observeTouchInput(p);
  const tap=async id=>{await p.locator('#'+id).tap();await ready(p)};
  const canvas=p.locator('#viewport canvas');await canvas.scrollIntoViewIfNeeded();
  const box=await canvas.boundingBox();assert.ok(box);
  await p.touchscreen.tap(box.x+box.width/2,box.y+box.height/2);
  await p.waitForFunction(()=>document.querySelector('#instance').value==='G01');
  assert.match(await p.locator('#selection').textContent(),/^G01 /);
  await tap('add');assert.equal(await p.locator('#instance').inputValue(),'P1');
  await p.locator('#x').fill('8');await p.locator('#y').fill('2');await p.locator('#z').fill('0');
  await tap('move');await tap('right');await tap('save');
  const a=JSON.parse(await p.locator('#json').inputValue());
  assert.equal(a.instances.length,4);
  assert.deepEqual(a.instances.find(i=>i.id==='P1').translation_m,[8,2,0]);
  assert.equal(a.instances.find(i=>i.id==='P1').yaw_quarters,1);
  assert.deepEqual(a.instances.slice(0,3),original.instances);
  await tap('left');
  await p.selectOption('#port-a',key('F02','right'));await p.selectOption('#port-b',key('P1','left'));
  await tap('align');await tap('save');
  assert.equal(JSON.parse(await p.locator('#json').inputValue()).connections.length,3);
  const conn=await p.locator('#connection option').evaluateAll(os=>os.map(o=>o.value).filter(Boolean).find(v=>JSON.parse(v).b.instance_id==='P1'));
  await p.selectOption('#connection',conn);await tap('disconnect');await tap('remove');await tap('save');
  assert.deepEqual(JSON.parse(await p.locator('#json').inputValue()),original);
  for(const id of ['fit','turn','zoom','zoom-out'])await p.locator('#'+id).tap();
  row.touchEvents=await readTouchInput(p);
  for(const id of ['CANVAS','add','move','right','left','align','disconnect','remove','save','fit','turn','zoom','zoom-out'])
    requireTrustedTap(row.touchEvents,id);
  row.checks=['trusted touch pointerdown/up and touchstart/end','3D touch selection','tap edit and view controls','saved design equality'];
}
let fatal;
try{
  const {chromium,webkit}=await import(pathToFileURL(process.env.PW_MODULE||'/tmp/castle2d-pw/node_modules/playwright/index.mjs').href);
  for(const engine of engines){
    const b=await({chromium,webkit}[engine]).launch({
      headless:true,executablePath:engine==='webkit'?process.env.WEBKIT_EXECUTABLE:undefined,
      args:engine==='chromium'?['--no-sandbox','--enable-unsafe-swiftshader']:[]
    });
    try{
      await probeTouchInput(b,engine);
      for(const width of [375,390,765,1280])for(const motion of ['no-preference','reduce']){
        const id=engine+'-'+width+'-'+motion,row={engine,width,motion,status:'FAIL',checks:[],errors:[]};
        const c=await b.newContext({viewport:{width,height:900},reducedMotion:motion});
        try{
          await dependencies(c);const p=await c.newPage();p.on('pageerror',e=>row.errors.push(e.message));
          await c.tracing.start({screenshots:true,snapshots:true});
          try{await normal(p,row);assert.deepEqual(row.errors,[]);await p.screenshot({path:resolve(out,id+'.png'),fullPage:true});row.status='PASS'}
          catch(e){row.error=e.stack;await p.screenshot({path:resolve(out,'FAIL-'+id+'.png'),fullPage:true}).catch(()=>{})}
          finally{await c.tracing.stop({path:resolve(out,id+'.zip')})}
        }catch(e){row.error=e.stack;row.status='FAIL'}
        finally{rows.push(row);await c.close()}
      }
      for(const [width,motion] of [[375,'no-preference'],[390,'reduce']]){
        const id=engine+'-touch-'+width+'-'+motion,row={engine,width,motion,input:'touch',status:'FAIL',errors:[]};
        const c=await b.newContext({viewport:{width,height:900},reducedMotion:motion,hasTouch:true});
        try{
          await dependencies(c);const p=await c.newPage();p.on('pageerror',e=>row.errors.push(e.message));
          await c.tracing.start({screenshots:true,snapshots:true});
          try{await touchNormal(p,row);assert.deepEqual(row.errors,[]);await p.screenshot({path:resolve(out,id+'.png'),fullPage:true});row.status='PASS'}
          catch(e){row.error=e.stack;await p.screenshot({path:resolve(out,'FAIL-'+id+'.png'),fullPage:true}).catch(()=>{})}
          finally{await c.tracing.stop({path:resolve(out,id+'.zip')})}
        }catch(e){row.error=e.stack;row.status='FAIL'}
        finally{rows.push(row);await c.close()}
      }
      for(const fault of ['missing-glb','wrong-glb']){
        const id=engine+'-'+fault,row={engine,fault,status:'FAIL',errors:[]},c=await b.newContext();
        try{
          await dependencies(c);
          const pattern='**/cad/stage3a/generated/B0/assembly.glb';
          let injected=0;
          const handler=r=>{injected++;return r.fulfill(fault==='missing-glb'?{status:404,body:'missing'}:{status:200,body:Buffer.from([0,1,2,3])})};
          await c.route(pattern,handler);
          const p=await c.newPage();p.on('pageerror',e=>row.errors.push(e.message));
          await c.tracing.start({screenshots:true,snapshots:true});
          try{
            await p.goto(base,{waitUntil:'domcontentloaded'});await error(p);
            assert.equal(injected,1);
            assert.equal(await p.locator('#add').isDisabled(),true);
            assert.match(await p.locator('#summary').textContent(),/—/);
            row.failureReason=await p.locator('#status').textContent();
            assert.ok(row.failureReason.includes(fault==='missing-glb'?'asset HTTP 404 cad/stage3a/generated/B0/assembly.glb':'GLB SHA-256 mismatch'));
            await p.screenshot({path:resolve(out,id+'-rejected.png'),fullPage:true});
            await c.unroute(pattern,handler);
            const [response]=await Promise.all([p.waitForResponse(r=>r.url().endsWith('/cad/stage3a/generated/B0/assembly.glb')&&r.status()===200),p.reload({waitUntil:'domcontentloaded'})]);
            assert.ok((await response.body()).length>4);
            await ready(p);
            assert.equal(await p.locator('#viewport canvas').count(),1);
            assert.equal(await p.locator('#instance option').count(),3);
            assert.equal(await p.locator('#summary').textContent(),'配置数：3 / メッシュ数：21 / 接続数：2（接続点一致のみ）');
            assert.equal(await p.locator('#add').isEnabled(),true);
            assert.deepEqual(await save(p),original);
            assert.equal(injected,1);assert.deepEqual(row.errors,[]);
            row.recoveredSummary=await p.locator('#summary').textContent();
            await p.screenshot({path:resolve(out,id+'-recovered.png'),fullPage:true});
            row.status='PASS';
          }finally{await c.tracing.stop({path:resolve(out,id+'.zip')})}
        }catch(e){row.error=e.stack;row.status='FAIL'}finally{rows.push(row);await c.close()}
      }
    }finally{await b.close()}
  }
}catch(e){fatal=e.stack}
finally{
  server.close();
  writeFileSync(resolve(out,'results.json'),JSON.stringify({
    head:execFileSync('git',['rev-parse','HEAD']).toString().trim(),
    tree:execFileSync('git',['rev-parse','HEAD^{tree}']).toString().trim(),
    expected:12*engines.length,rows,touchProbes,fatal:fatal??null,physical_iphone:'NOT_TESTED'
  },null,2));
  if(fatal||rows.length!==12*engines.length||rows.some(r=>r.status!=='PASS')||
      touchProbes.length!==2*engines.length||touchProbes.some(r=>r.status!=='PASS'))process.exitCode=1;
}
