import {createGlbAssembler} from '../../assembly/stage4a/glb-scene.mjs';
import {saveAssembly} from '../../assembly/stage4a/contract.mjs';
import {parseUniqueJson} from '../../assembly/stage4a/json-data.mjs';
import {createWorkshopController,nextPlacement,translationFromFields,portOptions,MAX_IMPORT_BYTES} from '../../assembly/stage4a/workshop-ui.mjs';

const $=id=>document.getElementById(id);
const host=$('viewport'),status=$('status'),root=new URL('../../',import.meta.url);
const msg=(state,text)=>{status.dataset.state=state;status.textContent=text};
const gatePage=document.body.dataset.model==='west-gate-left';
const viewing=gatePage&&document.body.dataset.view==='exhibit';
const modelRoot=gatePage?'assembly/stage4b/':'assembly/stage4a/';
const label=d=>d.label??(d.id==='PAL-U01'?'木柵 U01（B0）':'簡易木戸（固定B0）');
const opt=(text,value)=>new Option(text,value);
const endLabel=e=>e.instance_id+' / '+e.port;
async function fetchText(path){const r=await fetch(new URL(path,root));if(!r.ok)throw Error('HTTP '+r.status+' '+path);return r.text()}
let lost=false;
try{
  const [THREE,{GLTFLoader},{OrbitControls},catalogText,exampleText]=await Promise.all([
    import('three'),import('three/addons/loaders/GLTFLoader.js'),import('three/addons/controls/OrbitControls.js'),
    fetchText(modelRoot+'catalog.json'),fetchText(modelRoot+'example.json')
  ]);
  const catalog=parseUniqueJson(catalogText);
  if(gatePage){
    const {validateFixedLeaf}=await import('../../assembly/stage4b/fixed-leaf.mjs');
    await validateFixedLeaf(catalog,exampleText);
  }
  const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'low-power'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  host.append(renderer.domElement);
  const scene=new THREE.Scene();scene.background=new THREE.Color('#c7cdbb');
  const camera=new THREE.PerspectiveCamera(40,1,.05,200);camera.position.set(9,6,15);
  const orbit=new OrbitControls(camera,renderer.domElement);
  orbit.enableDamping=false;orbit.minDistance=.5;orbit.maxDistance=100;orbit.target.set(0,1,0);
  scene.add(new THREE.HemisphereLight(0xffffff,0x554c3b,2.4));
  const light=new THREE.DirectionalLight(0xffeed0,3);light.position.set(-4,8,5);scene.add(light);
  const grid=new THREE.GridHelper(24,24,0x9aa99a,0xaeb9a9);grid.position.y=-.015;scene.add(grid);
  const markerGeometry=new THREE.SphereGeometry(.045,12,8),markerMaterial=new THREE.MeshBasicMaterial({color:0x17834b});
  const assembler=createGlbAssembler({THREE,GLTFLoader,catalog,root});
  let view=null,selected='',busy=false,selectionBox=null;
  const render=()=>{if(!lost)renderer.render(scene,camera)};
  const size=()=>{
    if(lost||!host.clientWidth||!host.clientHeight)return;
    renderer.setSize(host.clientWidth,host.clientHeight,false);
    camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();render();
  };
  function fit(target=view){
    if(!target||lost)return;
    const b=new THREE.Box3().setFromObject(target.group,true),centre=b.getCenter(new THREE.Vector3());
    const radius=Math.max(.2,b.getBoundingSphere(new THREE.Sphere()).radius);
    const halfY=THREE.MathUtils.degToRad(camera.fov)/2;
    const halfX=Math.atan(Math.tan(halfY)*camera.aspect);
    const dist=1.2*radius/Math.sin(Math.min(halfX,halfY));
    orbit.maxDistance=Math.max(100,dist*2);camera.far=Math.max(200,dist*4);camera.updateProjectionMatrix();
    orbit.target.copy(centre);camera.position.copy(centre).add(new THREE.Vector3(gatePage ? .08 : .30,gatePage ? .22 : .36,gatePage ? -1 : 1).normalize().multiplyScalar(dist));
    orbit.update();render();
  }
  function clearBox(){
    if(selectionBox){scene.remove(selectionBox);selectionBox.geometry.dispose();selectionBox.material.dispose();selectionBox=null}
  }
  function showSelection(){
    clearBox();
    const g=view?.instances.get(selected);
    if(g&&!viewing){selectionBox=new THREE.BoxHelper(g,0x1465a3);scene.add(selectionBox)}
    render();
  }
  function publish(candidate,next){
    const old=view;
    const oldCamera=camera.position.clone(),oldTarget=orbit.target.clone(),oldFar=camera.far,oldMax=orbit.maxDistance;
    const markers=new THREE.Group();
    for(const row of candidate.connectionRows){
      const marker=new THREE.Mesh(markerGeometry,markerMaterial);marker.position.fromArray(row.point);markers.add(marker);
    }
    candidate.group.add(markers);
    if(old)scene.remove(old.group);
    clearBox();scene.add(candidate.group);
    try{
      if(!old||viewing)fit(candidate);else render();
      if(lost||renderer.getContext().isContextLost())throw Error('WebGL context lost');
      view=candidate;
    }catch(e){
      scene.remove(candidate.group);
      if(old)scene.add(old.group);
      camera.position.copy(oldCamera);orbit.target.copy(oldTarget);camera.far=oldFar;orbit.maxDistance=oldMax;camera.updateProjectionMatrix();
      view=old;
      if(!lost){try{orbit.update();showSelection()}catch{}}
      throw e;
    }
  }
  const controller=createWorkshopController({catalog,prepare:a=>assembler.prepare(a),publish});
  function setOptions(el,options,preferred){
    const keep=preferred??el.value;
    el.replaceChildren(...options);
    if([...el.options].some(o=>o.value===keep))el.value=keep;
  }
  function syncEnabled(){
    const a=controller.snapshot(),ready=Boolean(a)&&!busy&&!lost;
    for(const el of document.querySelectorAll('[data-edit]'))el.disabled=!ready;
    for(const el of document.querySelectorAll('[data-selected]'))el.disabled=!ready||!selected;
    for(const el of document.querySelectorAll('button[data-view], button[data-preset]'))el.disabled=!view||lost||busy;
    for(const el of document.querySelectorAll('[data-connect]'))el.disabled=!ready||!$('port-a').value||!$('port-b').value;
    $('disconnect').disabled=!ready||!$('connection').value;
  }
  function fillSelection(a){
    const i=a.instances.find(i=>i.id===selected);
    $('selection').textContent=i?i.id+' / '+label(catalog.definitions.find(d=>d.id===i.definition_id)):'未選択';
    ['x','y','z'].forEach((key,k)=>$(key).value=i?String(i.translation_m[k]):'');
    $('yaw').textContent='回転角：'+(i?i.yaw_quarters*90+'°':'—');
    showSelection();
  }
  function refresh(preferred){
    const a=controller.snapshot();if(!a){syncEnabled();return}
    selected=a.instances.some(i=>i.id===preferred)?preferred:
      a.instances.some(i=>i.id===selected)?selected:a.instances[0].id;
    setOptions($('instance'),a.instances.map(i=>opt(i.id+' · '+label(catalog.definitions.find(d=>d.id===i.definition_id)),i.id)),selected);
    const free=portOptions(catalog,a).filter(p=>!p.occupied);
    for(const id of ['port-a','port-b'])setOptions($(id),[opt('選択してください',''),...free.map(p=>opt(endLabel(p.endpoint),p.key))]);
    setOptions($('connection'),[opt('選択してください',''),...a.connections.map(c=>opt(endLabel(c.a)+' ↔ '+endLabel(c.b),JSON.stringify(c)))]);
    $('summary').textContent='配置数：'+a.instances.length+' / メッシュ数：'+view.rows.length+' / 接続数：'+a.connections.length+'（接続点一致のみ）';
    fillSelection(a);syncEnabled();
  }
  async function run(action,success,preferred){
    if(busy||lost)return;
    busy=true;syncEnabled();msg('loading','処理中…');
    let applied=false;
    try{
      await action();applied=true;
      if(lost)return;
      refresh(typeof preferred==='function'?preferred():preferred);
      msg('ready',success);
    }catch(e){
      if(!lost){
        if(applied){controller.stop();lost=true;msg('error','操作完了後の画面更新に失敗しました。ページを再読み込みしてください：'+e.message);}
        else msg('error','操作を拒否しました：'+e.message+(controller.snapshot()?'（最後の有効配置を保持）':''));
      }
    }finally{busy=false;syncEnabled()}
  }
  const edit=(command,success,preferred)=>run(()=>controller.edit(command()),success,preferred);
  const current=()=>controller.snapshot().instances.find(i=>i.id===selected);
  const pair=()=>({a:JSON.parse($('port-a').value),b:JSON.parse($('port-b').value)});
  setOptions($('definition'),catalog.definitions.map(d=>opt(label(d),d.id)));
  function select(id){
    if(busy||lost)return;
    selected=id;$('instance').value=id;
    try{fillSelection(controller.snapshot());syncEnabled()}
    catch(e){controller.stop();lost=true;syncEnabled();msg('error','選択表示に失敗しました。ページを再読み込みしてください：'+e.message)}
  }
  $('instance').onchange=()=>select($('instance').value);
  for(const id of ['port-a','port-b','connection'])$(id).onchange=syncEnabled;
  $('add').onclick=()=>{
    let id='';
    edit(()=>{const op=nextPlacement(controller.snapshot(),$('definition').value);id=op.id;return op},'部品を追加しました。',()=>id);
  };
  $('move').onclick=()=>edit(()=>({kind:'move',id:selected,translation_m:translationFromFields(['x','y','z'].map(k=>$(k).value))}),'座標を更新しました。');
  for(const [id,step] of [['left',3],['right',1]])$(id).onclick=()=>edit(()=>({kind:'rotate',id:selected,yaw_quarters:(current().yaw_quarters+step)%4}),'回転しました。');
  $('remove').onclick=()=>edit(()=>({kind:'remove',id:selected}),'部品を削除しました。');
  $('connect').onclick=()=>edit(()=>({kind:'connect',...pair()}),'接続点を照合し、接続しました。');
  $('align').onclick=()=>edit(()=>({kind:'align-connect',...pair()}),'移動側を位置合わせし、接続しました。');
  $('disconnect').onclick=()=>edit(()=>({kind:'disconnect',...JSON.parse($('connection').value)}),'接続を解除しました。');
  $('save').onclick=()=>run(async()=>{$('json').value=await controller.save()},'保存用JSONを作成しました。');
  $('download').onclick=()=>run(async()=>{
    const text=await controller.save();$('json').value=text;
    const url=URL.createObjectURL(new Blob([text],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='castle-assembly-v2.json';document.body.append(a);
    a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
  },'保存用JSONを作成し、ダウンロードを要求しました。');
  $('load').onclick=()=>run(()=>controller.load($('json').value),'JSONを読み込みました。');
  $('load-file').onclick=()=>run(async()=>{
    const file=$('file').files[0];if(!file)throw Error('ファイルを選択してください。');
    if(file.size>MAX_IMPORT_BYTES)throw Error('ファイルが大きすぎます。');
    await controller.load(await file.text());
  },'ファイルを読み込みました。');
  $('example').onclick=()=>run(()=>controller.load(exampleText),gatePage?'左門扉の初期配置に戻しました。':'代表配置に戻しました。',gatePage?'B01':'F01');
  $('fit').onclick=()=>fit();$('turn').onclick=()=>{camera.position.sub(orbit.target).applyAxisAngle(new THREE.Vector3(0,1,0),Math.PI/6).add(orbit.target);orbit.update()};
  function zoom(scale){
    const d=camera.position.clone().sub(orbit.target);
    d.setLength(THREE.MathUtils.clamp(d.length()*scale,orbit.minDistance,orbit.maxDistance));
    camera.position.copy(orbit.target).add(d);orbit.update();
  }
  $('zoom').onclick=()=>zoom(.8);$('zoom-out').onclick=()=>zoom(1.25);
  orbit.addEventListener('change',render);
  new ResizeObserver(size).observe(host);size();
  let pointer=null;
  const ray=new THREE.Raycaster();
  renderer.domElement.addEventListener('pointerdown',e=>{if(e.isPrimary)pointer={id:e.pointerId,x:e.clientX,y:e.clientY};else pointer=null});
  renderer.domElement.addEventListener('pointercancel',()=>pointer=null);
  renderer.domElement.addEventListener('pointerup',e=>{
    const p=pointer;pointer=null;
    if(!p||p.id!==e.pointerId||busy||lost||!view||Math.hypot(e.clientX-p.x,e.clientY-p.y)>5)return;
    const b=renderer.domElement.getBoundingClientRect();
    if(!b.width||!b.height)return;
    ray.setFromCamera(new THREE.Vector2((e.clientX-b.left)/b.width*2-1,-(e.clientY-b.top)/b.height*2+1),camera);
    const hit=ray.intersectObjects([...view.instances.values()],true)[0]?.object;
    if(hit?.parent?.userData.instance_id){
      select(hit.parent.userData.instance_id);
    }
  });
  renderer.domElement.addEventListener('webglcontextlost',e=>{
    e.preventDefault();lost=true;controller.stop();syncEnabled();msg('error','WebGL接続喪失。ページを再読み込みしてください。');
  });
  if(viewing){
    const a=parseUniqueJson(exampleText);
    const choices={assembly:null,board:'YAM-WEST-LEFT-BOARD',rail:'YAM-WEST-LEFT-RAIL'};
    for(const button of document.querySelectorAll('button[data-preset]')){
      button.onclick=()=>run(async()=>{
        const key=button.dataset.preset;
        if(!Object.hasOwn(choices,key))throw new Error('不明な展示');
        const entry=catalog.definitions.find(d=>d.id===choices[key]);
        await controller.load(entry?await saveAssembly(catalog,{...a,instances:[{
          id:'P01',definition_id:entry.id,revision:entry.revision,pose:entry.pose,translation_m:[0,0,0],yaw_quarters:0,
        }],connections:[]}):exampleText);
        for(const b of document.querySelectorAll('button[data-preset]'))b.setAttribute('aria-pressed',String(b===button));
      },button.textContent+'を表示しました。');
    }
  }
  await run(()=>controller.load(exampleText),gatePage?'左門扉を読み込みました。':'代表配置を読み込みました。',gatePage?'B01':'F01');
  // Initial loading may fail; a reload is a deliberate fresh page request.
  if(!controller.snapshot()&&!lost)msg('error',status.textContent+' ページを再読み込みしてください。');
}catch(e){msg('error','3D工房を開始できません：'+e.message)}
