import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve,extname,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {screenshotCoverage} from '../png.mjs';
import {createHash} from 'node:crypto';
import {poseDocument} from '../../../assembly/stage4b-wave2/poses.mjs';
import {execFileSync} from 'node:child_process';

const out=resolve(process.env.STAGE4B_WAVE2_OUT);
const root=resolve('dist'),prefix='/castle-3d-parts/';
const three=resolve(process.env.THREE_ROOT);
const module=await import(pathToFileURL(resolve(process.env.PW_MODULE)));
const engine=process.env.STAGE4B_WAVE2_ENGINE;
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
const json=p=>JSON.parse(readFileSync('dist/assembly/'+p,'utf8'));
const cat=json('stage4b-wave2/catalog.json'),design=json('stage4b-wave2/design.json'),left=json('stage4b/example.json');
const presetDoc=async name=>JSON.parse(await poseDocument(cat,design,left,name));
const status=(page,s='ready')=>page.locator('#status[data-state="'+s+'"]').waitFor({timeout:20000});
const counts=async(page,n,c)=>{
 await status(page);
 await page.waitForFunction(([n,c])=>document.querySelector('#summary').textContent.includes('配置数：'+n+' / メッシュ数：'+n+' / 接続数：'+c),[n,c]);
};
async function go(page,id,url,keyboard,ready=true){
 const b=page.locator('#'+id);
 await Promise.all([page.waitForURL(url),keyboard?b.press('Enter'):b.click()]);
 if(ready)await status(page);
}
async function preset(page,key,keyboard=false){
 const b=page.locator('[data-preset="'+key+'"]');
 if(keyboard)await b.press('Enter');else await b.click();
 await status(page);
 assert.equal(await b.getAttribute('aria-pressed'),'true');
 assert.equal(await page.locator('#wave2-state').textContent(),await b.textContent());
}
async function save(page){
 await page.locator('#save').click();await status(page);
 return JSON.parse(await page.locator('#json').inputValue());
}
let browser;
try{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const home='http://127.0.0.1:'+server.address().port+prefix;
 const newGallery=home+'stage4b/wave2/exhibit/',newWorkshop=home+'stage4b/wave2/workshop/';
 const launch={args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']};
 browser=await module[engine].launch(engine==='chromium'?launch:{});
 meta.browser=browser.version();
 for(const width of [390,1280])for(const reducedMotion of ['reduce','no-preference']){
  const context=await browser.newContext({viewport:{width,height:850},reducedMotion});
  const row={width,reducedMotion,checks:[],errors:[],images:{}};rows.push(row);
  const chk=s=>row.checks.push(s);
  await context.route('https://cdn.jsdelivr.net/npm/three@0.180.0/**',route=>{
   const f=resolve(three,new URL(route.request().url()).pathname.split('/three@0.180.0/')[1]??'');
   return f.startsWith(three+sep)?route.fulfill({path:f,contentType:'text/javascript'}):route.abort();
  });
  const page=await context.newPage();
  page.setDefaultTimeout(25000);
  page.on('pageerror',e=>row.errors.push(e.message));
  page.on('response',r=>{if(!r.ok()&&/\/(assembly|cad)\//.test(r.url()))row.errors.push('HTTP '+r.status()+' '+r.url());});
  const overflow=()=>page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1);
  try{
   await page.goto(home,{waitUntil:'domcontentloaded'});
   await go(page,'west-gate-wave2',newGallery,true);
   await counts(page,26,8);assert(!(await overflow()));chk('public gallery route by keyboard and 26 rendered at viewport');
   const hashes=new Set();
   for(const p of ['closed','left','right','both']){
    await preset(page,p,true);await counts(page,26,8);
    const file=width+'-'+reducedMotion+'-'+p+'.png';
    const png=await page.locator('#viewport canvas').screenshot({path:resolve(out,file)});
    const pix=screenshotCoverage(png);
    assert(pix.ratio>.01&&pix.ratio<.9,JSON.stringify(pix));
    const sha=createHash('sha256').update(png).digest('hex');
    assert(!hashes.has(sha),'two poses rendered an identical canvas');
    hashes.add(sha);row.images[p]={file,sha,...pix};chk('independent visible pose '+p);
   }
   for(const [key,num,con] of [['inspect-left',13,4],['inspect-right',13,4],['post',1,0],['bearing',1,0],['pivot',1,0]]){
    await preset(page,key);await counts(page,num,con);chk('observable '+key);
   }
   await preset(page,'right');
   await go(page,'open-wave2-workshop',newWorkshop+'?pose=right',true);
   await counts(page,26,8);assert(!(await overflow()));chk('workshop transfers prescribed pose and responsive display');
   assert.deepEqual(await save(page),await presetDoc('right'));chk('right pose save includes rotation and connections');
   for(const p of ['left','closed','both']){
    await preset(page,p,true);
    assert.deepEqual(await save(page),await presetDoc(p));chk('workshop save for '+p);
   }
   const edited=structuredClone(await presetDoc('both'));
   edited.instances.find(a=>a.id==='L-B01').translation_m[2]+=.001;
   await page.locator('#json').fill(JSON.stringify(edited));await page.locator('#load').click();await status(page);
   assert.deepEqual(await save(page),edited);chk('edited placement restored with reference anchors');
   const bad=structuredClone(edited);bad.instances.find(a=>a.id==='L-bearing-0').translation_m[1]+=.004;
   await page.locator('#json').fill(JSON.stringify(bad));await page.locator('#load').click();await status(page,'error');
   assert.deepEqual(await save(page),edited);chk('misaligned anchor rejected preserving prior scene');
   await page.locator('#example').click();await status(page);
   assert.deepEqual(await save(page),await presetDoc('closed'));chk('reset closed');
   await go(page,'open-wave2-exhibit',newGallery,true);await counts(page,26,8);chk('workshop to gallery');
   await go(page,'exhibition-entry',home,true,false);
   await go(page,'west-gate-exhibit',home+'stage4b/exhibit/',true);await counts(page,8,0);chk('D0 exhibit regression');
   assert.deepEqual(row.errors,[]);
   row.status='PASS';
  }catch(e){
   row.status='FAIL';row.error=String(e);
   await page.screenshot({path:resolve(out,width+'-'+reducedMotion+'-failure.png')}).catch(()=>{});
  }finally{await context.close();}
 }
}finally{
 await browser?.close();server.close();
 writeFileSync(resolve(out,'results.json'),JSON.stringify(meta,null,2)+'\n');
}
if(rows.length!==4||rows.some(r=>r.status!=='PASS'||r.checks.length!==20))process.exitCode=1;
console.log(JSON.stringify(meta,null,2));
