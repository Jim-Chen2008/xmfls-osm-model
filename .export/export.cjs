// Export the OSM campus model to GLB with the football-pitch centre as origin.
const fs = require('fs');
const path = require('path');
const { chromium } = require('C:/Users/Jim/AppData/Roaming/npm/node_modules/rea-agents/node_modules/playwright-core');

const EXE = 'C:/Users/Jim/AppData/Local/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-win64/chrome-headless-shell.exe';
const SRC = 'C:/xmfls test/ds/xmfls-osm-model/dist/' + encodeURIComponent('厦门外国语学校海沧校区-OSM模型 - 副本.html');
const PAGE = 'file:///' + SRC;
const OUT = 'C:/xmfls test/ds/xmfls-osm-model/dist/厦门外国语学校海沧校区-足球场原点.glb';

const exporterSrc = fs.readFileSync(path.join(__dirname, 'GLTFExporter.js'), 'utf8');
const inpage = fs.readFileSync(path.join(__dirname, 'inpage_export.js'), 'utf8');

(async () => {
  const browser = await chromium.launch({
    executablePath: EXE,
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--allow-file-access-from-files', '--font-render-hinting=none'],
  });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const logs = [];
  page.on('console', m => logs.push(m.type() + ': ' + m.text()));
  page.on('pageerror', e => logs.push('PAGEERROR: ' + e.message));

  await page.goto(PAGE, { waitUntil: 'load', timeout: 90000 });
  await page.waitForFunction('!!window.__MODEL', null, { timeout: 60000 });
  await page.addScriptTag({ content: exporterSrc });
  await page.waitForFunction('!!window.THREE.GLTFExporter', null, { timeout: 15000 });

  const info = await page.evaluate(inpage);
  console.log('INFO', JSON.stringify(info, null, 2));

  const len = await page.evaluate(() => window.__GLB_B64.length);
  const parts = [];
  const CH = 1 << 21;
  for (let i = 0; i < len; i += CH) {
    parts.push(await page.evaluate(([a, b]) => window.__GLB_B64.slice(a, b), [i, i + CH]));
  }
  const b64 = parts.join('');
  const buf = Buffer.from(b64, 'base64');
  fs.writeFileSync(OUT, buf);
  console.log('WROTE', OUT, buf.length, 'bytes');
  const interesting = logs.filter(l => !/GLTFExporter: Use MeshStandardMaterial|THREE\.GLTFExporter: Use/.test(l));
  console.log('LOGS', JSON.stringify(interesting.slice(0, 30), null, 2));
  await browser.close();
})().catch(e => { console.error('FAILED', e); process.exit(1); });
