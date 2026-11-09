import {cp,mkdir,readFile,writeFile}from'node:fs/promises';import{resolve}from'node:path';import{execFileSync}from'node:child_process';
execFileSync(process.execPath,['scripts/build-site.mjs'],{stdio:'inherit'});
for(const revision of ['B0','B1','B2']){const base=`cad/stage2c/generated/${revision}`;await mkdir(resolve('dist',base),{recursive:true});for(const file of ['assembly.glb','drawing.svg','link-manifest.json'])await cp(resolve(base,file),resolve('dist',base,file));}
for(const directory of ['research','sources','observations','design'])await cp(resolve(directory),resolve('dist',directory),{recursive:true});
console.log('Stage 2-C standalone /stage2c/ and linked assets built. No deployment.');

const entry=resolve('dist/stage2c/index.html');
await writeFile(entry,(await readFile(entry,'utf8')).replace('name="repository-root" content="../../"','name="repository-root" content="../"'));
