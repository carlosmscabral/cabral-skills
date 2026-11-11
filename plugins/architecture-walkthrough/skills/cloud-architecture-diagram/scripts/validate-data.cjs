#!/usr/bin/env node
// Executes trusted diagram JavaScript. This is a validator, not a sandbox.
const fs = require('node:fs');
const vm = require('node:vm');
if (!process.argv[2]) { console.error('Usage: node validate-data.cjs <trusted-data.js>'); process.exit(2); }
const data = vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8') +
  ';({DIAGRAM, OUTSIDE, GROUPS, CARDS, EDGES, SLIDES})', {}, {timeout: 2000});
const {DIAGRAM, OUTSIDE, GROUPS, CARDS, EDGES, SLIDES} = data;
const errors = [], units = [...OUTSIDE, ...CARDS];
const byId = new Map(units.map(u => [u.id, u]));
for (const [name, list] of [['units', units], ['groups', GROUPS], ['edges', EDGES]]) {
  const ids = new Set();
  for (const item of list) {
    if (!item.id || ids.has(item.id)) errors.push(`${name}: missing or duplicate ID ${item.id}`);
    ids.add(item.id);
  }
}
for (const u of units) {
  if (![u.x,u.y,u.w,u.h].every(Number.isFinite) || u.w <= 0 || u.h <= 0) errors.push(`${u.id}: invalid bounds`);
  if (!u.what) errors.push(`${u.id}: missing explanation`);
}
for (const c of CARDS) if (!GROUPS.some(g => g.id === c.group)) errors.push(`${c.id}: unknown group`);
function onBoundary(u, p) {
  if (!u || !p) return false;
  const [x,y] = p, t = 0.5;
  return x >= u.x-t && x <= u.x+u.w+t && y >= u.y-t && y <= u.y+u.h+t &&
    [Math.abs(x-u.x),Math.abs(x-u.x-u.w),Math.abs(y-u.y),Math.abs(y-u.y-u.h)].some(d => d <= t);
}
for (const e of EDGES) {
  if (!Array.isArray(e.pts) || e.pts.length < 2) { errors.push(`${e.id}: insufficient route points`); continue; }
  for (const [id,p] of [[e.from,e.pts[0]],[e.to,e.pts.at(-1)]])
    if (!onBoundary(byId.get(id),p)) errors.push(`${e.id}: endpoint misses ${id}`);
  for (let i=1;i<e.pts.length;i++) {
    const a=e.pts[i-1], b=e.pts[i];
    if (a[0] !== b[0] && a[1] !== b[1]) errors.push(`${e.id}: non-orthogonal segment`);
  }
}
for (const s of SLIDES) {
  for (const id of s.units) if (!byId.has(id)) errors.push(`${s.title}: unknown unit ${id}`);
  for (const id of s.edges) if (!EDGES.some(e=>e.id===id)) errors.push(`${s.title}: unknown edge ${id}`);
}
if (!SLIDES.length || [SLIDES[0],SLIDES.at(-1)].some(s=>s.units.length || s.edges.length)) errors.push('First/last slides must be whole-system views');
if (!Array.isArray(DIAGRAM.viewBox) || DIAGRAM.viewBox.length !== 2 || !DIAGRAM.viewBox.every(n=>Number.isFinite(n)&&n>0)) errors.push('Invalid viewBox');
console.log(JSON.stringify(errors,null,2));
process.exitCode = errors.length ? 1 : 0;
