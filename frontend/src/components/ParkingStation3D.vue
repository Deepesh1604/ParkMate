<template>
  <div class="parking-station-container" ref="container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import * as THREE from 'three';

// OrbitControls implementation (simplified for this use case)
class OrbitControls {
  constructor(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;
    this.enableDamping = false;
    this.dampingFactor = 0.25;
    this.minDistance = 1;
    this.maxDistance = Infinity;
    this.maxPolarAngle = Math.PI;
    
    this.autoRotate = true;
    this.autoRotateSpeed = 0.5;
    
    this.spherical = new THREE.Spherical();
    this.sphericalDelta = new THREE.Spherical();
    this.target = new THREE.Vector3();
    
    this.lastPosition = new THREE.Vector3();
    this.lastQuaternion = new THREE.Quaternion();
    
    this.init();
  }
  
  init() {
    this.update();
  }
  
  update() {
    if (this.autoRotate) {
      this.camera.position.x = Math.cos(Date.now() * 0.0005) * 20;
      this.camera.position.z = Math.sin(Date.now() * 0.0005) * 20;
      this.camera.lookAt(0, 0, 0);
    }
    return true;
  }
}

const container = ref(null);
let scene, camera, renderer, controls;
let parkingLot, cars = [];
let animationId = null;

// Car colors
const carColors = [
  0x3498db, // Blue
  0xe74c3c, // Red
  0x2ecc71, // Green
  0xf39c12, // Yellow
  0x9b59b6, // Purple
  0x1abc9c  // Teal
];

// Create a car mesh
const createCar = (color, position) => {
  const carGroup = new THREE.Group();
  
  // Car body
  const carBodyGeometry = new THREE.BoxGeometry(1.8, 0.6, 4);
  const carBodyMaterial = new THREE.MeshPhysicalMaterial({
    color: color,
    metalness: 0.7,
    roughness: 0.2,
    clearcoat: 0.5,
    clearcoatRoughness: 0.1
  });
  const carBody = new THREE.Mesh(carBodyGeometry, carBodyMaterial);
  carBody.position.y = 0.5;
  carGroup.add(carBody);

  // Car top
  const carTopGeometry = new THREE.BoxGeometry(1.6, 0.5, 2.5);
  const carTopMaterial = new THREE.MeshPhysicalMaterial({
    color: color,
    metalness: 0.7,
    roughness: 0.2,
    clearcoat: 0.5,
    clearcoatRoughness: 0.1
  });
  const carTop = new THREE.Mesh(carTopGeometry, carTopMaterial);
  carTop.position.y = 1.05;
  carTop.position.z = 0.2;
  carGroup.add(carTop);

  // Windows
  const windowMaterial = new THREE.MeshPhysicalMaterial({
    color: 0x111111,
    metalness: 0.2,
    roughness: 0.1,
    transmission: 0.9,
    transparent: true
  });

  // Front window
  const frontWindowGeometry = new THREE.BoxGeometry(1.5, 0.4, 0.1);
  const frontWindow = new THREE.Mesh(frontWindowGeometry, windowMaterial);
  frontWindow.position.set(0, 1.05, 1.4);
  frontWindow.rotation.x = Math.PI / 8;
  carGroup.add(frontWindow);

  // Rear window
  const rearWindowGeometry = new THREE.BoxGeometry(1.5, 0.4, 0.1);
  const rearWindow = new THREE.Mesh(rearWindowGeometry, windowMaterial);
  rearWindow.position.set(0, 1.05, -1.05);
  rearWindow.rotation.x = -Math.PI / 8;
  carGroup.add(rearWindow);

  // Wheels
  const wheelGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 24);
  const wheelMaterial = new THREE.MeshPhongMaterial({ color: 0x111111 });
  
  // Front-left wheel
  const wheelFL = new THREE.Mesh(wheelGeometry, wheelMaterial);
  wheelFL.position.set(-1, 0.4, 1.3);
  wheelFL.rotation.z = Math.PI / 2;
  carGroup.add(wheelFL);
  
  // Front-right wheel
  const wheelFR = new THREE.Mesh(wheelGeometry, wheelMaterial);
  wheelFR.position.set(1, 0.4, 1.3);
  wheelFR.rotation.z = Math.PI / 2;
  carGroup.add(wheelFR);
  
  // Rear-left wheel
  const wheelRL = new THREE.Mesh(wheelGeometry, wheelMaterial);
  wheelRL.position.set(-1, 0.4, -1.3);
  wheelRL.rotation.z = Math.PI / 2;
  carGroup.add(wheelRL);
  
  // Rear-right wheel
  const wheelRR = new THREE.Mesh(wheelGeometry, wheelMaterial);
  wheelRR.position.set(1, 0.4, -1.3);
  wheelRR.rotation.z = Math.PI / 2;
  carGroup.add(wheelRR);

  // Headlights
  const headlightGeometry = new THREE.SphereGeometry(0.2, 16, 16);
  const headlightMaterial = new THREE.MeshPhongMaterial({ 
    color: 0xffffff,
    emissive: 0xffffee,
    emissiveIntensity: 0.8
  });
  
  // Left headlight
  const headlightLeft = new THREE.Mesh(headlightGeometry, headlightMaterial);
  headlightLeft.position.set(-0.7, 0.5, 2);
  headlightLeft.scale.z = 0.5;
  carGroup.add(headlightLeft);
  
  // Right headlight
  const headlightRight = new THREE.Mesh(headlightGeometry, headlightMaterial);
  headlightRight.position.set(0.7, 0.5, 2);
  headlightRight.scale.z = 0.5;
  carGroup.add(headlightRight);

  // Position the car
  carGroup.position.copy(position);
  
  return carGroup;
};

// Create a parking spot
const createParkingSpot = (position, isOccupied = false) => {
  const spotGroup = new THREE.Group();
  
  // Parking spot base
  const spotGeometry = new THREE.BoxGeometry(2.5, 0.1, 5);
  const spotMaterial = new THREE.MeshPhongMaterial({ 
    color: 0x333333,
    emissive: 0x111111
  });
  const spot = new THREE.Mesh(spotGeometry, spotMaterial);
  spot.position.y = 0.05;
  spotGroup.add(spot);
  
  // Parking lines
  const lineGeometry = new THREE.BoxGeometry(0.1, 0.12, 5);
  const lineMaterial = new THREE.MeshPhongMaterial({ color: 0xffffff });
  
  // Left line
  const lineLeft = new THREE.Mesh(lineGeometry, lineMaterial);
  lineLeft.position.x = -1.25;
  lineLeft.position.y = 0.1;
  spotGroup.add(lineLeft);
  
  // Right line
  const lineRight = new THREE.Mesh(lineGeometry, lineMaterial);
  lineRight.position.x = 1.25;
  lineRight.position.y = 0.1;
  spotGroup.add(lineRight);
  
  // End line
  const endLineGeometry = new THREE.BoxGeometry(2.5, 0.12, 0.1);
  const endLine = new THREE.Mesh(endLineGeometry, lineMaterial);
  endLine.position.z = 2.5;
  endLine.position.y = 0.1;
  spotGroup.add(endLine);

  // Create and add a car if the spot is occupied
  if (isOccupied) {
    const carColor = carColors[Math.floor(Math.random() * carColors.length)];
    const carPosition = new THREE.Vector3(0, 0, 0);
    const car = createCar(carColor, carPosition);
    spotGroup.add(car);
    cars.push(car);
  }

  // Position the spot
  spotGroup.position.copy(position);
  
  return spotGroup;
};

// Initialize the scene
const init = () => {
  // Create scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1a2e);
  
  // Create camera
  camera = new THREE.PerspectiveCamera(
    40, 
    container.value.clientWidth / container.value.clientHeight, 
    0.1, 
    1000
  );
  camera.position.set(20, 20, 20);
  camera.lookAt(0, 0, 0);
  
  // Create renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  container.value.appendChild(renderer.domElement);
  
  // Add controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.minDistance = 10;
  controls.maxDistance = 50;
  controls.maxPolarAngle = Math.PI / 2.1;
  
  // Add lights
  const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
  scene.add(ambientLight);
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(10, 20, 10);
  directionalLight.castShadow = true;
  directionalLight.shadow.mapSize.width = 2048;
  directionalLight.shadow.mapSize.height = 2048;
  directionalLight.shadow.camera.near = 0.5;
  directionalLight.shadow.camera.far = 50;
  directionalLight.shadow.camera.left = -20;
  directionalLight.shadow.camera.right = 20;
  directionalLight.shadow.camera.top = 20;
  directionalLight.shadow.camera.bottom = -20;
  scene.add(directionalLight);
  
  // Add parking lot ground
  const groundGeometry = new THREE.PlaneGeometry(50, 50);
  const groundMaterial = new THREE.MeshPhongMaterial({ 
    color: 0x222222,
    side: THREE.DoubleSide
  });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);
  
  // Create parking lot
  parkingLot = new THREE.Group();
  
  // Create 2 rows of parking spots
  const rows = 2;
  const spotsPerRow = 5;
  const spotWidth = 3;
  const spotDepth = 6;
  
  for (let row = 0; row < rows; row++) {
    for (let spot = 0; spot < spotsPerRow; spot++) {
      const x = (spot - (spotsPerRow - 1) / 2) * spotWidth;
      const z = row * spotDepth * 1.5 - 6;
      
      // Randomly decide if spot is occupied (50% chance)
      const isOccupied = Math.random() > 0.5;
      
      const parkingSpot = createParkingSpot(
        new THREE.Vector3(x, 0, z),
        isOccupied
      );
      
      parkingLot.add(parkingSpot);
    }
  }
  
  // Add road
  const roadGeometry = new THREE.PlaneGeometry(spotWidth * spotsPerRow * 1.2, 5);
  const roadMaterial = new THREE.MeshPhongMaterial({ 
    color: 0x333333,
    side: THREE.DoubleSide
  });
  const road = new THREE.Mesh(roadGeometry, roadMaterial);
  road.rotation.x = -Math.PI / 2;
  road.position.y = 0.01;
  road.position.z = 3;
  parkingLot.add(road);
  
  // Road markings
  const roadLineGeometry = new THREE.PlaneGeometry(0.2, 3);
  const roadLineMaterial = new THREE.MeshPhongMaterial({ 
    color: 0xffffff,
    side: THREE.DoubleSide
  });
  const roadLine = new THREE.Mesh(roadLineGeometry, roadLineMaterial);
  roadLine.rotation.x = -Math.PI / 2;
  roadLine.position.y = 0.02;
  roadLine.position.z = 3;
  parkingLot.add(roadLine);
  
  scene.add(parkingLot);
  
  // Create animated car driving on the road
  const movingCar = createCar(0xff0000, new THREE.Vector3(-20, 0, 3));
  scene.add(movingCar);
  
  // Animate the moving car
  const animateCar = () => {
    // Move the car across the scene
    if (movingCar.position.x < 20) {
      movingCar.position.x += 0.1;
    } else {
      movingCar.position.x = -20;
    }
    
    // Rotate the wheels
    movingCar.children.forEach(child => {
      if (child.isMesh && child.geometry.type === 'CylinderGeometry') {
        child.rotation.x += 0.1;
      }
    });
  };
  
  // Add fog
  scene.fog = new THREE.FogExp2(0x1a1a2e, 0.02);
  
  // Particle system for ambient effect
  const particleCount = 500;
  const particles = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  
  for (let i = 0; i < particleCount * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 60;
    positions[i + 1] = Math.random() * 30;
    positions[i + 2] = (Math.random() - 0.5) * 60;
  }
  
  particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  
  const particleMaterial = new THREE.PointsMaterial({
    color: 0x3498db,
    size: 0.2,
    transparent: true,
    opacity: 0.7,
    blending: THREE.AdditiveBlending
  });
  
  const particleSystem = new THREE.Points(particles, particleMaterial);
  scene.add(particleSystem);
  
  // Animation function for particles
  const animateParticles = () => {
    const positions = particleSystem.geometry.attributes.position.array;
    
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 1] += 0.01 * (Math.sin(Date.now() * 0.001 + i) * 0.1);
    }
    
    particleSystem.geometry.attributes.position.needsUpdate = true;
  };
  
  // Animation loop
  const animate = () => {
    animationId = requestAnimationFrame(animate);
    
    // Update controls
    controls.update();
    
    // Animate the moving car
    animateCar();
    
    // Animate particles
    animateParticles();
    
    // Render the scene
    renderer.render(scene, camera);
  };
  
  // Start animation
  animate();
  
  // Handle window resize
  const handleResize = () => {
    camera.aspect = container.value.clientWidth / container.value.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  };
  
  window.addEventListener('resize', handleResize);
  
  // Return cleanup function
  return () => {
    window.removeEventListener('resize', handleResize);
    if (animationId) {
      cancelAnimationFrame(animationId);
    }
    if (renderer) {
      renderer.dispose();
    }
  };
};

onMounted(() => {
  const cleanup = init();
  
  onBeforeUnmount(() => {
    if (cleanup) {
      cleanup();
    }
    
    if (container.value && container.value.firstChild) {
      container.value.removeChild(container.value.firstChild);
    }
  });
});
</script>

<style scoped>
.parking-station-container {
  width: 100%;
  height: 500px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  background: rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

@media (max-width: 768px) {
  .parking-station-container {
    height: 350px;
  }
}
</style>
