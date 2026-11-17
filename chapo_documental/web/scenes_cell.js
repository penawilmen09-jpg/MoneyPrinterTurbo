// ===== Escenas 2, 3 y 4: celda, regaderas (cámara) y descubrimiento =====
const CELL = { w: 1600, ceil: 400, floor: 1230, gy: 1262 };
let cellStatic = null;
function buildCell() {
  const c = mk(CELL.w, H), g = c.getContext('2d'); const { ceil, floor } = CELL;
  // pared
  rect(g, 0, 0, CELL.w, H, '#0b0c10');
  rect(g, 0, ceil, CELL.w, floor - ceil, lg(g, 0, ceil, 0, floor, [[0, '#6d6a62'], [1, '#8b877c']]));
  for (let x = 0; x < CELL.w; x += 260) { rect(g, x, ceil, 4, floor - ceil, 'rgba(0,0,0,.28)'); rect(g, x + 4, ceil, 2, floor - ceil, 'rgba(255,255,255,.07)'); }
  rect(g, 0, 1000, CELL.w, 4, 'rgba(0,0,0,.25)');
  speckle(g, 0, ceil, CELL.w, floor - ceil, 3, 2600, ['#4f4c46', '#a29e92', '#3c3a35'], 2, 9, .16);
  for (let i = 0; i < 9; i++) { const r = rng(i + 40); const x = r() * CELL.w, y = ceil + r() * 600; g.fillStyle = lg(g, 0, y, 0, y + 220, [[0, 'rgba(40,36,30,.35)'], [1, 'rgba(40,36,30,0)']]); g.fillRect(x, y, 30 + r() * 40, 220); }
  // techo en perspectiva
  g.fillStyle = lg(g, 0, 0, 0, ceil, [[0, '#08090c'], [1, '#2a2a2c']]); g.fillRect(0, 0, CELL.w, ceil);
  g.strokeStyle = 'rgba(255,255,255,.06)'; g.lineWidth = 3;
  for (let x = 0; x < CELL.w; x += 200) { g.beginPath(); g.moveTo(x, ceil); g.lineTo(CELL.w / 2 + (x - CELL.w / 2) * .55, 0); g.stroke(); }
  rect(g, 0, ceil - 10, CELL.w, 10, '#1a1a1c');
  // piso
  g.fillStyle = lg(g, 0, floor, 0, H, [[0, '#3b3a3a'], [.4, '#232324'], [1, '#101012']]); g.fillRect(0, floor, CELL.w, H - floor);
  g.strokeStyle = 'rgba(255,255,255,.05)'; g.lineWidth = 3;
  for (let x = -400; x < CELL.w + 400; x += 160) { g.beginPath(); g.moveTo(x, floor); g.lineTo(CELL.w / 2 + (x - CELL.w / 2) * 2.2, H); g.stroke(); }
  speckle(g, 0, floor, CELL.w, H - floor, 5, 1800, ['#555', '#222', '#6a6a68'], 2, 7, .18);
  rect(g, 0, floor - 6, CELL.w, 16, '#2a2825');       // zócalo
  // cama de concreto
  rect(g, 290, 1090, 480, 140, lg(g, 0, 1090, 0, 1230, [[0, '#8a867c'], [1, '#5c5a54']])); g.strokeStyle = OL; g.lineWidth = 4; g.strokeRect(290, 1090, 480, 140);
  rect(g, 308, 1230, 444, 8, 'rgba(0,0,0,.55)');
  rrect(g, 300, 1054, 460, 40, 14, '#5d6a73', OL, 4); rrect(g, 300, 1054, 460, 14, 8, 'rgba(255,255,255,.12)');
  rrect(g, 330, 1020, 120, 36, 16, '#c9c6bd', OL, 4);                      // almohada
  rrect(g, 560, 1040, 190, 30, 10, '#6e5b45', OL, 4);                      // cobija doblada
  // ventana estrecha alta + marco
  rect(g, 480, 520, 92, 300, '#05070b'); rect(g, 488, 528, 76, 284, lg(g, 0, 528, 0, 812, [[0, '#5d7799'], [1, '#2a3a50']]));
  g.strokeStyle = '#1b1c20'; g.lineWidth = 6; for (let i = 1; i < 4; i++) { g.beginPath(); g.moveTo(488 + i * 19, 528); g.lineTo(488 + i * 19, 812); g.stroke(); }
  g.beginPath(); g.moveTo(488, 670); g.lineTo(564, 670); g.stroke(); g.strokeStyle = OL; g.lineWidth = 6; g.strokeRect(480, 520, 92, 300);
  // unidad de acero: lavabo y sanitario
  rrect(g, 820, 1100, 110, 130, 12, lg(g, 820, 0, 930, 0, [[0, '#9aa0a6'], [1, '#6c7279']]), OL, 4);
  rrect(g, 835, 1000, 80, 36, 10, '#a9afb5', OL, 4); rect(g, 868, 960, 14, 40, '#7a8086'); rrect(g, 855, 950, 50, 14, 6, '#8b9197', OL, 3);
  rrect(g, 828, 1128, 94, 24, 8, '#222a30');
  // puerta de acero con mirilla
  rect(g, 28, floor - 720, 236, 720, '#0c0d10');
  rect(g, 40, floor - 705, 212, 705, lg(g, 40, 0, 252, 0, [[0, '#59635a'], [1, '#3e473f']]));
  g.strokeStyle = 'rgba(0,0,0,.45)'; g.lineWidth = 5; g.strokeRect(58, floor - 660, 176, 620);
  rect(g, 70, floor - 600, 150, 38, '#0a0b0d'); rect(g, 70, floor - 510, 150, 8, 'rgba(0,0,0,.5)');
  rect(g, 100, floor - 330, 90, 34, '#25282a'); rect(g, 200, floor - 360, 16, 52, '#8c8a7e');
  // alcove de regaderas (fondo): azulejos y regadera
  rect(g, 1010, ceil + 20, 590, floor - ceil - 20, '#46484b');
  rect(g, 1010, 700, 590, floor - 700, lg(g, 0, 700, 0, floor, [[0, '#8f9694'], [1, '#6a7170']]));
  g.strokeStyle = 'rgba(0,0,0,.35)'; g.lineWidth = 2; for (let x = 1010; x < 1600; x += 56) { g.beginPath(); g.moveTo(x, 700); g.lineTo(x, floor); g.stroke(); } for (let y = 700; y < floor; y += 56) { g.beginPath(); g.moveTo(1010, y); g.lineTo(1600, y); g.stroke(); }
  speckle(g, 1010, 700, 590, 530, 9, 500, ['#3a3f3e', '#a9b0ae'], 2, 6, .18);
  g.fillStyle = '#3d4245'; g.fillRect(1010, ceil + 20, 8, floor - ceil); rect(g, 1590, ceil + 20, 10, floor - ceil, '#26292c');
  // regadera
  rect(g, 1325, 560, 12, 190, '#8e9499'); rrect(g, 1315, 540, 90, 30, 14, '#9aa0a5', OL, 4); rrect(g, 1330, 750, 70, 16, 6, '#7c8286', OL, 3);
  rrect(g, 1262, 585, 44, 44, 10, '#6a6e72', OL, 3);
  // piso del alcove (inclinado a desagüe)
  g.fillStyle = lg(g, 0, floor, 0, H, [[0, '#2f3535'], [1, '#101313']]); g.beginPath(); g.moveTo(1010, floor); g.lineTo(1600, floor); g.lineTo(1860, H); g.lineTo(780, H); g.closePath(); g.save(); g.globalAlpha = .55; g.fill(); g.restore();
  return c;
}
function drawHole(ctx, t, open) {
  const cx = 1330, ty = 1312, by = 1398, tw = 150, bw = 200;
  ctx.save();
  ctx.fillStyle = '#9a9c98'; ctx.beginPath(); ctx.moveTo(cx - tw / 2 - 10, ty - 6); ctx.lineTo(cx + tw / 2 + 10, ty - 6); ctx.lineTo(cx + bw / 2 + 12, by + 8); ctx.lineTo(cx - bw / 2 - 12, by + 8); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#030304'; ctx.beginPath(); ctx.moveTo(cx - tw / 2, ty); ctx.lineTo(cx + tw / 2, ty); ctx.lineTo(cx + bw / 2, by); ctx.lineTo(cx - bw / 2, by); ctx.closePath(); ctx.fill();
  // interior: paredes del conducto y escalera
  ctx.fillStyle = lg(ctx, 0, ty, 0, by + 60, [[0, '#0b0b0d'], [1, '#17130f']]); ctx.beginPath(); ctx.moveTo(cx - tw / 2, ty); ctx.lineTo(cx + tw / 2, ty); ctx.lineTo(cx + tw / 2 - 18, ty + 36); ctx.lineTo(cx - tw / 2 + 18, ty + 36); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#6b6258'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(cx - 40, ty + 4); ctx.lineTo(cx - 34, by - 6); ctx.moveTo(cx + 40, ty + 4); ctx.lineTo(cx + 36, by - 6); ctx.stroke();
  for (let i = 0; i < 4; i++) { const y = ty + 12 + i * 20; ctx.beginPath(); ctx.moveTo(cx - 40 + i * 1.5, y); ctx.lineTo(cx + 40 - i * 1.2, y); ctx.stroke(); }
  ctx.strokeStyle = OL; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(cx - tw / 2 - 10, ty - 6); ctx.lineTo(cx + tw / 2 + 10, ty - 6); ctx.lineTo(cx + bw / 2 + 12, by + 8); ctx.lineTo(cx - bw / 2 - 12, by + 8); ctx.closePath(); ctx.stroke();
  ctx.restore();
  glow(ctx, cx, ty + 40, 160 * open, '255,190,110', .22 * open);
}
function drawPartition(ctx) {   // pared frontal del alcove (oculta lo que ocurre dentro)
  const { ceil, floor } = CELL;
  rect(ctx, 1096, ceil, 504, floor - ceil + 46, lg(ctx, 0, ceil, 0, floor, [[0, '#5e5c56'], [1, '#7a766c']]));
  speckle(ctx, 1096, ceil, 504, floor - ceil, 12, 900, ['#46443f', '#9a968a'], 2, 7, .15);
  ctx.strokeStyle = OL; ctx.lineWidth = 5; ctx.strokeRect(1096, ceil, 504, floor - ceil + 46);
  rect(ctx, 1096, ceil, 12, floor - ceil + 46, 'rgba(0,0,0,.35)');
  // piso frente a partición
  rect(ctx, 1096, floor + 46, 504, 8, 'rgba(0,0,0,.5)');
}
function cellMask(ctx, f, mode, redA, lampX = 520, flick = 1) {
  ctx.save(); ctx.globalCompositeOperation = 'multiply';
  const g = rgr(ctx, lampX, 560, 60, 1100, [[0, `rgb(${255 * flick | 0},${232 * flick | 0},${186 * flick | 0})`], [.45, '#a09a8e'], [1, '#2d3038']]);
  ctx.fillStyle = g; ctx.fillRect(-300, 0, CELL.w + 600, H); ctx.restore();
  glow(ctx, lampX, 440, 330, '255,214,150', .42 * flick);
  glow(ctx, lampX, 1300, 420, '255,214,150', .07 * flick);
  // luz de la ventana (rayo frío)
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = lg(ctx, 520, 560, 700, 1230, [[0, 'rgba(120,150,200,.22)'], [1, 'rgba(120,150,200,0)']]);
  ctx.beginPath(); ctx.moveTo(488, 560); ctx.lineTo(564, 560); ctx.lineTo(760, 1260); ctx.lineTo(560, 1260); ctx.closePath(); ctx.fill(); ctx.restore();
  // motas de polvo
  const r = rng(21); ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 34; i++) { const bx = 540 + (r() - .3) * 200, by = 600 + r() * 600, ph = r() * 6; const x = bx + Math.sin(f / 60 + ph) * 18 + (by - 600) * .22, y = (by - f * .35 * (0.5 + r())) % 700 + 560; ctx.fillStyle = `rgba(190,210,240,${.18 + .15 * Math.sin(f / 15 + ph)})`; ctx.fillRect(x, y, 3, 3); }
  ctx.restore();
  if (redA > 0) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = `rgba(190,15,15,${redA * .28})`; ctx.fillRect(-300, 0, CELL.w + 600, H); ctx.restore(); }
}
function lampFixture(ctx, x, y) {
  rect(ctx, x - 4, CELL.ceil - 10, 8, 22, '#222'); rrect(ctx, x - 70, y - 8, 140, 44, 10, '#2a2b2e', OL, 4);
  rrect(ctx, x - 52, y + 2, 104, 24, 8, '#f4e6bf');
  ctx.strokeStyle = '#111'; ctx.lineWidth = 3; for (let i = -40; i <= 40; i += 20) { ctx.beginPath(); ctx.moveTo(x + i, y - 4); ctx.lineTo(x + i, y + 34); ctx.stroke(); }
}
function lerpArr(a, b, w) { return a.map((v, i) => v + (b[i] - v) * w); }
function lerpPose(a, b, w) { const o = {}; for (const k in b) { o[k] = Array.isArray(b[k]) ? lerpArr(a[k] || b[k], b[k], w) : lerp(a[k] ?? b[k], b[k], w); } return o; }
// caminantes guiados por la línea de tiempo: sin deslizamiento de pies
function walker(id, t, sc = 1) {
  const w = TL.walks.find(x => x.id === id); const L = .49 * CHARS[w.who].H * sc;
  const dur = w.t1 - w.t0, v = (w.x1 - w.x0) / dur, per = 2 * dur / w.N;
  const A = Math.asin(clamp(Math.abs(v) * per / (4 * L), 0, .7)) * 180 / Math.PI;
  const dir = Math.sign(v) || 1;
  if (t <= w.t0) return { x: w.x0, dir, pose: null, moving: false };
  if (t >= w.t1) return { x: w.x1, dir, pose: null, moving: false };
  const p = (t - w.t0) / per + .75, wt = Math.min(1, (t - w.t0) / .3, (w.t1 - t) / .3);
  return { x: w.x0 + v * (t - w.t0), dir, pose: lerpPose(IDLE, walkPose(p, A), ease(wt)), moving: true };
}
// ----- ESCENA 2: la celda -----
const S2 = {
  draw(ctx, lt, f) {
    if (!cellStatic) cellStatic = buildCell();
    const t = 7 + lt;
    ctx.save(); const camX = lerp(250, 80, ease(lt / 7.6)), z = lerp(1.0, 1.1, lt / 7.6);
    ctx.translate(W / 2, 790); ctx.scale(z, z); ctx.translate(-(camX + W / 2), -860);
    ctx.drawImage(cellStatic, 0, 0);
    const flick = 1 - (Math.sin(f * .9) > .96 ? .25 : 0);
    lampFixture(ctx, 520, 430);
    // acciones
    const wa = walker('chapo_a', t), wb = walker('chapo_b', t);
    let x, dir, pose, opt = {};
    if (t < 11.0) {
      x = wa.x; dir = wa.dir;
      if (t < 9.7) pose = wa.pose || IDLE;
      else { const k = ease(seg(t, 9.7, 10.4)), k2 = ease(seg(t, 10.2, 10.9)); pose = { lean: 2, head: -16 * k + 14 * k2, la: [4, 14], ra: [-3, 14], ll: [2, 4], rl: [-4, 6] }; }
      if (t >= 10.3 && t < 11.0) { dir = wa.dir; }
    } else { x = wb.x; dir = 1; pose = wb.pose || IDLE; }
    if (t >= 10.0 && t < 11.0) { dir = t < 10.5 ? -1 : 1; }
    if (t >= 9.7 && t < 10.5) { opt.look = -3; }
    if (t >= 13.6) { pose = { lean: 3, head: 4, la: [6, 18], ra: [-4, 14], ll: [2, 4], rl: [-4, 6] }; }
    drawPerson(ctx, 'chapo', x, CELL.gy, dir, pose, opt);
    drawPartition(ctx);
    cellMask(ctx, f, 'normal', 0, 520, flick);
    ctx.restore();
    post(ctx, f, { vig: .6 });
  }
};
// ----- ESCENA 3: último registro (cámara de vigilancia ilustrada) -----
let tmpCv = null;
const S3 = {
  draw(ctx, lt, f) {
    if (!cellStatic) cellStatic = buildCell();
    if (!tmpCv) tmpCv = mk(W, H);
    const t = 14 + lt, g = tmpCv.getContext('2d');
    g.clearRect(0, 0, W, H);
    const intro = lt < 1.6;
    if (intro) {   // cápsula de la cámara en el techo (inserto)
      g.fillStyle = '#0a0b0e'; g.fillRect(0, 0, W, H);
      const k = lt / 1.6;
      g.save(); g.translate(W / 2, 760); g.scale(1 + k * .06, 1 + k * .06);
      g.fillStyle = lg(g, 0, -420, 0, 400, [[0, '#2a2b30'], [1, '#14151a']]); g.fillRect(-W, -760, 2 * W, 560);
      for (let i = -6; i < 7; i++) { g.strokeStyle = 'rgba(255,255,255,.05)'; g.lineWidth = 3; g.beginPath(); g.moveTo(i * 160, -200); g.lineTo(i * 90, -760); g.stroke(); }
      rrect(g, -80, -230, 160, 28, 6, '#3a3b40', OL, 4); rect(g, -10, -204, 20, 80, '#2a2b30');
      g.beginPath(); g.ellipse(0, -30, 150, 120, 0, 0, 7); g.fillStyle = lg(g, -150, 0, 150, 0, [[0, '#585b62'], [.45, '#c9ccd2'], [1, '#43464c']]); g.fill(); g.strokeStyle = OL; g.lineWidth = 6; g.stroke();
      g.fillStyle = '#07080a'; g.beginPath(); g.ellipse(18, -14, 64, 56, rad(-12), 0, 7); g.fill(); g.strokeStyle = '#44484f'; g.lineWidth = 6; g.stroke();
      g.fillStyle = rgr(g, 4, -30, 2, 40, [[0, '#6e90c6'], [1, '#0b1120']]); g.beginPath(); g.ellipse(18, -14, 40, 36, 0, 0, 7); g.fill();
      g.restore();
      const on = Math.floor(f / 12) % 2 === 0; glow(g, W / 2 + 120, 700, on ? 90 : 20, '255,30,30', on ? .9 : .2); g.fillStyle = on ? '#ff3b2f' : '#5a1511'; g.beginPath(); g.arc(W / 2 + 120, 700, 10, 0, 7); g.fill();
    } else {
      g.save(); const camX = lerp(140, 300, ease((lt - 1.6) / 6.4));
      g.translate(-camX, -70); g.drawImage(cellStatic, 0, 0); lampFixture(g, 520, 430);
      const wc = walker('chapo_c', t); const standA = IDLE;
      if (t < 20.3) drawPerson(g, 'chapo', wc.x, CELL.gy, 1, wc.pose || standA);
      drawPartition(g); cellMask(g, f, 'cctv', 0, 520, 1); g.restore();
    }
    ctx.save(); ctx.filter = 'grayscale(.88) sepia(.25) hue-rotate(70deg) contrast(1.18) brightness(1.12)'; ctx.drawImage(tmpCv, 0, 0); ctx.restore();
    // capa de cámara: líneas de barrido, REC, marca de hora diegética
    ctx.save(); ctx.globalAlpha = .18; ctx.fillStyle = '#000'; for (let y = (f % 4); y < H; y += 4) ctx.fillRect(0, y, W, 1.5); ctx.restore();
    if (!intro) {
      const fl = ((f / 3) | 0) % 40 === 0 ? .06 : 0; ctx.fillStyle = `rgba(160,255,190,${fl})`; ctx.fillRect(0, 0, W, H);
      ctx.save(); ctx.strokeStyle = 'rgba(210,255,225,.75)'; ctx.lineWidth = 5;
      [[60, 120, 1, 1], [W - 60, 120, -1, 1], [60, 1360, 1, -1], [W - 60, 1360, -1, -1]].forEach(([x, y, sx, sy]) => { ctx.beginPath(); ctx.moveTo(x, y + 60 * sy); ctx.lineTo(x, y); ctx.lineTo(x + 60 * sx, y); ctx.stroke(); });
      ctx.font = '700 40px "DejaVu Sans Mono", monospace'; ctx.fillStyle = 'rgba(225,255,235,.92)'; ctx.textBaseline = 'top';
      const colon = Math.floor(f / 15) % 2 ? ' ' : ':'; ctx.fillText('11-JUL-2015   20' + colon + '52', 90, 140);
      const on = Math.floor(f / 15) % 2 === 0; if (on) { ctx.fillStyle = '#ff3b30'; ctx.beginPath(); ctx.arc(W - 250, 160, 12, 0, 7); ctx.fill(); } ctx.fillStyle = 'rgba(225,255,235,.92)'; ctx.fillText('REC', W - 215, 140); ctx.restore();
    }
    // salto de señal al desaparecer
    if (t > 20.3 && t < 20.5) { ctx.save(); ctx.globalAlpha = .5; ctx.fillStyle = '#fff'; ctx.fillRect(0, (f * 97) % H, W, 6); ctx.restore(); }
    post(ctx, f, { vig: .7, grain: .2 });
  }
};
// ----- ESCENA 4: el descubrimiento (corte transversal de la celda) -----
const S4 = {
  draw(ctx, lt, f) {
    if (!cellStatic) cellStatic = buildCell();
    const t = 22 + lt;
    const camX = lerp(0, 470, ease(seg(t, 24.2, 28.2))), z = lerp(1.0, 1.08, seg(t, 22, 30));
    ctx.save(); ctx.translate(W / 2, 790); ctx.scale(z, z); ctx.translate(-(camX + W / 2), -860);
    ctx.drawImage(cellStatic, 0, 0); lampFixture(ctx, 520, 430);
    // puerta: abre hacia la celda
    const open = ease(seg(t, 22.2, 23.1));
    rect(ctx, 40, CELL.floor - 705, 212, 705, lg(ctx, 40, 0, 252, 0, [[0, '#2a2f2b'], [1, '#585f56']]));  // vano
    const corr = lg(ctx, 40, 0, 252, 0, [[0, '#4a4538'], [1, '#2b2a25']]); ctx.fillStyle = corr; ctx.fillRect(48, CELL.floor - 690, 196, 690);
    glow(ctx, 150, CELL.floor - 380, 260, '210,190,130', .4 * open);
    const pw = 212 * (1 - open * .82);
    ctx.fillStyle = '#4f5951'; ctx.beginPath(); ctx.moveTo(40, CELL.floor - 705); ctx.lineTo(40 + pw, CELL.floor - 705 + open * 26); ctx.lineTo(40 + pw, CELL.floor - open * 22); ctx.lineTo(40, CELL.floor); ctx.fill(); ctx.strokeStyle = OL; ctx.lineWidth = 4; ctx.stroke();
    // personajes
    const g1 = walker('g1_a', t), g2 = walker('g2_a', t);
    const h = drawHole.bind(null, ctx, t);
    // guardia 1: llega, mira, se inclina sobre la abertura
    let p1 = g1.pose || IDLE, o1 = {}, p2 = g2.pose || IDLE;
    const arrive1 = seg(t, 27.0, 27.9);
    if (!g1.moving && t >= 27.0) p1 = { lean: lerp(4, 46, ease(arrive1)), head: lerp(0, 8, arrive1), la: [lerp(4, 62, ease(arrive1)), lerp(14, 6, arrive1)], ra: [lerp(-3, 22, arrive1), 28], ll: [lerp(2, 18, arrive1), lerp(4, 42, arrive1)], rl: [lerp(-4, -10, arrive1), lerp(6, 30, arrive1)] };
    if (t < 27.0 && t > 24.6 && t < 25.8) { const k = Math.sin(seg(t, 24.6, 25.8) * Math.PI); p1 = Object.assign({}, p1, { head: (p1.head || 0) - 8 * k }); }
    const radioK = ease(seg(t, 28.2, 28.8));
    if (!g2.moving && t >= 27.6) p2 = { lean: 3, head: 4, la: [lerp(4, 128, radioK), lerp(14, 110, radioK)], ra: [-2, 14], ll: [3, 6], rl: [-3, 8] };
    drawHoleLayer = () => { };
    // el hueco aparece al abrirse la vista del alcove
    drawHole(ctx, t, ease(seg(t, 23.0, 24.0)));
    const a = drawPerson(ctx, 'g2', g2.x, CELL.gy + 6, 1, p2);
    const b = drawPerson(ctx, 'g1', g1.x, CELL.gy + 40, 1, p1);
    // linternas
    const fl = (hand, tx, ty, rgb, al) => { const ang = Math.atan2(ty - hand.y, tx - hand.x); rect(ctx, hand.x - 4, hand.y - 8, 26, 14, '#222'); cone(ctx, hand.x + 18, hand.y, ang, 520, 110, rgb, al); glow(ctx, hand.x + 18, hand.y, 60, rgb, .5); };
    if (t > 24.4) { const tx = t < 27.2 ? lerp(b.handN.x + 280, 1330, ease(seg(t, 24.4, 27.0))) : 1330, ty = t < 27.2 ? lerp(CELL.floor - 60, 1340, seg(t, 24.4, 27.0)) : 1340; fl(b.handN, tx, ty, '255,250,225', .55); }
    // llaves y radio
    if (t >= 28.2) { ctx.fillStyle = '#111'; ctx.fillRect(a.handN.x - 10, a.handN.y - 20, 22, 34); ctx.fillStyle = '#2f353a'; ctx.fillRect(a.handN.x - 6, a.handN.y - 26, 4, 10); if (Math.floor(f / 6) % 2) glow(ctx, a.handN.x, a.handN.y - 4, 22, '255,60,40', .8); }
    // alarma: baliza roja
    const alarmOn = t > 25.2; const pulse = alarmOn ? .5 + .5 * Math.sin(f * .55) : 0;
    cellMask(ctx, f, 'cut', alarmOn ? Math.max(0, .15 + .85 * pulse) * ease(seg(t, 25.2, 25.8)) : 0, 520, 1);
    if (alarmOn) { rrect(ctx, 760, CELL.ceil - 2, 50, 32, 6, '#391010', OL, 3); glow(ctx, 785, CELL.ceil + 14, 120, '255,30,20', .3 + .7 * pulse); const ang = f * .18; cone(ctx, 785, CELL.ceil + 14, ang, 480, 60, '255,40,30', .22 * pulse + .06); }
    ctx.restore();
    post(ctx, f, { vig: .65 });
  }
};
let drawHoleLayer = () => { };
