const cv = document.getElementById('cv'), MAIN = cv.getContext('2d');
let cv2 = null;
const SCENES = [S1, S2, S3, S4, S5, S6, S7, S8];
const XF = .22; // mitad del fundido entre escenas
function drawScene(ctx, i, t, f) { const sc = TL.scenes[i], o = SCENES[i]; if (!o) { rect(ctx, 0, 0, W, H, '#101018'); return; } o.draw(ctx, t - sc.start, f); }
let subCache = {};
function renderFrame(f) {
  const t = f / TL.fps; const ctx = MAIN;
  let i = TL.scenes.findIndex(s => t >= s.start && t < s.end); if (i < 0) i = TL.scenes.length - 1;
  drawScene(ctx, i, t, f);
  const sc = TL.scenes[i];
  if (i < TL.scenes.length - 1 && t > sc.end - XF) {
    if (!cv2) cv2 = mk(W, H); const c2 = cv2.getContext('2d'); c2.clearRect(0, 0, W, H);
    drawScene(c2, i + 1, t, f); ctx.save(); ctx.globalAlpha = ease((t - (sc.end - XF)) / (2 * XF)); ctx.drawImage(cv2, 0, 0); ctx.restore();
  }
  if (i > 0 && t < sc.start + XF) { /* la escena previa se funde sobre ésta: ya cubierto arriba */ }
  // subtítulos
  const s = TL.subs.find(s => t >= s.a && t <= s.b);
  if (s) {
    const a = Math.min(1, (t - s.a) / .25, (s.b - t) / .2);
    if (!subCache[s.a]) subCache[s.a] = layoutSub(ctx, s.text, 900);
    const lines = subCache[s.a]; const h = lines.length * 80 + 44; drawSubs(ctx, lines, a, 1655 - h);
  }
  // cierre: fundido a negro
  if (t > 59.4) { ctx.fillStyle = `rgba(0,0,0,${clamp((t - 59.4) / .6)})`; ctx.fillRect(0, 0, W, H); }
}
