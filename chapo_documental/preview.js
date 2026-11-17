// uso: node preview.js out_dir f1 f2 ...   (renderiza fotogramas sueltos a PNG)
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [out, ...frames] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--no-sandbox'] }); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('PAGEERR', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await p.goto('file://' + path.resolve(__dirname, 'web/index.html'));
  const TL = JSON.parse(fs.readFileSync(path.join(__dirname, 'web/timeline.json'), 'utf8'));
  await p.evaluate(t => { window.TL = t; }, TL);
  for (const f of ['lib.js', 'scenes_cell.js', 'scenes_out.js', 'main.js']) { const fp = path.join(__dirname, 'web', f); if (fs.existsSync(fp)) await p.addScriptTag({ content: fs.readFileSync(fp, 'utf8') }); }
  await p.evaluate(() => document.fonts.load('800 62px Inter'));
  for (const f of frames) { const d = await p.evaluate(f => { renderFrame(f); return cv.toDataURL('image/png'); }, +f); fs.writeFileSync(path.join(out, `f${String(f).padStart(4, '0')}.png`), Buffer.from(d.split(',')[1], 'base64')); }
  await b.close();
})();
