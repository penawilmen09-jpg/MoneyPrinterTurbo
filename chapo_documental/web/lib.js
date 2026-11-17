// ===== Librería 2D: ayudas de dibujo, personajes con esqueleto, efectos =====
const W = 1080, H = 1920;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => { t = clamp(t); return t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; };
const easeOut = t => { t = clamp(t); return 1 - Math.pow(1 - t, 3); };
const seg = (t, a, b) => clamp((t - a) / (b - a));       // progreso 0..1 de t en [a,b]
const rad = d => d * Math.PI / 180;
function rng(s) { return function () { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function lg(ctx, x0, y0, x1, y1, stops) { const g = ctx.createLinearGradient(x0, y0, x1, y1); stops.forEach(s => g.addColorStop(s[0], s[1])); return g; }
function rgr(ctx, x, y, r0, r1, stops) { const g = ctx.createRadialGradient(x, y, r0, x, y, r1); stops.forEach(s => g.addColorStop(s[0], s[1])); return g; }
function rect(ctx, x, y, w, h, fill) { ctx.fillStyle = fill; ctx.fillRect(x, y, w, h); }
function poly(ctx, pts, fill, stroke, lw) {
  ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 2; ctx.lineJoin = 'round'; ctx.stroke(); }
}
function rrect(ctx, x, y, w, h, r, fill, stroke, lw) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 2; ctx.stroke(); }
}
function glow(ctx, x, y, r, rgb, a = 1) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgr(ctx, x, y, 0, r, [[0, `rgba(${rgb},${a})`], [.35, `rgba(${rgb},${a * .35})`], [1, `rgba(${rgb},0)`]]);
  ctx.fillRect(x - r, y - r, 2 * r, 2 * r); ctx.restore();
}
function cone(ctx, x, y, ang, len, spread, rgb, a) {   // haz de luz (linterna, reflector, faro)
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(x, y); ctx.rotate(ang);
  ctx.fillStyle = lg(ctx, 0, 0, len, 0, [[0, `rgba(${rgb},${a})`], [.6, `rgba(${rgb},${a * .35})`], [1, `rgba(${rgb},0)`]]);
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(len, -spread); ctx.lineTo(len, spread); ctx.closePath(); ctx.fill(); ctx.restore();
}
// textura de ruido/hormigón estática
function speckle(ctx, x, y, w, h, seed, n, cols, smin, smax, alpha) {
  const r = rng(seed); ctx.save(); ctx.globalAlpha = alpha;
  for (let i = 0; i < n; i++) { ctx.fillStyle = cols[(r() * cols.length) | 0]; const s = smin + r() * (smax - smin); ctx.fillRect(x + r() * w, y + r() * h, s, s * (.4 + r())); }
  ctx.restore();
}
// ===== Postproceso: viñeta, grano, gradación =====
let grainCv = null;
function initGrain() {
  grainCv = mk(540, 960); const g = grainCv.getContext('2d'); const im = g.createImageData(540, 960); const r = rng(77);
  for (let i = 0; i < im.data.length; i += 4) { const v = 128 + (r() - .5) * 140; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
  g.putImageData(im, 0, 0);
}
function post(ctx, f, o = {}) {
  const r = rng(f * 13 + 5);
  if (!grainCv) initGrain();
  ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = o.grain ?? .13;
  ctx.drawImage(grainCv, 0, 0, 540, 960, -r() * 40, -r() * 40, W + 80, H + 80); ctx.restore();
  ctx.save(); ctx.fillStyle = rgr(ctx, W / 2, H * .45, H * .28, H * .78, [[0, 'rgba(0,0,0,0)'], [1, `rgba(0,0,0,${o.vig ?? .62})`]]); ctx.fillRect(0, 0, W, H); ctx.restore();
}
// ===== Personajes 2D con esqueleto =====
const CHARS = {
  chapo: { H: 560, build: 1.16, skin: '#c8966f', skinD: '#a3765a', hair: '#1b1613', gray: '#7a746d', shirt: '#b8a272', shirtD: '#8a7850', pants: '#a08c62', pantsD: '#76683f', shoe: '#2a241f', stache: true, cap: null },
  chapoB: { H: 560, build: 1.16, skin: '#c8966f', skinD: '#a3765a', hair: '#1b1613', gray: '#7a746d', shirt: '#e4e0d6', shirtD: '#b9b4a6', pants: '#2c3340', pantsD: '#1c212b', shoe: '#1d1a18', stache: true, cap: null, sleeveless: true },
  g1: { H: 610, build: 1.0, skin: '#b98962', skinD: '#966b4a', hair: '#15110e', shirt: '#26365a', shirtD: '#18233d', pants: '#1c2744', pantsD: '#121a2f', shoe: '#0c0c0c', stache: false, cap: '#1b2846', belt: true },
  g2: { H: 625, build: 1.12, skin: '#d2a47d', skinD: '#b08158', hair: '#2b1d12', shirt: '#2a3d63', shirtD: '#1a2a47', pants: '#1c2744', pantsD: '#121a2f', shoe: '#0c0c0c', stache: false, cap: null, belt: true, bald: true },
  agent: { H: 620, build: 1.05, skin: '#b98962', skinD: '#966b4a', hair: '#15110e', shirt: '#3a4452', shirtD: '#262d38', pants: '#2b323d', pantsD: '#1b2028', shoe: '#0c0c0c', stache: false, cap: '#2b333f', belt: true, vest: '#1d232c' },
  agent2: { H: 640, build: 1.1, skin: '#c99a72', skinD: '#a67a55', hair: '#1c140e', shirt: '#3a4452', shirtD: '#262d38', pants: '#2b323d', pantsD: '#1b2028', shoe: '#0c0c0c', stache: true, cap: null, belt: true, vest: '#1d232c' },
  marine: { H: 630, build: 1.12, skin: '#b88860', skinD: '#966a48', hair: '#15110e', shirt: '#3d4a3a', shirtD: '#283226', pants: '#3a4636', pantsD: '#262e24', shoe: '#14110e', stache: false, cap: null, helmet: '#2f3a2c', belt: true, vest: '#232b21' },
};
const OL = '#0c0e14';
function limb(ctx, a, b, w, fill, ol) {
  ctx.lineCap = 'round'; ctx.strokeStyle = ol || OL; ctx.lineWidth = w + 6;
  ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  ctx.strokeStyle = fill; ctx.lineWidth = w; ctx.stroke();
}
const sd = (p, a, l) => [p[0] + Math.sin(rad(a)) * l, p[1] + Math.cos(rad(a)) * l];
// pose: {lean,head,la:[sh,el],ra:[sh,el],ll:[hip,knee],rl:[hip,knee],yaw}
function drawPerson(ctx, name, x, gy, facing, pose, opt = {}) {
  const c = CHARS[name], Hh = c.H * (opt.scale || 1), b = c.build;
  const L1 = .245 * Hh, L2 = .245 * Hh, T = .30 * Hh, U = .17 * Hh, F = .16 * Hh, ft = .018 * Hh;
  const P = Object.assign({ lean: 2, head: 0, la: [0, 10], ra: [0, 10], ll: [0, 4], rl: [0, 4] }, pose);
  const down = lh => Math.max(L1 * Math.cos(rad(lh[0])) + L2 * Math.cos(rad(lh[0] - lh[1])));
  const py = gy - ft - Math.max(down(P.ll), down(P.rl)) - (opt.sink || 0);
  const pel = [0, py];
  ctx.save(); ctx.translate(x, 0); ctx.scale(facing, 1);
  if (opt.clipY !== undefined) { ctx.beginPath(); ctx.rect(-600, -2000, 1200, 2000 + opt.clipY); ctx.clip(); }
  const kneeOf = l => sd(pel, l[0], L1), ankOf = l => { const k = kneeOf(l); return sd(k, l[0] - l[1], L2); };
  const shP = [pel[0] + Math.sin(rad(P.lean)) * T, pel[1] - Math.cos(rad(P.lean)) * T];
  const out = {};
  // sombra de contacto
  ctx.save(); ctx.globalAlpha = .35; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(0, gy + 4, Hh * .2, Hh * .02, 0, 0, 7); ctx.fill(); ctx.restore();
  const bb = 1 + (b - 1) * .6; const legW = [.074 * Hh * bb, .058 * Hh * bb], armW = [.05 * Hh * bb, .041 * Hh * bb];
  const drawLeg = (l, far) => {
    const k = kneeOf(l), a = ankOf(l);
    const pc = far ? c.pantsD : c.pants;
    limb(ctx, pel, k, legW[0], pc); limb(ctx, k, a, legW[1], pc);
    // zapato
    ctx.fillStyle = c.shoe; ctx.strokeStyle = OL; ctx.lineWidth = 3; ctx.beginPath();
    ctx.ellipse(a[0] + Hh * .03, a[1] + ft * .7, Hh * .05, Hh * .022, 0, 0, 7); ctx.fill(); ctx.stroke();
  };
  const drawArm = (arm, far, hold) => {
    const e = sd(shP, arm[0], U), h = sd(e, arm[0] + arm[1], F);
    const sc = far ? c.shirtD : c.shirt;
    limb(ctx, shP, e, armW[0], sc); limb(ctx, e, h, armW[1], c.sleeveless ? c.skin : sc);
    if (c.sleeveless) limb(ctx, sd(e, arm[0] + arm[1], F * .12), h, armW[1] * .92, c.skin, 'rgba(0,0,0,0)');
    ctx.fillStyle = far ? c.skinD : c.skin; ctx.strokeStyle = OL; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(h[0], h[1], armW[1] * .55, 0, 7); ctx.fill(); ctx.stroke();
    return { x: x + h[0] * facing, y: h[1], lx: h[0], ly: h[1], ang: arm[0] + arm[1] };
  };
  drawLeg(P.rl, true);
  out.handF = drawArm(P.ra, true);
  // torso
  ctx.lineCap = 'round';
  const tw = .135 * Hh * b;
  ctx.strokeStyle = OL; ctx.lineWidth = tw + 7; ctx.beginPath(); ctx.moveTo(pel[0], pel[1] - 4); ctx.lineTo(shP[0], shP[1] + 6); ctx.stroke();
  ctx.strokeStyle = c.shirt; ctx.lineWidth = tw; ctx.stroke();
  // sombreado del torso
  ctx.save(); ctx.globalAlpha = .45; ctx.strokeStyle = c.shirtD; ctx.lineWidth = tw * .4; ctx.beginPath();
  ctx.moveTo(pel[0] - tw * .22, pel[1] - 4); ctx.lineTo(shP[0] - tw * .22, shP[1] + 6); ctx.stroke(); ctx.restore();
  if (name === 'chapo' || name === 'chapoB') { // complexión robusta
    const mx = (pel[0] + shP[0]) / 2 + 12, my = (pel[1] + shP[1]) / 2 + 20;
    ctx.fillStyle = c.shirt; ctx.beginPath(); ctx.ellipse(mx + 8, my, tw * .58, Hh * .075, rad(P.lean), 0, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(12,14,20,.5)'; ctx.lineWidth = 2; ctx.stroke();
  }
  if (c.vest) { ctx.fillStyle = c.vest; ctx.globalAlpha = .9; ctx.beginPath(); ctx.moveTo(shP[0] - tw * .45, shP[1] + 10); ctx.lineTo(shP[0] + tw * .4, shP[1] + 10); ctx.lineTo(pel[0] + tw * .38, pel[1] - Hh * .06); ctx.lineTo(pel[0] - tw * .42, pel[1] - Hh * .06); ctx.closePath(); ctx.fill(); ctx.globalAlpha = 1; }
  if (c.belt) { ctx.save(); ctx.translate(pel[0], pel[1] - 4); ctx.rotate(rad(P.lean * .4)); ctx.fillStyle = '#0d0d10'; ctx.fillRect(-tw * .52, -Hh * .018, tw * 1.04, Hh * .03); ctx.fillStyle = '#9a8a4a'; ctx.fillRect(tw * .12, -Hh * .016, Hh * .02, Hh * .026); ctx.restore(); }
  if (c.sleeveless) { /* camiseta sin mangas: tirantes */ ctx.strokeStyle = c.skin; ctx.lineWidth = armW[0] * .5; ctx.beginPath(); ctx.moveTo(shP[0] - 4, shP[1] - 2); ctx.lineTo(shP[0] + 3, shP[1] + 2); ctx.stroke(); }
  drawLeg(P.ll, false);
  // cuello y cabeza
  const nk = [shP[0] + Math.sin(rad(P.lean)) * Hh * .035, shP[1] - Math.cos(rad(P.lean)) * Hh * .035];
  limb(ctx, shP, nk, Hh * .06 * b, c.skin);
  const hr = Hh * .068, hd = [nk[0] + Math.sin(rad(P.lean + P.head)) * hr * .9 + 2, nk[1] - Math.cos(rad(P.lean + P.head)) * hr * 1.05];
  out.head = { x: x + hd[0] * facing, y: hd[1], lx: hd[0] };
  ctx.save(); ctx.translate(hd[0], hd[1]); ctx.rotate(rad(P.lean * .3 + P.head));
  const hw = hr * (name.startsWith('chapo') ? 1.02 : .94), hh = hr * 1.14;
  // pelo trasero
  ctx.fillStyle = c.hair; ctx.strokeStyle = OL; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.ellipse(-hw * .12, -hh * .12, hw * 1.0, hh * 1.0, 0, 0, 7); ctx.fill();
  // cara
  ctx.fillStyle = lg(ctx, -hw, 0, hw, 0, [[0, c.skinD], [.55, c.skin], [1, c.skin]]);
  ctx.beginPath(); ctx.moveTo(-hw * .7, -hh * .55);
  ctx.bezierCurveTo(-hw * .2, -hh * 1.05, hw * .85, -hh * .95, hw * .98, -hh * .3);
  ctx.bezierCurveTo(hw * 1.0, -hh * .1, hw * 1.2, hh * .0, hw * 1.12, hh * .12);  // nariz
  ctx.bezierCurveTo(hw * 1.05, hh * .22, hw * .98, hh * .24, hw * .95, hh * .3);
  ctx.bezierCurveTo(hw * .96, hh * .55, hw * .55, hh * .98, -hw * .1, hh * .95);
  ctx.bezierCurveTo(-hw * .7, hh * .85, -hw * .85, hh * .1, -hw * .7, -hh * .55); ctx.closePath(); ctx.fill(); ctx.stroke();
  // oreja
  ctx.fillStyle = c.skinD; ctx.beginPath(); ctx.ellipse(-hw * .22, hh * .05, hw * .15, hh * .2, 0, 0, 7); ctx.fill(); ctx.stroke();
  // cabello superior
  if (!c.bald && !c.cap && !c.helmet) {
    ctx.fillStyle = c.hair; ctx.beginPath(); ctx.moveTo(-hw * .8, -hh * .1);
    ctx.bezierCurveTo(-hw * .9, -hh * 1.12, hw * .5, -hh * 1.32, hw * 1.0, -hh * .55);
    ctx.bezierCurveTo(hw * .8, -hh * .66, hw * .4, -hh * .58, hw * .1, -hh * .5);
    ctx.bezierCurveTo(-hw * .2, -hh * .45, -hw * .5, -hh * .3, -hw * .8, -hh * .1); ctx.fill(); ctx.stroke();
    if (name.startsWith('chapo')) { ctx.strokeStyle = c.gray; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-hw * .55, -hh * .5); ctx.quadraticCurveTo(-hw * .15, -hh * .95, hw * .3, -hh * 1.0); ctx.stroke(); }
  }
  if (c.bald) { ctx.fillStyle = c.hair; ctx.beginPath(); ctx.ellipse(-hw * .45, -hh * .2, hw * .3, hh * .45, rad(-10), 0, 7); ctx.fill(); }
  // ceja, ojo, nariz sombra, boca
  ctx.strokeStyle = '#150f0b'; ctx.lineWidth = 4; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(hw * .38, -hh * .22 - (opt.brow || 0)); ctx.lineTo(hw * .78, -hh * .28 + (opt.brow || 0) * .5); ctx.stroke();
  ctx.fillStyle = '#efe9de'; ctx.beginPath(); ctx.ellipse(hw * .6, -hh * .08, hw * .15, hh * .075, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#1a120d'; ctx.beginPath(); ctx.arc(hw * .66 + (opt.look || 0), -hh * .08, hh * .052, 0, 7); ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,.28)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(hw * .72, hh * .1); ctx.quadraticCurveTo(hw * .85, hh * .2, hw * .74, hh * .22); ctx.stroke();
  ctx.strokeStyle = '#2a1510'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(hw * .42, hh * .5); ctx.lineTo(hw * .82, hh * .48); ctx.stroke();
  if (c.stache) { ctx.fillStyle = '#17110d'; ctx.strokeStyle = OL; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(hw * .3, hh * .3); ctx.quadraticCurveTo(hw * .7, hh * .24, hw * 1.0, hh * .32); ctx.quadraticCurveTo(hw * .85, hh * .46, hw * .5, hh * .44); ctx.quadraticCurveTo(hw * .3, hh * .42, hw * .3, hh * .3); ctx.fill(); ctx.stroke(); }
  // barbilla sombreada
  ctx.fillStyle = 'rgba(0,0,0,.14)'; ctx.beginPath(); ctx.ellipse(hw * .2, hh * .8, hw * .6, hh * .18, 0, 0, 7); ctx.fill();
  if (c.cap) { ctx.fillStyle = c.cap; ctx.strokeStyle = OL; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-hw * .95, -hh * .3); ctx.bezierCurveTo(-hw * .9, -hh * 1.3, hw * .9, -hh * 1.3, hw * 1.0, -hh * .4); ctx.lineTo(hw * 1.5, -hh * .38); ctx.lineTo(hw * 1.5, -hh * .27); ctx.lineTo(-hw * .95, -hh * .22); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#9a8a4a'; ctx.fillRect(hw * .3, -hh * .85, hw * .2, hh * .16); }
  if (c.helmet) { ctx.fillStyle = c.helmet; ctx.strokeStyle = OL; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-hw * 1.0, -hh * .05); ctx.bezierCurveTo(-hw * 1.05, -hh * 1.45, hw * 1.0, -hh * 1.45, hw * 1.08, -hh * .3); ctx.lineTo(hw * .3, -hh * .25); ctx.lineTo(-hw * 1.0, -hh * .05); ctx.fill(); ctx.stroke(); }
  ctx.restore();
  out.handN = drawArm(P.la, false);
  ctx.restore();
  return out;
}
// ciclo de caminata: p en ciclos (0..1). devuelve pose; velocidad px/s para no deslizar
function walkPose(p, A = 22, extra = {}) {
  const s = Math.sin(p * 2 * Math.PI), c = Math.cos(p * 2 * Math.PI);
  return Object.assign({
    lean: 4, head: -2,
    ll: [A * s, 6 + 40 * Math.max(0, c)], rl: [-A * s, 6 + 40 * Math.max(0, -c)],
    la: [-A * .75 * s, 14 + 6 * Math.abs(s)], ra: [A * .75 * s, 14 + 6 * Math.abs(s)],
  }, extra);
}
function walkSpeed(name, A, period, scale = 1) { const c = CHARS[name]; return 4 * (.49 * c.H * scale) * Math.sin(rad(A)) / period; }
const IDLE = { lean: 2, head: 0, la: [4, 14], ra: [-3, 14], ll: [2, 4], rl: [-4, 6] };
// ===== Subtítulos =====
function drawSubs(ctx, lines, alpha, y0, fs = 62) {
  if (alpha <= 0) return;
  const lh = Math.round(fs * 1.29);
  ctx.save(); ctx.globalAlpha = alpha; ctx.font = `800 ${fs}px Inter, "DejaVu Sans", sans-serif`; ctx.textBaseline = 'middle';
  const h = lines.length * lh + 44, wmax = Math.max(...lines.map(l => l.reduce((s, w) => s + ctx.measureText(w.t).width, 0)));
  const bx = (W - wmax) / 2 - 36, bw = wmax + 72, by = y0;
  rrect(ctx, bx, by, bw, h, 26, 'rgba(6,8,14,.62)');
  lines.forEach((l, i) => {
    const tw = l.reduce((s, w) => s + ctx.measureText(w.t).width, 0); let x = (W - tw) / 2; const y = by + 22 + lh * i + lh / 2;
    l.forEach(w => {
      ctx.lineWidth = 9; ctx.lineJoin = 'round'; ctx.strokeStyle = 'rgba(0,0,0,.85)'; ctx.strokeText(w.t, x, y);
      ctx.fillStyle = w.y ? '#FFD400' : '#FFFFFF'; ctx.fillText(w.t, x, y); x += ctx.measureText(w.t).width;
    });
  });
  ctx.restore();
}
// separa texto con [[amarillo]] en líneas ajustadas al ancho
function layoutSub(ctx, text, maxW, fs = 62) {
  ctx.save(); ctx.font = `800 ${fs}px Inter, "DejaVu Sans", sans-serif`;
  const toks = []; text.split(/(\[\[.*?\]\])/).forEach(part => { const y = part.startsWith('[['); const s = y ? part.slice(2, -2) : part; s.split(/(\s+)/).forEach(w => { if (w !== '') toks.push({ t: w, y }); }); });
  const lines = [[]]; let cw = 0;
  toks.forEach(w => { const wd = ctx.measureText(w.t).width; if (/^\s+$/.test(w.t)) { if (lines[lines.length - 1].length) { lines[lines.length - 1].push(w); cw += wd; } return; } if (cw + wd > maxW && lines[lines.length - 1].length) { const l = lines[lines.length - 1]; while (l.length && /^\s+$/.test(l[l.length - 1].t)) l.pop(); lines.push([]); cw = 0; } lines[lines.length - 1].push(w); cw += wd; });
  const l = lines[lines.length - 1]; while (l.length && /^\s+$/.test(l[l.length - 1].t)) l.pop();
  ctx.restore(); return lines.filter(l => l.length);
}
