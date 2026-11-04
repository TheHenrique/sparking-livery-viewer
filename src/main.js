import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const el = (id) => document.getElementById(id);
const status = (msg, tipo = '') => { el('status').textContent = msg; el('status').className = tipo; };

// --- cena -------------------------------------------------------------
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.NoToneMapping;   // cor na tela = cor do PNG (sem correcao de tons)
el('viewer').appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.15;   // so um reflexo leve para dar volume

// luz uniforme (sem luz vinda de cima), para a livery aparecer com as cores reais
scene.add(new THREE.AmbientLight(0xffffff, 2.5));

const camera = new THREE.PerspectiveCamera(35, 1, 0.05, 100);
camera.position.set(5.5, 2.2, 6);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 0.6, 0);
controls.minDistance = 2;
controls.maxDistance = 15;
controls.maxPolarAngle = Math.PI * 0.55;

function resize() {
  renderer.setSize(innerWidth, innerHeight);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize);
resize();
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });

// --- carros -------------------------------------------------------------
const loader = new GLTFLoader();
let cars = [];
let atual = null;      // { car, root, skinMats }
let skinTex = null;    // textura importada (mantida ao trocar de carro)

function aplicarSkin() {
  if (!atual || !skinTex) return;
  for (const m of atual.skinMats) { m.map = skinTex; m.color.set(0xffffff); m.needsUpdate = true; }
}

async function carregarCarro(car) {
  el('carregando').hidden = false;
  try {
    const gltf = await loader.loadAsync(car.model);
    if (atual) { scene.remove(atual.root); }
    const root = gltf.scene;
    const skinMats = [];
    root.traverse((o) => {
      if (!o.isMesh) return;
      const m = o.material;
      if (m.name === car.skinMaterial) skinMats.push(m);
      if (m.transparent) { m.depthWrite = false; o.renderOrder = 1; }
    });
    // centraliza no chão
    const box = new THREE.Box3().setFromObject(root);
    root.position.x -= (box.min.x + box.max.x) / 2;
    root.position.z -= (box.min.z + box.max.z) / 2;
    root.position.y -= box.min.y;
    scene.add(root);
    atual = { car, root, skinMats };
    aplicarSkin();
  } catch (e) {
    console.error(e);
    status('Não foi possível carregar o modelo.', 'erro');
  } finally {
    el('carregando').hidden = true;
  }
}

el('carro').addEventListener('change', (e) => {
  const car = cars.find((c) => c.id === e.target.value);
  if (car) carregarCarro(car);
});

// --- skin -------------------------------------------------------------
el('skin').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  e.target.value = '';
  if (!file) return;
  if (file.type !== 'image/png') { status('O arquivo precisa ser PNG.', 'erro'); return; }
  try {
    const bmp = await createImageBitmap(file, { imageOrientation: 'none' });
    const tex = new THREE.Texture(bmp);
    tex.flipY = false;                  // UVs do rFactor usam origem no topo
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
    tex.needsUpdate = true;
    if (skinTex) skinTex.dispose();
    skinTex = tex;
    aplicarSkin();
    status(`Skin aplicada: ${file.name} (${bmp.width}×${bmp.height})`);
  } catch (err) {
    console.error(err);
    status('Não foi possível ler a imagem.', 'erro');
  }
});

// --- início -------------------------------------------------------------
cars = await (await fetch('cars.json')).json();
el('carro').innerHTML = cars.map((c) => `<option value="${c.id}">${c.name}</option>`).join('');
carregarCarro(cars[0]);
