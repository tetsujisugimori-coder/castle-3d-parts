import {inflateSync} from 'node:zlib';

const paeth=(a,b,c)=>{
 const p=a+b-c,da=Math.abs(p-a),db=Math.abs(p-b),dc=Math.abs(p-c);
 return da<=db&&da<=dc?a:db<=dc?b:c;
};

/** Decode 8-bit, non-interlaced Chromium/WebKit RGB(A) screenshots for pixel evidence. */
export function screenshotCoverage(png){
 if(!Buffer.isBuffer(png)||png.length<45||png.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('not PNG');
 const chunks=[];
 let w=0,h=0,n=0;
 for(let i=8;i<png.length;){
  const len=png.readUInt32BE(i),type=png.toString('ascii',i+4,i+8),p=i+8;
  if(p+len+4>png.length)throw Error('truncated PNG');
  if(type==='IHDR'){
   w=png.readUInt32BE(p);h=png.readUInt32BE(p+4);
   n=({2:3,6:4})[png[p+9]];
   if(len!==13||png[p+8]!==8||!n||png[p+10]||png[p+11]||png[p+12]||w*h>4000000||!w||!h)
    throw Error('unsupported screenshot format');
  }else if(type==='IDAT')chunks.push(png.subarray(p,p+len));
  i=p+len+4;
 }
 if(!n||!chunks.length)throw Error('missing PNG data');
 const stride=w*n;
 const input=inflateSync(Buffer.concat(chunks),{maxOutputLength:h*(stride+1)});
 if(input.length!==h*(stride+1))throw Error('wrong PNG raster length');
 let previous=new Uint8Array(stride),woodPixels=0;
 let xmin=w,xmax=-1,ymin=h,ymax=-1;
 for(let y=0;y<h;y++){
  const at=y*(stride+1),filter=input[at],row=new Uint8Array(stride);
  if(filter>4)throw Error('unknown PNG filter');
  for(let x=0;x<stride;x++){
   const left=x<n?0:row[x-n],up=previous[x],corner=x<n?0:previous[x-n];
   const adjust=filter===0?0:filter===1?left:filter===2?up:filter===3?((left+up)>>1):paeth(left,up,corner);
   row[x]=input[at+1+x]+adjust;
  }
  // D0 meshes are brown, unlike the pale neutral green grid and background.
  for(let x=0;x<w;x++){
   const i=x*n,[red,green,blue]=row.subarray(i,i+3);
   if(red>green+14 && green>blue+10 && red<235 && (n===3||row[i+3]===255)){
    woodPixels++;xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);
   }
  }
  previous=row;
 }
 return {width:w,height:h,woodPixels,ratio:woodPixels/(w*h),bounds:[xmin,ymin,xmax,ymax]};
}
export function assertLeafPixels(png){
 const r=screenshotCoverage(png),[x0,y0,x1,y1]=r.bounds;
 if(r.ratio<.015||r.ratio>.75||x1-x0<r.width*.05||y1-y0<r.height*.35)
  throw Error('left gate brown rendered surface not found: '+JSON.stringify(r));
 return r;
}
