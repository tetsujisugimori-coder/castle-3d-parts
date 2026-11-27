import {rotate,saveAssembly} from '../stage4a/contract.mjs';

export const poses=Object.freeze({closed:'閉鎖',left:'左だけ開放',right:'右だけ開放',both:'両開放'});
const check=(ok,message)=>{if(!ok)throw Error(message)};
const sideKeys=['L','R'];
const own=(o,k)=>Object.hasOwn(o,k);
const conn=(a,p,b,q)=>({a:{instance_id:a,port:p},b:{instance_id:b,port:q}});
const instance=(id,definition_id,revision,mm,yaw_quarters=0)=>({id,definition_id,revision,pose:null,translation_m:mm.map(x=>x/1000),yaw_quarters});

export function modelPose(catalog,design,leftExample,pose){
 check(own(poses,pose),'unknown fixed gate pose');
 const ids=['YAM-WEST-LEFT-BOARD','YAM-WEST-LEFT-RAIL'];
 check(leftExample.instances.length===8&&leftExample.instances.every(i=>ids.includes(i.definition_id)&&i.revision==='D0'&&i.yaw_quarters===0),'incompatible D0 leaf');
 const instances=[],connections=[];
 for(const side of sideKeys){
  const isLeft=side==='L', outward=isLeft?-1:1;
  const opening=pose===(isLeft?'left':'right')||pose==='both';
  const q=opening?(isLeft?1:3):0;
  const fixedYaw=isLeft?0:2;
  const pivot=[outward*design.pivot_x,design.pivot_y,0];
  const post=side+'-post';
  const place=(v)=>rotate(v.map((x,k)=>x-pivot[k]),q).map((x,k)=>x+pivot[k]);
  instances.push(instance(post,'YAM-WEST-POST','D1',[outward*(design.pivot_x+300),design.pivot_y,0],fixedYaw));
  for(const p of leftExample.instances){
   const wide=p.definition_id===ids[0]?270:1850;
   const [dx,y,z]=p.translation_m.map(v=>Math.round(v*1000));
   // D0 preserved as local part geometry; right placement mirrors the occupied
   // rectangle, not a negative scale or a flip of the face/grain orientation.
   const x=dx-1805;
   instances.push(instance(side+'-'+p.id,p.definition_id,'D0',place([isLeft?x:-x-wide,y,z+design.leaf_ground]),q));
  }
  design.bearing_z.forEach((z,i)=>{
   const b=side+'-bearing-'+i,p=side+'-pin-'+i;
   instances.push(instance(b,'YAM-WEST-BEARING','D1',[pivot[0],pivot[1],z],fixedYaw),
     instance(p,'YAM-WEST-PIVOT','D1',[pivot[0],pivot[1],z],(fixedYaw+q)%4));
   connections.push(conn(post,'mount-'+i,b,'post'),conn(b,'axis',p,'axis'));
  });
 }
 return {schema_version:2,unit:'m',frame:catalog.frame,basis:'D',catalog_commit:catalog.baseline_commit,instances,connections};
}

export async function poseDocument(catalog, design, leftExample, key){
 if(own(poses,key))return saveAssembly(catalog,modelPose(catalog,design,leftExample,key));
 const raw=modelPose(catalog,design,leftExample,'closed');
 if(key==='inspect-left'||key==='inspect-right'){
  const side=key==='inspect-left'?'L-':'R-';
  raw.instances=raw.instances.filter(i=>i.id.startsWith(side));
  raw.connections=raw.connections.filter(c=>c.a.instance_id.startsWith(side)&&c.b.instance_id.startsWith(side));
 }else{
  const part={post:'YAM-WEST-POST',bearing:'YAM-WEST-BEARING',pivot:'YAM-WEST-PIVOT'}[key];
  check(own(design.parts,part),'unknown inspection preset');
  raw.instances=[instance('P01',part,'D1',[0,0,0])];
  raw.connections=[];
 }
 return saveAssembly(catalog,raw);
}
