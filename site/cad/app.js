const host=document.querySelector('#viewport'),status=document.querySelector('#status');
const buttons=[...document.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);
let unavailable=false;
function failure(message){unavailable=true;delete status.dataset.loaded;status.textContent=message;status.dataset.error='true';buttons.forEach(b=>b.disabled=true)}
try{
 const THREE=await import('three');const {OrbitControls}=await import('three/addons/controls/OrbitControls.js');const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#c5c9b5');const camera=new THREE.PerspectiveCamera(40,1,.05,100);
 const controls=new OrbitControls(camera,renderer.domElement);controls.minDistance=3;controls.maxDistance=25;controls.enablePan=false;
 scene.add(new THREE.HemisphereLight(0xffffff,0x4d493b,2.4));const sun=new THREE.DirectionalLight(0xffebca,3);sun.position.set(-4,8,5);scene.add(sun);
 const render=()=>{if(!unavailable)renderer.render(scene,camera)};function reset(){camera.position.set(5,3.2,7);controls.target.set(0,1,0);controls.update();render()}
 new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();render()}).observe(host);controls.addEventListener('change',render);reset();
 renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();failure('WebGLの接続が失われました。ページを再読み込みしてください。')});
 const gltf=await new GLTFLoader().loadAsync('./palisade.glb');if(unavailable){gltf.scene.traverse(o=>{o.geometry?.dispose();if(o.material)o.material.dispose()});throw new Error('WebGL接続喪失後の遅延ロードを無効化しました')}scene.add(gltf.scene);const box=new THREE.Box3().setFromObject(gltf.scene);const size=box.getSize(new THREE.Vector3());
 if(Math.abs(size.x-4.95)>1e-5||Math.abs(size.y-2)>1e-5)throw new Error('GLB寸法が契約と一致しません');
 document.querySelector('#measured').textContent=`GLB実測: 幅 ${size.x.toFixed(2)} m / 高さ ${size.y.toFixed(2)} m`;
 status.textContent='CAD由来GLBを読み込みました（試作D・5本／横木2段）';status.dataset.loaded='true';buttons.forEach(b=>b.disabled=false);render();
 for(const [id,angle]of [['left',-.2],['right',.2]])document.querySelector('#'+id).onclick=()=>{camera.position.sub(controls.target).applyAxisAngle(new THREE.Vector3(0,1,0),angle).add(controls.target);controls.update();render()};
 for(const [id,factor]of [['near',.85],['far',1.15]])document.querySelector('#'+id).onclick=()=>{camera.position.sub(controls.target).multiplyScalar(factor).add(controls.target);controls.update();render()};document.querySelector('#reset').onclick=reset;
}catch(e){failure('3D表示を開始できません。WebGL対応・GLB・CDNの接続を確認してください。詳細: '+e.message)}
