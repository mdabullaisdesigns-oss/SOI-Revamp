/* Spirit of Islam – shared behaviour for the website and the app (everything prefixed soi).
   1. menu bar (dropdowns, Archives menu with covers, phone menu)
   2. reading memory kept in this browser: where you stopped (article, place on the page, audio time),
      which articles are finished, saved articles and quotes
   3. Save / Share buttons on every article
   4. home page: Continue reading, Quote of the day
   No account and nothing leaves the device; sign-in and sync come later. */
(function () {
  if (window.soi) return;
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
    return '<span class="soi-cover"><span class="soi-cover-fb" aria-hidden="true"><b>Spirit of Islam</b><i>' + esc(i.period || '') + '</i></span>' +
      '<img loading="lazy" decoding="async" alt="" src="' + cover(i.slug, big) + '" onerror="this.remove()"></span>';
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
    var url = shareBase() + path, data = { title: title, text: title + ' – Spirit of Islam', url: url };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { toast('Link copied'); }, function () { window.prompt('Copy this link', url); });
  }

  /* ---------- quote as a picture ---------- */
  function wrap(ctx, t, max) { var w = t.split(' '), lines = [], l = ''; w.forEach(function (x) { var n = l ? l + ' ' + x : x; if (ctx.measureText(n).width > max && l) { lines.push(l); l = x; } else l = n; }); if (l) lines.push(l); return lines; }
  function quoteImage(q) {
    var W = 1080, H = 1350, c = document.createElement('canvas'); c.width = W; c.height = H; var x = c.getContext('2d');
    function draw() {
      x.fillStyle = '#204E60'; x.fillRect(0, 0, W, H); x.strokeStyle = '#D4CC73'; x.lineWidth = 3; x.strokeRect(48, 48, W - 96, H - 96);
      x.fillStyle = '#D4CC73'; x.save(); x.translate(W / 2, 170); x.rotate(Math.PI / 4); x.fillRect(-13, -13, 26, 26); x.restore();
      var size = q.t.length > 330 ? 40 : q.t.length > 220 ? 46 : q.t.length > 120 ? 54 : 64, lines;
      x.fillStyle = '#EEEEE5'; x.textAlign = 'center'; x.textBaseline = 'middle';
      do { x.font = 'italic ' + size + 'px "Cita Pro Ita","Cita Pro",Georgia,serif'; lines = wrap(x, '“' + q.t + '”', W - 240); size -= 2; } while (lines.length * (size * 1.42) > H - 560 && size > 26);
      var lh = (size + 2) * 1.42, y = H / 2 - ((lines.length - 1) * lh) / 2 - 30; lines.forEach(function (l, i) { x.fillText(l, W / 2, y + i * lh); });
      x.fillStyle = '#D4CC73'; x.fillRect(W / 2 - 60, H - 330, 120, 3);
      x.fillStyle = '#EEEEE5'; x.font = '600 30px "Plus Jakarta Sans",Arial,sans-serif'; x.fillText('Spirit of Islam', W / 2, H - 270);
      x.globalAlpha = .8; x.font = '26px "Plus Jakarta Sans",Arial,sans-serif'; x.fillText('Issue ' + q.n + ' · ' + q.p, W / 2, H - 225); x.globalAlpha = 1;
      c.toBlob(function (b) {
        var f = new File([b], 'spirit-of-islam-quote.png', { type: 'image/png' });
        if (navigator.canShare && navigator.canShare({ files: [f] })) { navigator.share({ files: [f], text: shareBase() + '/issues/' + q.s + '/#soi-' + q.a }).catch(function () {}); return; }
        var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = f.name; document.body.appendChild(a); a.click(); a.remove(); toast('Image saved');
      }, 'image/png');
    }
    (document.fonts && document.fonts.load ? document.fonts.load('italic 40px "Cita Pro Ita"').then(draw, draw) : draw());
  }
  function quoteOfDay() {
    return fetch('/assets/quotes.json').then(function (r) { return r.json(); }).then(function (d) {
      var p = d.quotes.filter(function (q) { return q.t.length < 220; }), day = Math.floor(Date.now() / 864e5 - new Date().getTimezoneOffset() / 1440);
      return p[(day * 7919) % p.length];
    });
  }

  /* ---------- 1. menu ---------- */
  function menu() {
    var bar = $('.soi-menu'); if (!bar) return;
    var toggle = $('.soi-menu-toggle', bar), list = $('.soi-menu-list', bar);
    function closeAll(except) { $$('.soi-has-sub.is-open', bar).forEach(function (li) { if (li !== except) { li.classList.remove('is-open'); var b = $('.soi-menu-top', li); if (b) b.setAttribute('aria-expanded', 'false'); } }); }
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
      yearsEl.addEventListener('mouseover', function (e) { var b = e.target.closest('button'); if (b) pick(+b.dataset.y); });
      yearsEl.addEventListener('focusin', function (e) { var b = e.target.closest('button'); if (b) pick(+b.dataset.y); });
      yearsEl.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; if (window.matchMedia('(max-width: 980px)').matches) location.href = '/archive/#y' + b.dataset.y; else pick(+b.dataset.y); });
      pick(years[0]);
    }).catch(function () { delete box.dataset.ready; });
  }

  /* ---------- 2. reading memory on an issue page ---------- */
  var meta = $('meta[name="soi-issue"]'), SLUG = meta ? meta.content : '', LABEL = meta ? meta.getAttribute('data-label') : '';
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
    var prevHook = A.soi ? null : null;
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
  function start() { menu(); issuePage(); continueCard(); qotd(); savedWeb(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
