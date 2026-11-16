/* Spirit of Islam – shared behaviour for the website and the app (everything prefixed soi).
   1. menu bar (dropdowns, Archives menu with covers, phone menu)
   2. reading memory kept in this browser: where you stopped (article, place on the page, audio time),
      which articles are finished, saved articles and quotes
   3. Save / Share buttons on every article
   4. home page: Continue reading, Quote of the day
   No account and nothing leaves the device; sign-in and sync come later. */
(function () {
  if (window.soi) { window.soi.restart(); return; }
  var LS = {
    get: function (k, d) { try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return [].slice.call((r || document).querySelectorAll(s)); }
  function mmss(t) { t = Math.max(0, Math.round(t || 0)); return Math.floor(t / 60) + ':' + ('0' + (t % 60)).slice(-2); }
  function toast(msg) {
    var t = $('#soi-toast');
    if (!t) { t = document.createElement('div'); t.id = 'soi-toast'; t.setAttribute('role', 'status'); t.setAttribute('aria-live', 'polite'); document.body.appendChild(t); }
    t.textContent = msg; t.classList.add('is-on'); clearTimeout(toast.t); toast.t = setTimeout(function () { t.classList.remove('is-on'); }, 2400);
  }
  function cover(slug, big) { return '/assets/covers/' + slug + (big ? '@2x' : '') + '.webp'; }
  function coverHTML(i, big) {
    return '<span class="soi-cover"><span class="soi-cover-fb" aria-hidden="true"><img class="soi-cover-dove" src="/assets/brand/Peogen-logo.png" alt=""><b>Spirit of Islam</b><i>' + esc(i.period || '') + '</i></span>' +
      '<img loading="lazy" decoding="async" alt="" src="' + cover(i.slug, big) + '" onload="this.classList.add(\'is-in\')" onerror="this.remove()"></span>';
  }
  var issuesP = null;
  function issues() {
    if (!issuesP) issuesP = fetch('/issues.json').then(function (r) { return r.json(); }).then(function (j) { return j.issues; });
    return issuesP;
  }

  /* ---------- saved things ---------- */
  var store = {
    progress: function () { return LS.get('soiProgress', null); },
    read: function () { return LS.get('soiRead', {}); },
    markRead: function (slug, id) { var r = store.read(); r[slug] = r[slug] || {}; if (!r[slug][id]) { r[slug][id] = Date.now(); LS.set('soiRead', r); store.day(); } },
    day: function () { var d = LS.get('soiDays', {}), k = new Date().toISOString().slice(0, 10); if (!d[k]) { d[k] = 1; LS.set('soiDays', d); } },
    articles: function () { return LS.get('soiSavedArticles', []); },
    hasArticle: function (slug, id) { return store.articles().some(function (a) { return a.slug === slug && a.id === id; }); },
    toggleArticle: function (a) {
      var l = store.articles(), n = l.filter(function (x) { return !(x.slug === a.slug && x.id === a.id); });
      if (n.length === l.length) { a.at = Date.now(); n.unshift(a); }
      LS.set('soiSavedArticles', n); return n.length > l.length;
    },
    quotes: function () { return LS.get('soiSavedQuotes', []); },
    hasQuote: function (q) { return store.quotes().some(function (x) { return x.t === q.t; }); },
    toggleQuote: function (q) {
      var l = store.quotes(), n = l.filter(function (x) { return x.t !== q.t; });
      if (n.length === l.length) n.unshift({ t: q.t, s: q.s, a: q.a, at: q.at, n: q.n, p: q.p });
      LS.set('soiSavedQuotes', n); return n.length > l.length;
    }
  };

  /* ---------- share ---------- */
  function shareBase() { return window.soiShareBase || location.origin; }
  function share(title, path) {
    if (window.soiNativeShare) { window.soiNativeShare(title, shareBase() + path); return; }
    var url = shareBase() + path, data = { title: title, text: title + ' – Spirit of Islam', url: url };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { toast('Link copied'); }, function () { window.prompt('Copy this link', url); });
  }

  /* ---------- quote as a picture ---------- */
  function wrap(ctx, t, max) { var w = t.split(' '), lines = [], l = ''; w.forEach(function (x) { var n = l ? l + ' ' + x : x; if (ctx.measureText(n).width > max && l) { lines.push(l); l = x; } else l = n; }); if (l) lines.push(l); return lines; }
  var QPH = [];
  function quoteImage(q) {
    var W = 1080, H = 1350, c = document.createElement('canvas'); c.width = W; c.height = H; var x = c.getContext('2d'), bg = new Image();
    var hh = 0, ht = q.s + q.a + q.t.length; for (var hi = 0; hi < ht.length; hi++) hh = (hh * 31 + ht.charCodeAt(hi)) | 0;
    var ph = QPH.length ? QPH[Math.abs(hh) % QPH.length] : '';
    function draw() {
      x.fillStyle = '#204E60'; x.fillRect(0, 0, W, H);
      if (bg.naturalWidth) { var r = Math.max(W / bg.naturalWidth, H / bg.naturalHeight), bw = bg.naturalWidth * r, bh = bg.naturalHeight * r; x.drawImage(bg, (W - bw) / 2, (H - bh) / 2, bw, bh);
        var g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(23,58,72,.55)'); g.addColorStop(.5, 'rgba(23,58,72,.72)'); g.addColorStop(1, 'rgba(23,58,72,.92)'); x.fillStyle = g; x.fillRect(0, 0, W, H); } x.strokeStyle = '#D4CC73'; x.lineWidth = 3; x.strokeRect(48, 48, W - 96, H - 96);
      x.fillStyle = '#D4CC73'; x.save(); x.translate(W / 2, 170); x.rotate(Math.PI / 4); x.fillRect(-13, -13, 26, 26); x.restore();
      var size = q.t.length > 330 ? 40 : q.t.length > 220 ? 46 : q.t.length > 120 ? 54 : 64, lines;
      x.fillStyle = '#EEEEE5'; x.textAlign = 'center'; x.textBaseline = 'middle';
      do { x.font = 'italic ' + size + 'px "Cita Pro Ita","Cita Pro",Georgia,serif'; lines = wrap(x, '“' + q.t + '”', W - 240); size -= 2; } while (lines.length * (size * 1.42) > H - 560 && size > 26);
      var lh = (size + 2) * 1.42, y = H / 2 - ((lines.length - 1) * lh) / 2 - 30; lines.forEach(function (l, i) { x.fillText(l, W / 2, y + i * lh); });
      x.fillStyle = '#D4CC73'; x.fillRect(W / 2 - 60, H - 330, 120, 3);
      if (logo.naturalWidth) { var lw2 = 230; x.drawImage(logo, W / 2 - lw2 / 2, H - 290, lw2, lw2 * 51.17 / 79.08); }
      x.fillStyle = '#FFFFFF'; x.globalAlpha = .9; x.font = '600 28px "Plus Jakarta Sans",Arial,sans-serif'; x.fillText('spiritofislam.co.in', W / 2, H - 105); x.globalAlpha = 1;
      c.toBlob(function (b) {
        var f = new File([b], 'spirit-of-islam-quote.png', { type: 'image/png' });
        if (navigator.canShare && navigator.canShare({ files: [f] })) { navigator.share({ files: [f], text: 'spiritofislam.co.in' }).catch(function (e) { if (!e || e.name !== 'AbortError') { var a2 = document.createElement('a'); a2.href = URL.createObjectURL(b); a2.download = f.name; document.body.appendChild(a2); a2.click(); a2.remove(); } }); return; }
        var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = f.name; document.body.appendChild(a); a.click(); a.remove(); toast('Image saved');
      }, 'image/png');
    }
    var fl = document.fonts && document.fonts.load ? document.fonts.load('italic 40px "Cita Pro Ita"') : Promise.resolve();
    var logo = new Image(); fl.then(function () { logo.onload = logo.onerror = function () { if (!ph) return draw(); bg.onload = draw; bg.onerror = draw; bg.src = ph; }; logo.src = '/assets/brand/soi-mark-white.svg'; }, draw);
  }
  function quoteOfDay() {
    return fetch('/assets/quotes.json').then(function (r) { return r.json(); }).then(function (d) {
      QPH = d.photos || []; var p = d.quotes.filter(function (q) { return q.t.length < 220; }), day = Math.floor(Date.now() / 864e5 - new Date().getTimezoneOffset() / 1440);
      return p[(day * 7919) % p.length];
    });
  }

  /* ---------- 1. menu ---------- */
  function menu() {
    var bar = $('.soi-menu'); if (!bar) return;
    var toggle = $('.soi-menu-toggle', bar), list = $('.soi-menu-list', bar);
    function closeAll(except) { $$('.soi-has-sub.is-open', bar).forEach(function (li) { if (li !== except) { li.classList.remove('is-open'); var b = $('.soi-menu-top', li); if (b) b.setAttribute('aria-expanded', 'false'); } }); }
    /* get the issue list ready early, so Archives opens at once on phones */
    var warm = function () { var li = $('.soi-has-mega', bar); if (li) mega(li); };
    if ('requestIdleCallback' in window) requestIdleCallback(warm, { timeout: 2500 }); else setTimeout(warm, 1200);
    if (toggle) toggle.addEventListener('pointerdown', warm, { once: true });
    if (toggle) toggle.addEventListener('click', function () {
      var on = !bar.classList.contains('is-open'); bar.classList.toggle('is-open', on); toggle.setAttribute('aria-expanded', on ? 'true' : 'false'); if (!on) closeAll();
    });
    $$('.soi-has-sub', bar).forEach(function (li) {
      var top = $('.soi-menu-top', li);
      top.addEventListener('click', function (e) {
        var wide = window.matchMedia('(min-width: 981px) and (hover: hover)').matches;
        if (wide && top.tagName === 'A') return;                 /* desktop: hover opens it, a click follows the link */
        e.preventDefault(); var on = !li.classList.contains('is-open'); closeAll(li); li.classList.toggle('is-open', on); top.setAttribute('aria-expanded', on ? 'true' : 'false');
        if (on && li.classList.contains('soi-has-mega')) mega(li);
      });
      li.addEventListener('mouseenter', function () { if (li.classList.contains('soi-has-mega')) mega(li); });
      li.addEventListener('focusin', function () { if (li.classList.contains('soi-has-mega')) mega(li); });
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeAll(); if (document.activeElement && bar.contains(document.activeElement)) document.activeElement.blur(); } });
    document.addEventListener('click', function (e) { if (!bar.contains(e.target)) closeAll(); });
  }
  function mega(li) {
    var box = $('.soi-mega', li); if (!box || box.dataset.ready) return; box.dataset.ready = '1';
    issues().then(function (all) {
      var years = []; all.forEach(function (i) { if (years.indexOf(i.year) < 0) years.push(i.year); }); years.sort(function (a, b) { return b - a; });
      var yearsEl = $('.soi-mega-years', box), coversEl = $('.soi-mega-covers', box), label = $('.soi-mega-label', box);
      function pick(y) {
        $$('button', yearsEl).forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.y) === String(y) ? 'true' : 'false'); });
        label.textContent = 'Issues of ' + y;
        coversEl.innerHTML = all.filter(function (i) { return i.year === y; }).reverse().map(function (i) {
          return '<a href="/issues/' + i.slug + '/">' + coverHTML(i) + '<b>' + esc(i.period.replace(/ \d{4}$/, '')) + '</b><small>' + (i.number ? 'Issue ' + i.number : '') + '</small></a>';
        }).join('');
      }
      yearsEl.innerHTML = years.map(function (y) { return '<button type="button" data-y="' + y + '" aria-pressed="false">' + y + '</button>'; }).join('');
      var pinned = null;                                   /* a clicked year stays until the pointer leaves the menu */
      yearsEl.addEventListener('mouseover', function (e) { var b = e.target.closest('button'); if (b && !pinned) pick(+b.dataset.y); });
      yearsEl.addEventListener('focusin', function (e) { var b = e.target.closest('button'); if (b && !pinned) pick(+b.dataset.y); });
      box.addEventListener('mouseleave', function () { pinned = null; });
      yearsEl.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; if (window.matchMedia('(max-width: 980px)').matches) { location.href = '/archive/#y' + b.dataset.y; return; } pinned = +b.dataset.y; pick(pinned); });
      pick(years[0]);
    }).catch(function () { delete box.dataset.ready; });
  }

  /* ---------- 2. reading memory on an issue page ---------- */
  var SLUG = '', LABEL = '';
  function readMeta() { var meta = $('meta[name="soi-issue"]'); SLUG = meta ? meta.content : ''; LABEL = meta ? meta.getAttribute('data-label') : ''; }
  var theAudio = null, resume = null, resumed = false;
  function itemInfo(item) {
    var t = $('.ev-tab-title', item), m = ($('.ev-meta', item) || {}).textContent || '', mm = m.match(/(\d+)\s*min/);
    return { slug: SLUG, id: item.id.replace(/^soi-/, ''), title: t ? t.textContent.trim() : '', label: LABEL, min: mm ? +mm[1] : 0, audio: !!$('.ev-player audio[src]', item) && !$('.ev-player', item).hidden };
  }
  function currentItem() {
    if (theAudio && !theAudio.paused) { var a = audioItem(); if (a) return a; }
    var open = $$('.soi-ev .ev-item.is-open'), best = null, mid = window.innerHeight * 0.4;
    open.forEach(function (it) { var r = it.getBoundingClientRect(); if (r.top < mid && r.bottom > 80) best = it; });
    return best || open[0] || null;
  }
  var lastAudioItem = null;
  function audioItem() {
    if (!theAudio) return null;
    var src = theAudio.currentSrc || theAudio.src || '', hit = null;
    $$('.soi-ev .ev-player audio[src]').forEach(function (t) { var s = t.getAttribute('src'); if (s && (src === s || src.slice(-s.length) === s || new URL(s, location.href).href === src)) hit = t.closest('.ev-item'); });
    if (hit) lastAudioItem = hit;
    return hit || lastAudioItem;
  }
  var saveT = 0;
  function remember(force) {
    if (!SLUG) return; var n = Date.now(); if (!force && n - saveT < 1500) return; saveT = n;
    var it = currentItem(); if (!it) return;
    var info = itemInfo(it), body = $('.ev-body', it) || it, r = body.getBoundingClientRect();
    var frac = Math.max(0, Math.min(1, (window.innerHeight * 0.5 - r.top) / Math.max(1, r.height)));
    var p = { slug: SLUG, id: info.id, title: info.title, label: info.label, min: info.min, frac: +frac.toFixed(3), off: Math.round(window.scrollY - (it.getBoundingClientRect().top + window.scrollY)), at: n };
    var prev = store.progress();
    if (theAudio && audioItem() === it && theAudio.currentTime > 0) { p.t = Math.floor(theAudio.currentTime); p.dur = Math.floor(theAudio.duration || 0); if (p.dur) p.frac = Math.max(p.frac, +(p.t / p.dur).toFixed(3)); }
    else if (prev && prev.slug === p.slug && prev.id === p.id && prev.t) { p.t = prev.t; p.dur = prev.dur; }
    LS.set('soiProgress', p);
    if (frac > 0.92 && r.bottom < window.innerHeight * 0.9) store.markRead(SLUG, info.id);
  }
  function hookAudio(a) {
    theAudio = a;
    a.addEventListener('timeupdate', function () { remember(false); });
    a.addEventListener('pause', function () { remember(true); });
    a.addEventListener('ended', function () { var it = audioItem(); if (it && SLUG) store.markRead(SLUG, it.id.replace(/^soi-/, '')); });
    a.addEventListener('loadedmetadata', function () {
      if (!resume || resumed || !resume.t) return; var it = audioItem();
      if (it && it.id === 'soi-' + resume.id && a.currentTime < 2 && resume.t < (a.duration || 1e9) - 5) { resumed = true; try { a.currentTime = resume.t; } catch (e) {} }
    });
  }
  (function patchAudio() {
    var A = window.Audio; if (!A) return;
    function SoiAudio(src) { var a = src === undefined ? new A() : new A(src); hookAudio(a); return a; }
    SoiAudio.prototype = A.prototype; if (A.soi) SoiAudio.soi = true; window.Audio = SoiAudio;
  })();
  function issuePage() {
    if (!SLUG) return;
    store.day();
    var p = store.progress(), q = new URLSearchParams(location.search);
    if (q.get('resume') && p && p.slug === SLUG) {
      resume = p;
      var go = function () {
        var it = document.getElementById('soi-' + p.id); if (!it) return;
        if (!it.classList.contains('is-open')) { var tab = $('.ev-tab', it); if (tab) tab.click(); }
        setTimeout(function () { window.scrollTo(0, it.getBoundingClientRect().top + window.scrollY + (p.off || 0)); if (p.t) toast('Audio will continue from ' + mmss(p.t)); }, 650);
      };
      if (document.readyState === 'complete') setTimeout(go, 300); else window.addEventListener('load', function () { setTimeout(go, 300); });
    }
    window.addEventListener('scroll', function () { remember(false); }, { passive: true });
    document.addEventListener('visibilitychange', function () { if (document.hidden) remember(true); });
    window.addEventListener('pagehide', function () { remember(true); });
    actions();
  }

  /* ---------- 3. Save / Share on every article ---------- */
  var ICON = {
    save: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>',
    share: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v13M7 8l5-5 5 5M5 14v6h14v-6"/></svg>'
  };
  function actions() {
    $$('.soi-ev .ev-item').forEach(function (it) {
      var m = $('.ev-meta', it); if (!m || $('.soi-acts', it)) return;
      var info = itemInfo(it), box = document.createElement('span'); box.className = 'soi-acts';
      var on = store.hasArticle(SLUG, info.id);
      box.innerHTML = '<button type="button" class="soi-act-save" aria-pressed="' + on + '">' + ICON.save + '<span>' + (on ? 'Saved' : 'Save') + '</span></button>' +
        '<button type="button" class="soi-act-share">' + ICON.share + '<span>Share</span></button>';
      box.addEventListener('click', function (e) {
        var b = e.target.closest('button'); if (!b) return; e.stopPropagation();
        if (b.classList.contains('soi-act-share')) { share(info.title, '/issues/' + SLUG + '/#soi-' + info.id); return; }
        var now = store.toggleArticle(itemInfo(it)); b.setAttribute('aria-pressed', now); $('span', b).textContent = now ? 'Saved' : 'Save'; toast(now ? 'Saved to this device' : 'Removed from Saved');
      });
      m.appendChild(box);
    });
  }

  /* ---------- 4. home page ---------- */
  function continueCard() {
    var box = $('#soi-continue'); if (!box) return;
    var p = store.progress();
    if (!p) return;                                              /* first visit: the card keeps its "start here" text */
    var left = p.min ? Math.max(1, Math.round(p.min * (1 - (p.frac || 0)))) : 0;
    $('.soi-cont-title', box).textContent = p.title;
    $('.soi-cont-meta', box).textContent = [p.label, left ? left + ' min left' : '', p.t ? 'paused at ' + mmss(p.t) : ''].filter(Boolean).join(' · ');
    $('.soi-cont-bar i', box).style.width = Math.round((p.frac || 0) * 100) + '%';
    var a = $('.soi-cont-go', box); a.href = '/issues/' + p.slug + '/?resume=1#soi-' + p.id; a.firstChild.textContent = 'Resume ';
    $('.soi-cont-kicker', box).textContent = 'Continue reading';
  }
  function qotd() {
    var box = $('#soi-qotd-home'); if (!box) return;
    quoteOfDay().then(function (q) {
      $('.soi-qotd-text', box).textContent = '“' + q.t + '”';
      var s = $('.soi-qotd-src', box); s.innerHTML = '<a href="/issues/' + q.s + '/#soi-' + q.a + '">' + esc(q.at) + '</a> · Issue ' + q.n;
      $('.soi-qotd-share', box).addEventListener('click', function () { quoteImage(q); });
      box.classList.add('is-ready');
    }).catch(function () {});
  }

  /* ---------- website "Saved" page ---------- */
  function savedWeb() {
    var box = $('#soi-saved-web'); if (!box) return;
    var arts = store.articles(), qs = store.quotes(), p = store.progress(), h = '';
    if (p) h += '<h2 class="soi-h2"><span>Continue reading</span></h2><a class="soi-saved-row" href="/issues/' + p.slug + '/?resume=1#soi-' + p.id + '"><b>' + esc(p.title) + '</b><small>' + esc(p.label) + (p.t ? ' · paused at ' + mmss(p.t) : '') + '</small></a>';
    h += '<h2 class="soi-h2"><span>Articles</span><small>' + arts.length + '</small></h2>' + (arts.length ? arts.map(function (a) {
      return '<a class="soi-saved-row" href="/issues/' + a.slug + '/#soi-' + a.id + '"><b>' + esc(a.title) + '</b><small>' + esc(a.label) + (a.min ? ' · ' + a.min + ' min' : '') + (a.audio ? ' · audio' : '') + '</small></a>';
    }).join('') : '<p class="soi-saved-none">Nothing saved yet. Open an article and press Save.</p>');
    h += '<h2 class="soi-h2"><span>Quotes</span><small>' + qs.length + '</small></h2>' + (qs.length ? qs.map(function (q) {
      return '<a class="soi-saved-row soi-saved-quote" href="/issues/' + q.s + '/#soi-' + q.a + '"><b>“' + esc(q.t) + '”</b><small>' + esc(q.at) + ' · Issue ' + q.n + '</small></a>';
    }).join('') : '<p class="soi-saved-none">No quotes saved yet. Press Save on any quote in the <a href="/quotes/">quotes library</a>.</p>');
    box.innerHTML = h;
  }

  window.soi = { store: store, share: share, toast: toast, esc: esc, issues: issues, coverHTML: coverHTML, cover: cover, quoteImage: quoteImage, quoteOfDay: quoteOfDay, mmss: mmss, LS: LS };
  function start() { readMeta(); resume = null; resumed = false; lastAudioItem = null; menu(); issuePage(); continueCard(); qotd(); savedWeb(); }
  function boot() { if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start(); }
  window.soi.restart = boot; window.soi.slug = function () { return SLUG; };
  boot();
})();

/* ---- owner's changes (14 Nov 2026): archive grid/list, custom drop-downs ---- */
(function () {
  function ready(f) { if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', f); else f(); }
  /* a drop-down that is not the browser's default: soiDropdown(el, [[value,label],…], onChange) */
  window.soiDropdown = function (el, opts, onChange) {
    var btn = el.querySelector('.soi-dd-btn'), list = el.querySelector('.soi-dd-list'), label = btn.querySelector('span'), val = opts[0][0], act = 0;
    list.innerHTML = '';
    opts.forEach(function (o, k) { var li = document.createElement('li'); li.setAttribute('role', 'option'); li.dataset.v = o[0]; li.textContent = o[1]; li.id = el.id + '-o' + k; li.setAttribute('aria-selected', k ? 'false' : 'true'); list.appendChild(li); });
    var items = list.children;
    function mark() { [].forEach.call(items, function (li, k) { li.classList.toggle('is-active', k === act); }); if (items[act]) { btn.setAttribute('aria-activedescendant', items[act].id); items[act].scrollIntoView({ block: 'nearest' }); } }
    function open(on) { list.hidden = !on; btn.setAttribute('aria-expanded', on ? 'true' : 'false'); if (on) mark(); }
    function choose(k) { var li = items[k]; if (!li) return; val = li.dataset.v; label.textContent = li.textContent; [].forEach.call(items, function (x) { x.setAttribute('aria-selected', x === li ? 'true' : 'false'); }); open(false); btn.focus(); onChange(val); }
    btn.addEventListener('click', function () { open(list.hidden); });
    list.addEventListener('click', function (e) { var li = e.target.closest('li'); if (li) choose([].indexOf.call(items, li)); });
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (list.hidden) open(true); act = Math.max(0, Math.min(items.length - 1, act + (e.key === 'ArrowDown' ? 1 : -1))); mark(); }
      else if ((e.key === 'Enter' || e.key === ' ') && !list.hidden) { e.preventDefault(); choose(act); }
      else if (e.key === 'Escape') open(false);
    });
    document.addEventListener('click', function (e) { if (!el.contains(e.target)) open(false); });
    return { get value() { return val; } };
  };
  ready(function () {
    var arch = document.querySelector('.soi-arch'), view = document.querySelector('.soi-view');
    if (!arch || !view) return;
    function set(v) { arch.dataset.view = v; [].forEach.call(view.querySelectorAll('button'), function (b) { b.setAttribute('aria-pressed', b.dataset.view === v ? 'true' : 'false'); }); try { localStorage.setItem('soi-arch-view', v); } catch (e) {} }
    try { var v = localStorage.getItem('soi-arch-view'); if (v === 'list') set('list'); } catch (e) {}
    view.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b) set(b.dataset.view); });
  });
})();

/* ---------- go-to-top with reading progress, on every page (issue pages bring their own copy; this one then stays out) ---------- */
(function () {
  function start() {
    if (document.getElementById('soi-gotop')) return;
    var btn = document.createElement('button');
    btn.id = 'soi-gotop'; btn.type = 'button'; btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg><span class="soi-gotop-pct" aria-hidden="true">0%</span>';
    document.body.appendChild(btn);
    var pct = btn.querySelector('.soi-gotop-pct'), ticking = false, last = -1;
    function update() {
      ticking = false;
      var doc = document.documentElement, max = Math.max(1, doc.scrollHeight - window.innerHeight);
      var y = window.pageYOffset || doc.scrollTop, p = Math.min(1, Math.max(0, y / max)), n = Math.round(p * 100);
      btn.style.setProperty('--soi-p', p.toFixed(4));
      if (n !== last) { last = n; pct.textContent = n + '%'; btn.setAttribute('aria-label', 'Back to top, ' + n + '% read'); }
      btn.classList.toggle('is-shown', y > 500);
    }
    function request() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
    window.addEventListener('scroll', request, { passive: true }); window.addEventListener('resize', request);
    btn.addEventListener('click', function () { var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }); btn.blur(); });
    btn.addEventListener('touchstart', function () { btn.classList.add('is-pressed'); }, { passive: true });
    ['touchend', 'touchcancel'].forEach(function (t) { btn.addEventListener(t, function () { setTimeout(function () { btn.classList.remove('is-pressed'); }, 250); }, { passive: true }); });
    update();
  }
  /* wait for the issue's own script (it runs later in the page) */
  if (document.readyState === 'complete') start(); else window.addEventListener('load', start);
})();

/* ---------- "Ask AI": Gemini can't take a question from a link, so it is copied and the reader is told why ---------- */
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[data-copy-prompt]'); if (!a) return;
  e.preventDefault();
  var box = a.closest('[data-prompt]'), q = box ? box.getAttribute('data-prompt') : '', href = a.href;
  function copy() {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(q).then(function () { return true; }, function () { return false; });
    try { var t = document.createElement('textarea'); t.value = q; t.style.position = 'fixed'; t.style.opacity = '0'; document.body.appendChild(t); t.select(); var ok = document.execCommand('copy'); t.remove(); return Promise.resolve(ok); } catch (x) { return Promise.resolve(false); }
  }
  copy().then(function (ok) {
    var d = document.createElement('div'); d.className = 'soi-modal'; d.setAttribute('role', 'dialog'); d.setAttribute('aria-modal', 'true'); d.setAttribute('aria-labelledby', 'soi-modal-t');
    d.innerHTML = '<div class="soi-modal-card"><p class="soi-kicker">Ask Gemini</p><h2 id="soi-modal-t">' + (ok ? 'Your question has been copied' : 'Copy your question') + '</h2>' +
      '<p>Unlike the other AI tools, Gemini does not accept a question sent from another website. ' + (ok ? 'Please paste it into Gemini (Ctrl+V, ⌘V, or long-press › Paste) and ask.' : 'Please copy the question below, paste it into Gemini and ask.') + '</p>' +
      '<blockquote>' + q.replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }) + '</blockquote>' +
      '<div class="soi-modal-btns"><button type="button" class="soi-btn" data-close>Close</button><a class="soi-btn soi-btn-solid" href="' + href + '" target="_blank" rel="noopener" data-close>Open Gemini</a></div></div>';
    document.body.appendChild(d);
    function close() { d.remove(); document.removeEventListener('keydown', esc); a.focus(); }
    function esc(ev) { if (ev.key === 'Escape') close(); }
    d.addEventListener('click', function (ev) { if (ev.target === d || ev.target.closest('[data-close]')) { if (ev.target.tagName !== 'A') ev.preventDefault(); setTimeout(close, 0); } });
    document.addEventListener('keydown', esc);
    d.querySelector('a[data-close]').focus();
  });
});

/* ---------- menu colour preview: ?menu=teal (or ?menu=gold) is remembered in this browser ---------- */
(function () {
  try {
    var m = (location.search.match(/[?&]menu=(teal|gold)\b/) || [])[1];
    if (m) localStorage.setItem('soi-menu', m); else m = localStorage.getItem('soi-menu');
    if (m === 'teal') document.documentElement.classList.add('soi-menu-teal');
  } catch (e) {}
})();

/* ---------- website tour: quick guided cards on the first visit to the home page (replay: any [data-soi-tour] link) ---------- */
(function () {
  var KEY = 'soi-tour-done';
  var STEPS = [
    { t: 'Welcome to Spirit of Islam', d: 'A one-minute tour of the website: where to find every issue, how to listen, search and save. You can skip it at any time.' },
    { sel: '.soi-has-mega > .soi-menu-top', alt: '.soi-menu-toggle', t: 'Every issue since 2013', d: 'Open Archives and point at a year to see that year’s covers. Click a cover to read the issue.' },
    { sel: '.soi-menu-list a[href="/quotes/"]', alt: '.soi-menu-toggle', t: 'Quotes', d: 'Short reflections from every issue. Listen to them, or share one as a picture.' },
    { sel: '.soi-menu-right a[href="/search/"]', t: 'Search everything', d: 'Search all articles by word, topic or Quran reference (for example 51:56). A small spelling mistake is fine.' },
    { sel: '.soi-menu-right a[href="/saved/"]', t: 'Saved', d: 'Articles, issues and quotes you save are kept here, on this device.' },
    { sel: '#soi-continue', t: 'Continue where you left off', d: 'The last article you read is waiting here, at the same place, with the audio where you paused.' },
    { sel: '.soi-hero-main', t: 'Inside each issue', d: 'Tap an article to open it. Press play to hear it read aloud while the words light up, or tap any sentence to listen from there. A short quiz waits at the end.' },
    { t: 'You are all set', d: 'You can take this tour again any time from the link at the bottom of every page. Happy reading.' }
  ];
  var ov, hole, card, i = 0;
  function vis(el) { if (!el) return false; var r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; }
  function target(s) { if (!s.sel) return null; var e = document.querySelector(s.sel); if (vis(e)) return e; e = s.alt && document.querySelector(s.alt); return vis(e) ? e : null; }
  function steps() { return STEPS.filter(function (s) { return !s.sel || target(s); }); }
  function close(done) { if (!ov) return; ov.remove(); ov = null; document.removeEventListener('keydown', key); window.removeEventListener('resize', place); window.removeEventListener('scroll', place, true); if (done) try { localStorage.setItem(KEY, '1'); } catch (e) {} }
  function key(e) { if (e.key === 'Escape') close(true); if (e.key === 'ArrowRight') go(1); if (e.key === 'ArrowLeft') go(-1); }
  function place() {
    var S = steps(), s = S[i], el = target(s), vw = window.innerWidth, vh = window.innerHeight;
    if (!el) { hole.style.cssText = 'left:50%;top:50%;width:0;height:0'; card.style.left = Math.max(12, (vw - card.offsetWidth) / 2) + 'px'; card.style.top = Math.max(12, (vh - card.offsetHeight) / 2) + 'px'; card.removeAttribute('data-arrow'); return; }
    var r = el.getBoundingClientRect(), pad = 8;
    hole.style.cssText = 'left:' + (r.left - pad) + 'px;top:' + (r.top - pad) + 'px;width:' + (r.width + pad * 2) + 'px;height:' + (r.height + pad * 2) + 'px';
    var cw = card.offsetWidth, ch = card.offsetHeight, below = r.bottom + pad + 14 + ch < vh, top = below ? r.bottom + pad + 14 : Math.max(12, r.top - pad - 14 - ch);
    if (!below && top + ch > r.top - pad) top = Math.max(12, vh - ch - 12);
    card.style.top = top + 'px'; card.style.left = Math.min(vw - cw - 12, Math.max(12, r.left + r.width / 2 - cw / 2)) + 'px'; card.setAttribute('data-arrow', below ? 'up' : 'down');
  }
  function show() {
    var S = steps(), s = S[i], el = target(s);
    card.innerHTML = '<p class="soi-tour-step">' + (i + 1) + ' of ' + S.length + '</p><h2 class="soi-tour-t">' + s.t + '</h2><p class="soi-tour-d">' + s.d + '</p>' +
      '<div class="soi-tour-dots" aria-hidden="true">' + S.map(function (_, k) { return '<span' + (k === i ? ' class="is-on"' : '') + '></span>'; }).join('') + '</div>' +
      '<div class="soi-tour-btns"><button type="button" class="soi-tour-skip" data-t="skip">' + (i === S.length - 1 ? 'Close' : 'Skip tour') + '</button>' +
      (i > 0 ? '<button type="button" class="soi-tour-back" data-t="back">Back</button>' : '') +
      '<button type="button" class="soi-tour-next" data-t="next">' + (i === 0 ? 'Start the tour' : i === S.length - 1 ? 'Finish' : 'Next') + '</button></div>';
    if (el) { var r = el.getBoundingClientRect(); if (r.top < 70 || r.bottom > window.innerHeight - 220) { el.scrollIntoView({ block: 'center' }); } }
    requestAnimationFrame(place); card.querySelector('.soi-tour-next').focus();
  }
  function go(d) { var n = steps().length; i += d; if (i >= n) return close(true); if (i < 0) i = 0; show(); }
  function start() {
    if (ov) return; i = 0;
    ov = document.createElement('div'); ov.className = 'soi-tour'; ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true'); ov.setAttribute('aria-label', 'Website tour');
    ov.innerHTML = '<div class="soi-tour-hole"></div><div class="soi-tour-card"></div>';
    document.body.appendChild(ov); hole = ov.firstChild; card = ov.lastChild;
    card.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var t = b.dataset.t; if (t === 'skip') close(true); else go(t === 'back' ? -1 : 1); });
    document.addEventListener('keydown', key); window.addEventListener('resize', place); window.addEventListener('scroll', place, true);
    show();
  }
  document.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('[data-soi-tour]'); if (!a) return; e.preventDefault(); if (!document.body.classList.contains('soi-home')) { location.href = '/?tour=1'; return; } start(); });
  window.addEventListener('load', function () {
    var want = /[?&]tour=1\b/.test(location.search), done = false;
    try { done = localStorage.getItem(KEY) === '1'; } catch (e) {}
    if (document.body.classList.contains('soi-home') && (want || (!done && !navigator.webdriver))) setTimeout(start, 700);
  });
  window.soiTour = start;
})();
