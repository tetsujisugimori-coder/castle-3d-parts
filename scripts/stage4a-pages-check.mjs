import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';

const h=bytes=>createHash('sha256').update(bytes).digest('hex');

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
