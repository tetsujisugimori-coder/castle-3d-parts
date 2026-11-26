import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve,extname,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {assertLeafPixels} from './png.mjs';
import {execFileSync} from 'node:child_process';

const out=resolve(process.env.STAGE4B_OUT);
const root=resolve('dist'),prefix='/castle-3d-parts/';
const three=resolve(process.env.THREE_ROOT);
const module=await import(pathToFileURL(resolve(process.env.PW_MODULE)));
const engine=process.env.STAGE4B_ENGINE;
assert(['chromium','webkit'].includes(engine));
mkdirSync(out,{recursive:true});
const rows=[],meta={engine,rows,head:execFileSync('git',['rev-parse','HEAD']).toString().trim(),
 tree:execFileSync('git',['rev-parse','HEAD^{tree}']).toString().trim(),
 playwright:JSON.parse(readFileSync(resolve(process.env.PW_MODULE,'../package.json'))).version};
if (process.env.EXPECTED_HEAD) assert.equal(meta.head,process.env.EXPECTED_HEAD);
const mime={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.json':'application/json','.glb':'model/gltf-binary'};
const server=createServer((req,res)=>{
 try {
  let pathname=decodeURIComponent(new URL(req.url,'http://local').pathname);
  if(!pathname.startsWith(prefix))throw Error('prefix');
  pathname=pathname.slice(prefix.length);
  if(!pathname||pathname.endsWith('/'))pathname+='index.html';
  const path=resolve(root,pathname);
  if(!path.startsWith(root+sep))throw Error('invalid path');
  res.writeHead(200,{'Content-Type':mime[extname(path)]??'application/octet-stream'});
  res.end(readFileSync(path));
 }catch(e){if(!res.headersSent)res.writeHead(404);res.end('missing');}
});
const canonical=JSON.parse(readFileSync('dist/assembly/stage4b/example.json','utf8'));
const assertSummary=async(page,n)=>{await page.waitForFunction(n=>document.getElementById('summary').textContent.includes('配置数：'+n+' / メッシュ数：'+n),n)};
const status=(page,s='ready')=>page.locator('#status[data-state="'+s+'"]').waitFor({timeout:20000});
async function click(page,id,s){await page.locator('#'+id).click();await status(page,s);}
async function follow(page,id,url,keyboard=false){await Promise.all([page.waitForURL(url),keyboard?page.locator('#'+id).press('Enter'):page.locator('#'+id).click()]);}
async function save(page){await click(page,'save');return JSON.parse(await page.locator('#json').inputValue());}
const noOverflow=page=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1);
let browser;
try{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const index='http://127.0.0.1:'+server.address().port+prefix;
 const chrome={args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']};
 browser=await module[engine].launch(engine==='chromium'?chrome:{});
 meta.browser=browser.version();
 for(const width of [390,1280])for(const reducedMotion of ['reduce','no-preference']){
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion});
  const row={width,reducedMotion,checks:[],errors:[]};rows.push(row);
  const chk=s=>row.checks.push(s);
  await context.route('https://cdn.jsdelivr.net/npm/three@0.180.0/**',route=>{
   const pathname=new URL(route.request().url()).pathname;
   const path=resolve(three,pathname.split('/three@0.180.0/')[1]??'');
   if(!path.startsWith(three+sep))return route.abort();
   return route.fulfill({path,contentType:'text/javascript'});
  });
  const page=await context.newPage();
  page.setDefaultTimeout(25000);
  page.on('pageerror',e=>row.errors.push(e.message));
  page.on('response',r=>{if(!r.ok()&&/\/(assembly|cad)\/stage4b\//.test(r.url()))row.errors.push('HTTP '+r.status()+' '+r.url());});
  try{
   await page.goto(index,{waitUntil:'domcontentloaded'});
   await follow(page,'west-gate-exhibit',index+'stage4b/exhibit/',width!==390);
   await status(page);await assertSummary(page,8);chk('exhibit 8 rendered instances');
   assert(await noOverflow(page));chk('exhibit horizontal range');
   const view=page.locator('#viewport canvas');
   await view.waitFor({state:'visible'});
   const image=await view.screenshot({path:resolve(out,width+'-'+reducedMotion+'-complete.png')});
   row.exhibitPixels=assertLeafPixels(image);chk('exhibit canvas contains actual gate pixels');
   for(const [preset,count] of [['board',1],['rail',1],['assembly',8]]){
    const b=page.locator('[data-preset="'+preset+'"]');
    await b.click();await status(page);await assertSummary(page,count);
    assert.equal(await b.getAttribute('aria-pressed'),'true');chk('preset '+preset);
   }
   await follow(page,'open-gate-workshop',index+'stage4b/workshop/',width!==390);
   await status(page);await assertSummary(page,8);
   assert(await noOverflow(page));chk('workshop 8 rendered, no overflow');
   row.workshopPixels=assertLeafPixels(await page.locator('#viewport canvas').screenshot({path:resolve(out,width+'-'+reducedMotion+'-workshop.png')}));
   chk('workshop canvas contains actual gate pixels');
   assert.deepEqual(await save(page),canonical);chk('v2 original round trip');
   const x=page.locator('#x');
   await x.fill('0.01');await click(page,'move');
   const edited=await save(page);
   assert.equal(edited.instances[0].translation_m[0],.01);chk('editable placement');
   for(const [key,value] of [['definition_id','missing'],['translation_m',[0,1,10001]]]){
    const fault=structuredClone(edited);fault.instances[1][key]=value;
    await page.locator('#json').fill(JSON.stringify(fault));await click(page,'load','error');
    assert.deepEqual(await save(page),edited);chk('reject '+key+' without changing active model');
   }
   await page.locator('#json').fill(JSON.stringify(canonical));await click(page,'load');
   assert.deepEqual(await save(page),canonical);chk('loaded exact original');
   await click(page,'example');assert.deepEqual(await save(page),canonical);chk('reset returns fixed leaf');
   await follow(page,'open-gate-exhibit',index+'stage4b/exhibit/');
   await status(page);await assertSummary(page,8);
   await follow(page,'exhibition-entry',index);
   await follow(page,'workshop-entry',index+'stage4a/workshop/');
   await status(page);
   assert.equal(await page.locator('#instance option').count(),3);chk('old workshop and reciprocal navigation');
   assert.deepEqual(row.errors,[]);
   row.status='PASS';
  }catch(e){row.status='FAIL';row.error=String(e);await page.screenshot({path:resolve(out,width+'-'+reducedMotion+'-failure.png')}).catch(()=>{});}
  finally{await context.close();}
 }
}finally{
 await browser?.close();
 server.close();
 writeFileSync(resolve(out,'results.json'),JSON.stringify(meta,null,2)+'\n');
}
if(rows.length!==4||rows.some(r=>r.status!=='PASS'||r.checks.length!==15))process.exitCode=1;
console.log(JSON.stringify(meta,null,2));
