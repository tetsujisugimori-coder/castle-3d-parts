import test, {before} from 'node:test';import assert from 'node:assert/strict';import{readFileSync,mkdtempSync,mkdirSync,writeFileSync,readdirSync,cpSync,rmSync,existsSync}from'node:fs';import{resolve,dirname}from'node:path';import{tmpdir}from'node:os';import{createHash}from'node:crypto';import{execFileSync}from'node:child_process';import{originalBytes,REPLACEMENTS}from'../scripts/stage2d/preservation.mjs';
const root=resolve('.'),h=b=>createHash('sha256').update(b).digest('hex'),baseline=JSON.parse(readFileSync('design/stage2d/baseline.json'));
test('all 948 Stage2C source files retained; exact reviewed code migrations distinguished',()=>{assert.equal(Object.keys(baseline.files).length,948);for(const[p,sha]of Object.entries(baseline.files))assert.equal(h(originalBytes(root,p,sha)),sha,p)});
for(const path of ['cad/stage2c/generated/B0/assembly.FCStd','cad/stage2c/generated/B2/link-manifest.json','sources/records/SRC-0001.json','site/stage2c/app.mjs',...REPLACEMENTS])test('preservation rejects third bytes: '+path,()=>{const dir=mkdtempSync(resolve(tmpdir(),'stage2d-mutation-'));try{cpSync('design/stage2d',resolve(dir,'design/stage2d'),{recursive:true});mkdirSync(dirname(resolve(dir,path)),{recursive:true});writeFileSync(resolve(dir,path),'intentional damaged input');assert.throws(()=>originalBytes(dir,path,baseline.files[path]))}finally{rmSync(dir,{recursive:true,force:true})}});
test('official Pages workflow selects final integrated builder',()=>{assert.match(readFileSync('.github/workflows/pages.yml','utf8'),/node scripts\/build-stage2d-site.mjs/)});
before(()=>execFileSync(process.execPath,['scripts/build-stage2d-site.mjs']));
test('build publishes only correct linked bytes and repository-prefix paths',()=>{assert.match(readFileSync('dist/index.html','utf8'),/id="linked-viewer-entry" href=".\/stage2c\/"/);assert.match(readFileSync('dist/stage2c/index.html','utf8'),/repository-root" content="..\/"/);assert.match(readFileSync('dist/stage2c/app.mjs','utf8'),/location\.assign\(u\.href\)/);assert.doesNotMatch(readFileSync('dist/stage2c/app.mjs','utf8'),/history\.pushState/);assert.doesNotMatch(readFileSync('dist/stage2b/app.mjs','utf8'),/\.\.\/\.\.\/cad\//);for(const rev of ['B0','B1','B2']){const m=JSON.parse(readFileSync(`dist/cad/stage2c/generated/${rev}/link-manifest.json`));assert.equal(m.dimensions.length,19);assert.equal(m.basis,'D');for(const f of ['assembly.glb','drawing.svg','link-manifest.json'])assert.deepEqual(readFileSync(`dist/cad/stage2c/generated/${rev}/${f}`),readFileSync(`cad/stage2c/generated/${rev}/${f}`));for(const p of m.parts)for(const r of p.research_refs)assert(existsSync('dist/'+r.path));assert(!existsSync(`dist/cad/stage2c/generated/${rev}/assembly.FCStd`))}const deployment=JSON.parse(readFileSync('dist/deployment-manifest.json'));assert.equal(Object.keys(deployment.assets).length,9);assert.equal(deployment.physical_iphone,'NOT_TESTED')});

test('Pages connects the exhibition and workshop under the project prefix',()=>{
 const exhibition=new URL('https://example.test/castle-3d-parts/');
 const home=readFileSync('dist/index.html','utf8');
 const entrance=home.match(/<a id="workshop-entry" href="([^"]+)"/);
 assert.ok(entrance);
 const workshop=new URL(entrance[1],exhibition);
 assert.equal(workshop.href,exhibition.href+'stage4a/workshop/');
 const html=readFileSync('dist/stage4a/workshop/index.html','utf8');
 const exit=html.match(/<a id="exhibition-entry" href="([^"]+)"/);
 assert.ok(exit);
 assert.equal(new URL(exit[1],workshop).href,exhibition.href);
 assert.doesNotMatch(html,/開発用|preview\.html/);
 assert.match(html,/試作D・参照模型/);
 for(const file of ['workshop.css','workshop.mjs']){
  assert.ok(html.includes('"./'+file+'"'));
  assert.deepEqual(readFileSync('dist/stage4a/workshop/'+file),readFileSync('previews/stage4a/'+file));
 }
});

test('Pages ships only the runtime workshop files and catalog-pinned assets',()=>{
 const runtime=['catalog.json','example.json','contract.mjs','json-data.mjs','glb-scene.mjs','workshop.mjs','workshop-ui.mjs'].sort();
 assert.deepEqual(readdirSync('dist/assembly/stage4a').sort(),runtime);
 for(const file of runtime)assert.deepEqual(readFileSync('dist/assembly/stage4a/'+file),readFileSync('assembly/stage4a/'+file));
 const catalog=JSON.parse(readFileSync('dist/assembly/stage4a/catalog.json','utf8'));
 for(const {manifest,glb,glb_sha256} of catalog.definitions){
  for(const path of [manifest,glb])assert.deepEqual(readFileSync('dist/'+path),readFileSync(path),path);
  assert.equal(h(readFileSync('dist/'+glb)),glb_sha256);
 }
 assert.deepEqual(readdirSync('dist/cad/stage3a/generated/B0').sort(),['assembly.glb','link-manifest.json']);
 assert.deepEqual(readdirSync('dist/stage4a/workshop').sort(),['index.html','workshop.css','workshop.mjs']);
 assert(!existsSync('dist/previews'));
});
