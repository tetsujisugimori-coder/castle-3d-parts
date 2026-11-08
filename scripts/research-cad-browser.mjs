import {mkdirSync, writeFileSync, readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {createServer} from 'node:http';
import {resolve, extname} from 'node:path';
import {pathToFileURL} from 'node:url';
const root = resolve(process.env.RESEARCH_CAD_SITE || 'dist');
const out = process.env.RESEARCH_CAD_EVIDENCE_DIR || 'evidence/stage2a/browser';
mkdirSync(out, {recursive:true});
const rows = [];
const inputs = {};
for(const file of ['research-cad/index.html','research-cad/style.css','research-cad/app.mjs','research-cad/view-model.mjs','research-cad/data.json','cad/palisade.glb']) {
  try {inputs[file]=createHash('sha256').update(readFileSync(resolve(root,file))).digest('hex');} catch {inputs[file]=null;}
}
const save = () => writeFileSync(out + '/results.json', JSON.stringify({
  rows, inputs, expected_matrix_rows:16, matrix_pass:rows.filter(r=>r.width && r.status==='PASS').length,
  failed:rows.some(r=>r.status!=='PASS') || rows.filter(r=>r.width && r.status==='PASS').length!==16,
  scope:'Research UI + unchanged embedded CAD GLB viewer; not native iPhone Safari or CAD GUI execution',
  dependency_mode:process.env.THREE_DIR ? 'local unmodified Three.js route mapping; CDN delivery not covered' : 'CDN'
}, null, 2)+'\n');
const server = createServer(async (req,res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/\/$/,'/index.html');
    const path = resolve(root, '.' + pathname);
    if (!path.startsWith(root + '/')) throw Error('path');
    res.setHeader('Content-Type', ({'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.json':'application/json','.glb':'model/gltf-binary'})[extname(path)] || 'application/octet-stream');
    res.end(await readFile(path));
  } catch { res.statusCode=404; res.end('not found'); }
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base = 'http://127.0.0.1:' + server.address().port;
async function dependencies(context) {
  if(process.env.THREE_DIR) await context.route('https://cdn.jsdelivr.net/npm/three@0.180.0/**', route=> {
    const rel = route.request().url().split('/three@0.180.0/')[1];
    return route.fulfill({path:resolve(process.env.THREE_DIR,rel),contentType:'text/javascript'});
  });
}
try {
  const {chromium,webkit} = await import(pathToFileURL(process.env.PW_MODULE || '/tmp/cad-pw/node_modules/playwright/index.mjs'));
  for(const [engineName,engine] of Object.entries({chromium,webkit})) {
    let browser;
    try { browser=await engine.launch({headless:true,args:engineName==='chromium'?['--no-sandbox','--enable-unsafe-swiftshader']:[]}); }
    catch(error) { rows.push({engine:engineName,status:'BLOCKED',error:error.message});save();continue; }
    try {
      for(const width of [375,390,765,1280]) for(const motion of ['no-preference','reduce']) {
        const context = await browser.newContext({viewport:{width,height:900},reducedMotion:motion,hasTouch:width<800});
        await dependencies(context);
        const page=await context.newPage(), errors=[], writes=[];
        page.on('pageerror',error=>errors.push(error.message));
        page.on('request',request=>{if(!['GET','HEAD'].includes(request.method()))writes.push(request.method()+' '+request.url());});
        const row={engine:engineName,width,motion,status:'FAIL'};
        try {
          await page.goto(base+'/research-cad/');
          await page.waitForSelector('#status[data-loaded=true]',{timeout:15000});
          await page.locator('#candidate').focus();
          const options=await page.locator('#candidate option').count();
          if(options>1) {await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');}
          row.candidates=options;
          const exported=await page.evaluate(async()=>await (await fetch('./data.json')).json());
          row.research_records=exported.snapshot.records?.length ?? 0;
          row.candidate_states=[];
          const researchText=await page.locator('#research').textContent();
          for(const record of exported.snapshot.records ?? []) if(!researchText.includes(record.id))throw Error('Missing record '+record.id);
          for(let index=0;index<exported.candidates.length;index++) {
            await page.locator('#candidate').selectOption(String(index));
            const candidate=exported.candidates[index];
            const rendered=await page.locator('#candidate-detail').textContent();
            for(const [key,value] of Object.entries(candidate)) {
              if(['parameter_changes','evidence_changes'].includes(key))continue;
              const expected=value===null?'未設定 / 未確認':typeof value==='object'?JSON.stringify(value,null,2):String(value);
              if(!rendered.includes(expected))throw Error('Candidate field not rendered: '+key);
            }
            for(const change of candidate.parameter_changes ?? []) {
              if(!rendered.includes(String(change.current_value)) || !rendered.includes(String(change.proposed_value)))throw Error('Parameter difference missing');
            }
            row.candidate_states.push(candidate.status);
          }
          if(options)await page.locator('#candidate').selectOption('0');
          if(!await page.locator('#candidate-detail').textContent())throw Error('Missing candidate detail');
          await page.locator('iframe').scrollIntoViewIfNeeded();
          const iframe=page.frameLocator('iframe');
          await iframe.locator('#status[data-loaded=true]').waitFor({timeout:30000});
          await iframe.locator('#right').click();
          if(width<800)await iframe.locator('#left').tap();
          await iframe.locator('#reset').focus();await page.keyboard.press('Enter');
          row.glb_status=await iframe.locator('#status').textContent();
          row.overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
          row.errors=errors; row.mutation_requests=writes;
          if(row.overflow || errors.length || writes.length)throw Error('Overflow, page error, or mutation request');
          await page.screenshot({path:`${out}/${engineName}-${width}-${motion}.png`,fullPage:true});
          row.status='PASS';
        } catch(error) {row.error=error.message;}
        finally {rows.push(row);save();await context.close();}
      }
      for(const fault of ['missing-data','invalid-json','invalid-contract','hostile-text','missing-glb']) {
        const context=await browser.newContext({viewport:{width:375,height:900}});await dependencies(context);
        const page=await context.newPage();const row={engine:engineName,fault,status:'FAIL'};
        try {
          if(fault==='missing-data')await page.route('**/research-cad/data.json',route=>route.fulfill({status:404,body:'not found'}));
          if(fault==='invalid-json')await page.route('**/research-cad/data.json',route=>route.fulfill({contentType:'application/json',body:'{'}));
          if(fault==='invalid-contract')await page.route('**/research-cad/data.json',route=>route.fulfill({contentType:'application/json',body:'{}'}));
          if(fault==='hostile-text')await page.route('**/research-cad/data.json',route=>route.fulfill({json:{part:{id:'<img src=x onerror="window.pwned=true">'},snapshot:{records:[],edges:[]},candidates:[],manifest:{status:'NOT_TESTED'}}}));
          if(fault==='missing-glb')await page.route('**/palisade.glb',route=>route.abort());
          await page.goto(base+'/research-cad/');
          if(fault==='hostile-text') {
            await page.waitForSelector('#status[data-loaded=true]');
            if(await page.locator('#part img').count() || await page.evaluate(()=>Boolean(window.pwned)))throw Error('HTML injection');
            if(!await page.locator('#candidate').isDisabled())throw Error('Empty candidate list enabled');
          } else if(fault==='missing-glb') {
            await page.locator('iframe').scrollIntoViewIfNeeded();
            await page.frameLocator('iframe').locator('#status[data-error=true]').waitFor({timeout:30000});
            if(!await page.frameLocator('iframe').locator('#reset').isDisabled())throw Error('Failed GLB controls enabled');
          } else {
            await page.waitForSelector('#status[data-error=true]');
            if(await page.locator('#data-panels').isVisible())throw Error('Invalid data displayed');
            row.message=await page.locator('#status').textContent();
          }
          row.status='PASS';
        } catch(error){row.error=error.message;}
        finally{rows.push(row);save();await context.close();}
      }
    } finally {await browser.close();}
  }
} catch(error) { rows.push({status:'BLOCKED',error:error.message}); }
finally {server.close();save();}
if(rows.some(r=>r.status!=='PASS') || rows.filter(r=>r.width && r.status==='PASS').length!==16)process.exitCode=1;
