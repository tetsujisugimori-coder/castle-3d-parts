import{test}from'node:test';import assert from'node:assert/strict';import{readFileSync,existsSync}from'node:fs';import{validateManifest,validateMeshes}from'../site/stage3a/contract.mjs';
for(const pose of['B0','B1','B2'])test('gate '+pose+' strict manifest and corruption controls',()=>{
 const m=JSON.parse(readFileSync('cad/stage3a/generated/'+pose+'/link-manifest.json'));
 assert.equal(validateManifest(m,pose),m);
 const meshes=m.parts.map(p=>({name:p.glb_node,revision:m.assembly_id+'/'+pose,basis:'D',eligibility:'reference_only',bounds_m:[...p.bounds_m]}));assert.equal(validateMeshes(m,meshes),true);
 for(const mutate of[x=>x.pop(),x=>x[0].revision=pose,x=>x[0].bounds_m[0]+=.01]){const x=structuredClone(meshes);mutate(x);assert.throws(()=>validateMeshes(m,x))}

 for(const [name,mutate]of Object.entries({missingPart:x=>x.parts.pop(),duplicatePart:x=>x.parts[1]=x.parts[0],wrongPose:x=>x.revision='B9',wrongBasis:x=>x.basis='A',badHash:x=>x.files.glb.sha256='bad',unsafeRef:x=>x.parts[0].research_refs[0].path='../secret',dimensionNaN:x=>x.dimensions[0].value_m=NaN,missingDimension:x=>x.parts[0].dimension_ids=[],poseAncestry:x=>x.previous_revision='B0'})){const x=structuredClone(m);mutate(x);assert.throws(()=>validateManifest(x,pose),undefined,name)}
 for(const view of['front','side','top','pivot','connection'])assert(existsSync(`cad/stage3a/generated/${pose}/native-${view}.svg`));
});
