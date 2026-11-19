/* Spirit of Islam app – the layer that turns the website pages into a phone app.
   - keeps links inside the app (an issue opens from the app, from a saved copy, or is fetched once)
   - saves issues on the phone for offline reading
   - home top bar (menu, logo, gems, sign in), bottom tabs (Home · Archive · Saved · Profile), menu drawer, launch logo
   - sharing, links that open the app, lock-screen / notification audio controls
   Reading memory (Continue where you left, saved articles and quotes) lives in site.js, shared with the website.
   Everything is prefixed soi. No accounts yet, no tracking. */
(function () {
  if (window.soiApp) { window.soiApp.init(); return; }
  var CFG = { remote: '', bundled: [], fonts: false };
  var cfgReady = fetch('/assets/app-config.json').then(function (r) { return r.json(); })
    .then(function (c) { CFG = c; window.soiShareBase = c.share || c.remote; }).catch(function () {});
  var native = !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
  var platform = native ? window.Capacitor.getPlatform() : 'web';
  function plugin(n) { try { return native ? (window.Capacitor.Plugins[n] || window.Capacitor.registerPlugin(n)) : null; } catch (e) { return null; } }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function $(s, r) { return (r || document).querySelector(s); }

  /* ---------- links ---------- */
  var SCREENS = { '/': '/index.html', '/search/': '/search.html', '/saved/': '/saved.html', '/signin/': '/profile.html' };
  function route(href) {
    var u; try { u = new URL(href, location.href); } catch (e) { return null; }
    if (u.origin !== location.origin) return null;
    var m = u.pathname.match(/^\/issues\/([\w-]+)\/?(?:index\.html)?$/);
    if (m) {
      if (CFG.bundled.indexOf(m[1]) >= 0) return '/issues/' + m[1] + '/index.html' + u.search + u.hash;
      var q = new URLSearchParams(u.search); q.set('issue', m[1]); return '/reader.html?' + q.toString() + u.hash;
    }
    if (SCREENS[u.pathname]) return SCREENS[u.pathname] + u.search + u.hash;
    if (/\/$/.test(u.pathname)) return u.pathname + 'index.html' + u.search + u.hash;
    return null;
  }
  function openExternal(url) {                         /* the PDF opens in the phone's own viewer/browser */
    var B = plugin('Browser'); if (B && B.open) { B.open({ url: url }).catch(function () { window.open(url, '_system'); }); return; }
    window.open(url, '_system');
  }
  function go(href) { location.href = route(href) || href; }
  function onClick(e) {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a || a.hasAttribute('download')) return;
    var raw = a.getAttribute('href');
    if (/\.pdf(\?|#|$)/i.test(raw)) { e.preventDefault(); openExternal(a.href.indexOf('/media/') > -1 && a.href.indexOf(CFG.remote) !== 0 ? CFG.remote + raw.slice(raw.indexOf('/media/')) : a.href); return; }
    if (a.target === '_blank') return;
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
    keys: function () { return tx('readonly', function (s) { return s.getAllKeys(); }).catch(function () { return []; }); }
  };
  function timed(url, ms) {
    var c = new AbortController(), t = setTimeout(function () { c.abort(); }, ms || 20000);
    return fetch(url, { signal: c.signal, cache: 'no-store' }).then(function (r) { clearTimeout(t); if (!r.ok) throw new Error('HTTP ' + r.status); return r; },
      function (e) { clearTimeout(t); throw e; });
  }
  function download(slug, v) {
    return timed(CFG.remote + '/issues/' + slug + '/').then(function (r) { return r.text(); }).then(function (html) {
      if (html.indexOf('soi-ev') < 0) throw new Error('not an issue page');
      html = html.replace(/(["'(=])\/media\//g, '$1' + CFG.remote + '/media/');      /* audio and PDFs stream from the website */
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
    html = html.replace('<html lang="en">', '<html lang="en" class="soi-app">');
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
    if (!/^[\w-]+$/.test(slug)) { location.replace('/index.html'); return; }
    if (CFG.bundled.indexOf(slug) >= 0) { location.replace('/issues/' + slug + '/index.html' + location.search + location.hash); return; }
    store.get(slug).catch(function () { return null; }).then(function (rec) {
      if (rec) {
        show(rec.html);
        manifest(true).then(function (list) {            /* quietly pick up a corrected version for next time */
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
          '<p class="soi-app-actions"><a class="soi-app-btn" href="#" onclick="location.reload();return false">Try again</a> <a class="soi-app-btn soi-app-btn-quiet" href="/saved.html">See saved issues</a></p>');
      });
    });
  }

  /* ---------- app bar and bottom tabs ---------- */
  var IC = {
    home: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11l9-8 9 8v10h-6v-6H9v6H3z"/></svg>',
    search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>',
    saved: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>',
    profile: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>',
    back: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12H5M11 6l-6 6 6 6"/></svg>',
    share: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v13M7 8l5-5 5 5M5 14v6h14v-6"/></svg>'
  };
  var LOGO = '<img src="/assets/brand/Peogen-logo.png" alt="" width="470" height="453"><span class="soi-app-logo-rule"></span><img src="/assets/brand/soi-mark-white.svg" alt="Spirit of Islam" width="790" height="511">';
  IC.menu = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>';
  IC.archive = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h3.2v16H4zM9.4 4h3.2v16H9.4zM14.6 5.1l3.1-.8 3.8 15-3.1.8z"/></svg>';
  IC.gem = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/><path d="M2.5 9h19M9 3.5 7.5 9 12 20.5 16.5 9 15 3.5"/></svg>';
  IC.close = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>';
  function splash() {                                   /* the SOI logo for a moment when the app opens */
    if (!/\/(index\.html)?$/.test(location.pathname) || sessionStorage.getItem('soiSplash') || !localStorage.getItem('soiWelcomed')) return;
    sessionStorage.setItem('soiSplash', '1');
    var s = document.createElement('div'); s.id = 'soi-app-splash'; s.innerHTML = '<div class="soi-app-splash-logo">' + LOGO + '</div><p>Towards Global Peace &amp; Spiritual Living</p>';
    document.body.appendChild(s);
    setTimeout(function () { s.classList.add('is-out'); setTimeout(function () { s.remove(); }, 600); }, 1300);
  }
  function drawer() {                                   /* the menu: everything from the website footer */
    var d = document.createElement('div'); d.id = 'soi-app-drawer'; d.hidden = true;
    var G = function (t, l) { return '<div class="soi-app-dg"><h2>' + t + '</h2>' + l.map(function (x) { return '<a href="' + x[1] + '"' + (x[2] ? ' id="' + x[2] + '"' : '') + '>' + x[0] + '</a>'; }).join('') + '</div>'; };
    d.innerHTML = '<div class="soi-app-drawer-in" role="dialog" aria-label="Menu"><div class="soi-app-drawer-top"><span class="soi-app-logo">' + LOGO + '</span><button type="button" aria-label="Close menu">' + IC.close + '</button></div>' +
      '<a class="soi-app-dsign" href="/profile.html"><span>' + IC.profile + '</span><b>Sign in</b><small>Keep your progress on every device</small></a>' +
      G('Read', [['Latest issue', '/archive/', 'soi-app-dl'], ['Archive · every issue', '/archive/'], ['Quotes', '/quotes/'], ['Search', '/search.html?focus=1']]) +
      G('You', [['Saved', '/saved.html'], ['Gems', '/gems.html'], ['Your profile &amp; progress', '/profile.html'], ['Welcome tour', '/index.html?welcome=1']]) +
      '<div class="soi-app-drawer-more"></div></div>';
    document.body.appendChild(d);
    fetch('/assets/app-menu.html').then(function (r) { return r.ok ? r.text() : ''; }).then(function (h) {
      var t = document.createElement('div'), out = ''; t.innerHTML = h;
      var f = $('a[href^="/issues/"]', t); if (f) $('#soi-app-dl', d).setAttribute('href', f.getAttribute('href'));
      Array.prototype.forEach.call(t.querySelectorAll('.soi-foot2-col'), function (c) {   /* every footer column except "Read" (already above) */
        var hh = $('h2', c); if (hh && /^read$/i.test(hh.textContent.trim())) return;
        out += '<div class="soi-app-dg' + ($('.soi-soc', c) ? ' is-soc' : '') + '">' + c.innerHTML + '</div>';
      });
      $('.soi-app-drawer-more', d).innerHTML = out;
    }).catch(function () {});
    function close() { d.classList.remove('is-open'); setTimeout(function () { d.hidden = true; }, 300); document.documentElement.style.overflow = ''; }
    d.addEventListener('click', function (e) { if (e.target === d || e.target.closest('.soi-app-drawer-top button') || e.target.closest('a')) close(); });
    return function () { d.hidden = false; requestAnimationFrame(function () { d.classList.add('is-open'); }); document.documentElement.style.overflow = 'hidden'; };
  }
  function chrome() {
    var b = document.body; if (!b || $('#soi-app-tabs') || $('#soi-app-bar') || $('#soi-app-top')) return;
    var issue = $('meta[name="soi-issue"]'), screen = b.getAttribute('data-screen') || '';
    if (/\/reader\.html$/.test(location.pathname) && !issue) screen = 'loading';
    splash();
    if (screen === 'home') {                             /* home: menu, logo, gems, sign in */
      var open = drawer(), top = document.createElement('header'); top.id = 'soi-app-top';
      top.innerHTML = '<button type="button" class="soi-app-ibtn" aria-label="Menu">' + IC.menu + '</button><span class="soi-app-logo">' + LOGO + '</span>' +
        '<a class="soi-app-ibtn soi-app-gemb" href="/gems.html" aria-label="Gems">' + IC.gem + '</a><a class="soi-app-signin" href="/profile.html">Sign in</a>';
      b.insertBefore(top, b.firstChild);
      $('button', top).addEventListener('click', open);
    } else if (!screen) {                                /* a website page shown inside the app: slim bar on top */
      var bar = document.createElement('div'); bar.id = 'soi-app-bar';
      var title = issue ? issue.getAttribute('data-label') : (($('main h1') || {}).textContent || 'Spirit of Islam');
      bar.innerHTML = '<button type="button" class="soi-app-back" aria-label="Back">' + IC.back + '</button><b>' + esc(title) + '</b>' +
        (issue ? '<button type="button" class="soi-app-share" aria-label="Share this issue">' + IC.share + '</button>' : '<span></span>');
      b.insertBefore(bar, b.firstChild);
      $('.soi-app-back', bar).addEventListener('click', function () { if (history.length > 1) history.back(); else location.href = '/index.html'; });
      var sh = $('.soi-app-share', bar);
      if (sh) sh.addEventListener('click', function () { window.soi && window.soi.share($('meta[name="soi-issue"]').getAttribute('data-label'), '/issues/' + issue.content + '/'); });
      if (issue) {                                       /* no magazine introduction on every issue: small logo + two buttons */
        var y = (issue.getAttribute('data-label') || '').match(/(19|20)\d\d/), ban = $('.soi-auto-banner');
        var h = document.createElement('div'); h.className = 'soi-app-ihead';
        h.innerHTML = '<span class="soi-app-ihead-logo"><img src="/assets/brand/Peogen-logo.png" alt=""></span>' + (y ? '<a href="/archive/#y' + y[0] + '">' + y[0] + ' issues</a>' : '') + '<a href="/archive/">All issues</a>';
        if (ban) ban.parentNode.replaceChild(h, ban); else { var m = $('main') || b; m.insertBefore(h, m.firstChild); }
      }
    }
    if (issue || screen === 'gems' || screen === 'loading') return;      /* reading and the gems page are full screen */
    var cur = screen || (/\/archive\//.test(location.pathname) ? 'archive' : '');
    var nav = document.createElement('nav'); nav.id = 'soi-app-tabs'; nav.setAttribute('aria-label', 'Tabs');
    nav.innerHTML = [['home', '/index.html', 'Home'], ['archive', '/archive/', 'Archive'], ['saved', '/saved.html', 'Saved'], ['profile', '/profile.html', 'Profile']].map(function (t) {
      return '<a href="' + t[1] + '"' + (t[0] === cur ? ' aria-current="page"' : '') + '>' + IC[t[0]] + t[2] + '</a>';
    }).join('');
    b.appendChild(nav); b.classList.add('soi-app-has-tabs');
  }

  /* ---------- sharing and links that open the app ---------- */
  var Share = plugin('Share');
  if (Share) window.soiNativeShare = function (title, url) { Share.share({ title: title, text: title + ' – Spirit of Islam', url: url, dialogTitle: 'Share' }).catch(function () {}); };
  var App = plugin('App');
  if (App && App.addListener) {
    App.addListener('backButton', function (e) { if (e && e.canGoBack) history.back(); else App.exitApp(); });
    App.addListener('appUrlOpen', function (e) {         /* a shared article link opened on a phone that has the app */
      try { var u = new URL(e.url); if (/^\/issues\/[\w-]+\/?$/.test(u.pathname)) cfgReady.then(function () { location.href = route(location.origin + u.pathname + u.search + u.hash); }); } catch (x) {}
    });
  }

  /* ---------- audio: lock-screen / notification controls ----------
     The website player uses one Audio element and already fills navigator.mediaSession.
     iPhone: the system reads navigator.mediaSession itself (needs the "audio" background mode, see README).
     Android: the web view shows no media notification, so the same information is passed to the MediaSession
     plugin, whose foreground service keeps audio playing with the screen off. */
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
    var A = window.Audio; if (!A) return;
    function SoiAudio(src) { var a = src === undefined ? new A() : new A(src); hook(a); return a; }
    SoiAudio.prototype = A.prototype; SoiAudio.soi = true; window.Audio = SoiAudio;
    if (!MS || !('mediaSession' in navigator)) return;
    var nms = navigator.mediaSession, set = nms.setActionHandler.bind(nms);
    nms.setActionHandler = function (action, h) { try { set(action, h); } catch (e) {} ms('setActionHandler', { action: action }, h ? function (d) { h(d || { action: action }); } : null); };
    var d = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(nms), 'metadata');
    if (d && d.set) Object.defineProperty(nms, 'metadata', {
      configurable: true, get: function () { return d.get.call(nms); },
      set: function (m) { d.set.call(nms, m); if (m) ms('setMetadata', { title: m.title, artist: m.artist, album: m.album, artwork: [{ src: location.origin + '/assets/brand/Peogen-logo.png', sizes: '470x453', type: 'image/png' }] }); }
    });
    ms('setActionHandler', { action: 'play' }, function () { if (theAudio) theAudio.play(); });
    ms('setActionHandler', { action: 'pause' }, function () { if (theAudio) theAudio.pause(); });
    ms('setActionHandler', { action: 'seekto' }, function (x) { if (theAudio && x && x.seekTime != null) theAudio.currentTime = x.seekTime; });
  })();

  /* ---------- start ---------- */
  function start() { chrome(); if (window.soiExp) window.soiExp(); }
  function init() {
    document.documentElement.classList.add('soi-app');
    document.addEventListener('click', onClick);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  }
  window.soiApp = { init: init, store: store, route: route, go: go, download: download, manifest: manifest, ready: cfgReady, cfg: function () { return CFG; }, esc: esc };
  init();
  cfgReady.then(function () {
    var run = function () { if (/\/reader\.html$/.test(location.pathname)) reader(); else if (window.soiScreens) window.soiScreens(); };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
  });
})();
