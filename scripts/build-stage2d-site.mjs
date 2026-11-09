/** Official Pages composition. Original source viewers and CAD bytes are never rewritten. */
import {execFileSync} from 'node:child_process';
import {readFile,writeFile,cp,mkdir,rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {validateManifest} from '../site/stage2c/contract.mjs';
execFileSync(process.execPath,['scripts/build-stage2c-site.mjs'],{stdio:'inherit'});
// Stage2C copies entire research directories; publish only metadata, not source CAD or old logs.
for(const dir of ['research','sources','observations','design'])await rm(resolve('dist',dir),{recursive:true,force:true});
const refs=new Set();
for(const rev of ['B0','B1','B2']){
 const m=validateManifest(JSON.parse(await readFile(`cad/stage2c/generated/${rev}/link-manifest.json`)),rev);
 for(const view of ['front','top','side'])await cp(`cad/stage2c/generated/${rev}/native-${view}.svg`,`dist/cad/stage2c/generated/${rev}/native-${view}.svg`);
 for(const p of m.parts)for(const r of p.research_refs)refs.add(r.path);
 for(const f of ['assembly.glb','drawing.svg','manifest.json','cad-audit.json']){const d=`dist/cad/stage2b/generated/${rev}`;await mkdir(d,{recursive:true});await cp(`cad/stage2b/generated/${rev}/${f}`,`${d}/${f}`)}
}
for(const path of refs){await mkdir(resolve('dist',path,'..'),{recursive:true});await cp(path,resolve('dist',path))}
const replace=async(path,fn)=>writeFile(path,fn(await readFile(path,'utf8')));
await replace('dist/stage2b/app.mjs',s=>s.replaceAll('../../cad/','../cad/'));
await replace('dist/index.html',s=>s.replace('<main>','<main><nav aria-label="部品カタログ"><p><a id="linked-viewer-entry" href="./stage2c/">木柵 B0・B1・B2：CAD原本由来の3Dと設計図を比較</a>（試作D）</p><p><a href="./research-cad/">研究根拠・設計判断</a> · <a href="./guide.html">PC・iPhone操作ガイドと検証範囲</a></p></nav>'));
await replace('dist/stage2c/index.html',s=>s.replace('TechDraw設計図</h2>','CAD投影図（TechDraw実寸照合済み）</h2>').replace('Stage 2-C','Stage 2-D').replace('CASTLE 3D PARTS / Stage 2-C','CASTLE 3D PARTS / Stage 2-D').replace('</header>','<p>A：現況・実測 / B：史料に基づく復元 / C：推定 / D：試作・演出。現在の木柵はDです。</p><p><a href="../guide.html">操作ガイド・実機確認状況</a></p></header>').replace('<a id="raw-svg" href="#">図面SVG</a>','<a id="raw-svg" href="#">連携SVG</a> · TechDraw原出力：<a id="native-front">正面</a> · <a id="native-top">平面</a> · <a id="native-side">側面</a>').replace('<button id="clear"','<button id="retry">再読込み</button><button id="clear"').replace('<button id="zoom-3d"','<button id="zoom-out-3d" data-ready>3D縮小</button><button id="zoom-3d"').replace('<script type="module" src="./app.mjs"></script>','<script type="module" src="./app.mjs"></script>'));
// Small reviewed integration hooks into the existing application, not a second renderer.
await replace('dist/stage2c/app.mjs',s=>s.replace("$('raw-svg').href=base+'drawing.svg';","$('raw-svg').href=base+'drawing.svg';for(const v of ['front','top','side'])$('native-'+v).href=base+'native-'+v+'.svg';").replace("['manifest','raw-svg']","['manifest','raw-svg','native-front','native-top','native-side']").replace("$('revision').addEventListener('change',load)","$('retry').onclick=load;$('zoom-out-3d').onclick=()=>{camera.position.sub(controls.target).multiplyScalar(1/.85).add(controls.target);controls.update()};$('revision').addEventListener('change',()=>{const u=new URL(location.href);u.searchParams.set('revision',$('revision').value);history.pushState(null,'',u);load()})").replace('await load();',`const fromURL=()=>{const rev=new URL(location.href).searchParams.get('revision');$('revision').value=['B0','B1','B2'].includes(rev)?rev:'B0'};fromURL();addEventListener('popstate',()=>{fromURL();load()});await load();`));
await cp('docs/stage2d/guide.html','dist/guide.html');
const version={schema_version:1,stage:'2-D',source_commit:execFileSync('git',['rev-parse','HEAD']).toString().trim(),source_tree:execFileSync('git',['rev-parse','HEAD^{tree}']).toString().trim(),basis:'D',physical_iphone:'NOT_TESTED',assets:{}};
for(const rev of ['B0','B1','B2'])for(const f of ['assembly.glb','drawing.svg','link-manifest.json']){const p=`cad/stage2c/generated/${rev}/${f}`;version.assets[p]=createHash('sha256').update(await readFile('dist/'+p)).digest('hex')}
await writeFile('dist/deployment-manifest.json',JSON.stringify(version,null,2)+'\n');
await writeFile('dist/.nojekyll','');
console.log('Stage2D official Pages composition complete. No deployment performed by this command.');
