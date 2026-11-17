// Renderiza los 1800 fotogramas (30 fps x 60 s) con Chromium headless en paralelo -> tmp/frames/%05d.jpg
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const OUT = path.join(__dirname, 'tmp/frames'); fs.mkdirSync(OUT, { recursive: true });
const TL = JSON.parse(fs.readFileSync(path.join(__dirname, 'web/timeline.json'), 'utf8'));
const TOTAL = TL.duration * TL.fps, WORKERS = +(process.env.WORKERS || 4);
async function worker(id, b) {
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => { console.log('PAGEERR', e.message); process.exit(1); });
  await p.goto('file://' + path.join(__dirname, 'web/index.html'));
  await p.evaluate(t => { window.TL = t; }, TL);
  for (const f of ['lib.js', 'scenes_cell.js', 'scenes_out.js', 'main.js']) await p.addScriptTag({ content: fs.readFileSync(path.join(__dirname, 'web', f), 'utf8') });
  await p.evaluate(() => document.fonts.load('800 62px Inter'));
  for (let f = id; f < TOTAL; f += WORKERS) {
    const d = await p.evaluate(f => { renderFrame(f); return cv.toDataURL('image/jpeg', 0.95); }, f);
    fs.writeFileSync(path.join(OUT, String(f).padStart(5, '0') + '.jpg'), Buffer.from(d.split(',')[1], 'base64'));
    if (f % 120 === id) console.log('frame', f);
  }
  await p.close();
}
(async () => { const b = await chromium.launch({ args: ['--no-sandbox'] }); await Promise.all([...Array(WORKERS)].map((_, i) => worker(i, b))); await b.close(); console.log('OK', fs.readdirSync(OUT).length); })();
