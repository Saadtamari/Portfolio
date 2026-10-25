// Bake the rendered HTML into every page (for crawlers and no-JS readers) and write llms-full.txt.
// Needs the site running locally:  npx wrangler dev --port 8799   then:  node tools/prerender.cjs
// Requires Playwright (npm i playwright).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..'), OUT = path.join(ROOT, 'public');
const BASE = process.env.BASE || 'http://127.0.0.1:8799';
const SITE = (process.env.SITE_URL || 'https://saadaltamari.com').replace(/\/$/, '');
const pages = require('./pages.json');
const order = ['index', 'work', 'services', 'about', 'writing',
  ...Object.keys(pages).filter(n => n.startsWith('case-')).sort(),
  ...Object.keys(pages).filter(n => n.startsWith('writing-')).sort()];

function snapshot() {
  const root = document.getElementById('dc-root');
  // mark layout on the live page so the copies know where blocks start and what is hidden
  root.querySelectorAll('*').forEach(e => {
    const d = getComputedStyle(e).display;
    if (d === 'none') e.setAttribute('data-h', ''); else if (d.startsWith('inline-')) e.setAttribute('data-s', ''); else if (d !== 'inline' && d !== 'contents') e.setAttribute('data-b', '');
  });
  const c = root.cloneNode(true);
  const unmark = el => el.querySelectorAll('[data-b],[data-h],[data-s]').forEach(e => ['data-b', 'data-h', 'data-s'].forEach(a => e.removeAttribute(a)));
  unmark(root);
  // animated figures and logos are exposed as role="img" + aria-label: keep the label as text
  // (same for headings and other labelled elements whose visible text is all aria-hidden)
  c.querySelectorAll('[aria-label]').forEach(e => {
    if (e.matches('button, a, input, nav, figure') || e.querySelector('img, svg, [aria-label]')) return;
    const probe = e.cloneNode(true); probe.querySelectorAll('[aria-hidden="true"]').forEach(x => x.remove());
    if (e.getAttribute('role') === 'img' || !probe.textContent.trim()) { e.textContent = e.getAttribute('aria-label'); e.removeAttribute('role'); }
  });
  c.querySelectorAll('script, noscript, template, [aria-hidden="true"], .menu, .mcta').forEach(e => e.remove());
  c.querySelectorAll('*').forEach(e => {
    for (const a of [...e.attributes]) if (/^on/i.test(a.name) || /^data-dc/.test(a.name) || a.name === 'id' || a.name === 'ref') e.removeAttribute(a.name);
  });
  const m = c.cloneNode(true);
  m.querySelectorAll('[data-h]').forEach(e => e.remove());
  m.querySelectorAll('br').forEach(e => e.replaceWith(' '));
  m.querySelectorAll('[data-b],[data-s]').forEach(e => { e.before(' '); e.after(' '); });
  unmark(c);
  // ---------- markdown for llms-full.txt ----------
  const BLOCK = /^(ADDRESS|ARTICLE|ASIDE|BLOCKQUOTE|DD|DIV|DL|DT|FIELDSET|FIGCAPTION|FIGURE|FOOTER|FORM|H[1-6]|HEADER|HR|LI|MAIN|NAV|OL|P|PRE|SECTION|TABLE|TBODY|THEAD|TR|TD|TH|UL)$/;
  const txt = e => e.textContent.replace(/\s+/g, ' ').trim();
  const hasBlock = e => [...e.children].some(k => BLOCK.test(k.tagName) || k.hasAttribute('data-b') || hasBlock(k));
  const out = [];
  const walk = e => {
    if (e.nodeType !== 1) return;
    const t = e.tagName;
    if (t === 'NAV' || t === 'BUTTON' || t === 'SVG' || t === 'svg' || e.matches('.island, .prog')) return;
    if (/^H[1-6]$/.test(t)) { const s = txt(e); if (s) out.push('#'.repeat(+t[1] + 1) + ' ' + s); return; }
    if (t === 'TR') { const s = [...e.children].map(txt).filter(Boolean).join(' | '); if (s) out.push('- ' + s); return; }
    if (!hasBlock(e)) {
      const s = txt(e); if (!s) return;
      if (t === 'LI') out.push('- ' + s);
      else if (t === 'BLOCKQUOTE') out.push('> ' + s);
      else if (t === 'PRE') out.push('```\n' + e.textContent.trim() + '\n```');
      else if (t === 'A' && /^https?:/.test(e.getAttribute('href') || '')) out.push(`[${s}](${e.getAttribute('href')})`);
      else out.push(s);
      return;
    }
    let buf = '';
    const flush = () => { const s = buf.replace(/\s+/g, ' ').trim(); if (s) out.push(s); buf = ''; };
    for (const k of e.childNodes) {
      if (k.nodeType === 3) buf += k.textContent;
      else if (k.nodeType === 1 && !BLOCK.test(k.tagName) && !k.hasAttribute('data-b') && !hasBlock(k)) {
        if (k.tagName === 'BUTTON' || k.tagName === 'NAV') continue;
        buf += ' ' + k.textContent + ' ';
      } else { flush(); walk(k); }
    }
    flush();
  };
  walk(m);
  const md = out.filter((l, i) => l !== out[i - 1]).join('\n\n');
  return { html: c.innerHTML, md };
}

(async () => {
  const b = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  let full = `# Saad Tamari: full site text\n\nSource: ${SITE}/ · Summary: ${SITE}/llms.txt\n`;
  for (const name of order) {
    const pg = await ctx.newPage();
    await pg.goto(BASE + (name === 'index' ? '/' : '/' + name), { waitUntil: 'networkidle' });
    await pg.waitForFunction(() => document.getElementById('dc-root')?.childElementCount > 0);
    await pg.waitForTimeout(1200);
    const { html, md } = await pg.evaluate(snapshot);
    const f = path.join(OUT, name + '.html');
    let s = fs.readFileSync(f, 'utf8');
    if (!s.includes('<!--SSR-->')) throw new Error('no SSR marker in ' + f);
    s = s.replace('<!--SSR-->', '<div id="ssr">' + html.replace(/\$/g, '$$$$') + '</div>');
    fs.writeFileSync(f, s);
    full += `\n\n---\n\n# ${pages[name].title}\n\nURL: ${pages[name].url}\n\n${md}\n`;
    console.log(name.padEnd(30), (html.length / 1024).toFixed(0) + 'KB html', md.length + ' chars md');
    await pg.close();
  }
  fs.writeFileSync(path.join(OUT, 'llms-full.txt'), full);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
