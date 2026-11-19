// Isolated Stage 3-B initial-load network probe. No acceptance thresholds are relaxed.
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync, appendFileSync } from 'node:fs';
import { resolve, relative, isAbsolute, extname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const out = resolve(process.argv[2] || 'stage3b-transport-ci');
if (existsSync(out)) throw Error('Diagnostic output must be a new directory');
if (!process.env.PW_MODULE || !process.env.THREE_DIR) throw Error('PW_MODULE and THREE_DIR required');
mkdirSync(out, { recursive: true });
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const eventFile = join(out, 'transport.jsonl');
let sequence = 0;
const log = (type, details = {}) => {
  const row = { seq: ++sequence, timestamp: new Date().toISOString(), ms: Date.now(), type, ...details };
  appendFileSync(eventFile, JSON.stringify(row) + '\n');
};
const meta = {
  suite: 'stage3b-initial-load-only',
  source_sha256: sha(readFileSync('scripts/stage3b-browser.mjs')),
  runtime_sha256: sha(readFileSync('scripts/stage3c-browser-runtime.mjs')),
  manifest_sha256: sha(readFileSync('cad/stage3b/generated/manifest.json')),
  head: execFileSync('git', ['rev-parse', 'HEAD']).toString().trim(),
  tree: execFileSync('git', ['rev-parse', 'HEAD^{tree}']).toString().trim(),
  node: process.version,
  platform: process.platform,
  dependency_versions: {
    playwright: JSON.parse(readFileSync(resolve(process.env.PW_MODULE, '../package.json'))).version,
    three: JSON.parse(readFileSync(join(process.env.THREE_DIR, 'package.json'))).version,
  },
  normal_wait_timeout_ms: 30000,
  evidence_scope: 'initial-load-network; not the full 44-condition Stage 3-B contract',
};
writeFileSync(join(out, 'identity.json'), JSON.stringify(meta, null, 2));
log('build-start');
execFileSync(process.execPath, ['scripts/build-stage3b-site.mjs'], { stdio: 'pipe' });
log('build-done');

const root = resolve('dist');
const contentTypes = { '.html':'text/html', '.mjs':'text/javascript', '.js':'text/javascript', '.json':'application/json', '.css':'text/css', '.svg':'image/svg+xml', '.glb':'model/gltf-binary' };
let socketId = 0;
const server = createServer((req, res) => {
  const url = req.url || '';
  log('server-request', { url, socket: req.socket._stage3bDiagId || null });
  res.on('finish', () => log('server-response-finish', { url, status:res.statusCode, bytesWritten:res.socket?.bytesWritten ?? null }));
  res.on('close', () => log('server-response-close', { url, status:res.statusCode, writableEnded:res.writableEnded }));
  try {
    const pathname = new URL(url, 'http://local').pathname.replace(/\/$/, '/index.html');
    const path = resolve(root, '.' + pathname);
    const rel = relative(root, path);
    if (rel.startsWith('..') || isAbsolute(rel)) throw Error('path traversal');
    res.setHeader('Content-Type', contentTypes[extname(path)] || 'application/octet-stream');
    res.end(readFileSync(path));
  } catch (err) {
    log('server-read-error', { url, error:err.message });
    res.statusCode=404;
    res.end('missing');
  }
});
server.on('connection', socket => {
  const id = ++socketId;
  socket._stage3bDiagId = id;
  log('server-connection', { socket:id, remoteAddress:socket.remoteAddress, remotePort:socket.remotePort });
  socket.on('error', err => log('server-socket-error', { socket:id, code:err.code||null, message:err.message }));
  socket.on('close', hadError => log('server-socket-close', { socket:id, hadError }));
});
server.on('clientError', err => log('server-client-error', { code:err.code||null, message:err.message }));
server.on('error', err => log('server-error', { code:err.code||null, message:err.message }));
await new Promise((ok, fail) => server.listen(0, '127.0.0.1', err => err ? fail(err) : ok()));
const base = `http://127.0.0.1:${server.address().port}/`;
log('server-ready', { base });
const { chromium, webkit } = await import(pathToFileURL(process.env.PW_MODULE));
const scenarios = [
  { engine:'chromium', width:390, motion:'reduce', count:3, synthetic:false },
  { engine:'chromium', width:390, motion:'no-preference', count:1, synthetic:false },
  { engine:'webkit', width:390, motion:'reduce', count:1, synthetic:false },
  { engine:'chromium', width:390, motion:'reduce', count:1, synthetic:true },
];
const results = [];
try {
  for (const scenario of scenarios) {
    const browser = await ({ chromium, webkit }[scenario.engine]).launch({headless:true, chromiumSandbox:true, args:scenario.engine==='chromium' ? ['--enable-unsafe-swiftshader'] : []});
    try {
      for (let repeat=1; repeat<=scenario.count; repeat++) {
        const tag = `${scenario.engine}-${scenario.width}-${scenario.motion}-${scenario.synthetic?'synthetic':'normal'}-${repeat}`;
        const row = { tag, ...scenario, repeat, status:'NOT_TESTED', appResponse:[], requestFailed:[], pageErrors:[] };
        const context = await browser.newContext({ viewport:{width:scenario.width,height:950}, reducedMotion:scenario.motion });
        await context.route('https://cdn.jsdelivr.net/npm/three@0.180.0/**', route => {
          const suffix = route.request().url().split('/three@0.180.0/')[1];
          return route.fulfill({ path:resolve(process.env.THREE_DIR, suffix), contentType:'text/javascript' });
        });
        const page = await context.newPage();
        page.on('requestfailed', request => {
          const item = { url:request.url(), failure:request.failure()?.errorText || null };
          row.requestFailed.push(item);log('browser-requestfailed', { tag, ...item });
        });
        page.on('response', response => {
          if (response.url().includes('/stage3b/app.mjs')) {
            const item = { url:response.url(), status:response.status() };
            row.appResponse.push(item);log('browser-app-response', {tag,...item});
          }
        });
        page.on('pageerror', error => {row.pageErrors.push(error.message);log('browser-pageerror',{tag,message:error.message});});
        await context.tracing.start({screenshots:true,snapshots:true});
        try {
          if (scenario.synthetic) {
            // A negative control for the monitor, not a reproduction of the original failure.
            await page.route('**/stage3b/app.mjs', route => route.abort('failed'));
          }
          log('case-start', { tag, synthetic:scenario.synthetic });
          await page.goto(base + 'stage3b/');
          if (scenario.synthetic) {
            try { await page.waitForSelector('#status[data-loaded=true]', {timeout:1500}); row.status='INVALID_NEGATIVE_CONTROL'; }
            catch {row.status=row.requestFailed.some(x=>x.url.includes('/stage3b/app.mjs')) ? 'EXPECTED_SYNTHETIC_FAIL' : 'INVALID_NEGATIVE_CONTROL';}
          } else {
            await page.waitForSelector('#status[data-loaded=true]', {timeout:30000});
            if (!row.appResponse.some(x=>x.status===200)) throw Error('Stage3B app.mjs never returned HTTP 200');
            if (row.requestFailed.some(x=>x.url.includes('/stage3b/app.mjs'))) throw Error('Stage3B app.mjs failed network request');
            row.status='PASS';
          }
        } catch (error) { row.status='FAIL';row.error=error.stack||String(error); }
        finally {
          try { await page.screenshot({path:join(out, tag+'.png'),fullPage:true}); }
          catch (error) { row.screenshotError=String(error); }
          try { await context.tracing.stop({path:join(out, tag+'.zip')}); }
          catch (error) { row.traceError=String(error); }
          results.push(row);log('case-end', {tag,status:row.status});
          await context.close();
        }
      }
    } finally { await browser.close(); }
  }
} finally {
  server.closeAllConnections?.();
  await new Promise(resolve => server.close(resolve));
  log('server-closed');
  const report={metadata:meta,scenarios,results,counts:results.reduce((c,r)=>(c[r.status]=(c[r.status]||0)+1,c),{})};
  writeFileSync(join(out, 'results.json'), JSON.stringify(report,null,2));
  const expectedNormal=scenarios.filter(s=>!s.synthetic).reduce((n,s)=>n+s.count,0);
  const normalPass=results.filter(r=>!r.synthetic&&r.status==='PASS').length;
  const syntheticPass=results.filter(r=>r.synthetic&&r.status==='EXPECTED_SYNTHETIC_FAIL').length;
  console.log(JSON.stringify({normalPass,expectedNormal,syntheticPass,expectedSynthetic:1,results:results.map(r=>({tag:r.tag,status:r.status,error:r.error?.slice(0,250)}))}));
  if(normalPass!==expectedNormal||syntheticPass!==1)process.exitCode=1;
}
