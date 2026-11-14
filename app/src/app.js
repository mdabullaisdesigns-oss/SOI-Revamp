/* Spirit of Islam app – the small layer that turns the website into a phone app.
   - keeps links working inside the app (issue pages open from the app, a saved copy, or the internet)
   - saves issues on the phone for offline reading
   - connects the website's audio player to the phone's lock-screen / notification controls
   Everything is prefixed soi. No accounts, no tracking. */
(function () {
  if (window.soiApp) { window.soiApp.init(); return; }
  var CFG = { remote: '', bundled: [], fonts: false };
  var cfgReady = fetch('/assets/app-config.json').then(function (r) { return r.json(); })
    .then(function (c) { CFG = c; }).catch(function () {});
  var native = !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
  var platform = native ? window.Capacitor.getPlatform() : 'web';
  function plugin(n) { try { return native ? (window.Capacitor.Plugins[n] || window.Capacitor.registerPlugin(n)) : null; } catch (e) { return null; } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  /* ---------- links ---------- */
  function route(href) {
    var u; try { u = new URL(href, location.href); } catch (e) { return null; }
    if (u.origin !== location.origin) return null;
    var m = u.pathname.match(/^\/issues\/([\w-]+)\/?(?:index\.html)?$/);
    if (m) return (CFG.bundled.indexOf(m[1]) >= 0 ? '/issues/' + m[1] + '/index.html' : '/reader.html?issue=' + m[1]) + u.hash;
    if (/\/$/.test(u.pathname)) return u.pathname + 'index.html' + u.search + u.hash;
    return null;
  }
  function onClick(e) {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a || a.target === '_blank' || a.hasAttribute('download')) return;
    var raw = a.getAttribute('href');
    if (!raw || raw.charAt(0) === '#') return;
    var to = route(a.href);
    if (!to) return;
    e.preventDefault();
    location.href = to;
  }

  /* ---------- saved issues (kept on the phone) ---------- */
  var dbp = null;
  function db() {
    if (!dbp) dbp = new Promise(function (ok, no) {
      var q = indexedDB.open('soi-app', 1);
      q.onupgradeneeded = function () { q.result.createObjectStore('issues', { keyPath: 'slug' }); };
      q.onsuccess = function () { ok(q.result); }; q.onerror = function () { no(q.error); };
    });
    return dbp;
  }
  function tx(mode, fn) {
    return db().then(function (d) {
      return new Promise(function (ok, no) {
        var t = d.transaction('issues', mode), r = fn(t.objectStore('issues'));
        t.oncomplete = function () { ok(r && r.result); }; t.onerror = t.onabort = function () { no(t.error); };
      });
    });
  }
  var store = {
    get: function (slug) { return tx('readonly', function (s) { return s.get(slug); }); },
    put: function (rec) { return tx('readwrite', function (s) { return s.put(rec); }); },
    del: function (slug) { return tx('readwrite', function (s) { return s.delete(slug); }); },
    keys: function () { return tx('readonly', function (s) { return s.getAllKeys(); }); }
  };
  function timed(url, ms) {
    var c = new AbortController(), t = setTimeout(function () { c.abort(); }, ms || 20000);
    return fetch(url, { signal: c.signal, cache: 'no-store' }).then(function (r) { clearTimeout(t); if (!r.ok) throw new Error('HTTP ' + r.status); return r; },
      function (e) { clearTimeout(t); throw e; });
  }
  function download(slug, v) {
    return timed(CFG.remote + '/issues/' + slug + '/').then(function (r) { return r.text(); }).then(function (html) {
      if (html.indexOf('soi-ev') < 0) throw new Error('not an issue page');
      var rec = { slug: slug, html: html, v: v || '', bytes: html.length, at: Date.now() };
      return store.put(rec).then(function () { return rec; });
    });
  }
  function manifest(refresh) {
    var cached = null;
    try { cached = JSON.parse(localStorage.getItem('soiAppIssues') || 'null'); } catch (e) {}
    var local = cached ? Promise.resolve(cached) : fetch('/issues.json').then(function (r) { return r.json(); }).then(function (j) { return j.issues; });
    if (!refresh) return local;
    return timed(CFG.remote + '/issues.json', 8000).then(function (r) { return r.json(); }).then(function (j) {
      try { localStorage.setItem('soiAppIssues', JSON.stringify(j.issues)); } catch (e) {}
      return j.issues;
    }).catch(function () { return local; });
  }

  /* ---------- reader: opens an issue that is not packed inside the app ---------- */
  function prep(html) {
    if (CFG.fonts) html = html.replace(/<link[^>]+fonts\.(?:googleapis|gstatic)\.com[^>]*>/g, '');
    html = html.replace('content="width=device-width, initial-scale=1"', 'content="width=device-width, initial-scale=1, viewport-fit=cover"');
    return html.replace('</head>', '<link rel="stylesheet" href="/assets/app.css"></head>');
  }
  function show(html) { document.open(); document.write(prep(html)); document.close(); init(); }
  function say(title, text, extra) {
    var box = document.getElementById('soi-app-reader');
    if (box) box.innerHTML = '<h1>' + esc(title) + '</h1><p>' + esc(text) + '</p>' + (extra || '');
  }
  function reader() {
    var slug = new URLSearchParams(location.search).get('issue') || '';
    if (!/^[\w-]+$/.test(slug)) { location.replace('/archive/index.html'); return; }
    if (CFG.bundled.indexOf(slug) >= 0) { location.replace('/issues/' + slug + '/index.html' + location.hash); return; }
    store.get(slug).catch(function () { return null; }).then(function (rec) {
      if (rec) {
        show(rec.html);
        /* quietly pick up a corrected version for next time */
        manifest(true).then(function (list) {
          var it = list.filter(function (x) { return x.slug === slug; })[0];
          if (it && it.v && it.v !== rec.v) download(slug, it.v).catch(function () {});
        });
        return;
      }
      say('Opening the issue…', 'Fetching it once; after that it stays on your phone and opens without internet.');
      manifest(false).catch(function () { return []; }).then(function (list) {
        var it = list.filter(function (x) { return x.slug === slug; })[0];
        return download(slug, it && it.v);
      }).then(function (r) { show(r.html); }, function () {
        say('This issue is not on your phone yet', 'It needs an internet connection the first time. Once opened, it is saved and can be read offline.',
          '<p class="soi-app-actions"><a class="soi-app-btn" href="' + esc(location.pathname + location.search + location.hash) + '" onclick="location.reload();return false">Try again</a> <a class="soi-app-btn soi-app-btn-quiet" href="/saved.html">See saved issues</a></p>');
      });
    });
  }

  /* ---------- "Saved" page ---------- */
  function savedPage() {
    var root = document.getElementById('soi-app-saved'); if (!root) return;
    var listEl = root.querySelector('.soi-app-list'), stat = root.querySelector('.soi-app-stat'), allBtn = root.querySelector('.soi-app-all');
    var issues = [], have = {}, busy = false;
    function mb(n) { return (n / 1048576).toFixed(n > 10485760 ? 0 : 1) + ' MB'; }
    function draw() {
      var missing = issues.filter(function (i) { return !have[i.slug] && CFG.bundled.indexOf(i.slug) < 0; });
      var size = missing.reduce(function (a, i) { return a + (i.bytes || 0); }, 0);
      stat.textContent = (issues.length - missing.length) + ' of ' + issues.length + ' issues can be read without internet.';
      allBtn.hidden = !missing.length;
      if (!busy) allBtn.textContent = 'Save all ' + missing.length + ' remaining issues (' + mb(size) + ')';
      listEl.innerHTML = issues.slice().reverse().map(function (i) {
        var inApp = CFG.bundled.indexOf(i.slug) >= 0, st = inApp ? 'In the app' : have[i.slug] ? 'Saved' : '';
        return '<li class="soi-app-row" data-slug="' + i.slug + '"><a href="/issues/' + i.slug + '/"><b>' + esc(i.period) + '</b><small>Issue ' + i.number + ' · ' + i.articles + ' articles</small></a>' +
          (st ? '<span class="soi-app-chip">' + st + '</span>' : '') +
          (inApp ? '' : have[i.slug] ? '<button type="button" class="soi-app-rm" aria-label="Remove ' + esc(i.period) + ' from this phone">Remove</button>'
            : '<button type="button" class="soi-app-get" aria-label="Save ' + esc(i.period) + ' on this phone">Save</button>') + '</li>';
      }).join('');
    }
    function load() { return store.keys().catch(function () { return []; }).then(function (k) { have = {}; k.forEach(function (s) { have[s] = 1; }); draw(); }); }
    listEl.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var slug = b.closest('li').dataset.slug, it = issues.filter(function (x) { return x.slug === slug; })[0];
      if (b.classList.contains('soi-app-rm')) { store.del(slug).then(load); return; }
      b.disabled = true; b.textContent = 'Saving…';
      download(slug, it.v).then(load, function () { b.disabled = false; b.textContent = 'Try again'; stat.textContent = 'Could not reach the internet. Please check your connection.'; });
    });
    allBtn.addEventListener('click', function () {
      if (busy) return; busy = true; allBtn.disabled = true;
      if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(function () {});
      var todo = issues.filter(function (i) { return !have[i.slug] && CFG.bundled.indexOf(i.slug) < 0; }).reverse(), total = todo.length, done = 0, failed = 0;
      function next() {
        var it = todo.shift(); if (!it) return Promise.resolve();
        return download(it.slug, it.v).then(function () { done++; }, function () { failed++; }).then(function () {
          allBtn.textContent = 'Saving… ' + (done + failed) + ' of ' + total; return next();
        });
      }
      Promise.all([next(), next(), next()]).then(function () {
        busy = false; allBtn.disabled = false;
        return load().then(function () { if (failed) stat.textContent += ' ' + failed + ' could not be saved – check your connection and try again.'; });
      });
    });
    manifest(false).then(function (l) { issues = l; return load(); }).then(function () { return manifest(true); }).then(function (l) { issues = l; draw(); }).catch(function () {});
  }

  /* ---------- audio: lock-screen / notification controls ----------
     The website player uses one Audio element and already fills navigator.mediaSession.
     iPhone: the system reads navigator.mediaSession itself (needs the "audio" background mode, see README).
     Android: the web view does not show a media notification, so the same information is passed to the
     MediaSession plugin, which runs the foreground service that keeps audio playing with the screen off. */
  var MS = platform === 'android' ? plugin('MediaSession') : null, theAudio = null, lastPos = 0;
  function ms(fn, a, b) { try { var p = MS[fn](a, b); if (p && p.catch) p.catch(function () {}); } catch (e) {} }
  function pos() {
    var a = theAudio; if (!MS || !a || !isFinite(a.duration) || !a.duration) return;
    ms('setPositionState', { duration: a.duration, position: Math.min(a.currentTime, a.duration), playbackRate: a.playbackRate || 1 });
  }
  function hook(a) {
    theAudio = a; if (!MS) return;
    a.addEventListener('play', function () { theAudio = a; ms('setPlaybackState', { playbackState: 'playing' }); pos(); });
    a.addEventListener('pause', function () { ms('setPlaybackState', { playbackState: 'paused' }); pos(); });
    ['loadedmetadata', 'ratechange', 'seeked'].forEach(function (ev) { a.addEventListener(ev, pos); });
    a.addEventListener('timeupdate', function () { var n = Date.now(); if (n - lastPos > 5000) { lastPos = n; pos(); } });
  }
  (function patchAudio() {
    var A = window.Audio; if (!A || A.soi) return;
    function SoiAudio(src) { var a = src === undefined ? new A() : new A(src); hook(a); return a; }
    SoiAudio.prototype = A.prototype; SoiAudio.soi = true; window.Audio = SoiAudio;
    if (!MS || !('mediaSession' in navigator)) return;
    var nms = navigator.mediaSession, set = nms.setActionHandler.bind(nms);
    nms.setActionHandler = function (action, h) { try { set(action, h); } catch (e) {} ms('setActionHandler', { action: action }, h ? function (d) { h(d || { action: action }); } : null); };
    var d = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(nms), 'metadata');
    if (d && d.set) Object.defineProperty(nms, 'metadata', {
      configurable: true, get: function () { return d.get.call(nms); },
      set: function (m) { d.set.call(nms, m); if (m) ms('setMetadata', { title: m.title, artist: m.artist, album: m.album, artwork: [{ src: location.origin + '/assets/app-art.png', sizes: '512x512', type: 'image/png' }] }); }
    });
    ms('setActionHandler', { action: 'play' }, function () { if (theAudio) theAudio.play(); });
    ms('setActionHandler', { action: 'pause' }, function () { if (theAudio) theAudio.pause(); });
    ms('setActionHandler', { action: 'seekto' }, function (x) { if (theAudio && x && x.seekTime != null) theAudio.currentTime = x.seekTime; });
  })();

  /* ---------- start ---------- */
  function nav() {
    var n = document.querySelector('.soi-nav');
    if (!n || n.querySelector('.soi-app-navlink')) return;
    var a = document.createElement('a'); a.href = '/saved.html'; a.className = 'soi-app-navlink'; a.textContent = 'Saved';
    if (/\/saved\.html$/.test(location.pathname)) a.setAttribute('aria-current', 'page');
    n.appendChild(a);
  }
  function init() {
    document.documentElement.classList.add('soi-app');
    document.addEventListener('click', onClick);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', nav); else nav();
  }
  var App = plugin('App');
  if (App && App.addListener) App.addListener('backButton', function (e) { if (e && e.canGoBack) history.back(); else App.exitApp(); });

  window.soiApp = { init: init, store: store, route: route, download: download };
  init();
  cfgReady.then(function () {
    var go = function () { if (/\/reader\.html$/.test(location.pathname)) reader(); else savedPage(); };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  });
})();
