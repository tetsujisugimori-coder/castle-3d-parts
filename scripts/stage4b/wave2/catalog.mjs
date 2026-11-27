import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {poseDocument} from '../../../assembly/stage4b-wave2/poses.mjs';
const assembly='assembly/stage4b-wave2/';
const cad='cad/stage4b/west-gate-wave2/';
const old='assembly/stage4b/';
const read=p=>readFile(p);
const json=async p=>JSON.parse(await read(p));
const pretty=x=>JSON.stringify(x,null,2)+'\n';
const hash=async p=>createHash('sha256').update(await read(p)).digest('hex');
const write=process.argv[2]==='--generate';
if(!write&&process.argv[2]!=='--check')throw Error('use --generate or --check');
async function output(file,text){
 if(write)await writeFile(file,text);
 else if(await readFile(file,'utf8')!==text)throw Error('wave2 artifact not reproducible: '+file);
}
const d=await json(assembly+'design.json');
const previous=await json(old+'catalog.json');
const left=await json(old+'example.json');
const port=(point_m,outward,type)=>({point_m,outward,type});
const mount='west-gate-mount-D1',axis='west-gate-axis-D1';
const ports={
 'YAM-WEST-POST':Object.fromEntries(d.bearing_z.map((z,i)=>['mount-'+i,port([.15,0,z/1000],[1,0,0],mount)])),
 'YAM-WEST-BEARING':{post:port([-.15,0,0],[-1,0,0],mount),axis:port([0,0,0],[0,0,1],axis)},
 'YAM-WEST-PIVOT':{axis:port([0,0,0],[0,0,-1],axis)},
};
const definitions=[...previous.definitions], manifestFiles=[];
for(const [id,p] of Object.entries(d.parts)){
 const glb=cad+p.stem+'.glb',manifest=cad+p.stem+'.manifest.json',sha=await hash(glb);
 const files={};
 for(const [k,f] of Object.entries({glb,cad:cad+p.stem+'.FCStd',step:cad+p.stem+'.step',blender:'blender/stage4b/wave2/'+p.stem+'.blend'})){
  files[k]={path:f.split('/').at(-1),repository_path:f,sha256:await hash(f)};
 }
 const def={id,upstream_id:id,revision:d.revision,pose:null,subset:null,basis:'D',eligibility:'reference_only',label:p.label,nodes:[p.node],ports:ports[id],manifest,glb,glb_sha256:sha};
 definitions.push(def);
 await output(manifest,pretty({schema_version:1,assembly_id:id,revision:d.revision,basis:'D',cad_eligibility:'reference_only',unit:'m',frame:d.frame,material:p.material,ports:def.ports,files,parts:[{glb_node:p.node,bounds_m:p.bounds_mm.map(v=>v/1000)}]}));
 manifestFiles.push(...Object.values(files).map(f=>f.repository_path),manifest);
}
const catalog={schema_version:1,unit:'m',frame:d.frame,basis:'D',baseline_commit:d.baseline,definitions,limits:{model:'D1_REFERENCE_ONLY',historical:'UNKNOWN',continuous_mechanical_certification:'UNKNOWN',load:'NOT_TESTED'}};
await output(assembly+'catalog.json',pretty(catalog));
await output(assembly+'example.json',await poseDocument(catalog,d,left,'closed'));
const files=[...manifestFiles,assembly+'catalog.json',assembly+'design.json',assembly+'example.json',assembly+'poses.mjs'].sort();
await output('docs/stage4b/wave2-SHA256SUMS',(await Promise.all(files.map(async p=>(await hash(p))+'  '+p))).join('\n')+'\n');
console.log('Stage 4-B wave 2: fixed catalog, originals and closed pose',write?'generated':'checked');
