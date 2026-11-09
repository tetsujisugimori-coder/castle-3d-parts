/** Independent minimal reproduction: no CAD, SVG, Three.js, or application functions. */
import {createServer} from 'node:http';
import {writeFileSync, mkdirSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
const {chromium, webkit} = await import(pathToFileURL(process.env.PW_MODULE || '/tmp/castle2d-pw/node_modules/playwright/index.mjs'));
const out = process.env.STAGE2D_HISTORY_OUT || '/tmp/stage2d-history';
mkdirSync(out, {recursive: true});
const server = createServer((request, response) => {
  const mode = new URL(request.url, 'http://local').pathname.includes('document') ? 'document' : 'same-document';
  const action = mode === 'document' ? "location.assign('?revision='+this.value)" : "history.pushState(null,'','?revision='+this.value)";
  response.setHeader('Content-Type', 'text/html');
  response.end(`<!doctype html><html><body><label>Revision<select id="revision" onchange="${action}"><option>B0</option><option>B1</option><option>B2</option></select></label><script>const sync=()=>document.getElementById('revision').value=new URL(location.href).searchParams.get('revision')||'B0';sync();addEventListener('popstate',sync)</script></body></html>`);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const rows = [];
try {
  for (const [name, engine] of Object.entries({chromium, webkit})) {
    const browser = await engine.launch({headless: true, executablePath: name === 'webkit' ? process.env.STAGE2D_WEBKIT_EXECUTABLE : undefined, args: name === 'chromium' ? ['--no-sandbox'] : []});
    for (const mode of ['legacy', 'document']) {
      const context = await browser.newContext();
      await context.tracing.start({screenshots: true, snapshots: true});
      const page = await context.newPage();
      const row = {engine: name, browser_version: browser.version(), mode, result: 'FAIL', physical_iphone: 'NOT_TESTED'};
      try {
        await page.goto(`http://127.0.0.1:${server.address().port}/${mode}/`);
        for (const revision of ['B1', 'B2']) {
          if (mode === 'document') await Promise.all([page.waitForEvent('framenavigated', f => f === page.mainFrame()), page.selectOption('#revision', revision, {noWaitAfter: true})]);
          else await page.selectOption('#revision', revision);
        }
        await page.goBack();
        await page.goForward();
        await page.reload();
        if (await page.locator('#revision').inputValue() !== 'B2') throw Error('wrong revision after reload');
        row.result = 'PASS';
      } catch (error) { row.error = error.message; }
      await context.tracing.stop({path: `${out}/${name}-${mode}.zip`});
      rows.push(row);
      console.log(JSON.stringify(row));
      await context.close();
    }
    await browser.close();
  }
} finally {
  server.close();
  writeFileSync(`${out}/results.json`, JSON.stringify({head: execFileSync('git', ['rev-parse', 'HEAD']).toString().trim(), measured_at: new Date().toISOString(), rows, note: 'Legacy result is observed, not required to fail on every future browser. Document navigation must pass. Physical Safari is untested.'}, null, 2) + '\n');
  if (rows.length !== 4 || rows.some(r => r.mode === 'document' && r.result !== 'PASS')) process.exitCode = 1;
}
