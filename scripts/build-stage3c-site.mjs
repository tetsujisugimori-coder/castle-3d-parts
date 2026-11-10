import{execFileSync}from'node:child_process';import{cp,mkdir,readFile,writeFile}from'node:fs/promises';
execFileSync(process.execPath,['scripts/build-stage3b-site.mjs'],{stdio:'inherit'});
await mkdir('dist/shared',{recursive:true});await cp('site/shared/gate-viewer.mjs','dist/shared/gate-viewer.mjs');
await mkdir('dist/stage3c',{recursive:true});for(const f of['index.html','style.css','app.mjs','contract.mjs'])await cp('site/stage3c/'+f,'dist/stage3c/'+f);
await mkdir('dist/cad/stage3c',{recursive:true});await cp('cad/stage3c/generated','dist/cad/stage3c/generated',{recursive:true});
await mkdir('dist/docs/stage3c',{recursive:true});await cp('docs/stage3c','dist/docs/stage3c',{recursive:true});
let h=await readFile('dist/index.html','utf8');h=h.replace('<main>','<main><p><a id="gate-lock-entry" href="./stage3c/">木戸の閂・閉鎖機構（試作D）</a></p>');await writeFile('dist/index.html',h);
console.log('Stage3C candidate build only; not deployed.');
