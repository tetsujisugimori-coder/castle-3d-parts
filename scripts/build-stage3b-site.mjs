import{execFileSync}from'node:child_process';import{cp,mkdir,readFile,writeFile}from'node:fs/promises';
execFileSync(process.execPath,['scripts/build-stage3a-site.mjs'],{stdio:'inherit'});
await mkdir('dist/stage3b',{recursive:true});for(const f of['index.html','style.css','app.mjs','contract.mjs'])await cp('site/stage3b/'+f,'dist/stage3b/'+f);
await mkdir('dist/cad/stage3b',{recursive:true});await cp('cad/stage3b/generated','dist/cad/stage3b/generated',{recursive:true});
await mkdir('dist/docs/stage3b',{recursive:true});await cp('docs/stage3b','dist/docs/stage3b',{recursive:true});
let h=await readFile('dist/index.html','utf8');h=h.replace('<main>','<main><p><a id="gate-mechanism-entry" href="./stage3b/">木戸の機構と連続開閉（試作D）</a></p>');await writeFile('dist/index.html',h);
console.log('Stage3B candidate build only; not deployed.');
