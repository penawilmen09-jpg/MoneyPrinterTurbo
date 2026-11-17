// ===== Escenas 1, 5, 6, 7, 8 =====
function sky(g, w, h, stops) { g.fillStyle = lg(g, 0, 0, 0, h, stops); g.fillRect(0, 0, w, h); }
function stars(g, w, h, n, seed, a = 1) { const r = rng(seed); for (let i = 0; i < n; i++) { g.fillStyle = `rgba(255,250,235,${(.2 + r() * .7) * a})`; const s = r() < .1 ? 3 : 2; g.fillRect(r() * w, r() * h, s, s); } }
function tree(g, x, y, s, col, col2) {
  g.fillStyle = '#1a1410'; g.fillRect(x - 6 * s, y - 90 * s, 12 * s, 90 * s);
  [[0, -150, 70], [-40, -110, 55], [40, -115, 55], [0, -100, 60]].forEach(([dx, dy, r]) => { g.fillStyle = lg(g, x + dx * s, y + (dy - r) * s, x + dx * s, y + (dy + r) * s, [[0, col2], [1, col]]); g.beginPath(); g.arc(x + dx * s, y + dy * s, r * s, 0, 7); g.fill(); });
}
function palm(g, x, y, s, col) {
  g.strokeStyle = '#2a1f17'; g.lineWidth = 16 * s; g.lineCap = 'round'; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + 24 * s, y - 180 * s, x + 6 * s, y - 330 * s); g.stroke();
  g.strokeStyle = col; g.lineWidth = 8 * s;
  for (let i = 0; i < 9; i++) { const a = -Math.PI * .95 + i * Math.PI * .24; g.beginPath(); g.moveTo(x + 6 * s, y - 330 * s); g.quadraticCurveTo(x + 6 * s + Math.cos(a) * 80 * s, y - 330 * s + Math.sin(a) * 60 * s - 20 * s, x + 6 * s + Math.cos(a) * 150 * s, y - 330 * s + Math.sin(a) * 70 * s + 70 * s); g.stroke(); }
}
function razor(g, x0, x1, y) { g.strokeStyle = 'rgba(190,195,205,.75)'; g.lineWidth = 2; for (let x = x0; x < x1; x += 11) { g.beginPath(); g.arc(x, y, 9, 0, Math.PI * 2); g.stroke(); } }
function litWindows(g, x, y, cols, rows, dx, dy, w, h, seed, onP) { const r = rng(seed); for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) { const on = r() < onP; g.fillStyle = on ? '#ffd78a' : '#12151d'; g.fillRect(x + i * dx, y + j * dy, w, h); } }
// ===== ESCENA 1: panorámica del penal (anochecer) =====
let s1 = null;
function buildS1() {
  const o = {};
  o.far = mk(1500, 900); let g = o.far.getContext('2d');
  g.fillStyle = '#251d3a'; g.beginPath(); g.moveTo(0, 900); g.lineTo(0, 700); g.lineTo(220, 610); g.lineTo(380, 660); g.lineTo(560, 470); g.lineTo(650, 430); g.lineTo(700, 450); g.lineTo(760, 410); g.lineTo(860, 470); g.lineTo(1000, 640); g.lineTo(1200, 600); g.lineTo(1500, 690); g.lineTo(1500, 900); g.closePath(); g.fill();
  o.mid = mk(2000, 700); g = o.mid.getContext('2d');
  g.fillStyle = '#1b1830'; g.beginPath(); g.moveTo(0, 700); g.lineTo(0, 420); for (let x = 0; x <= 2000; x += 40) g.lineTo(x, 400 - 80 * Math.sin(x / 260) - 40 * Math.sin(x / 90)); g.lineTo(2000, 700); g.closePath(); g.fill();
  const r = rng(5); for (let i = 0; i < 70; i++) { g.fillStyle = '#12111f'; const x = r() * 2000, y = 360 + r() * 60 - 40 * Math.sin(x / 260); g.beginPath(); g.arc(x, y, 14 + r() * 10, 0, 7); g.fill(); }
  // complejo penitenciario
  o.pris = mk(3000, 1250); g = o.pris.getContext('2d'); const gy = 1180;
  const bld = (x, y, w, h, c1, c2) => { rect(g, x, y, w, h, lg(g, 0, y, 0, y + h, [[0, c1], [1, c2]])); g.strokeStyle = OL; g.lineWidth = 4; g.strokeRect(x, y, w, h); };
  // edificios traseros
  bld(560, 760, 880, 280, '#4a4b57', '#2c2d37'); bld(1560, 860, 640, 180, '#444553', '#2a2b35'); bld(2300, 900, 500, 140, '#444553', '#2a2b35');
  bld(900, 700, 300, 60, '#555662', '#33343e');
  litWindows(g, 600, 800, 22, 3, 38, 58, 16, 30, 11, .55); litWindows(g, 1600, 900, 15, 2, 40, 62, 18, 30, 12, .5); litWindows(g, 2330, 930, 11, 2, 42, 56, 18, 26, 13, .5);
  for (let x = 600; x < 1440; x += 120) rect(g, x, 780, 4, 260, 'rgba(0,0,0,.25)');
  rect(g, 1100, 640, 4, 60, '#222'); rect(g, 1060, 610, 80, 4, '#222'); rect(g, 700, 690, 3, 70, '#222');
  // muro perimetral y alambre
  rect(g, 0, 1040, 3000, 140, lg(g, 0, 1040, 0, 1180, [[0, '#62636e'], [1, '#2f3039']])); g.strokeStyle = OL; g.lineWidth = 5; g.strokeRect(-5, 1040, 3010, 140);
  for (let x = 0; x < 3000; x += 150) rect(g, x, 1040, 5, 140, 'rgba(0,0,0,.35)');
  razor(g, 0, 3000, 1028); razor(g, 0, 3000, 1010);
  speckle(g, 0, 1040, 3000, 140, 8, 1600, ['#3a3b44', '#7a7b84'], 2, 6, .18);
  // torres de vigilancia
  [[360], [1520], [2540]].forEach(([x]) => {
    rect(g, x - 24, 780, 48, 400, lg(g, x - 24, 0, x + 24, 0, [[0, '#6a6b76'], [1, '#34353f']])); g.strokeStyle = OL; g.lineWidth = 4; g.strokeRect(x - 24, 780, 48, 400);
    poly(g, [[x - 70, 780], [x + 70, 780], [x + 54, 700], [x - 54, 700]], '#3a3b46', OL, 4); rect(g, x - 52, 700, 104, 76, '#ffcf7d'); g.strokeStyle = '#2a2b33'; g.lineWidth = 4; g.strokeRect(x - 52, 702, 104, 74); g.beginPath(); g.moveTo(x - 17, 702); g.lineTo(x - 17, 776); g.moveTo(x + 17, 702); g.lineTo(x + 17, 776); g.stroke();
    poly(g, [[x - 80, 700], [x + 80, 700], [x + 60, 668], [x - 60, 668]], '#2a2b34', OL, 4); rect(g, x - 2, 620, 4, 50, '#222');
  });
  // cerco y postes de luz
  g.strokeStyle = '#25262d'; g.lineWidth = 3; for (let x = 0; x < 3000; x += 22) { g.beginPath(); g.moveTo(x, 1180); g.lineTo(x, 1120); g.stroke(); } g.beginPath(); g.moveTo(0, 1122); g.lineTo(3000, 1122); g.moveTo(0, 1150); g.lineTo(3000, 1150); g.stroke();
  g.fillStyle = '#13141a'; g.fillRect(0, 1180, 3000, 70);
  o.pris.lamps = [140, 520, 920, 1320, 1720, 2120, 2520, 2900];
  o.pris.lamps.forEach(x => { rect(g, x - 3, 920, 6, 260, '#191a20'); rect(g, x - 40, 916, 80, 8, '#191a20'); });
  s1 = o;
}
function drawPrison(ctx, lt, f, camX, z, op = {}) {
    if (!s1) buildS1();
    sky(ctx, W, 1010, [[0, '#04061a'], [.3, '#0f1332'], [.55, '#2d2150'], [.78, '#7a3d5e'], [.92, '#d4754f'], [1, '#f5a86a']]); rect(ctx, 0, 1010, W, H - 1010, '#07080c');
    stars(ctx, W, 700, 140, 3, .8 + .2 * Math.sin(f / 9));
    glow(ctx, 420 - camX * .08, 980, 520, '255,150,90', .55);
    // nubes lentas
    ctx.save(); for (let i = 0; i < 6; i++) { const cx = ((i * 330 + lt * 16 * (1 + i % 3 * .3)) % 1500) - 200, cy = 640 + i * 30; ctx.globalAlpha = .55; ctx.fillStyle = i % 2 ? '#5a3556' : '#6b3c58'; ctx.beginPath(); ctx.ellipse(cx, cy, 260, 20 + (i % 3) * 6, 0, 0, 7); ctx.fill(); ctx.globalAlpha = .3; ctx.fillStyle = '#f09b6a'; ctx.beginPath(); ctx.ellipse(cx - 30, cy + 8, 200, 8, 0, 0, 7); ctx.fill(); } ctx.restore();
    // aves
    for (let i = 0; i < 7; i++) { const bx = ((lt * 70 + i * 90) % 1400) - 150, by = 500 + i * 22 + Math.sin(lt * 2 + i) * 14, fl = Math.sin(f * .35 + i) * 8; ctx.strokeStyle = '#150f1c'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(bx - 14, by + fl); ctx.quadraticCurveTo(bx - 6, by - 4, bx, by); ctx.quadraticCurveTo(bx + 6, by - 4, bx + 14, by + fl); ctx.stroke(); }
    ctx.save(); ctx.translate(W / 2, 1000); ctx.scale(z, z); ctx.translate(-W / 2, -1000 - 170);
    ctx.drawImage(s1.far, -camX * .1 - 50, 170); ctx.drawImage(s1.mid, -camX * .25 - 100, 480);
    // neblina
    ctx.fillStyle = lg(ctx, 0, 1000, 0, 1230, [[0, 'rgba(120,80,100,0)'], [1, 'rgba(150,100,110,.35)']]); ctx.fillRect(0, 1000, W, 230);
    ctx.drawImage(s1.pris, -camX * 1.0, 0);
    ctx.save(); ctx.translate(-camX, 0);
    // faros de patio y reflectores de torres (vivos)
    s1.pris.lamps.forEach((x, i) => { glow(ctx, x, 920, 240, '255,214,140', .55); cone(ctx, x, 922, Math.PI / 2, 260, 150, '255,214,140', .2); });
    [[360, 0], [1520, 1.3], [2540, 2.6]].forEach(([x, ph]) => { const a = Math.PI / 2 + Math.sin(lt * .9 + ph) * .85; glow(ctx, x, 738, 120, '255,200,120', .8); cone(ctx, x, 736, a, 900, 190, '235,240,255', .26); const gx = x + Math.cos(a) * 520, gy = 736 + Math.sin(a) * 520; if (gy > 1170) glow(ctx, x + Math.cos(a) * (444 / Math.sin(a)), 1180, 120, '235,240,255', .18); });
    ctx.restore();
    // primer plano: pasto oscuro y cerca difusa
    ctx.fillStyle = lg(ctx, 0, 1230, 0, 1500, [[0, '#0e1016'], [1, '#05060a']]); ctx.fillRect(-100, 1230, W + 200, 800);
    ctx.restore();
    ctx.save(); ctx.fillStyle = '#07080c'; for (let x = -((camX * 1.7) % 220); x < W + 220; x += 220) { ctx.fillRect(x, 1180, 14, 420); ctx.fillStyle = '#07080c'; } ctx.strokeStyle = 'rgba(180,185,200,.5)'; ctx.lineWidth = 2; for (let x = -((camX * 1.7) % 220) - 220; x < W + 220; x += 220) { ctx.beginPath(); ctx.moveTo(x + 7, 1198); ctx.quadraticCurveTo(x + 117, 1232, x + 227, 1198); ctx.stroke(); } ctx.restore();
    if (op.dawn) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = lg(ctx, 0, 560, 0, 1080, [[0, 'rgba(255,150,90,0)'], [1, `rgba(255,150,90,${.32 * op.dawn})`]]); ctx.fillRect(0, 560, W, 520); ctx.restore(); }
    post(ctx, f, { vig: op.vig ?? .62 });
}
const S1 = { draw(ctx, lt, f) { const p = ease(lt / 7); drawPrison(ctx, lt, f, lerp(0, 1550, p), lerp(1.0, 1.07, p)); } };
// Introducción: el penal de noche, cámara acercándose lentamente
const INTRO = { draw(ctx, lt, f) { const u = clamp(lt / 4); drawPrison(ctx, lt + 3, f, lerp(520, 760, u), lerp(1.0, 1.5, ease(u)), { vig: .72 }); } };
// Vista cinematográfica del penal (cámara retrocede) antes de la recaptura
const PV = { draw(ctx, lt, f) { const u = clamp(lt / 2.8); drawPrison(ctx, lt + 9, f, lerp(1250, 1000, u), lerp(1.5, 1.18, ease(u)), { dawn: .4 * u, vig: .66 }); } };
// Cierre: vista amplia del penal al amanecer y transición de salida (barrotes + negro)
const CLOSE = { draw(ctx, lt, f) {
  const u = clamp(lt / 4.8); drawPrison(ctx, lt + 14, f, lerp(1000, 1500, ease(u)), lerp(1.18, 1.0, ease(u)), { dawn: lerp(.4, 1, u), vig: .66 });
  const bk = ease(seg(lt, 3.2, 4.1)); if (bk > 0) { const bw = 70, n = 8; ctx.save(); ctx.fillStyle = '#0a0b0f'; for (let i = 0; i < n; i++) { const x = (i + .5) * (W / n) - bw / 2, h = H * bk; ctx.fillStyle = '#0a0b0f'; ctx.fillRect(x, 0, bw, h); ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.fillRect(x + 6, 0, 8, h); } ctx.fillStyle = '#0a0b0f'; ctx.fillRect(0, 0, W, 90 * bk); ctx.restore(); }
} };
// ===== ESCENA 5: el túnel (corte lateral) =====
const TN = { w: 6600, y: 1000, h: 190, surf: 560, shaftA: 380, shaftB: 6200 };
let s5 = null;
function buildS5() {
  const c = mk(TN.w, 2400), g = c.getContext('2d'); const sy = TN.surf, r = rng(31);
  // cielo nocturno
  sky(g, TN.w, sy, [[0, '#05071a'], [.6, '#151a3a'], [1, '#2a2650']]); stars(g, TN.w, sy - 100, 260, 9, .9);
  // suelo/estratos
  g.fillStyle = lg(g, 0, sy, 0, 2400, [[0, '#4a3524'], [.3, '#3a2a1d'], [.6, '#2a1e15'], [1, '#150f0b']]); g.fillRect(0, sy, TN.w, 2400 - sy);
  for (let i = 0; i < 9; i++) { const y0 = sy + 80 + i * 110; g.strokeStyle = `rgba(${i % 2 ? '120,90,60' : '20,14,10'},.35)`; g.lineWidth = 3 + r() * 5; g.beginPath(); g.moveTo(0, y0); for (let x = 0; x <= TN.w; x += 120) g.lineTo(x, y0 + Math.sin(x / 400 + i) * 22 + r() * 8); g.stroke(); }
  speckle(g, 0, sy, TN.w, 2400 - sy, 4, 12000, ['#6a5238', '#1c130d', '#7d6648', '#2c2016'], 3, 14, .35);
  for (let i = 0; i < 220; i++) { const x = r() * TN.w, y = sy + 60 + r() * 1500; g.fillStyle = `rgba(${90 + r() * 50},${80 + r() * 40},${70 + r() * 30},.55)`; g.beginPath(); g.ellipse(x, y, 6 + r() * 18, 4 + r() * 10, r() * 3, 0, 7); g.fill(); }
  // superficie: colinas lejanas, campos, casas, postes
  g.fillStyle = '#1a1730'; g.beginPath(); g.moveTo(0, sy); for (let x = 0; x <= TN.w; x += 40) g.lineTo(x, sy - 60 - 40 * Math.sin(x / 500) - 25 * Math.sin(x / 170)); g.lineTo(TN.w, sy); g.closePath(); g.fill();
  g.fillStyle = '#1d3320'; g.fillRect(0, sy - 10, TN.w, 14); g.fillStyle = '#2f4a2a'; g.fillRect(0, sy - 4, TN.w, 6);
  for (let x = 1100; x < 5700; x += 140 + r() * 260) { if (r() < .55) tree(g, x, sy, .5 + r() * .5, '#0f2415', '#1c3a22'); else { const w = 90 + r() * 70, hh = 60 + r() * 30; rect(g, x, sy - hh, w, hh, '#3a3646'); g.strokeStyle = OL; g.lineWidth = 3; g.strokeRect(x, sy - hh, w, hh); poly(g, [[x - 8, sy - hh], [x + w / 2, sy - hh - 36], [x + w + 8, sy - hh]], '#6a3a34', OL, 3); rect(g, x + 14, sy - hh + 14, 20, 24, r() < .5 ? '#ffd38a' : '#1a1a22'); } }
  [2200, 3300, 4400].forEach(x => { g.strokeStyle = '#15151c'; g.lineWidth = 6; g.beginPath(); g.moveTo(x, sy); g.lineTo(x, sy - 220); g.moveTo(x - 40, sy - 200); g.lineTo(x + 40, sy - 200); g.stroke(); });
  g.strokeStyle = 'rgba(20,20,28,.9)'; g.lineWidth = 2; g.beginPath(); g.moveTo(2160, sy - 200); g.quadraticCurveTo(2750, sy - 150, 3260, sy - 200); g.quadraticCurveTo(3850, sy - 150, 4360, sy - 200); g.stroke();
  // penal (izquierda): muro, torre y edificio de celdas en corte
  rect(g, 0, sy - 120, 80, 120, '#44454f'); rect(g, 640, sy - 150, 500, 150, lg(g, 0, sy - 150, 0, sy, [[0, '#4f5060'], [1, '#2f303a']])); g.strokeStyle = OL; g.lineWidth = 4; g.strokeRect(640, sy - 150, 500, 150);
  litWindows(g, 668, sy - 128, 11, 2, 42, 54, 20, 24, 77, .6); razor(g, 640, 1140, sy - 158);
  // edificio de celdas (corte): piso de la celda y regadera
  rect(g, 200, sy - 230, 360, 230, '#3a3b45'); g.strokeStyle = OL; g.lineWidth = 5; g.strokeRect(200, sy - 230, 360, 230);
  rect(g, 212, sy - 218, 336, 218, lg(g, 0, sy - 218, 0, sy, [[0, '#7a766a'], [1, '#5a574e']])); rect(g, 212, sy - 20, 336, 20, '#37363a');
  rect(g, 440, sy - 180, 100, 160, '#8c9391'); rect(g, 476, sy - 190, 8, 40, '#8e9499'); rrect(g, 462, sy - 200, 52, 16, 6, '#9aa0a5', OL, 3);
  poly(g, [[180, sy - 230], [580, sy - 230], [560, sy - 262], [200, sy - 262]], '#2a2b33', OL, 4);
  // tubo/pozo vertical desde la regadera
  rect(g, TN.shaftA - 46, sy - 20, 92, TN.y - sy + TN.h / 2 + 30, '#0b0907'); g.strokeStyle = '#6a4d33'; g.lineWidth = 6;
  for (let y = sy + 10; y < TN.y + 60; y += 90) { g.beginPath(); g.moveTo(TN.shaftA - 46, y); g.lineTo(TN.shaftA + 46, y); g.stroke(); }
  g.strokeStyle = '#8b8174'; g.lineWidth = 6; g.beginPath(); g.moveTo(TN.shaftA - 24, sy - 12); g.lineTo(TN.shaftA - 24, TN.y + 80); g.moveTo(TN.shaftA + 24, sy - 12); g.lineTo(TN.shaftA + 24, TN.y + 80); g.stroke();
  for (let y = sy; y < TN.y + 70; y += 28) { g.beginPath(); g.moveTo(TN.shaftA - 24, y); g.lineTo(TN.shaftA + 24, y); g.stroke(); }
  // construcción de salida (derecha)
  const bx = 5740, by = sy;
  rect(g, bx, by - 330, 22, 330, '#6f6d68'); rect(g, bx + 300, by - 330, 22, 330, '#6f6d68'); rect(g, bx + 600, by - 330, 22, 330, '#6f6d68');
  rect(g, bx - 30, by - 340, 680, 24, '#85837d'); rect(g, bx - 30, by - 20, 680, 20, '#85837d'); rect(g, bx + 22, by - 150, 278, 150, '#9a7d63'); g.strokeStyle = 'rgba(0,0,0,.35)'; g.lineWidth = 2; for (let y = by - 150; y < by; y += 25) { g.beginPath(); g.moveTo(bx + 22, y); g.lineTo(bx + 300, y); g.stroke(); }
  g.strokeStyle = '#5b3a2a'; g.lineWidth = 4; for (let i = 0; i < 6; i++) { g.beginPath(); g.moveTo(bx + 4 + i * 4, by - 330); g.lineTo(bx + 4 + i * 4, by - 380); g.stroke(); g.beginPath(); g.moveTo(bx + 622 - i * 4, by - 330); g.lineTo(bx + 622 - i * 4, by - 372); g.stroke(); }
  rect(g, TN.shaftB - 46, sy - 20, 92, TN.y - sy + TN.h / 2 + 30, '#0b0907'); g.strokeStyle = '#8b8174'; g.lineWidth = 6; g.beginPath(); g.moveTo(TN.shaftB - 24, sy - 12); g.lineTo(TN.shaftB - 24, TN.y + 80); g.moveTo(TN.shaftB + 24, sy - 12); g.lineTo(TN.shaftB + 24, TN.y + 80); g.stroke(); for (let y = sy; y < TN.y + 70; y += 28) { g.beginPath(); g.moveTo(TN.shaftB - 24, y); g.lineTo(TN.shaftB + 24, y); g.stroke(); }
  g.fillStyle = '#6a4d33'; for (let y = sy + 10; y < TN.y + 60; y += 90) g.fillRect(TN.shaftB - 46, y, 92, 6);
  // el túnel
  const ty = TN.y - TN.h / 2;
  g.fillStyle = lg(g, 0, ty, 0, ty + TN.h, [[0, '#090806'], [1, '#17120d']]); g.fillRect(TN.shaftA - 46, ty, TN.shaftB - TN.shaftA + 92, TN.h);
  g.strokeStyle = '#0a0705'; g.lineWidth = 8; g.strokeRect(TN.shaftA - 46, ty, TN.shaftB - TN.shaftA + 92, TN.h);
  // soportes de madera cada 120 px
  for (let x = TN.shaftA; x < TN.shaftB; x += 120) { rect(g, x, ty, 12, TN.h, '#5a4228'); rect(g, x - 4, ty, 20, 14, '#6e5232'); rect(g, x + 2, ty, 3, TN.h, 'rgba(255,255,255,.08)'); }
  // tubería de ventilación PVC en el techo con juntas
  rect(g, TN.shaftA, ty + 16, TN.shaftB - TN.shaftA, 26, lg(g, 0, ty + 16, 0, ty + 42, [[0, '#e8e8e2'], [.5, '#b9b9b2'], [1, '#85857f']])); g.strokeStyle = OL; g.lineWidth = 2; g.strokeRect(TN.shaftA, ty + 16, TN.shaftB - TN.shaftA, 26);
  for (let x = TN.shaftA + 60; x < TN.shaftB; x += 160) { rect(g, x, ty + 12, 10, 34, '#a8a8a0'); g.strokeStyle = OL; g.lineWidth = 2; g.strokeRect(x, ty + 12, 10, 34); }
  // cables eléctricos
  g.strokeStyle = '#d0a040'; g.lineWidth = 3; g.beginPath(); g.moveTo(TN.shaftA, ty + 56); for (let x = TN.shaftA; x < TN.shaftB; x += 120) g.quadraticCurveTo(x + 60, ty + 70, x + 120, ty + 56); g.stroke();
  // rieles y durmientes
  const fy = TN.y + TN.h / 2 - 20;
  for (let x = TN.shaftA - 30; x < TN.shaftB + 40; x += 40) rect(g, x, fy + 4, 22, 10, '#4a3320');
  rect(g, TN.shaftA - 46, fy, TN.shaftB - TN.shaftA + 92, 6, '#7a8088'); rect(g, TN.shaftA - 46, fy + 6, TN.shaftB - TN.shaftA + 92, 2, '#2a2d33');
  rect(g, TN.shaftA - 46, fy + 14, TN.shaftB - TN.shaftA + 92, 6, '#241a12');
  // charcos y gravilla
  for (let i = 0; i < 40; i++) { const x = TN.shaftA + r() * (TN.shaftB - TN.shaftA); g.fillStyle = 'rgba(70,90,110,.5)'; g.beginPath(); g.ellipse(x, fy + 18, 20 + r() * 30, 3, 0, 0, 7); g.fill(); }
  s5 = c;
}
function drawBike(ctx, x, y, wheel, dir = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(dir, 1);
  // carrito de tierra y herramientas (remolque en rieles)
  rect(ctx, -250, -58, 150, 46, '#3b4048'); ctx.strokeStyle = OL; ctx.lineWidth = 3; ctx.strokeRect(-250, -58, 150, 46);
  ctx.fillStyle = '#4a3322'; ctx.beginPath(); ctx.moveTo(-246, -58); ctx.quadraticCurveTo(-190, -92, -104, -58); ctx.fill();
  ctx.strokeStyle = '#8a7f6e'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-200, -62); ctx.lineTo(-180, -108); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-190, -108); ctx.lineTo(-166, -104); ctx.stroke();
  ctx.strokeStyle = '#555'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(-100, -34); ctx.lineTo(-46, -34); ctx.stroke();
  [-216, -134].forEach(wx => { ctx.fillStyle = '#17181a'; ctx.beginPath(); ctx.arc(wx, -6, 12, 0, 7); ctx.fill(); ctx.strokeStyle = '#9aa0a8'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(wx, -6, 12, wheel, wheel + 1.2); ctx.stroke(); });
  // motocicleta adaptada
  const rw = 34; [[-46, 0], [78, 0]].forEach(([wx]) => { ctx.fillStyle = '#0e0e10'; ctx.beginPath(); ctx.arc(wx, -rw, rw, 0, 7); ctx.fill(); ctx.strokeStyle = '#8f949c'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(wx, -rw, rw - 6, 0, 7); ctx.stroke(); ctx.lineWidth = 3; for (let i = 0; i < 6; i++) { const a = wheel + i * Math.PI / 3; ctx.beginPath(); ctx.moveTo(wx, -rw); ctx.lineTo(wx + Math.cos(a) * (rw - 6), -rw + Math.sin(a) * (rw - 6)); ctx.stroke(); } });
  ctx.fillStyle = '#b22a24'; ctx.strokeStyle = OL; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-46, -rw); ctx.lineTo(-10, -100); ctx.lineTo(70, -108); ctx.lineTo(96, -78); ctx.lineTo(78, -rw); ctx.lineTo(20, -52); ctx.closePath(); ctx.fill(); ctx.stroke();
  rrect(ctx, -30, -112, 70, 20, 8, '#1b1b1e', OL, 3); rrect(ctx, 6, -78, 52, 36, 8, '#5a5e66', OL, 3);
  ctx.strokeStyle = '#2b2d31'; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(78, -rw); ctx.lineTo(84, -118); ctx.lineTo(70, -132); ctx.stroke();
  rrect(ctx, 80, -112, 26, 20, 8, '#e8e2c8', OL, 3);
  ctx.restore();
}
const S5 = {
  draw(ctx, lt, f) {
    if (!s5) buildS5();
    const t = lt;
    // trayectoria de la moto: sobre rieles, de izquierda a derecha
    const bt = seg(t, 1.6, 7.0), bikeX = lerp(TN.shaftA + 400, TN.shaftB - 340, bt * bt * (3 - 2 * bt) * .0 + bt);
    const camY = lerp(660, 980, ease(seg(t, 0, 1.7)));
    let cx, z = 1;
    if (t < 1.7) cx = TN.shaftA + 20 + 90 * ease(t / 1.7);
    else if (t < 7.0) cx = lerp(TN.shaftA + 110, bikeX - 100, ease(seg(t, 1.7, 2.6))) * 0 + (t < 2.6 ? lerp(TN.shaftA + 110, bikeX - 100, ease(seg(t, 1.7, 2.6))) : bikeX - 100);
    else cx = (TN.shaftB - 340 - 100) + 340 * ease(seg(t, 7.0, 10));
    z = lerp(1, .72, ease(seg(t, 7.4, 10)));
    ctx.fillStyle = '#04050c'; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.translate(W / 2, 900); ctx.scale(z, z); ctx.translate(-cx, -camY);
    const sx0 = cx - W / z / 2 - 100, sw = W / z + 200;
    ctx.drawImage(s5, Math.max(0, sx0), 0, Math.min(TN.w - Math.max(0, sx0), sw), 2400, Math.max(0, sx0), 0, Math.min(TN.w - Math.max(0, sx0), sw), 2400);
    // luces de la galería
    const ty = TN.y - TN.h / 2;
    for (let x = TN.shaftA + 60; x < TN.shaftB; x += 240) { if (x < cx - 800 / z || x > cx + 800 / z) continue; const fl = .85 + .15 * Math.sin(f * .3 + x); ctx.fillStyle = '#ffe9b0'; ctx.beginPath(); ctx.arc(x, ty + 62, 8, 0, 7); ctx.fill(); glow(ctx, x, ty + 70, 230, '255,200,120', .55 * fl); }
    // ventilador en la boca del túnel (inicio) y flujo de aire
    const fanX = TN.shaftA + 70, fy2 = ty + 29; ctx.save(); ctx.translate(fanX, fy2); ctx.fillStyle = '#1a1a1c'; ctx.beginPath(); ctx.arc(0, 0, 20, 0, 7); ctx.fill(); ctx.strokeStyle = '#8a8d94'; ctx.lineWidth = 4; for (let i = 0; i < 4; i++) { const a = f * .6 + i * Math.PI / 2; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * 17, Math.sin(a) * 17); ctx.stroke(); } ctx.restore();
    // polvo en suspensión
    const rr = rng(8); ctx.save(); ctx.globalCompositeOperation = 'lighter'; for (let i = 0; i < 160; i++) { const bx = TN.shaftA + rr() * (TN.shaftB - TN.shaftA), by = ty + 20 + rr() * (TN.h - 40); const x = bx + Math.sin(f / 40 + i) * 14 - f * .8 * (.3 + rr()); const xx = ((x - TN.shaftA) % (TN.shaftB - TN.shaftA) + (TN.shaftB - TN.shaftA)) % (TN.shaftB - TN.shaftA) + TN.shaftA; if (Math.abs(xx - cx) > 700 / z) continue; ctx.fillStyle = 'rgba(230,210,170,.35)'; ctx.fillRect(xx, by + Math.sin(f / 22 + i) * 5, 2, 2); } ctx.restore();
    // motocicleta
    const wheel = (bikeX / 34) % (Math.PI * 2);
    if (t > 1.0) { const bx = t < 1.6 ? TN.shaftA + 400 : bikeX; const bobb = Math.sin(f * 1.3) * 1.2; drawBike(ctx, bx, TN.y + TN.h / 2 - 18 + bobb, wheel); const hx = bx + 100; cone(ctx, hx, TN.y + 20, 0, 520, 60, '255,240,200', .55); glow(ctx, hx, TN.y + 22, 90, '255,240,200', .7); }
    // brillo del conducto durante el recorrido
    ctx.restore();
    // ranura de profundidad durante el descenso
    if (t < 2.0) { ctx.save(); ctx.globalAlpha = .35 * (1 - t / 2.0); rect(ctx, 0, 0, W, H, '#000'); ctx.restore(); }
    // minimapa gráfico sin texto: penal ----- casa en construcción
    const mp = ease(seg(t, .6, 1.2)) * (1 - ease(seg(t, 9.4, 10))); if (mp > 0) {
      ctx.save(); ctx.globalAlpha = mp; const mx0 = 140, mx1 = W - 140, my = 210; rrect(ctx, mx0 - 70, my - 54, mx1 - mx0 + 140, 108, 24, 'rgba(6,8,14,.55)');
      ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 4; ctx.setLineDash([14, 12]); ctx.lineDashOffset = -f * .6; ctx.beginPath(); ctx.moveTo(mx0, my); ctx.lineTo(mx1, my); ctx.stroke(); ctx.setLineDash([]);
      rect(ctx, mx0 - 26, my - 20, 52, 40, '#7d7e8c'); ctx.strokeStyle = OL; ctx.strokeRect(mx0 - 26, my - 20, 52, 40); rect(ctx, mx0 - 26, my - 30, 52, 10, '#3d3e48');
      ctx.strokeStyle = '#d7d2c4'; ctx.lineWidth = 4; ctx.strokeRect(mx1 - 24, my - 22, 48, 44); ctx.beginPath(); ctx.moveTo(mx1 - 24, my - 22); ctx.lineTo(mx1, my - 38); ctx.lineTo(mx1 + 24, my - 22); ctx.stroke();
      const prog = clamp((bikeX - (TN.shaftA)) / (TN.shaftB - TN.shaftA)); const mxx = lerp(mx0, mx1, prog); glow(ctx, mxx, my, 50, '255,70,50', .9); ctx.fillStyle = '#ff4a38'; ctx.beginPath(); ctx.arc(mxx, my, 11, 0, 7); ctx.fill();
      ctx.restore();
    }
    post(ctx, f, { vig: .66 });
  }
};
// ===== ESCENA 6: la salida en la construcción (Santa Juanita) =====
let s6 = null; const GY6 = 1010;
function buildS6() {
  const c = mk(2300, 2500), g = c.getContext('2d'); const r = rng(61);
  sky(g, 2200, 1050, [[0, '#04061a'], [.55, '#0f1430'], [.85, '#231d3e'], [1, '#3b2a45']]); stars(g, 2200, 700, 200, 12, .8);
  // horizonte: colinas, árboles y el penal iluminado a lo lejos
  g.fillStyle = '#12112a'; g.beginPath(); g.moveTo(0, GY6 - 40); for (let x = 0; x <= 2200; x += 40) g.lineTo(x, GY6 - 110 - 30 * Math.sin(x / 300) - 14 * Math.sin(x / 80)); g.lineTo(2200, GY6); g.lineTo(0, GY6); g.fill();
  // penal lejano (derecha)
  rect(g, 1620, GY6 - 120, 380, 60, '#2d2e3a'); litWindows(g, 1636, GY6 - 108, 18, 1, 20, 0, 8, 12, 5, .8); rect(g, 1600, GY6 - 90, 420, 40, '#34353f'); razor(g, 1600, 2020, GY6 - 96);
  [1660, 1980].forEach(x => { rect(g, x - 6, GY6 - 170, 12, 120, '#25262f'); rect(g, x - 22, GY6 - 188, 44, 24, '#ffcf7d'); });
  for (let x = 40; x < 1500; x += 90 + r() * 120) tree(g, x, GY6 - 20, .5 + r() * .35, '#0a1810', '#12301c');
  // suelo terroso en corte
  g.fillStyle = lg(g, 0, GY6, 0, 2500, [[0, '#46341f'], [.3, '#332416'], [1, '#120c08']]); g.fillRect(0, GY6, 2300, 1500);
  g.fillStyle = '#2b3a22'; g.fillRect(0, GY6 - 6, 2300, 12);
  speckle(g, 0, GY6, 2300, 1500, 4, 8000, ['#6a5238', '#1c130d', '#7d6648'], 3, 12, .35);
  for (let i = 0; i < 90; i++) { const x = r() * 2200, y = GY6 + 30 + r() * 800; g.fillStyle = 'rgba(110,95,75,.55)'; g.beginPath(); g.ellipse(x, y, 5 + r() * 14, 3 + r() * 8, r() * 3, 0, 7); g.fill(); }
  // pozo/túnel visible en corte (a la izquierda del pozo)
  g.fillStyle = '#080605'; g.fillRect(704, GY6, 140, 540); g.fillRect(150, GY6 + 440, 690, 130); g.strokeStyle = '#0a0705'; g.lineWidth = 7; g.strokeRect(704, GY6, 140, 540);
  g.strokeStyle = '#5a4228'; g.lineWidth = 8; for (let x = 170; x < 700; x += 110) { g.beginPath(); g.moveTo(x, GY6 + 440); g.lineTo(x, GY6 + 570); g.stroke(); }
  rect(g, 150, GY6 + 450, 690, 22, '#d4d4cc'); rect(g, 150, GY6 + 546, 690, 5, '#7a8088');
  g.strokeStyle = '#6a4d33'; g.lineWidth = 6; for (let y = GY6 + 20; y < GY6 + 500; y += 70) { g.beginPath(); g.moveTo(704, y); g.lineTo(844, y); g.stroke(); }
  // construcción inconclusa (escala humana: planta baja de ~2.5 m)
  const col = '#79776f', slab = '#8c8a82', FH = 840;
  [[470], [990], [1500]].forEach(([x]) => { rect(g, x, GY6 - FH - 130, 54, FH + 130, lg(g, x, 0, x + 54, 0, [[0, col], [1, '#55534d']])); g.strokeStyle = OL; g.lineWidth = 3; g.strokeRect(x, GY6 - FH - 130, 54, FH + 130); });
  rect(g, 400, GY6 - 26, 1230, 26, slab); g.strokeStyle = OL; g.lineWidth = 3; g.strokeRect(400, GY6 - 26, 1230, 26);
  rect(g, 400, GY6 - FH - 26, 1230, 26, slab); g.strokeRect(400, GY6 - FH - 26, 1230, 26);
  const blk = (x, y, w, h) => { rect(g, x, y, w, h, '#9a7d63'); g.strokeStyle = 'rgba(30,20,14,.55)'; g.lineWidth = 2; for (let yy = y; yy < y + h; yy += 40) { g.beginPath(); g.moveTo(x, yy); g.lineTo(x + w, yy); g.stroke(); for (let xx = x + ((yy - y) / 40 % 2) * 45; xx < x + w; xx += 90) { g.beginPath(); g.moveTo(xx, yy); g.lineTo(xx, yy + 40); g.stroke(); } } g.strokeStyle = OL; g.lineWidth = 3; g.strokeRect(x, y, w, h); };
  blk(524, GY6 - 26 - 330, 466, 330); blk(1044, GY6 - 26 - 620, 456, 620); blk(524, GY6 - FH - 26 - 170, 300, 170);
  g.strokeStyle = '#7a3f26'; g.lineWidth = 5; [[470, 150], [524, 110], [990, 150], [1044, 120], [1500, 150], [1554, 100]].forEach(([x, hh]) => { g.beginPath(); g.moveTo(x + 12, GY6 - FH - 130); g.lineTo(x + 12, GY6 - FH - 130 - hh); g.stroke(); });
  g.fillStyle = 'rgba(40,70,120,.5)'; g.beginPath(); g.moveTo(1050, GY6 - FH - 26); g.quadraticCurveTo(1110, GY6 - FH + 220, 1060, GY6 - FH + 330); g.lineTo(1150, GY6 - FH + 330); g.lineTo(1150, GY6 - FH - 26); g.fill();
  // andamio
  g.strokeStyle = '#6f6f6f'; g.lineWidth = 8; for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(1690 + i * 90, GY6); g.lineTo(1690 + i * 90, GY6 - 700); g.stroke(); } for (let j = 0; j < 6; j++) { g.beginPath(); g.moveTo(1690, GY6 - 40 - j * 130); g.lineTo(1870, GY6 - 40 - j * 130); g.stroke(); }
  // montones de arena y grava (escala grande)
  g.fillStyle = '#6a5a45'; g.beginPath(); g.moveTo(1880, GY6); g.quadraticCurveTo(2010, GY6 - 260, 2180, GY6); g.fill(); g.strokeStyle = OL; g.lineWidth = 3; g.stroke();
  g.fillStyle = '#8a8a8a'; g.beginPath(); g.moveTo(180, GY6); g.quadraticCurveTo(260, GY6 - 150, 380, GY6); g.fill();
  // carretilla
  g.save(); g.translate(300, GY6); g.scale(2.4, 2.4); g.strokeStyle = OL; g.lineWidth = 2; g.fillStyle = '#b57a2a'; g.beginPath(); g.moveTo(-60, -56); g.lineTo(60, -56); g.lineTo(32, -12); g.lineTo(-34, -12); g.closePath(); g.fill(); g.stroke(); g.fillStyle = '#111'; g.beginPath(); g.arc(70, -20, 18, 0, 7); g.fill(); g.restore();
  s6 = c;
}
const S6 = {
  draw(ctx, lt, f) {
    if (!s6) buildS6();
    const t = 40 + lt;
    const cxw = lerp(700, 860, ease(seg(t, 40, 46))) + 380 * ease(seg(t, 45.5, 48)), z = lerp(.86, 1.0, ease(seg(t, 40, 45)));
    const cyw = lerp(840, 905, ease(seg(t, 40, 43)));
    ctx.fillStyle = '#04050c'; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.translate(W / 2, 760); ctx.scale(z, z); ctx.translate(-cxw, -cyw);
    ctx.drawImage(s6, 0, 0);
    // luz cálida que sube del pozo y la escalera
    const wob = .8 + .2 * Math.sin(f * .45);
    glow(ctx, 774, GY6 + 220, 320, '255,170,90', .5 * wob); glow(ctx, 774, GY6 - 10, 200, '255,180,100', .35 * wob);
    rect(ctx, 750, GY6 + 6, 6, 520, '#8b8174'); rect(ctx, 792, GY6 + 6, 6, 520, '#8b8174'); for (let y = GY6 + 20; y < GY6 + 520; y += 40) rect(ctx, 750, y, 48, 5, '#8b8174');
    // Chapo sube por la escalera, sale y camina
    const cd = walker('chapo_d', t); const climbK = seg(t, 41.4, 44.3);
    const below = lerp(380, 0, climbK), cph = climbK * 7;
    let pose, x = 774, gy = GY6 + below, dir = 1;
    if (t < 44.3) { const sw = Math.sin(cph * Math.PI); pose = { lean: -4, head: -6, la: [lerp(176, 118, Math.max(0, sw)), lerp(4, 50, Math.max(0, sw))], ra: [lerp(176, 118, Math.max(0, -sw)), lerp(4, 50, Math.max(0, -sw))], ll: [lerp(25, 70, Math.max(0, sw)), lerp(40, 100, Math.max(0, sw))], rl: [lerp(25, 70, Math.max(0, -sw)), lerp(40, 100, Math.max(0, -sw))] }; }
    else if (t < 44.6) { const k = seg(t, 44.3, 44.6); pose = lerpPose({ lean: -4, head: -6, la: [168, 8], ra: [150, 10], ll: [25, 40], rl: [25, 40] }, IDLE, k); }
    else { x = cd.x; dir = 1; pose = cd.pose || IDLE; if (!cd.moving && t < 44.7) pose = IDLE; }
    if (t > 44.3 && t < 44.7) { dir = 1; }
    // mirada alrededor al salir
    let opt = {}; if (t > 44.0 && t < 44.8) { opt.look = 3; }
    if (t >= 41.0) drawPerson(ctx, 'chapo', x, gy, dir, pose, opt);
    // borde del pozo
    rect(ctx, 686, GY6 - 8, 36, 10, '#8c8a82'); rect(ctx, 826, GY6 - 8, 36, 10, '#8c8a82');
    // ambiente nocturno
    ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = 'rgba(40,48,90,.3)'; ctx.fillRect(-200, -400, 2800, 2800); ctx.restore();
    // reflectores del penal a lo lejos barriendo el cielo
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; [[1660, 0], [1980, 2]].forEach(([x, ph]) => { const a = -Math.PI / 2 + Math.sin(lt * .8 + ph) * .7; cone(ctx, x, GY6 - 160, a, 520, 70, '220,230,255', .1); }); ctx.restore();
    // vigilia: luciérnagas / grillos visuales: partículas de polvo
    const rr = rng(2); ctx.save(); ctx.globalCompositeOperation = 'lighter'; for (let i = 0; i < 30; i++) { const bx = rr() * 2000, by = GY6 - 40 - rr() * 500; ctx.fillStyle = `rgba(255,240,200,${.25 + .25 * Math.sin(f / 10 + i)})`; ctx.fillRect(bx + Math.sin(f / 50 + i) * 20, by + Math.cos(f / 60 + i) * 14, 3, 3); } ctx.restore();
    ctx.restore();
    post(ctx, f, { vig: .68 });
  }
};
// ===== ESCENA 7: la búsqueda (operativos en carretera) =====
function drawTruck(ctx, x, y, s, dir, col, wheel, f, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s * dir, s);
  const wr = 44;
  // cuerpo
  ctx.strokeStyle = OL; ctx.lineWidth = 5; ctx.fillStyle = lg(ctx, 0, -190, 0, -40, [[0, col[0]], [1, col[1]]]);
  ctx.beginPath(); ctx.moveTo(-230, -60); ctx.lineTo(-230, -128); ctx.lineTo(-30, -128); ctx.lineTo(-20, -190); ctx.lineTo(70, -190); ctx.lineTo(128, -140); ctx.lineTo(210, -128); ctx.lineTo(218, -78); ctx.lineTo(206, -60); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#10151e'; ctx.beginPath(); ctx.moveTo(-8, -180); ctx.lineTo(64, -180); ctx.lineTo(112, -140); ctx.lineTo(-10, -140); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.beginPath(); ctx.moveTo(0, -178); ctx.lineTo(30, -178); ctx.lineTo(10, -142); ctx.lineTo(-8, -142); ctx.fill();
  rect(ctx, -230, -96, 440, 6, 'rgba(255,255,255,.55)'); rect(ctx, -228, -110, 60, 10, 'rgba(255,255,255,.25)');
  // barra de luces
  const ph = Math.floor(f / 5) % 2; rect(ctx, 10, -204, 52, 14, '#1b1e26'); rect(ctx, 10, -204, 26, 14, ph ? '#ff2a2a' : '#6a1414'); rect(ctx, 36, -204, 26, 14, ph ? '#1b2a66' : '#2f6bff');
  // faros
  ctx.fillStyle = '#fff4d0'; ctx.beginPath(); ctx.ellipse(212, -100, 8, 14, 0, 0, 7); ctx.fill(); ctx.fillStyle = '#c02020'; ctx.fillRect(-232, -118, 8, 22);
  [[-140], [130]].forEach(([wx]) => { ctx.fillStyle = '#0d0d0f'; ctx.beginPath(); ctx.arc(wx, -wr, wr, 0, 7); ctx.fill(); ctx.strokeStyle = '#7e8590'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(wx, -wr, wr - 12, 0, 7); ctx.stroke(); ctx.lineWidth = 3; for (let i = 0; i < 5; i++) { const a = wheel + i * 1.2566; ctx.beginPath(); ctx.moveTo(wx, -wr); ctx.lineTo(wx + Math.cos(a) * (wr - 12), -wr + Math.sin(a) * (wr - 12)); ctx.stroke(); } });
  ctx.restore();
  // luces policiales y faros (en coordenadas de escena)
  const lx = x + dir * 36 * s, ly = y - 204 * s; const cr = ph ? '255,40,40' : '60,110,255';
  glow(ctx, lx, ly, 260 * s, cr, .8); glow(ctx, x + dir * 212 * s, y - 100 * s, 90 * s, '255,244,208', .6);
  if (o.beam !== false) cone(ctx, x + dir * 214 * s, y - 100 * s, dir > 0 ? .03 : Math.PI - .03, 760 * s, 120 * s, '255,244,208', .38);
}
let s7 = null; const GY7 = 1210;
function buildS7() {
  const c = mk(3600, 1300), g = c.getContext('2d'); const r = rng(71);
  sky(g, 3600, 900, [[0, '#04061a'], [.5, '#10152e'], [1, '#272346']]); stars(g, 3600, 700, 300, 22, .85);
  g.fillStyle = '#4a4560'; g.beginPath(); g.arc(520, 230, 46, 0, 7); g.fill(); g.fillStyle = '#04061a'; g.beginPath(); g.arc(544, 218, 42, 0, 7); g.fill();
  g.fillStyle = '#171631'; g.beginPath(); g.moveTo(0, 900); for (let x = 0; x <= 3600; x += 40) g.lineTo(x, 760 - 110 * Math.sin(x / 520) - 50 * Math.sin(x / 150)); g.lineTo(3600, 900); g.fill();
  g.fillStyle = '#10112a'; g.beginPath(); g.moveTo(0, 940); for (let x = 0; x <= 3600; x += 40) g.lineTo(x, 900 - 60 * Math.sin(x / 300 + 1) - 30 * Math.sin(x / 90)); g.lineTo(3600, 940); g.fill();
  for (let x = 30; x < 3600; x += 50 + r() * 140) tree(g, x, 960, .45 + r() * .4, '#08150d', '#102a18');
  // pueblo lejano con luces
  for (let x = 800; x < 3200; x += 40 + r() * 60) { const hh = 30 + r() * 50; rect(g, x, 940 - hh, 30 + r() * 30, hh, '#1b1c2a'); if (r() < .6) { g.fillStyle = '#ffd78a'; g.fillRect(x + 6, 940 - hh + 8, 6, 8); } }
  // carretera
  g.fillStyle = '#17181f'; g.fillRect(0, 960, 3600, 340); g.fillStyle = lg(g, 0, 960, 0, 1300, [[0, '#1a1b22'], [1, '#0e0f14']]); g.fillRect(0, 1060, 3600, 240);
  g.fillStyle = '#23242c'; g.fillRect(0, 1060, 3600, 6); speckle(g, 0, 1060, 3600, 240, 7, 2500, ['#2a2b34', '#101117'], 2, 6, .3);
  g.fillStyle = '#d9c46a'; for (let x = 0; x < 3600; x += 160) g.fillRect(x, 1190, 90, 8);
  g.fillStyle = '#0c0d10'; g.fillRect(0, 960, 3600, 100);
  // postes y reflejos
  for (let x = 160; x < 3600; x += 400) { rect(g, x, 780, 8, 200, '#14141a'); rect(g, x - 26, 776, 60, 8, '#14141a'); g.fillStyle = '#ffd9a0'; g.beginPath(); g.ellipse(x - 22, 790, 14, 5, 0, 0, 7); g.fill(); }
  c.lamps = []; for (let x = 160; x < 3600; x += 400) c.lamps.push(x - 22);
  // retén: barreras y conos
  c.barrierX = 2680; s7 = c;
}
const S7 = {
  draw(ctx, lt, f) {
    if (!s7) buildS7(); const t = 48 + lt;
    const camX = lerp(150, 1950, ease(lt / 7)), z = lerp(1.0, 1.06, lt / 7);
    ctx.fillStyle = '#04050c'; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.translate(W / 2, 960); ctx.scale(z, z); ctx.translate(-W / 2 - camX, -980);
    ctx.drawImage(s7, 0, 0);
    s7.lamps.forEach(x => { glow(ctx, x, 790, 300, '255,217,160', .5); cone(ctx, x, 794, Math.PI / 2, 340, 200, '255,217,160', .18); });
    const sp = u => 1 - Math.pow(1 - clamp(u / 6.4), 2.2), SC = 1.55;
    const lead = lerp(900, 1900, sp(lt)), wheelSp = (lead * 1.0) / (44 * SC);
    drawTruck(ctx, lead - 900, GY7 + 28, SC, 1, ['#59606c', '#2c3038'], wheelSp, f + 2, { beam: false });
    drawTruck(ctx, lead, GY7 + 22, SC, 1, ['#2f3b55', '#171e30'], wheelSp, f);
    // retén: conos, barrera, sedán civil detenido y agentes (escala humana)
    const bx = 2480;
    for (let i = 0; i < 3; i++) { const x = bx - 90 - i * 90, k = 2.0; ctx.fillStyle = '#e8641c'; ctx.beginPath(); ctx.moveTo(x - 16 * k, GY7 + 30); ctx.lineTo(x - 6 * k, GY7 - 70); ctx.lineTo(x + 6 * k, GY7 - 70); ctx.lineTo(x + 16 * k, GY7 + 30); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillRect(x - 12 * k, GY7 - 20, 24 * k, 14); glow(ctx, x, GY7 - 70, 50, '255,120,40', .35); }
    rect(ctx, bx, GY7 - 190, 22, 230, '#2c2d34'); rect(ctx, bx - 220, GY7 - 150, 440, 34, '#e8e8e8'); ctx.fillStyle = '#d83a2a'; for (let i = 0; i < 8; i++) ctx.fillRect(bx - 220 + i * 55, GY7 - 150, 27, 34); glow(ctx, bx + 11, GY7 - 200, 60, '255,60,40', .5 + .5 * Math.sin(f * .4));
    ctx.save(); ctx.translate(bx + 400, GY7 + 34); ctx.scale(1.5, 1.5); ctx.fillStyle = lg(ctx, 0, -130, 0, -30, [[0, '#cfd0d6'], [1, '#6a6c76']]); ctx.strokeStyle = OL; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-190, -36); ctx.lineTo(-190, -86); ctx.lineTo(-110, -96); ctx.lineTo(-60, -150); ctx.lineTo(60, -150); ctx.lineTo(120, -96); ctx.lineTo(190, -84); ctx.lineTo(190, -36); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#10151e'; ctx.beginPath(); ctx.moveTo(-52, -142); ctx.lineTo(52, -142); ctx.lineTo(98, -98); ctx.lineTo(-100, -98); ctx.closePath(); ctx.fill(); [[-110], [110]].forEach(([wx]) => { ctx.fillStyle = '#0d0d0f'; ctx.beginPath(); ctx.arc(wx, -34, 34, 0, 7); ctx.fill(); ctx.strokeStyle = '#7e8590'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(wx, -34, 20, 0, 7); ctx.stroke(); }); ctx.restore();
    glow(ctx, bx + 400 - 285, GY7 - 80, 120, '255,244,208', .5); cone(ctx, bx + 400 - 285, GY7 - 80, Math.PI, 600, 120, '255,244,208', .28);
    const SP = .5;
    const ag1 = drawPerson(ctx, 'agent', bx + 120, GY7 + 46, -1, { lean: 4, head: 2, la: [100 + 14 * Math.sin(f * .12), 30], ra: [-6, 24], ll: [4, 8], rl: [-6, 8] }, { scale: SP });
    cone(ctx, ag1.handN.x, ag1.handN.y, Math.PI * .97, 560, 80, '255,250,225', .55); glow(ctx, ag1.handN.x, ag1.handN.y, 50, '255,250,225', .7);
    const ag2 = drawPerson(ctx, 'agent2', bx + 230, GY7 + 56, 1, { lean: 5, head: 4, la: [60 + 8 * Math.sin(f * .08), 50], ra: [-4, 20], ll: [3, 6], rl: [-3, 8] }, { scale: SP });
    cone(ctx, ag2.handN.x, ag2.handN.y, .25, 460, 70, '255,250,225', .45);
    drawPerson(ctx, 'agent', bx - 420, GY7 + 60, 1, { lean: 3, head: 0, la: [4, 90 + 20 * Math.sin(f * .15)], ra: [-3, 18], ll: [3, 6], rl: [-3, 8] }, { scale: SP });
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; const ph = Math.floor(f / 5) % 2; ctx.fillStyle = ph ? 'rgba(200,20,20,.08)' : 'rgba(30,70,200,.09)'; ctx.fillRect(-200, 0, 4200, 1500); ctx.restore();
    ctx.restore();
    ctx.save(); ctx.fillStyle = '#06070a'; for (let i = 0; i < 12; i++) { const x = ((i * 210 - camX * 1.9) % 2400 + 2400) % 2400 - 300; ctx.beginPath(); ctx.moveTo(x, H); ctx.quadraticCurveTo(x + 40, 1560 - (i % 3) * 30, x + 80, H); ctx.fill(); } ctx.restore();
    post(ctx, f, { vig: .64 });
  }
};
// ===== ESCENA 8: captura en Los Mochis =====
let s8 = null; const GY8 = 1120;
function buildS8() {
  const c = mk(2200, 1400), g = c.getContext('2d'); const r = rng(81);
  sky(g, 2200, 1150, [[0, '#0a1230'], [.4, '#2a3560'], [.7, '#8a6a80'], [.88, '#f0a060'], [1, '#ffd08a']]); stars(g, 2200, 420, 90, 5, .7);
  g.fillStyle = 'rgba(255,200,130,.25)'; g.beginPath(); g.ellipse(1500, GY8 - 30, 600, 140, 0, 0, 7); g.fill();
  // casas bajas y muros
  const house = (x, w, h, col) => { rect(g, x, GY8 - h, w, h, lg(g, 0, GY8 - h, 0, GY8, [[0, col], [1, '#2a2530']])); g.strokeStyle = OL; g.lineWidth = 4; g.strokeRect(x, GY8 - h, w, h); rect(g, x - 6, GY8 - h - 12, w + 12, 12, '#3b3340'); for (let i = 0; i < Math.floor(w / 130); i++) { rect(g, x + 26 + i * 130, GY8 - h + 40, 60, 70, '#15161e'); g.strokeStyle = '#2a2b36'; g.lineWidth = 3; g.strokeRect(x + 26 + i * 130, GY8 - h + 40, 60, 70); } };
  house(-20, 360, 300, '#7a6a76'); house(420, 420, 240, '#6c7a86'); house(1250, 380, 330, '#8a7468'); house(1700, 560, 260, '#6a6e8a');
  rect(g, 0, GY8 - 90, 2200, 90, '#3d3a46'); g.strokeStyle = OL; g.lineWidth = 4; g.strokeRect(-2, GY8 - 90, 2204, 90); for (let x = 0; x < 2200; x += 160) rect(g, x, GY8 - 90, 4, 90, 'rgba(0,0,0,.3)');
  [200, 980, 1620].forEach(x => palm(g, x, GY8 - 90, 1, '#142214'));
  for (let x = 60; x < 2200; x += 380) { rect(g, x, GY8 - 520, 10, 440, '#1a1a20'); rect(g, x - 40, GY8 - 500, 90, 8, '#1a1a20'); } g.strokeStyle = '#15151c'; g.lineWidth = 2; for (let x = 60; x < 1800; x += 380) { g.beginPath(); g.moveTo(x, GY8 - 496); g.quadraticCurveTo(x + 190, GY8 - 440, x + 380, GY8 - 496); g.stroke(); }
  // calle
  g.fillStyle = lg(g, 0, GY8, 0, 1400, [[0, '#2a2a33'], [1, '#101116']]); g.fillRect(0, GY8, 2200, 280); speckle(g, 0, GY8, 2200, 280, 3, 1800, ['#3a3a44', '#14151a'], 2, 7, .3); g.fillStyle = '#c8b25a'; for (let x = 0; x < 2200; x += 180) g.fillRect(x, GY8 + 150, 100, 8);
  s8 = c;
}
function drawMarineTruck(ctx, x, y, f, dir = 1, k = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(dir * k, k);
  ctx.strokeStyle = OL; ctx.lineWidth = 5; ctx.fillStyle = lg(ctx, 0, -230, 0, -60, [[0, '#4a5a48'], [1, '#2a3528']]);
  ctx.beginPath(); ctx.moveTo(-250, -50); ctx.lineTo(-250, -170); ctx.lineTo(-20, -170); ctx.lineTo(-10, -240); ctx.lineTo(90, -240); ctx.lineTo(150, -184); ctx.lineTo(240, -170); ctx.lineTo(250, -50); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#0f151d'; ctx.beginPath(); ctx.moveTo(4, -228); ctx.lineTo(84, -228); ctx.lineTo(132, -184); ctx.lineTo(0, -184); ctx.fill();
  rect(ctx, -240, -160, 220, 12, 'rgba(0,0,0,.35)'); ctx.strokeStyle = '#1b2219'; ctx.lineWidth = 4; for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.moveTo(-230 + i * 60, -168); ctx.lineTo(-230 + i * 60, -172 - 34); ctx.stroke(); } ctx.strokeStyle = OL; ctx.beginPath(); ctx.moveTo(-250, -170); ctx.lineTo(-20, -170); ctx.stroke();
  [[-150], [150]].forEach(([wx]) => { ctx.fillStyle = '#0d0d0f'; ctx.beginPath(); ctx.arc(wx, -50, 52, 0, 7); ctx.fill(); ctx.strokeStyle = '#7e8590'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(wx, -50, 32, 0, 7); ctx.stroke(); });
  ctx.fillStyle = '#fff4d0'; ctx.beginPath(); ctx.ellipse(246, -122, 8, 14, 0, 0, 7); ctx.fill(); ctx.restore();
  glow(ctx, x + dir * 246 * k, y - 122 * k, 120, '255,244,208', .35); const ph = Math.floor(f / 6) % 2; glow(ctx, x + dir * 40 * k, y - 244 * k, 110, ph ? '255,40,40' : '60,110,255', .6);
}
const S8 = {
  draw(ctx, lt, f) {
    if (!s8) buildS8(); const t = 55 + lt;
    const camX = lerp(250, 560, ease(lt / 5)), z = lerp(1.0, 1.06, ease(lt / 5));
    ctx.fillStyle = '#05070f'; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.translate(W / 2, 900); ctx.scale(z, z); ctx.translate(-(W / 2) - camX, -900 + 20 - lerp(0, 60, ease(seg(lt, 2.6, 5)))); ctx.translate(0, 120);
    ctx.drawImage(s8, 0, 0);
    // vehículo de la Marina al fondo y personajes
    drawMarineTruck(ctx, 1240, GY8 + 40, f, -1, 1.6);
    drawMarineTruck(ctx, 1900, GY8 + 52, f + 3, -1, 1.6);
    const wm1 = walker('m1_a', t, .72), wm2 = walker('m2_a', t, .72), wc = walker('chapoB_a', t, .72);
    // fusiles en posición baja (sin apuntar)
    const rifle = (h, dirn) => { ctx.save(); ctx.translate(h.x, h.y); ctx.rotate(dirn > 0 ? .5 : -.5); rect(ctx, -30, -6, 120, 10, '#14161a'); rect(ctx, 30, 4, 20, 22, '#14161a'); ctx.restore(); };
    const SC8 = { scale: .72 };
    const mA = drawPerson(ctx, 'marine', wm1.x, GY8 + 36, 1, wm1.pose || IDLE, SC8);
    const cc = drawPerson(ctx, 'chapoB', wc.x, GY8 + 40, 1, wc.pose ? Object.assign({}, wc.pose, { la: [lerp(8, 18, 1), 26], ra: [14, 28], lean: 5 }) : { lean: 3, head: 4, la: [10, 24], ra: [12, 26], ll: [2, 4], rl: [-4, 6] }, SC8);
    const mB = drawPerson(ctx, 'marine', wm2.x, GY8 + 44, 1, wm2.pose || IDLE, SC8);
    rifle(mA.handN, 1); rifle(mB.handN, 1);
    // marinos de guardia en el cerco
    drawPerson(ctx, 'marine', 1020, GY8 + 30, -1, { lean: 4, head: 0, la: [24, 70], ra: [30, 60], ll: [3, 6], rl: [-3, 8] }, SC8);
    drawPerson(ctx, 'marine', 1500, GY8 + 52, -1, { lean: 4, head: 0, la: [24, 70], ra: [30, 60], ll: [3, 6], rl: [-3, 8] }, SC8);
    // amanecer: tinte cálido y rayos
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; glow(ctx, 1650, GY8 - 60, 700, '255,160,90', .22); ctx.restore();
    ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = lg(ctx, 0, 0, 0, 1500, [[0, 'rgba(70,80,140,.55)'], [1, 'rgba(120,100,120,.1)']]); ctx.fillRect(-300, -300, 3000, 2200); ctx.restore();
    ctx.restore();
    post(ctx, f, { vig: .6 });
  }
};
