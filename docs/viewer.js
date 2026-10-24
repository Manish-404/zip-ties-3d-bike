import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const params = new URLSearchParams(location.search);
const RENDER = params.has('render');
const el = document.getElementById('viewer');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: RENDER });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
el.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x15171c);
const camera = new THREE.PerspectiveCamera(32, 1, 1, 3000);
camera.position.set(0, 120, 520);

scene.add(new THREE.HemisphereLight(0xffffff, 0x303640, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(200, 300, 250); scene.add(key);
const rim = new THREE.DirectionalLight(0xff9a4d, 1.4); rim.position.set(-250, 100, -250); scene.add(rim);

const floor = new THREE.Mesh(new THREE.CircleGeometry(260, 64),
  new THREE.MeshStandardMaterial({ color: 0x1d2027, roughness: 0.9 }));
floor.rotation.x = -Math.PI / 2; scene.add(floor);
const grid = new THREE.PolarGridHelper(260, 8, 6, 64, 0x2c313b, 0x2c313b); scene.add(grid);

const mat = new THREE.MeshStandardMaterial({ color: 0xff6a13, roughness: 0.45, metalness: 0.05 });
const pivot = new THREE.Group(); scene.add(pivot);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.autoRotate = !RENDER; controls.autoRotateSpeed = 2.2;
controls.enablePan = false;

const models = {
  loop: 'models/hunter350_rear_loop.stl',
  straight: 'models/hunter350_rear_straight.stl',
  front: 'models/hunter350_front_straight.stl',
};
let current = null, cache = {};
async function show(key) {
  if (current) pivot.remove(current);
  if (!cache[key]) {
    const geo = await new STLLoader().loadAsync(models[key]);
    geo.computeVertexNormals();
    geo.computeBoundingBox();
    const c = new THREE.Vector3(); geo.boundingBox.getCenter(c);
    const m = new THREE.Mesh(geo, mat);
    const holder = new THREE.Group(); holder.add(m);
    // CAD z-up -> three y-up, centred on the floor
    m.position.sub(c);
    holder.rotation.x = -Math.PI / 2;
    const outer = new THREE.Group(); outer.add(holder);
    const size = new THREE.Vector3(); geo.boundingBox.getSize(size);
    // after rotation: CAD y -> -z, CAD z -> y
    outer.position.y = size.z / 2 + 4;
    outer.userData.span = Math.max(size.x, size.y, size.z);
    cache[key] = outer;
  }
  current = cache[key]; pivot.add(current);
  const s = current.userData.span;
  camera.position.set(0, s * 0.5, s * 1.45);
  controls.target.set(0, current.position.y, 0); controls.update();
}
function resize() {
  const w = el.clientWidth, h = el.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();

await show(params.get('m') || 'loop');
document.querySelectorAll('[data-model]').forEach(b => b.addEventListener('click', async () => {
  document.querySelectorAll('[data-model]').forEach(x => x.classList.toggle('on', x === b));
  await show(b.dataset.model);
}));
const spin = document.getElementById('spin');
if (spin) spin.addEventListener('change', () => controls.autoRotate = spin.checked);

let R0 = null;
window.setAngle = (deg) => {
  const t = controls.target;
  if (R0 === null) R0 = camera.position.distanceTo(t);
  const a = deg * Math.PI / 180, el_ = 0.38;
  camera.position.set(t.x + R0 * Math.cos(el_) * Math.sin(a), t.y + R0 * Math.sin(el_), t.z + R0 * Math.cos(el_) * Math.cos(a));
  camera.lookAt(t); renderer.render(scene, camera);
};
window.ready = true;
renderer.setAnimationLoop(() => { if (!RENDER) { controls.update(); renderer.render(scene, camera); } });
