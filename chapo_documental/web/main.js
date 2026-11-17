const cv = document.getElementById('cv'), MAIN = cv.getContext('2d');
let cv2 = null;
const SCENES = [INTRO, S1, S2, S3, S4, S5, S6, S7, PV, S8, CLOSE];
const XF = .22; // mitad del fundido entre escenas
function drawScene(ctx, i, t, f) { const sc = TL.scenes[i], o = SCENES[i]; const lt = Math.max(0, (t - sc.start) / (sc.end - sc.start)) * (sc.o1 - sc.o0); o.draw(ctx, lt, f); }
const subCache = {};
function fitLine(ctx, txt, fs, maxW) { ctx.font = `900 ${fs}px Inter, "DejaVu Sans", sans-serif`; const w = ctx.measureText(txt).width; return w > maxW ? fs * maxW / w : fs; }
// Título de la introducción (blanco y amarillo, animado línea por línea)
function drawTitle(ctx, t) {
  const L = [{ t: 'ASÍ FUE COMO EL', fs: 74, c: '#FFFFFF', at: .45, y: 640 }, { t: 'CHAPO GUZMÁN', fs: 170, c: '#FFD400', at: 1.0, y: 800 }, { t: 'ESCAPÓ DE UNA PRISIÓN', fs: 76, c: '#FFFFFF', at: 1.7, y: 960 }, { t: 'DE MÁXIMA SEGURIDAD', fs: 84, c: '#FFD400', at: 2.25, y: 1060 }];
  const out = 1 - ease(seg(t, 3.65, 4.1)); if (out <= 0) return;
  ctx.save(); ctx.globalAlpha = out * Math.min(1, t / .35); ctx.fillStyle = lg(ctx, 0, 460, 0, 1220, [[0, 'rgba(3,4,10,0)'], [.25, 'rgba(3,4,10,.62)'], [.75, 'rgba(3,4,10,.62)'], [1, 'rgba(3,4,10,0)']]); ctx.fillRect(0, 460, W, 760); ctx.restore();
  L.forEach(l => {
    const k = easeOut(seg(t, l.at, l.at + .5)); if (k <= 0) return; const fs = fitLine(ctx, l.t, l.fs, 940);
    ctx.save(); ctx.globalAlpha = k * out; ctx.translate(W / 2, l.y + (1 - k) * 36); const sc = 1 + (1 - k) * .1; ctx.scale(sc, sc); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = `900 ${fs}px Inter, "DejaVu Sans", sans-serif`;
    ctx.lineJoin = 'round'; ctx.lineWidth = fs * .16; ctx.strokeStyle = 'rgba(0,0,0,.92)'; ctx.strokeText(l.t, 0, 0); ctx.shadowColor = 'rgba(0,0,0,.7)'; ctx.shadowBlur = 24; ctx.fillStyle = l.c; ctx.fillText(l.t, 0, 0); ctx.restore();
  });
}
function renderFrame(f) {
  const t = f / TL.fps; const ctx = MAIN;
  let i = TL.scenes.findIndex(s => t >= s.start && t < s.end); if (i < 0) i = TL.scenes.length - 1;
  drawScene(ctx, i, t, f);
  const sc = TL.scenes[i];
  if (i < TL.scenes.length - 1 && t > sc.end - XF) {
    if (!cv2) cv2 = mk(W, H); const c2 = cv2.getContext('2d'); c2.clearRect(0, 0, W, H);
    drawScene(c2, i + 1, t, f); ctx.save(); ctx.globalAlpha = ease((t - (sc.end - XF)) / (2 * XF)); ctx.drawImage(cv2, 0, 0); ctx.restore();
  }
  if (t < 4.2) drawTitle(ctx, t);
  const s = TL.subs.find(s => t >= s.a && t <= s.b);
  if (s) {
    const a = Math.min(1, (t - s.a) / .25, (s.b - t) / .25);
    const fs = s.big ? 82 : 62;
    if (!subCache[s.a]) subCache[s.a] = layoutSub(ctx, s.text, s.big ? 900 : 900, fs);
    const lines = subCache[s.a]; const lh = Math.round(fs * 1.29), h = lines.length * lh + 44;
    drawSubs(ctx, lines, a, s.big ? 900 - h / 2 : 1655 - h, fs);
  }
  if (t > 59.45) { ctx.fillStyle = `rgba(0,0,0,${clamp((t - 59.45) / .55)})`; ctx.fillRect(0, 0, W, H); }
}
