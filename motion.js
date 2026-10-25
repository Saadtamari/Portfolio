/* Shared motion layer.
   - Drives the statement word-fill from scroll so it tracks the reading line in every browser.
   - Where CSS scroll timelines are missing (older Safari, Firefox), replays the same
     reveals, digit rolls, bars, log lines, timeline line and progress bar with JS.
   - Plays one-shot entrance animations on anything marked .anim when it scrolls into view,
     with optional per-child stagger (data-stagger="selector", data-cols for grid waves).
   - On touch screens, gives the big display words a letter wave (on view and on tap)
     and lets architecture nodes open their notes on tap.
   Every hidden state is opt-in through an attribute this file sets, so if it never
   runs, the page simply shows its finished state. */
(function () {
  if (window.__stMotion) return;
  window.__stMotion = true;

  var mm = function (q) { try { return window.matchMedia(q).matches; } catch (e) { return false; } };
  var reduce = mm('(prefers-reduced-motion: reduce)');
  var sda = false;
  try { sda = !!(window.CSS && CSS.supports && CSS.supports('animation-timeline: view()')); } catch (e) {}
  var touch = mm('(hover: none)');
  var html = document.documentElement;
  html.classList.add('js-fill');
  if (!sda) html.classList.add('no-sda');
  if (touch) html.classList.add('touch');
  if (reduce) return;

  var clamp = function (v) { return v < 0 ? 0 : v > 1 ? 1 : v; };
  var vh = function () { return window.innerHeight || html.clientHeight; };

  /* ---------- in-view triggers ---------- */
  var once = sda ? [] : ['.rv', '.rs', '.bar', '.tlog', '.rrow'];
  var waves = touch ? ['.name', '.cname'] : [];
  var seen = typeof WeakSet === 'function' ? new WeakSet() : null;

  function wave(el) {
    var ls = el.querySelectorAll('.pl');
    for (var i = 0; i < ls.length; i++) ls[i].style.setProperty('--i', i);
    el.classList.remove('wave');
    void el.offsetWidth;
    el.classList.add('wave');
    clearTimeout(el.__wt);
    el.__wt = setTimeout(function () { el.classList.remove('wave'); }, 1300 + ls.length * 70);
  }
  function waveSoon(el) {
    var wait = el.classList.contains('name') ? Math.max(0, 2300 - (performance.now ? performance.now() : 0)) : 0;
    setTimeout(function () { wave(el); }, wait);
  }

  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (ents) {
    ents.forEach(function (en) {
      if (!en.isIntersecting) return;
      var el = en.target;
      if (el.hasAttribute('data-wait')) { el.removeAttribute('data-wait'); io.unobserve(el); }
      if (el.matches('.name, .cname')) waveSoon(el);
    });
  }, { rootMargin: '0px 0px -10% 0px' }) : null;

  function stagger(el) {
    var sel = el.getAttribute('data-stagger');
    if (!sel) return;
    var cols = +el.getAttribute('data-cols') || 0;
    var kids = el.querySelectorAll(sel);
    for (var i = 0; i < kids.length; i++) kids[i].style.setProperty('--i', cols ? (i % cols) + Math.floor(i / cols) : i);
  }

  function scan() {
    if (!io) return;
    var h = vh();
    document.querySelectorAll('.anim').forEach(function (el) {
      if (seen && seen.has(el)) return;
      if (seen) seen.add(el);
      stagger(el);
      if (el.getBoundingClientRect().top > h * 0.88) { el.setAttribute('data-wait', ''); io.observe(el); }
    });
    once.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        if (seen && seen.has(el)) return;
        if (seen) seen.add(el);
        if (el.getBoundingClientRect().top > h * 0.9) { el.setAttribute('data-wait', ''); io.observe(el); }
      });
    });
    waves.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        if (seen && seen.has(el)) return;
        if (seen) seen.add(el);
        io.observe(el);
      });
    });
  }

  /* ---------- scroll-linked progress ---------- */
  var ticking = false;
  function frame() {
    ticking = false;
    var h = vh();
    document.querySelectorAll('.fill').forEach(function (f) {
      var box = (f.closest && f.closest('.stmt')) || f;
      var r = box.getBoundingClientRect();
      /* the fill edge rides from 62% to 42% of the screen height while the text passes */
      f.style.setProperty('--fp', clamp((h * 0.62 - r.top) / (r.height + h * 0.2)).toFixed(4));
    });
    var hero = document.querySelector('.hero');
    if (hero) html.classList.toggle('past-hero', hero.getBoundingClientRect().bottom < 0);
    document.querySelectorAll('.shrows').forEach(function (w) {
      var r = w.getBoundingClientRect();
      w.style.setProperty('--shp', clamp((h - r.top) / (h + r.height)).toFixed(4));
    });
    if (!sda) {
      var se = document.scrollingElement || html;
      var max = se.scrollHeight - h;
      var pr = document.querySelector('.prog');
      if (pr) pr.style.setProperty('--sp', (max > 0 ? clamp(se.scrollTop / max) : 0).toFixed(4));
      document.querySelectorAll('.tline').forEach(function (t) {
        var r = t.getBoundingClientRect();
        t.style.setProperty('--tp', clamp((h * 0.62 - r.top) / r.height).toFixed(4));
      });
    }
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }

  /* ---------- taps ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target && e.target.closest ? e.target : null;
    if (!t) return;
    var big = t.closest('.name, .cname');
    if (big && touch) wave(big);
    var node = t.closest('.anode');
    document.querySelectorAll('.anode.tap').forEach(function (n) { if (n !== node) n.classList.remove('tap'); });
    if (node && touch) node.classList.toggle('tap');
    var pt = t.closest('.portrait');
    if (pt) pt.classList.toggle('tap');
  });

  function start() {
    scan();
    frame();
    document.addEventListener('scroll', onScroll, { passive: true, capture: true });
    window.addEventListener('resize', onScroll);
    if ('MutationObserver' in window) {
      var mt = 0;
      new MutationObserver(function () {
        clearTimeout(mt);
        mt = setTimeout(function () { scan(); frame(); }, 120);
      }).observe(document.body, { childList: true, subtree: true });
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
