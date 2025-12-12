const WS_URL = (location.hostname === "localhost" || location.hostname === "127.0.0.1")
  ? "ws://127.0.0.1:8000/ws/positions"
  : wss://${location.host}/ws/positions;

// scaling: show ECI coordinates (km) scaled down for nice view
const KM_TO_UNITS = 1/1000; // 1 unit = 1000 km (coarse) — reduces geometry size for low-end GPUs

let scene, camera, renderer, controls;
let objectsMap = {}; // key: type-id -> mesh
let trailsMap = {};  // line geometries per object (history short)
let orbitLinesMap = {}; // precomputed trajectories (if fetched)
let clock = new THREE.Clock();

init();
animate();
connectWebSocket();

function init(){
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1e6);
  camera.position.set(0, 0, 5);

  renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  // simple ambient + directional light (low cost)
  scene.add(new THREE.AmbientLight(0x888888));
  const dir = new THREE.DirectionalLight(0xffffff, 0.6);
  dir.position.set(5,10,7);
  scene.add(dir);

  // Earth (simple sphere)
  const earthRadiusUnits = 6371 * KM_TO_UNITS; // Earth radius ~6371 km
  const earthGeo = new THREE.SphereGeometry(earthRadiusUnits, 24, 16);
  const earthMat = new THREE.MeshPhongMaterial({color:0x2233ff, flatShading:true});
  const earthMesh = new THREE.Mesh(earthGeo, earthMat);
  scene.add(earthMesh);

  // Simple Moon (for context) — small sphere orbiting Earth
  const moonDistUnits = 384400 * KM_TO_UNITS; // average distance km
  const moonGeo = new THREE.SphereGeometry(1737 * KM_TO_UNITS, 12, 10);
  const moonMat = new THREE.MeshPhongMaterial({color:0x888888});
  const moon = new THREE.Mesh(moonGeo, moonMat);
  moon.position.set(moonDistUnits, 0, 0);
  scene.add(moon);

  // grid for reference (very light)
  const grid = new THREE.GridHelper(20, 10);
  grid.rotation.x = Math.PI/2;
  grid.material.opacity = 0.12;
  grid.material.transparent = true;
  scene.add(grid);

  window.addEventListener('resize', onWindowResize, false);
}

// simple color map for risk
function colorFromRisk(risk){
  if(risk === "HIGH") return 0xff2200;
  if(risk === "MEDIUM") return 0xffcc00;
  return 0x22ff22;
}

function makeObjectMesh(type, id, name, risk){
  // small sphere size
  const radius = (type==='satellite') ? 0.05 : 0.03;
  const geo = new THREE.SphereGeometry(radius, 8, 8);
  const mat = new THREE.MeshPhongMaterial({color: colorFromRisk(risk)});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.userData = { type, id, name, risk };
  scene.add(mesh);

  // simple label (DOM) optionally omitted for performance
  return mesh;
}

function updateOrCreateObject(type, id, name, xkm, ykm, zkm, risk_class){
  const key = ${type}-${id};
  const pos = new THREE.Vector3(xkm*KM_TO_UNITS, ykm*KM_TO_UNITS, zkm*KM_TO_UNITS);
  if(!(key in objectsMap)){
    const mesh = makeObjectMesh(type, id, name, risk_class);
    objectsMap[key] = mesh;
    //initialize trail
    trailsMap[key] = { positions: [pos.clone()] };
  }
  const mesh = objectsMap[key];
  mesh.position.copy(pos);
  // update color if risk changed
  const newColor = colorFromRisk(risk_class);
  mesh.material.color.setHex(newColor);

  // update trail (keep last 50 points)
  const trail = trailsMap[key];
  trail.positions.push(pos.clone());
  if(trail.positions.length > 50) trail.positions.shift();
  // draw / update trail line geometry
  if(trail.line){
    scene.remove(trail.line);
  }
  const pts = trail.positions;
  const lineGeom = new THREE.BufferGeometry().setFromPoints(pts);
  const lineMat = new THREE.LineBasicMaterial({ color: 0x8888ff, transparent: true, opacity: 0.6 });
  const line = new THREE.Line(lineGeom, lineMat);
  trail.line = line;
  scene.add(line);
}

// WebSocket connection & handling
function connectWebSocket(){
  const ws = new WebSocket(WS_URL);
  ws.onopen = () => { console.log("WS connected"); };
  ws.onmessage = (evt) => {
    try{
      const msg = JSON.parse(evt.data);
      handleServerMessage(msg);
    }catch(e){
      console.warn("Invalid WS data", e);
    }
  };
  ws.onclose = () => {
    console.log("WS closed, reconnect in 3s");
    setTimeout(connectWebSocket, 3000);
  };
  ws.onerror = (e) => { console.warn("WS error", e); ws.close(); };
}

function handleServerMessage(payload){
  // payload: { timestamp, objects: [{type,id,name,x,y,z,vx,vy,vz}], alerts: [...] }
  if(!payload || !payload.objects) return;
  payload.objects.forEach(o => {
    // risk_class derived from alerts if present; default LOW
    let risk = "LOW";
    // find alert for object
    if(payload.alerts && payload.alerts.length>0){
      for(const a of payload.alerts){
        if(o.type==='satellite' && a.sat_id === o.id && a.risk_class) { risk = a.risk_class; break; }
        if(o.type==='debris' && a.debris_id === o.id && a.risk_class) { risk = a.risk_class; break; }
      }
    }
    updateOrCreateObject(o.type, o.id, o.name, o.x, o.y, o.z, risk);
  });
  // optionally, display alerts in UI (left panel)
  // For performance, we skip heavy DOM updates here
}

function animate(){
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}

function onWindowResize(){
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}
