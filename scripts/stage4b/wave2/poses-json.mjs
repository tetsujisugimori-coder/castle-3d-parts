import {readFileSync} from 'node:fs';
import {modelPose,poses} from '../../../assembly/stage4b-wave2/poses.mjs';
const data=p=>JSON.parse(readFileSync(p,'utf8'));
const c=data('assembly/stage4b-wave2/catalog.json'),d=data('assembly/stage4b-wave2/design.json'),l=data('assembly/stage4b/example.json');
console.log(JSON.stringify(Object.fromEntries(Object.keys(poses).map(p=>[p,modelPose(c,d,l,p)])),null,2));
