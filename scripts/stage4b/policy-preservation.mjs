import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const root='evidence/stage4b/policy-migration/';
const records={
 "AGENTS.md": { prior:"AGENTS.md.txt", before:"214c11b29e29c95284150648314ec7c9faaa41c42e89ab7c365af796f5ab09de", after:"9e369db30e5ec846a046be5ffbe3905b0bf8d860a0cb3d439bb0aa1c4d8285fe" },
 "scripts/stage2d/preservation.mjs": { prior:"stage2d-preservation.mjs.txt", before:"efe2cc3fc367162c0f104f0d41756456f0a611378c5c207a24aef78b3cb4b37b", after:"05ec48c77b34cf3ef046aa0100619b2cf348129ec1ccfcc1fc4c5a79dadcd311" },
};

const exactAgentsAppend = Buffer.from("\n## 開発・提出の基本単位（2026-11-27 JST・所有者方針）\n\n- Stage 4-B 以降の原則は、単体部品1点ではなく、左門扉・柵ユニットなど建築上意味のある**組立単位**で開発・提出すること。単体試作と個別の作業・妥当性検証は引き続き可能。\n- 同形状部品は一つの原本・型式を参照し、配置・姿勢・個数は組立側で管理する。提供時は版、固定コミット、ハッシュ、座標系、根拠、未確定事項を明記する。\n- [開発ロードマップ](docs/development-roadmap.md)を参照。展示室の部品観察と設計工房を維持し、城別採用、歴史的確証、構造安全性、本番公開は組立の技術的受入と別判断とする。\n",'utf8');
const h=b=>createHash('sha256').update(b).digest('hex');

/** Preserve exactly the prior two code/policy files, never an arbitrary alternative. */
export function priorPolicyBytes(path,current,read){
 if(!Object.hasOwn(records,path))return null;
 let raw;
 try{raw=read(root+'manifest.json')}
 catch(e){if(e.code==='ENOENT')return null;throw e;}
 const {files}=JSON.parse(raw);
 assert.deepEqual(Object.keys(files),Object.keys(records));
 const e=files[path], fixed=records[path];
 assert.equal(e.previous,root+fixed.prior);
 assert.equal(e.before_sha256,fixed.before,'unexpected predecessor fingerprint');
 assert.equal(e.after_sha256,fixed.after,'unexpected approved replacement fingerprint');
 if(h(current)!==fixed.after)return null;
 const prior=read(e.previous);
 assert.equal(h(prior),fixed.before);
 if(path==='AGENTS.md')assert(current.equals(Buffer.concat([prior,exactAgentsAppend])),'unapproved policy edit');
 return prior;
}
