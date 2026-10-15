/** Grounded capsule movement against exported Y-up boxes and cylinders.
 * Horizontal steps <= 0.12 m prevent tunnelling, even at low frame rates.
 * Feet remain on terrain or walkable stair treads; no jump/free-fall simulation.
 */
export function floorAt(x, z, currentFloor, data) {
  let floor = data.floor;
  const field=data.terrainHeightField;
  if(field){
    const fx=Math.max(0,Math.min(field.columns-1.000001,(x-field.origin[0])/field.step));
    const fz=Math.max(0,Math.min(field.rows-1.000001,(z-field.origin[1])/field.step));
    const ix=Math.floor(fx),iz=Math.floor(fz),tx=fx-ix,tz=fz-iz;
    const a=field.heights[iz*field.columns+ix],b=field.heights[iz*field.columns+ix+1];
    const c=field.heights[(iz+1)*field.columns+ix],d=field.heights[(iz+1)*field.columns+ix+1];
    floor=(a+(b-a)*tx)*(1-tz)+(c+(d-c)*tx)*tz+field.surfaceOffset;
  }
  for (const s of data.walkableSurfaces) {
    if (x >= s.min[0] && x <= s.max[0] && z >= s.min[1] && z <= s.max[1] && s.height <= currentFloor + data.capsule.stepHeight + .02) floor = Math.max(floor, s.height);
  }
  return floor;
}

export function intersects(x, z, feet, c, radius, height) {
  const cy = c.center[1], half = (c.type === 'box' ? c.size[1] : c.height) / 2;
  if (cy + half <= feet + .025 || cy - half >= feet + height) return false;
  if (c.type === 'cylinder') return Math.hypot(x - c.center[0], z - c.center[2]) < radius + c.radius;
  const nx = Math.max(c.center[0] - c.size[0] / 2, Math.min(x, c.center[0] + c.size[0] / 2));
  const nz = Math.max(c.center[2] - c.size[2] / 2, Math.min(z, c.center[2] + c.size[2] / 2));
  return Math.hypot(x - nx, z - nz) < radius;
}

export function moveCapsule(position, delta, data) {
  let [x, eye, z] = position;
  let feet = eye - data.capsule.height;
  const steps = Math.max(1, Math.ceil(Math.hypot(delta[0], delta[1]) / .12));
  const dx = delta[0] / steps, dz = delta[1] / steps;
  const blocked = (nx, nz, nf) => data.colliders.some(c => intersects(nx, nz, nf, c, data.capsule.radius, data.capsule.height));
  for (let i = 0; i < steps; i++) {
    let nf = floorAt(x + dx, z, feet, data);
    if (!blocked(x + dx, z, nf)) { x += dx; feet = nf; }
    nf = floorAt(x, z + dz, feet, data);
    if (!blocked(x, z + dz, nf)) { z += dz; feet = nf; }
    x = Math.max(data.bounds[0] + 1, Math.min(data.bounds[1] - 1, x));
    z = Math.max(data.bounds[2] + 1, Math.min(data.bounds[3] - 1, z));
  }
  return [x, feet + data.capsule.height, z];
}
