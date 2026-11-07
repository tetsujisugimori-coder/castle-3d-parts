import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { layoutFence } from "./fence.mjs";

const host = document.getElementById("viewport");
const loading = document.getElementById("loading");
const status = document.getElementById("status");
const inputs = Object.fromEntries(
  ["count", "height", "spacing", "rails"].map(k => [k, document.getElementById(k)])
);
const text = (id, value) => { document.getElementById(id).textContent = value; };
const fmt = n => n.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
let initial;
try {
  const response = await fetch("./data/wooden-palisade-v0.json");
  if (!response.ok) throw new Error("catalog HTTP " + response.status);
  initial = (await response.json()).dimensions_m;
  for (const name of Object.keys(inputs)) inputs[name].value = initial[name];
  start();
} catch (error) {
  loading.textContent = "表示の準備に失敗しました。通信接続と再読み込みを確認してください。";
  console.error(error);
}

function start() {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 150);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  host.appendChild(renderer.domElement);
  loading.remove();

  scene.add(new THREE.HemisphereLight(0xdce8db, 0x4e4837, 2.1));
  const sun = new THREE.DirectionalLight(0xffedcf, 2.8);
  sun.position.set(-4, 9, 6);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  sun.shadow.camera.left = -20;
  sun.shadow.camera.right = 20;
  sun.shadow.camera.top = 20;
  sun.shadow.camera.bottom = -20;
  scene.add(sun);

  const earth = new THREE.Mesh(new THREE.PlaneGeometry(80, 80),
    new THREE.MeshStandardMaterial({ color: 0x58664f, roughness: 1 }));
  earth.rotation.x = -Math.PI / 2;
  earth.receiveShadow = true;
  earth.position.y = -0.018;
  scene.add(earth);
  const grid = new THREE.GridHelper(36, 36, 0x798d77, 0x50624f);
  grid.position.y = -0.012;
  grid.material.transparent = true;
  grid.material.opacity = 0.16;
  scene.add(grid);

  const timber = new THREE.MeshStandardMaterial({ color: 0xa97a4c, roughness: 0.92 });
  const timberDark = new THREE.MeshStandardMaterial({ color: 0x805b37, roughness: 0.95 });
  let fence = new THREE.Group();
  scene.add(fence);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false;
  controls.minDistance = 2;
  controls.maxDistance = 40;
  controls.maxPolarAngle = Math.PI * 0.49;
  controls.addEventListener("change", render);
  camera.position.set(7, 4.0, 8);
  controls.target.set(0, 0.9, 0);

  let latest;
  function draw() {
    const next = { ...initial };
    for (const [name, el] of Object.entries(inputs)) next[name] = Number(el.value);
    latest = layoutFence(next);
    scene.remove(fence);
    fence.traverse(obj => { if (obj.isMesh) obj.geometry.dispose(); });
    fence = new THREE.Group();
    scene.add(fence);
    const { width, tipHeight, shaftHeight, postCenters, railHeights, params: p } = latest;
    for (const x of postCenters) {
      const shaft = new THREE.Mesh(new THREE.BoxGeometry(p.post_width, shaftHeight, p.post_width), timber);
      shaft.position.set(x, shaftHeight / 2, 0);
      shaft.castShadow = true;
      shaft.receiveShadow = true;
      fence.add(shaft);
      const tip = new THREE.Mesh(new THREE.ConeGeometry(p.post_width * 0.72, tipHeight, 4), timberDark);
      tip.rotation.y = Math.PI / 4;
      tip.position.set(x, shaftHeight + tipHeight / 2, 0);
      tip.castShadow = true;
      fence.add(tip);
    }
    for (const y of railHeights) {
      const bar = new THREE.Mesh(new THREE.BoxGeometry(width, p.post_width * 0.56, p.post_width * 0.66), timberDark);
      bar.position.set(0, y, -p.post_width * 0.85);
      bar.castShadow = true;
      bar.receiveShadow = true;
      fence.add(bar);
    }
    text("count-out", p.count + " 本");
    text("height-out", p.height.toFixed(1) + " m");
    text("spacing-out", p.spacing.toFixed(1) + " m");
    text("rails-out", p.rails + " 段");
    text("width-value", fmt(width) + " m");
    text("height-value", p.height.toFixed(1) + " m");
    text("count-value", p.count + " 本");
    status.textContent = "柵柱" + p.count + "本、全幅" + fmt(width) + "メートルの模型に更新";
    render();
  }
  function fitCamera() {
    if (!latest) return;
    const size = Math.max(latest.width, latest.params.height, 3);
    const dist = Math.min(37, Math.max(5, size * 1.4));
    camera.position.set(dist * 0.64, dist * 0.44, dist * 0.78);
    controls.target.set(0, latest.params.height * 0.42, 0);
    controls.update();
  }
  function render() {
    if (!host.clientWidth || !host.clientHeight) return;
    renderer.render(scene, camera);
  }
  function resize() {
    const w = Math.max(1, host.clientWidth);
    const h = Math.max(1, host.clientHeight);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    render();
  }
  for (const el of Object.values(inputs)) el.addEventListener("input", draw);
  document.getElementById("reset").addEventListener("click", () => {
    for (const [name, el] of Object.entries(inputs)) el.value = initial[name];
    draw();
    fitCamera();
  });
  draw();
  fitCamera();
  resize();
  if ("ResizeObserver" in window) new ResizeObserver(resize).observe(host);
  else window.addEventListener("resize", resize);
}