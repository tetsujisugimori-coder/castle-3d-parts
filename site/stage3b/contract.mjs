// CAD manifest is the sole source of pivot, range, moving parts and units.
export {verifyHash} from '../stage2c/contract.mjs';
const ok=(v,m)=>{if(!v)throw Error(m)};
export function validateMechanism(m){
 ok(m?.schema_version===1&&m.basis==='D'&&m.cad_eligibility==='reference_only'&&m.unit==='m'&&m.up==='Z','mechanism classification/units');
 ok(Array.isArray(m.pivot_m)&&m.pivot_m.length===3&&m.pivot_m.every(Number.isFinite),'CAD pivot');
 ok(Array.isArray(m.angle_range_deg)&&m.angle_range_deg.length===2&&m.angle_range_deg.every(Number.isFinite)&&m.angle_range_deg[0]===0&&m.angle_range_deg[1]>0,'angle range');
 ok(Array.isArray(m.parts)&&m.parts.length>=7&&new Set(m.parts.map(p=>p.id)).size===m.parts.length,'part identities');
 for(const p of m.parts)ok(typeof p.id==='string'&&/^[A-Za-z][A-Za-z0-9_]+$/.test(p.id)&&Array.isArray(p.bounds_m)&&p.bounds_m.length===6&&p.bounds_m.every(Number.isFinite)&&p.bounds_m.slice(0,3).every((v,i)=>v<=p.bounds_m[i+3]),'part bounds');
 ok(Array.isArray(m.moving_ids)&&m.moving_ids.length>0&&new Set(m.moving_ids).size===m.moving_ids.length&&m.moving_ids.every(id=>m.parts.some(p=>p.id===id)),'moving IDs');
 ok(m.glb?.path==='assembly.glb'&&/^[a-f0-9]{64}$/.test(m.glb.sha256),'GLB reference/hash');
 ok(Array.isArray(m.sampled_angles_deg)&&m.sampled_angles_deg.length>=2&&m.sampled_angles_deg.every((a,i)=>Number.isFinite(a)&&a>=m.angle_range_deg[0]&&a<=m.angle_range_deg[1]&&(i===0||a>m.sampled_angles_deg[i-1]&&a-m.sampled_angles_deg[i-1]<=1))&&m.sampled_angles_deg[0]===m.angle_range_deg[0]&&m.sampled_angles_deg.at(-1)===m.angle_range_deg[1],'collision sample coverage');return m;
}
export function angleWithin(value,range){if(!Number.isFinite(value)||value<range[0]||value>range[1])throw Error('angle outside CAD limits');return value}
export function posePoint(p,pivot,angle){const r=angle*Math.PI/180,c=Math.cos(r),s=Math.sin(r),x=p[0]-pivot[0],y=p[1]-pivot[1];return[pivot[0]+x*c-y*s,pivot[1]+x*s+y*c,p[2]]}
export function advance(angle,target,seconds,speed=30){if(![angle,target,seconds,speed].every(Number.isFinite)||seconds<0||speed<=0)throw Error('invalid motion input');return angle+Math.sign(target-angle)*Math.min(Math.abs(target-angle),seconds*speed)}
export function sampleStatus(m,angle){return m.sampled_angles_deg.some(a=>Math.abs(a-angle)<1e-8)?'静的角度検査の対象':'角度間は未検査（連続非干渉 UNKNOWN）'}
export function validateCollision(m,c){
 ok(m.collision?.path==='collision.json'&&/^[a-f0-9]{64}$/.test(m.collision.sha256),'collision hash/path');
 ok(Array.isArray(m.collision_ids)&&new Set(m.collision_ids).size===m.collision_ids.length&&m.parts.every(p=>m.collision_ids.includes(p.id)),'collision IDs');
 ok(Number.isFinite(c.tolerance_mm3)&&c.tolerance_mm3>=0&&c.tolerance_mm3<=1e-3,'collision tolerance');
 const key=(a,b)=>[a,b].sort().join('|'),expected=new Set();for(let i=0;i<m.collision_ids.length;i++)for(let j=0;j<i;j++)if(m.moving_ids.includes(m.collision_ids[i])||m.moving_ids.includes(m.collision_ids[j]))expected.add(key(m.collision_ids[i],m.collision_ids[j]));
 ok(Array.isArray(c.samples)&&c.samples.length===m.sampled_angles_deg.length,'collision samples');for(const[ridx,r]of c.samples.entries()){ok(r.angle_degrees===m.sampled_angles_deg[ridx]&&Array.isArray(r.pairs)&&r.pairs.length===expected.size,'collision coverage');const seen=new Set();for(const p of r.pairs){const k=key(p.a,p.b);ok(expected.has(k)&&!seen.has(k),'collision pair identity');seen.add(k);ok(Number.isFinite(p.distance_m)&&p.distance_m>=0&&Number.isFinite(p.overlap_mm3)&&p.overlap_mm3>=0,'collision quantities');const contact=p.overlap_mm3>c.tolerance_mm3?'PENETRATION':p.distance_m<1e-8?'TOUCHING':'CLEAR';ok(p.contact===contact,'collision classification')}}return c;
}
export function validateProjectionMesh(m,data){
 ok(/^[a-f0-9]{64}$/.test(m.evidence_hashes?.['mesh-transfer.json']||''),'projection hash');
 ok(Array.isArray(data.pivot_m)&&data.pivot_m.length===3&&data.pivot_m.every((v,i)=>v===m.pivot_m[i]),'projection pivot');
 ok(Array.isArray(data.objects)&&data.objects.length===m.parts.length&&new Set(data.objects.map(o=>o.id)).size===m.parts.length,'projection part count');
 for(const o of data.objects){const p=m.parts.find(p=>p.id===o.id);ok(p&&o.moving===m.moving_ids.includes(o.id),'projection identity/motion');ok(Array.isArray(o.vertices_m)&&o.vertices_m.length>=4&&o.vertices_m.every(v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite)),'projection vertices');ok(Array.isArray(o.faces)&&o.faces.length>0&&o.faces.every(f=>Array.isArray(f)&&f.length===3&&new Set(f).size===3&&f.every(i=>Number.isInteger(i)&&i>=0&&i<o.vertices_m.length)),'projection triangle indices');const b=[0,1,2].map(i=>Math.min(...o.vertices_m.map(v=>v[i]))).concat([0,1,2].map(i=>Math.max(...o.vertices_m.map(v=>v[i]))));ok(b.every((v,i)=>Math.abs(v-p.bounds_m[i])<1e-4),'projection CAD bounds')}return data;
}
export function projectedTriangles(vertices,faces,projection){const p=vertices.map(v=>projection==='top'?[v[0],-v[1]]:projection==='front'?[v[0],-v[2]]:[v[1],-v[2]]);return faces.map(f=>{let t=f.map(i=>p[i]);const cross=(t[1][0]-t[0][0])*(t[2][1]-t[0][1])-(t[1][1]-t[0][1])*(t[2][0]-t[0][0]);if(Math.abs(cross)<1e-14)return'';if(cross<0)t=[t[0],t[2],t[1]];return'M'+t.map(x=>x.join(',')).join('L')+'Z'}).join('')}
