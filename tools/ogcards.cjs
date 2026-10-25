// Social preview cards (1200x630): each page's own hero, captured without the nav.
// Needs the site running locally (npx wrangler dev --port 8799). Writes static/assets/og/<page>.jpg
// and copies them into public/. Run python3 tools/build.py afterwards only if og files were new.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const BASE = process.env.BASE || 'http://127.0.0.1:8799';
const pages = Object.keys(require('./pages.json'));
const outDirs = [path.join(ROOT, 'static/assets/og'), path.join(ROOT, 'public/assets/og')];
outDirs.forEach(d => fs.mkdirSync(d, { recursive: true }));

(async () => {
  const b = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
  const ctx = await b.newContext({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
  for (const name of pages) {
    const pg = await ctx.newPage();
    await pg.goto(BASE + (name === 'index' ? '/' : '/' + name), { waitUntil: 'networkidle' });
    await pg.waitForFunction(() => document.getElementById('dc-root')?.childElementCount > 0);
    await pg.evaluate(() => document.fonts.ready);
    await pg.addStyleTag({ content: '.island,.mcta{display:none!important} .anim,.rv{opacity:1!important;transform:none!important}' });
    await pg.waitForTimeout(1500);
    const file = path.join(outDirs[0], name + '.jpg');
    await pg.screenshot({ path: file, type: 'jpeg', quality: 86 });
    fs.copyFileSync(file, path.join(outDirs[1], name + '.jpg'));
    console.log('og', name);
    await pg.close();
  }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
