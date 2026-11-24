import {createGlbAssembler} from '../../assembly/stage4a/glb-scene.mjs';
import {parseUniqueJson} from '../../assembly/stage4a/json-data.mjs';

const $=id=>document.getElementById(id),host=$('viewport'),status=$('status');
const root=new URL('../../',import.meta.url);
const controlsIds=['fit','turn','zoom','zoom-out'];
const enable=value=>controlsIds.forEach(id=>$(id).disabled=!value);
const message=(state,text)=>{status.dataset.state=state;status.textContent=text};
async function json(path){
  const r=await fetch(new URL(path,root));
  if(!r.ok)throw Error('HTTP '+r.status+' '+path);
  return parseUniqueJson(await r.text());
}
try {
  const [THREE,{GLTFLoader},{OrbitControls}]=await Promise.all([
    import('three'),import('three/addons/loaders/GLTFLoader.js'),
    import('three/addons/controls/OrbitControls.js')
  ]);
  const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'low-power'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  host.append(renderer.domElement);
  const scene=new THREE.Scene();scene.background=new THREE.Color('#c7cdbb');
  const camera=new THREE.PerspectiveCamera(40,1,.05,200);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=false;controls.minDistance=.5;controls.maxDistance=100;
  camera.position.set(9,6,15);controls.target.set(0,1,0);
  scene.add(new THREE.HemisphereLight(0xffffff,0x554c3b,2.4));
  const light=new THREE.DirectionalLight(0xffeed0,3);light.position.set(-4,8,5);scene.add(light);
  const grid=new THREE.GridHelper(24,24,0x9aa99a,0xaeb9a9);grid.position.y=-.015;scene.add(grid);
  const markerGeometry=new THREE.SphereGeometry(.045,12,8);
  const markerMaterial=new THREE.MeshBasicMaterial({color:0x17834b});
  let current=null,epoch=0,lost=false;
  const render=()=>{if(!lost)renderer.render(scene,camera)};
  function size(){
    if(!host.clientWidth||!host.clientHeight)return;
    renderer.setSize(host.clientWidth,host.clientHeight,false);
    camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();render();
  }
  function fit(){
    if(!current||lost)return;
    const bounds=new THREE.Box3().setFromObject(current.group,true);
    const centre=bounds.getCenter(new THREE.Vector3());
    const radius=Math.max(.2,bounds.getBoundingSphere(new THREE.Sphere()).radius);
    const halfY=THREE.MathUtils.degToRad(camera.fov)/2;
    const halfX=Math.atan(Math.tan(halfY)*camera.aspect);
    const dist=1.2*radius/Math.sin(Math.min(halfX,halfY));
    controls.maxDistance=Math.max(100,dist*2);
    camera.far=Math.max(200,dist*4);camera.updateProjectionMatrix();
    controls.target.copy(centre);
    camera.position.copy(centre).add(new THREE.Vector3(.30,.36,1).normalize().multiplyScalar(dist));
    controls.update();render();
  }
  controls.addEventListener('change',render);
  new ResizeObserver(size).observe(host);size();
  $('fit').onclick=fit;
  $('turn').onclick=()=>{camera.position.sub(controls.target).applyAxisAngle(new THREE.Vector3(0,1,0),Math.PI/6).add(controls.target);controls.update()};
  function zoom(scale){
    const delta=camera.position.clone().sub(controls.target);
    delta.setLength(THREE.MathUtils.clamp(delta.length()*scale,controls.minDistance,controls.maxDistance));
    camera.position.copy(controls.target).add(delta);controls.update();
  }
  $('zoom').onclick=()=>zoom(.8);$('zoom-out').onclick=()=>zoom(1.25);
  renderer.domElement.addEventListener('webglcontextlost',e=>{
    e.preventDefault();lost=true;epoch++;enable(false);$('reload').disabled=true;
    message('error','WebGL接続喪失。ページを再読み込みしてください。');
  });
  async function reload(){
    const ticket=++epoch;
    message('loading','固定GLBと配置データを照合中…');
    let candidate=null;
    try {
      const [catalog,example]=await Promise.all([
        json('assembly/stage4a/catalog.json'),json('assembly/stage4a/example.json')
      ]);
      // Fresh assembler per reload ensures bytes are actually re-fetched.
      candidate=await createGlbAssembler({THREE,GLTFLoader,catalog,root}).prepare(example);
      if(ticket!==epoch||lost)return;
      const markers=new THREE.Group();markers.name='connection-markers';
      for(const row of candidate.connectionRows){
        const marker=new THREE.Mesh(markerGeometry,markerMaterial);
        marker.position.fromArray(row.point);markers.add(marker);
      }
      candidate.group.add(markers);
      const old=current;scene.add(candidate.group);
      if(old)scene.remove(old.group);
      current=candidate;
      try{fit()}catch(e){
        scene.remove(candidate.group);current=old;if(old)scene.add(old.group);throw e;
      }
      $('parts').replaceChildren(...example.instances.map(i=>{
        const li=document.createElement('li');
        li.textContent=i.id+' / '+i.definition_id+' / CAD座標 '+i.translation_m.join(', ')+' m';
        return li;
      }));
      enable(true);
      message('ready',candidate.instances.size+'配置・'+candidate.rows.length+'メッシュ・'+
        candidate.connectionRows.length+'接続点一致。試作D・参照模型。');
    }catch(e){
      if(ticket===epoch&&!lost){
        enable(Boolean(current));
        message('error','読込み失敗：'+e.message+(current?'（最後の有効表示を保持）':''));
      }
    }
  }
  $('reload').disabled=false;$('reload').onclick=reload;
  await reload();
}catch(e){enable(false);message('error','3D表示を開始できません：'+e.message)}
