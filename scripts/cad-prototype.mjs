import {readFileSync}from'node:fs';import{createHash}from'node:crypto';import{fileURLToPath}from'node:url';
export const root=fileURLToPath(new URL('../',import.meta.url));export const hash=b=>createHash('sha256').update(b).digest('hex');
export function validateSnapshot(s){
 if(s.eligibility!=='reference_only'||s.formal_cad_adoption!==false)throw Error('FORMAL_ADOPTION');
 if(s.commit!=='68c039d8c1c40b81cac0f7e16fa800678ccc6de8'||s.tree!=='6662636d218d2e359de694aede3b25a208f9cd99')throw Error('BASE_PIN');
 if(JSON.stringify(Object.keys(s.source_hashes).sort())!==JSON.stringify(['design/cad-reference.json','design/decisions/DEC-0001-r1.json','design/decisions/DEC-0002-r1.json','catalog/wooden-palisade-v0.json'].sort()))throw Error('SOURCE_SET');
 for(const [p,h]of Object.entries(s.source_hashes)){if(hash(readFileSync(root+p))!==h)throw Error('SOURCE_HASH')}
 const original=JSON.parse(readFileSync(root+'design/cad-reference.json'));if(JSON.stringify(s.decisions)!==JSON.stringify(original))throw Error('DECISION_MUTATION');
 
 for(const d of s.decisions){if(d.eligibility!=='reference_only'||d.write_allowed!==false)throw Error('CAD_WRITE');for(const p of d.parameters){if(p.historical_value!==null||p.hypothesis_value!==null)throw Error('HISTORY_PROMOTION');if(p.prototype_value!==null&&p.basis!=='D')throw Error('BASIS');}}
 return true;
}
export function preserve(){const bytes=readFileSync(root+'cad/prototype-v1/baseline.json');if(hash(bytes)!=='9f238a06004cbfa7d004e21779ada93981122463cff3fd71374347d54c258082')throw Error('BASELINE_PIN');const b=JSON.parse(bytes);for(const[p,h]of Object.entries(b.hashes))if(hash(readFileSync(root+p))!==h)throw Error('BASELINE_CHANGED '+p);return Object.keys(b.hashes).length}
export function glbAudit(bytes){
 if(bytes.toString('utf8',0,4)!=='glTF'||bytes.readUInt32LE(4)!==2||bytes.readUInt32LE(8)!==bytes.length)throw Error('GLB_HEADER');
 const n=bytes.readUInt32LE(12),g=JSON.parse(bytes.toString('utf8',20,20+n)),bin=bytes.subarray(28+n);const seen=[],points=[];
 function transform(p,node){if(node.matrix){const m=node.matrix;return[0,1,2].map(i=>m[i]*p[0]+m[i+4]*p[1]+m[i+8]*p[2]+m[i+12])}const s=node.scale??[1,1,1],q=node.rotation??[0,0,0,1],t=node.translation??[0,0,0];let[x,y,z]=p.map((v,i)=>v*s[i]);const[a,b,c,w]=q,tx=2*(b*z-c*y),ty=2*(c*x-a*z),tz=2*(a*y-b*x);return[x+w*tx+b*tz-c*ty+t[0],y+w*ty+c*tx-a*tz+t[1],z+w*tz+a*ty-b*tx+t[2]]}
 function visit(i,anc=[]){const node=g.nodes[i],chain=[node,...anc];if(node.mesh!==undefined){seen.push(node.name);for(const p of g.meshes[node.mesh].primitives){const a=g.accessors[p.attributes.POSITION],v=g.bufferViews[a.bufferView];if(a.componentType!==5126||a.type!=='VEC3')throw Error('POSITION_FORMAT');for(let j=0;j<a.count;j++){const offset=(v.byteOffset??0)+(a.byteOffset??0)+j*(v.byteStride??12);let point=[0,4,8].map(k=>bin.readFloatLE(offset+k));for(const nd of chain)point=transform(point,nd);points.push(point)}}}for(const c of node.children??[])visit(c,chain)}
 for(const n of g.scenes[g.scene??0].nodes)visit(n);const dims=[0,1,2].map(i=>Math.max(...points.map(p=>p[i]))-Math.min(...points.map(p=>p[i])));
 if(seen.length!==7||seen.filter(n=>n.startsWith('Post_')).length!==5||seen.filter(n=>n.startsWith('Rail_')).length!==2)throw Error('COMPONENT_SET');
 if(dims.some((d,i)=>Math.abs(d-[4.95,2,.249][i])>1e-5))throw Error('DIMENSIONS');
 if(!g.images?.length||g.images.some(x=>x.uri))throw Error('EMBEDDED_TEXTURE');
 return{dimensions_m_y_up:dims,objects:seen,bytes:bytes.length,materials:g.materials.length,images:g.images.length,vertices:points.length};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){validateSnapshot(JSON.parse(readFileSync(root+'cad/prototype-v1/reference-snapshot.json')));console.log(JSON.stringify({preserved:preserve(),glb:glbAudit(readFileSync(root+'site/cad/palisade.glb'))},null,2))}
