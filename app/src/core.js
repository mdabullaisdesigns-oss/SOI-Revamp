/* Spirit of Islam app – core.
   One page that never reloads, so audio keeps playing while the reader moves between screens.
   - screens and native-feeling transitions (router), theme (light/dark), text size, safe areas
   - reading view: the magazine block of an issue page, loaded into the app
   - reading memory: Continue reading (article, place on the page, audio time), finished articles, saved items
   - offline: an issue with its audio is kept on the phone (IndexedDB), with progress and storage used
   - audio: one mini player across all screens; lock-screen / notification controls
   Everything is prefixed soi. No account yet and nothing leaves the device. */
(function () {
  'use strict';
  var W = window, D = document, root = D.documentElement;
  var CFG = { remote: '', share: '', bundled: [] };
  var native = !!(W.Capacitor && W.Capacitor.isNativePlatform && W.Capacitor.isNativePlatform());
  var platform = native ? W.Capacitor.getPlatform() : 'web';
  function plugin(n) { try { return native ? (W.Capacitor.Plugins[n] || W.Capacitor.registerPlugin(n)) : null; } catch (e) { return null; } }
  var Haptics = plugin('Haptics'), StatusBar = plugin('StatusBar'), Share = plugin('Share'), AppP = plugin('App'), Splash = plugin('SplashScreen');

  /* ---------- small helpers ---------- */
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function $(s, r) { return (r || D).querySelector(s); }
  function $$(s, r) { return [].slice.call((r || D).querySelectorAll(s)); }
  function mmss(t) { t = Math.max(0, Math.round(t || 0)); return Math.floor(t / 60) + ':' + ('0' + (t % 60)).slice(-2); }
  function mb(n) { n = n || 0; return n < 1048576 ? Math.max(0.1, n / 1048576).toFixed(1) + ' MB' : n < 104857600 ? (n / 1048576).toFixed(1) + ' MB' : Math.round(n / 1048576) + ' MB'; }
  function shortPeriod(p) { return String(p || '').replace(/(January|February|March|April|June|July|August|September|October|November|December)/g, function (m) { return m.slice(0, 3); }); }
  function label(i) { return (i.number ? 'Issue ' + i.number + ' · ' : '') + shortPeriod(i.period); }
  var LS = {
    get: function (k, d) { try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  function emit(name, detail) { W.dispatchEvent(new CustomEvent(name, { detail: detail })); }
  function tap(kind) { if (Haptics) { try { (kind === 'ok' ? Haptics.notification({ type: 'SUCCESS' }) : Haptics.impact({ style: 'LIGHT' })).catch(function () {}); } catch (e) {} } }
  var toastT = 0;
  function toast(msg) {
    var t = $('#soi-app-toast'); t.textContent = msg; t.classList.add('is-on');
    clearTimeout(toastT); toastT = setTimeout(function () { t.classList.remove('is-on'); }, 2600);
  }
  function cover(i, big, eager) {
    var slug = i.slug, f = '/assets/covers/' + slug + (big ? '@2x' : '') + '.webp';
    return '<span class="soi-app-cover"><span class="soi-app-cover-fb" aria-hidden="true"><b>Spirit of Islam</b><i>' + esc(shortPeriod(i.period || '')) + '</i></span>' +
      '<img alt="" ' + (eager ? '' : 'loading="lazy" ') + 'decoding="async" src="' + f + '" data-slug="' + slug + '"></span>';
  }
  D.addEventListener('error', function (e) {                      /* a large cover that is not packed falls back to the small one */
    var im = e.target; if (!im || im.tagName !== 'IMG' || !im.dataset || !im.dataset.slug) return;
    if (im.dataset.fb) im.remove(); else { im.dataset.fb = '1'; im.src = '/assets/covers/' + im.dataset.slug + '.webp'; }
  }, true);

  /* ---------- theme and text size ---------- */
  var prefs = LS.get('soiAppPrefs', { theme: 'system', text: 1 });
  var darkMq = W.matchMedia('(prefers-color-scheme: dark)');
  function isDark() { return prefs.theme === 'dark' || (prefs.theme === 'system' && darkMq.matches); }
  function systemTextScale() {                                    /* iPhone Dynamic Type: the system body size, 17px at the default setting */
    var p = D.createElement('p'); p.style.cssText = 'font:-apple-system-body;position:absolute;visibility:hidden;margin:0';
    (D.body || root).appendChild(p); var px = parseFloat(getComputedStyle(p).fontSize) || 17; p.remove();
    return CSS.supports('font', '-apple-system-body') ? Math.max(0.8, Math.min(1.9, px / 17)) : 1;   /* Android scales web text by itself */
  }
  function applyPrefs() {
    var dark = isDark();
    root.classList.toggle('soi-app-dark', dark);
    root.style.colorScheme = dark ? 'dark' : 'light';
    var scale = (prefs.text || 1) * systemTextScale();
    root.style.fontSize = (16 * scale).toFixed(2) + 'px';
    root.style.setProperty('--soi-read-zoom', String(prefs.text || 1));
    var m = $('meta[name="theme-color"]'); if (m) m.content = dark ? '#0D1D24' : '#F6F5EE';
    if (StatusBar) { try { StatusBar.setStyle({ style: dark ? 'DARK' : 'LIGHT' }).catch(function () {}); } catch (e) {} }
  }
  function setPref(k, v) { prefs[k] = v; LS.set('soiAppPrefs', prefs); applyPrefs(); emit('soi-prefs'); }
  darkMq.addEventListener('change', applyPrefs);
  D.addEventListener('visibilitychange', function () { if (!D.hidden) applyPrefs(); });
  applyPrefs();

  /* ---------- scrolling belongs to the screen that is showing ----------
     The magazine block scrolls the window (to follow the audio, to open an article). While the reading
     view is hidden those calls must not move the screen the reader is on, so they are ignored then. */
  var realScrollTo = W.scrollTo.bind(W), realIntoView = Element.prototype.scrollIntoView, realReplace = history.replaceState.bind(history);
  var readerShown = false;
  function inReader(el) { return !!(el && el.closest && el.closest('#soi-app-read-body')); }
  W.scrollTo = function () { if (readerShown) realScrollTo.apply(null, arguments); };
  W.scroll = W.scrollTo;
  Element.prototype.scrollIntoView = function () { if (!inReader(this) || readerShown) realIntoView.apply(this, arguments); };
  history.replaceState = function (st, t, url) {                  /* the block writes "#article" into the address */
    if (typeof url === 'string' && url.charAt(0) === '#') { if (!readerShown) return; return realReplace(history.state, '', location.pathname + location.search + url); }
    return realReplace(st, t, url);
  };

  /* ---------- storage on the phone (IndexedDB) ---------- */
  var dbp = null;
  function db() {
    if (!dbp) dbp = new Promise(function (ok, no) {
      var q = indexedDB.open('soi-app', 2);
      q.onupgradeneeded = function () {
        var d = q.result;
        if (!d.objectStoreNames.contains('issues')) d.createObjectStore('issues', { keyPath: 'slug' });
        if (!d.objectStoreNames.contains('audio')) d.createObjectStore('audio', { keyPath: 'url' }).createIndex('slug', 'slug');
      };
      q.onsuccess = function () { ok(q.result); }; q.onerror = function () { no(q.error); };
    });
    return dbp;
  }
  function tx(name, mode, fn) {
    return db().then(function (d) {
      return new Promise(function (ok, no) {
        var t = d.transaction(name, mode), r = fn(t.objectStore(name));
        t.oncomplete = function () { ok(r && r.result); }; t.onerror = t.onabort = function () { no(t.error); };
      });
    });
  }
  var store = {
    getIssue: function (slug) { return tx('issues', 'readonly', function (s) { return s.get(slug); }).catch(function () { return null; }); },
    putIssue: function (rec) { return tx('issues', 'readwrite', function (s) { return s.put(rec); }); },
    delIssue: function (slug) { return tx('issues', 'readwrite', function (s) { return s.delete(slug); }); },
    audioOf: function (slug) { return tx('audio', 'readonly', function (s) { return s.index('slug').getAll(slug); }).catch(function () { return []; }); },
    putAudio: function (rec) { return tx('audio', 'readwrite', function (s) { return s.put(rec); }); },
    delAudioOf: function (slug) {
      return db().then(function (d) {
        return new Promise(function (ok, no) {
          var t = d.transaction('audio', 'readwrite'), q = t.objectStore('audio').index('slug').openKeyCursor(IDBKeyRange.only(slug));
          q.onsuccess = function () { var c = q.result; if (c) { t.objectStore('audio').delete(c.primaryKey); c.continue(); } };
          t.oncomplete = ok; t.onerror = t.onabort = function () { no(t.error); };
        });
      });
    }
  };
  /* what is on the phone, kept small so screens can show it at once:
     { slug: { text: bytes, audio: bytes, have: files saved, of: files in the issue, at } } */
  function index() { return LS.get('soiOffline', {}); }
  function setIndex(slug, patch) { var ix = index(); if (patch === null) delete ix[slug]; else ix[slug] = Object.assign(ix[slug] || { text: 0, audio: 0, have: 0, of: 0 }, patch); LS.set('soiOffline', ix); emit('soi-offline', { slug: slug }); }
  function packed(slug) { return CFG.bundled.indexOf(slug) >= 0; }
  function hasText(slug) { return packed(slug) || !!(index()[slug] && index()[slug].text); }
  function hasAudio(slug) { var x = index()[slug]; return !!(x && x.of && x.have >= x.of); }
  function storageUsed() { var ix = index(), t = 0, a = 0, n = 0, na = 0; Object.keys(ix).forEach(function (k) { t += ix[k].text || 0; a += ix[k].audio || 0; if (ix[k].text) n++; if (ix[k].have) na++; }); return { text: t, audio: a, total: t + a, issues: n, withAudio: na }; }

  /* ---------- the list of issues ---------- */
  function timed(url, ms, opt) {
    var c = new AbortController(), t = setTimeout(function () { c.abort(); }, ms || 20000);
    return fetch(url, Object.assign({ signal: c.signal, cache: 'no-store' }, opt || {})).then(function (r) { clearTimeout(t); if (!r.ok) throw new Error('HTTP ' + r.status); return r; },
      function (e) { clearTimeout(t); throw e; });
  }
  var manifestMem = null, manifestFresh = null;
  function manifest(refresh) {
    var local = manifestMem ? Promise.resolve(manifestMem) : (LS.get('soiAppIssues', null) ? Promise.resolve(LS.get('soiAppIssues', null)) :
      fetch('/issues.json').then(function (r) { return r.json(); }).then(function (j) { return j.issues; })).then(function (l) { manifestMem = manifestMem || l; return manifestMem; });
    if (!refresh) return local;
    if (!manifestFresh) manifestFresh = timed(CFG.remote + '/issues.json', 8000).then(function (r) { return r.json(); }).then(function (j) {
      if (j.issues && j.issues.length) { manifestMem = j.issues; LS.set('soiAppIssues', j.issues); }
      return manifestMem;
    }).catch(function () { manifestFresh = null; return local; });
    return manifestFresh;
  }
  function issueOf(slug) { return manifest(false).then(function (l) { return l.filter(function (i) { return i.slug === slug; })[0] || { slug: slug, period: '', articles: 0, arts: [] }; }); }

  /* ---------- an issue page -> the magazine block ---------- */
  function blockOf(html) {
    var a = html.indexOf('<div class="soi-issue">'); if (a < 0) return null;
    var b = html.indexOf('<nav class="soi-wrap soi-pager"', a); if (b < 0) b = html.indexOf('</main>', a);
    var s = html.slice(a + 23, b), cut = s.lastIndexOf('</div>');
    s = cut > 0 ? s.slice(0, cut) : s;
    return s.replace(/<link[^>]+fonts\.(?:googleapis|gstatic)\.com[^>]*>/g, '');
  }
  function audioList(html) {
    var out = [], re = /<audio\b[^>]*\bsrc="([^"]+)"/g, m;
    while ((m = re.exec(html))) if (out.indexOf(m[1]) < 0) out.push(m[1].replace(/&amp;/g, '&'));
    return out;
  }
  function absUrl(src) { return /^https?:/.test(src) ? src : CFG.remote + src; }
  function pageOf(slug, allowNet) {
    if (packed(slug)) return fetch('/issues/' + slug + '/index.html').then(function (r) { if (!r.ok) throw new Error('missing'); return r.text(); });
    return store.getIssue(slug).then(function (rec) {
      if (rec) return rec.html;
      if (allowNet === false) throw new Error('offline');
      return fetchPage(slug).then(function (rec) { return rec.html; });
    });
  }
  function fetchPage(slug) {
    return issueOf(slug).then(function (it) {
      return timed(CFG.remote + '/issues/' + slug + '/').then(function (r) { return r.text(); }).then(function (html) {
        if (!blockOf(html)) throw new Error('not an issue page');
        var rec = { slug: slug, html: html, v: it.v || '', bytes: html.length, at: Date.now() };
        return store.putIssue(rec).then(function () { setIndex(slug, { text: html.length, at: rec.at, of: audioList(html).length }); return rec; });
      });
    });
  }

  /* ---------- offline: an issue together with its audio ---------- */
  var jobs = {};                                                   /* slug -> { state, done, total, bytes, cancel } */
  function job(slug) { return jobs[slug] || null; }
  function getBlob(url, onBytes, signal) {
    return fetch(url, { signal: signal }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      if (!r.body || !r.body.getReader) return r.blob();
      var reader = r.body.getReader(), parts = [], type = r.headers.get('content-type') || 'audio/mpeg';
      function pump() { return reader.read().then(function (x) { if (x.done) return new Blob(parts, { type: type }); parts.push(x.value); onBytes(x.value.length); return pump(); }); }
      return pump();
    }).catch(function (e) {
      if (signal && signal.aborted) throw e;
      var Http = plugin('CapacitorHttp');                         /* a server that does not allow web downloads: fetch it natively */
      if (!Http) throw e;
      return Http.get({ url: url, responseType: 'blob' }).then(function (res) {
        if (res.status >= 400 || typeof res.data !== 'string') throw new Error('HTTP ' + res.status);
        var bin = atob(res.data), u8 = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
        onBytes(u8.length); return new Blob([u8], { type: 'audio/mpeg' });
      });
    });
  }
  function saveIssue(slug, withAudio) {
    if (jobs[slug]) return jobs[slug].promise;
    var ctl = new AbortController(), j = jobs[slug] = { state: 'text', done: 0, total: 0, bytes: 0, failed: 0, cancel: function () { ctl.abort(); } };
    function tick() { emit('soi-offline', { slug: slug }); }
    tick();
    j.promise = pageOf(slug).then(function (html) {
      var list = audioList(html);
      if (!packed(slug) && !(index()[slug] || {}).text) setIndex(slug, { text: html.length, at: Date.now() });
      setIndex(slug, { of: list.length });
      if (!withAudio || !list.length) return;
      j.state = 'audio'; j.total = list.length; tick();
      return store.audioOf(slug).then(function (have) {
        var got = {}; have.forEach(function (r) { got[r.url] = r.bytes; });
        var todo = list.filter(function (u) { return !got[u]; }); j.done = list.length - todo.length;
        var saved = have.reduce(function (a, r) { return a + (r.bytes || 0); }, 0), lastTick = 0;
        function next() {
          if (ctl.signal.aborted) return Promise.reject(new Error('cancelled'));
          var u = todo.shift(); if (!u) return Promise.resolve();
          return getBlob(absUrl(u), function (n) { j.bytes += n; var t = Date.now(); if (t - lastTick > 250) { lastTick = t; tick(); } }, ctl.signal)
            .then(function (blob) { return store.putAudio({ url: u, slug: slug, blob: blob, bytes: blob.size }).then(function () { saved += blob.size; j.done++; setIndex(slug, { audio: saved, have: j.done }); }); },
              function (e) { if (ctl.signal.aborted) throw e; j.failed++; })
            .then(next);
        }
        return Promise.all([next(), next()]);
      });
    }).then(function () {
      var f = j.failed; delete jobs[slug]; tick();
      if (f) throw new Error(f + ' audio files could not be saved');
    }, function (e) { delete jobs[slug]; tick(); throw e; });
    return j.promise;
  }
  function removeAudio(slug) { return store.delAudioOf(slug).then(function () { setIndex(slug, { audio: 0, have: 0 }); }); }
  function removeIssue(slug) {
    if (jobs[slug]) jobs[slug].cancel();
    return store.delAudioOf(slug).then(function () { return store.delIssue(slug); }).then(function () { setIndex(slug, null); });
  }
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(function () {});

  /* ---------- reading memory (same keys as the website) ---------- */
  var mem = {
    progress: function () { return LS.get('soiProgress', null); },
    read: function () { return LS.get('soiRead', {}); },
    readCount: function (slug) { return Object.keys(mem.read()[slug] || {}).length; },
    markRead: function (slug, id) { var r = mem.read(); r[slug] = r[slug] || {}; if (!r[slug][id]) { r[slug][id] = Date.now(); LS.set('soiRead', r); mem.day(); } },
    day: function () { var d = LS.get('soiDays', {}), k = new Date().toISOString().slice(0, 10); if (!d[k]) { d[k] = 1; LS.set('soiDays', d); } },
    articles: function () { return LS.get('soiSavedArticles', []); },
    hasArticle: function (slug, id) { return mem.articles().some(function (a) { return a.slug === slug && a.id === id; }); },
    toggleArticle: function (a) {
      var l = mem.articles(), n = l.filter(function (x) { return !(x.slug === a.slug && x.id === a.id); });
      if (n.length === l.length) { a.at = Date.now(); n.unshift(a); } LS.set('soiSavedArticles', n); return n.length > l.length;
    },
    quotes: function () { return LS.get('soiSavedQuotes', []); },
    hasQuote: function (q) { return mem.quotes().some(function (x) { return x.t === q.t; }); },
    toggleQuote: function (q) {
      var l = mem.quotes(), n = l.filter(function (x) { return x.t !== q.t; });
      if (n.length === l.length) n.unshift({ t: q.t, s: q.s, a: q.a, at: q.at, n: q.n, p: q.p });
      LS.set('soiSavedQuotes', n); return n.length > l.length;
    }
  };

  /* ---------- sharing ---------- */
  function share(title, path) {
    var url = (CFG.share || CFG.remote) + path, data = { title: title, text: title + ' – Spirit of Islam', url: url };
    if (Share) { Share.share({ title: data.title, text: data.text, url: url, dialogTitle: 'Share' }).catch(function () {}); return; }
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { toast('Link copied'); }, function () { toast(url); });
  }
  function wrapText(ctx, t, max) { var w = t.split(' '), lines = [], l = ''; w.forEach(function (x) { var n = l ? l + ' ' + x : x; if (ctx.measureText(n).width > max && l) { lines.push(l); l = x; } else l = n; }); if (l) lines.push(l); return lines; }
  function quoteImage(q) {
    var Wd = 1080, H = 1350, c = D.createElement('canvas'); c.width = Wd; c.height = H; var x = c.getContext('2d');
    function draw() {
      x.fillStyle = '#204E60'; x.fillRect(0, 0, Wd, H); x.strokeStyle = '#D4CC73'; x.lineWidth = 3; x.strokeRect(48, 48, Wd - 96, H - 96);
      x.fillStyle = '#D4CC73'; x.save(); x.translate(Wd / 2, 170); x.rotate(Math.PI / 4); x.fillRect(-13, -13, 26, 26); x.restore();
      var size = q.t.length > 330 ? 40 : q.t.length > 220 ? 46 : q.t.length > 120 ? 54 : 64, lines;
      x.fillStyle = '#EEEEE5'; x.textAlign = 'center'; x.textBaseline = 'middle';
      do { x.font = 'italic ' + size + 'px "Cita Pro",Georgia,serif'; lines = wrapText(x, '“' + q.t + '”', Wd - 240); size -= 2; } while (lines.length * (size * 1.42) > H - 560 && size > 26);
      var lh = (size + 2) * 1.42, y = H / 2 - ((lines.length - 1) * lh) / 2 - 30; lines.forEach(function (l, i) { x.fillText(l, Wd / 2, y + i * lh); });
      x.fillStyle = '#D4CC73'; x.fillRect(Wd / 2 - 60, H - 330, 120, 3);
      x.fillStyle = '#EEEEE5'; x.font = '600 30px "Plus Jakarta Sans",Arial,sans-serif'; x.fillText('Spirit of Islam', Wd / 2, H - 270);
      x.globalAlpha = .8; x.font = '26px "Plus Jakarta Sans",Arial,sans-serif'; x.fillText('Issue ' + q.n + ' · ' + q.p, Wd / 2, H - 225); x.globalAlpha = 1;
      c.toBlob(function (b) {
        var f = new File([b], 'spirit-of-islam-quote.png', { type: 'image/png' });
        if (navigator.canShare && navigator.canShare({ files: [f] })) { navigator.share({ files: [f] }).catch(function () {}); return; }
        var a = D.createElement('a'); a.href = URL.createObjectURL(b); a.download = f.name; D.body.appendChild(a); a.click(); a.remove(); toast('Picture saved');
      }, 'image/png');
    }
    (D.fonts && D.fonts.load ? D.fonts.load('italic 40px "Cita Pro"').then(draw, draw) : draw());
  }
  var quotesP = null;
  function quotes() { if (!quotesP) quotesP = fetch('/assets/quotes.json').then(function (r) { return r.json(); }); return quotesP; }
  function quoteOfDay() {
    return quotes().then(function (d) {
      var p = d.quotes.filter(function (q) { return q.t.length < 220; }), day = Math.floor(Date.now() / 864e5 - new Date().getTimezoneOffset() / 1440);
      return p[(day * 7919) % p.length];
    });
  }

  /* ---------- audio: one player for the whole app ----------
     The magazine block creates its own Audio element and fills navigator.mediaSession. Both are watched here so the
     mini player can show and control it from any screen. iPhone reads navigator.mediaSession itself for the lock
     screen (needs the "audio" background mode). Android shows no media notification from a web view, so the same
     information is passed to the MediaSession plugin, whose foreground service keeps audio playing when locked. */
  var MS = platform === 'android' ? plugin('MediaSession') : null;
  var audios = [], now = { audio: null, title: '', album: '', slug: '', id: '' }, handlers = {}, lastPos = 0, resumeAt = null;
  function ms(fn, a, b) { if (!MS) return; try { var p = MS[fn](a, b); if (p && p.catch) p.catch(function () {}); } catch (e) {} }
  function pos() { var a = now.audio; if (!MS || !a || !isFinite(a.duration) || !a.duration) return; ms('setPositionState', { duration: a.duration, position: Math.min(a.currentTime, a.duration), playbackRate: a.playbackRate || 1 }); }
  function audioItem(a) {
    var src = a.currentSrc || a.src || '', hit = null;
    $$('#soi-app-read-body .ev-player audio[src]').forEach(function (t) { var s = t.getAttribute('src'); if (s && (src === s || src.slice(-s.length) === s)) hit = t.closest('.ev-item'); });
    return hit;
  }
  function hook(a) {
    audios.push(a);
    a.addEventListener('play', function () {
      now.audio = a; now.slug = reader.slug; var it = audioItem(a); if (it) { now.id = it.id.replace(/^soi-/, ''); var t = $('.ev-tab-title', it); if (t) now.title = t.textContent.trim(); }
      ms('setPlaybackState', { playbackState: 'playing' }); pos(); emit('soi-audio');
    });
    a.addEventListener('pause', function () { ms('setPlaybackState', { playbackState: 'paused' }); pos(); remember(true); emit('soi-audio'); });
    a.addEventListener('ended', function () { var it = audioItem(a); if (it && reader.slug) mem.markRead(reader.slug, it.id.replace(/^soi-/, '')); emit('soi-audio'); });
    a.addEventListener('timeupdate', function () { var n = Date.now(); if (n - lastPos > 1000) { lastPos = n; if (n % 5000 < 1000) pos(); remember(false); emit('soi-audio-time'); } });
    ['loadedmetadata', 'ratechange', 'seeked'].forEach(function (ev) { a.addEventListener(ev, pos); });
    a.addEventListener('loadedmetadata', function () {             /* Continue reading: take the audio back to where it was paused */
      if (!resumeAt) return; var it = audioItem(a);
      if (it && it.id === 'soi-' + resumeAt.id && a.currentTime < 2 && resumeAt.t < (a.duration || 1e9) - 5) { try { a.currentTime = resumeAt.t; } catch (e) {} }
      if (it) resumeAt = null;
    });
  }
  (function patchAudio() {
    var A = W.Audio; if (!A) return;
    function SoiAudio(src) { var a = src === undefined ? new A() : new A(src); hook(a); return a; }
    SoiAudio.prototype = A.prototype; SoiAudio.soi = true; W.Audio = SoiAudio;
    if (!('mediaSession' in navigator)) return;
    var nms = navigator.mediaSession, set = nms.setActionHandler.bind(nms);
    nms.setActionHandler = function (action, h) { handlers[action] = h; try { set(action, h); } catch (e) {} ms('setActionHandler', { action: action }, h ? function (d) { h(d || { action: action }); } : null); };
    var d = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(nms), 'metadata');
    if (d && d.set) Object.defineProperty(nms, 'metadata', {
      configurable: true, get: function () { return d.get.call(nms); },
      set: function (m) {
        if (m) { now.title = m.title || now.title; now.album = m.album || now.album; }
        var art = now.slug ? [{ src: location.origin + '/assets/covers/' + now.slug + '.webp', sizes: '600x850', type: 'image/webp' }] : [];
        try { if (m && art.length) m.artwork = art; } catch (e) {}
        d.set.call(nms, m); if (m) ms('setMetadata', { title: m.title, artist: m.artist, album: m.album, artwork: art }); emit('soi-audio');
      }
    });
    ms('setActionHandler', { action: 'play' }, function () { if (now.audio) now.audio.play(); });
    ms('setActionHandler', { action: 'pause' }, function () { if (now.audio) now.audio.pause(); });
    ms('setActionHandler', { action: 'seekto' }, function (x) { if (now.audio && x && x.seekTime != null) now.audio.currentTime = x.seekTime; });
  })();
  function stopAudio() { audios.forEach(function (a) { try { a.pause(); } catch (e) {} }); now.audio = null; ms('setPlaybackState', { playbackState: 'none' }); emit('soi-audio'); }
  var player = {
    state: function () { var a = now.audio; return a && (a.currentSrc || a.src) ? { playing: !a.paused && !a.ended, t: a.currentTime || 0, dur: isFinite(a.duration) ? a.duration : 0, title: now.title, album: now.album, slug: now.slug, id: now.id } : null; },
    toggle: function () { var a = now.audio; if (!a) return; if (a.paused) a.play().catch(function () {}); else a.pause(); },
    jump: function (d) { var h = handlers[d < 0 ? 'seekbackward' : 'seekforward']; if (h) h({}); else if (now.audio) now.audio.currentTime = Math.max(0, now.audio.currentTime + d); },
    stop: stopAudio
  };

  /* ---------- screens and transitions ---------- */
  var TABS = ['home', 'search', 'saved', 'profile'], screens = {}, views = {}, cur = null, navSeq = 0;
  function parse(url) {
    var u = new URL(url || location.href, location.href), q = {}; u.searchParams.forEach(function (v, k) { q[k] = v; });
    var s = q.s || 'home'; delete q.s; if (u.hash) q.hash = u.hash.slice(1);
    return { s: s, q: q };
  }
  function urlOf(s, q) {
    var p = new URLSearchParams(); if (s !== 'home') p.set('s', s);
    var hash = ''; Object.keys(q || {}).forEach(function (k) { if (k === 'hash') hash = '#' + q[k]; else if (q[k] != null && q[k] !== '') p.set(k, q[k]); });
    var qs = p.toString(); return location.pathname + (qs ? '?' + qs : '') + hash;
  }
  function link(s, q) { return urlOf(s, q); }
  function depth(s) { return TABS.indexOf(s) >= 0 ? 0 : s === 'read' ? 2 : 1; }
  function go(s, q, opt) {
    opt = opt || {}; q = q || {};
    var url = urlOf(s, q), st = { n: (history.state && history.state.n || 0) + (opt.replace ? 0 : 1) };
    if (opt.replace) realReplace(st, '', url); else history.pushState(st, '', url);
    show({ s: s, q: q }, opt.replace ? 'none' : (depth(s) > 0 ? 'push' : 'tab'));
  }
  function back() { if (history.state && history.state.n > 0) history.back(); else go('home', {}, { replace: true }); }
  W.addEventListener('popstate', function () { var r = parse(); show(r, depth(r.s) < depth(cur ? cur.s : 'home') || (cur && cur.s === r.s) ? 'pop' : depth(r.s) === 0 ? 'tab' : 'push'); });
  function show(r, kind) {
    if (!screens[r.s]) r = { s: 'home', q: {} };
    var seq = ++navSeq, prev = cur;
    function swap() {
      if (prev && views[prev.s]) { views[prev.s].dataset.y = String(W.scrollY); views[prev.s].hidden = true; if (screens[prev.s].leave) screens[prev.s].leave(); }
      var v = views[r.s];
      if (!v) { v = views[r.s] = D.createElement('section'); v.className = 'soi-app-view soi-app-view-' + r.s; v.dataset.view = r.s; v.setAttribute('aria-label', screens[r.s].title || r.s); $('#soi-app-views').appendChild(v); if (screens[r.s].init) screens[r.s].init(v); }
      v.hidden = false; cur = r; readerShown = r.s === 'read';
      D.body.dataset.screen = r.s; D.body.classList.toggle('soi-app-notabs', !!screens[r.s].full);
      $$('#soi-app-tabs a').forEach(function (a) { var on = a.dataset.tab === r.s; if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
      var keep = kind === 'pop' || (kind === 'tab' && prev && prev.s !== r.s);
      if (screens[r.s].show) screens[r.s].show(v, r.q, { back: kind === 'pop' });
      realScrollTo(0, keep && r.s !== 'read' ? +(v.dataset.y || 0) : r.s === 'read' ? W.scrollY : 0);
      if (r.s === 'read') realScrollTo(0, +(v.dataset.y || 0));
      mini();
    }
    var motionOk = !W.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (D.startViewTransition && prev && kind !== 'none' && motionOk && !(prev.s === r.s)) {
      root.dataset.nav = kind;
      var t = D.startViewTransition(swap);
      t.finished.then(function () { if (seq === navSeq) delete root.dataset.nav; }, function () {});
    } else swap();
    if (prev && prev.s !== r.s) tap();
    if (prev && kind !== 'none') setTimeout(function () { var h = $('[data-focus]', views[r.s]); if (h && seq === navSeq) h.focus({ preventScroll: true }); }, 380);
  }
  D.addEventListener('click', function (e) {                       /* links inside the app */
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var a = e.target.closest && e.target.closest('a[href]'); if (!a) return;
    var raw = a.getAttribute('href') || '';
    if (a.target === '_blank' || raw.charAt(0) === '#' || /^(mailto|tel):/.test(raw)) return;
    var u; try { u = new URL(a.href, location.href); } catch (x) { return; }
    if (u.origin !== location.origin) return;
    var m = u.pathname.match(/^\/issues\/([\w-]+)\/?(?:index\.html)?$/);
    e.preventDefault();
    if (m) { var q = { issue: m[1] }; if (u.hash) q.art = u.hash.replace(/^#soi-/, '').replace(/^#/, ''); if (u.searchParams.get('resume')) q.resume = 1; go('read', q); return; }
    if (u.pathname === '/' || /\/index\.html$/.test(u.pathname)) { var r = parse(u.href); if (a.dataset.tab && cur && cur.s === r.s) { realScrollTo({ top: 0, behavior: 'smooth' }); return; } go(r.s, r.q, { replace: a.hasAttribute('data-replace') || (depth(r.s) === 0 && cur && depth(cur.s) === 0) }); return; }
    if (u.pathname === '/archive/') go('library'); else if (u.pathname === '/quotes/') go('quotes'); else if (u.pathname === '/search/') go('search'); else W.open(CFG.remote + u.pathname + u.search + u.hash, '_blank');
  });

  /* ---------- bottom sheet (choices) ---------- */
  function sheet(title, text, choices) {
    return new Promise(function (ok) {
      var el = $('#soi-app-sheet'), prev = D.activeElement;
      el.innerHTML = '<div class="soi-app-sheet-back" data-x></div><div class="soi-app-sheet-box" role="dialog" aria-modal="true" aria-labelledby="soi-app-sheet-t"><span class="soi-app-grab" aria-hidden="true"></span>' +
        '<h2 id="soi-app-sheet-t">' + esc(title) + '</h2>' + (text ? '<p>' + esc(text) + '</p>' : '') +
        choices.map(function (c, k) { return '<button type="button" data-k="' + k + '" class="' + (c.kind || '') + '"><b>' + esc(c.label) + '</b>' + (c.note ? '<small>' + esc(c.note) + '</small>' : '') + '</button>'; }).join('') +
        '<button type="button" data-x class="is-cancel">Cancel</button></div>';
      el.hidden = false; requestAnimationFrame(function () { el.classList.add('is-on'); var b = $('button[data-k]', el); if (b) b.focus(); });
      function done(v) { el.classList.remove('is-on'); el.removeEventListener('click', click); D.removeEventListener('keydown', key); setTimeout(function () { el.hidden = true; el.innerHTML = ''; }, 260); if (prev && prev.focus) prev.focus(); ok(v); }
      function click(e) { var b = e.target.closest('[data-k],[data-x]'); if (!b) return; done(b.hasAttribute('data-x') ? null : choices[+b.dataset.k].value); }
      function key(e) { if (e.key === 'Escape') done(null); if (e.key === 'Tab') { var f = $$('button', el), i = f.indexOf(D.activeElement); e.preventDefault(); f[(i + (e.shiftKey ? f.length - 1 : 1)) % f.length].focus(); } }
      el.addEventListener('click', click); D.addEventListener('keydown', key);
    });
  }
  /* "Save for offline" on any issue: text only, or with its audio */
  function saveFlow(slug) {
    return issueOf(slug).then(function (it) {
      var n = it.audio || (index()[slug] || {}).of || 0;
      if (!n) { if (hasText(slug)) { toast('Already on this phone'); return; } toast('Saving for offline…'); return saveIssue(slug, false).then(function () { tap('ok'); toast('Saved for offline'); }, function () { toast('No internet – try again later'); }); }
      if (hasAudio(slug)) { toast('This issue and its audio are on this phone'); return; }
      var choices = [{ label: 'Text and audio', note: n + ' recordings · best on Wi-Fi', value: 'audio', kind: 'is-main' }];
      if (!hasText(slug)) choices.push({ label: 'Text only', note: mb(it.bytes || 400000), value: 'text' });
      return sheet('Save for offline', label(it) + (hasText(slug) ? ' is already on this phone. Add its audio?' : ''), choices).then(function (v) {
        if (!v) return;
        toast(v === 'audio' ? 'Saving text and audio…' : 'Saving for offline…');
        return saveIssue(slug, v === 'audio').then(function () { tap('ok'); toast(v === 'audio' ? 'Text and audio saved' : 'Saved for offline'); }, function (e) { toast(/cancel/.test(e.message) ? 'Stopped' : /could not/.test(e.message) ? e.message : 'No internet – try again later'); });
      });
    });
  }

  /* ---------- reading view ---------- */
  var IC = {
    back: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
    share: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V3M7.5 7.5 12 3l4.5 4.5M5 12v7a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-7"/></svg>',
    save: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>',
    down: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7.5 10.5 12 15l4.5-4.5M5 20h14"/></svg>',
    play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.2v13.6a.6.6 0 0 0 .9.5l11-6.8a.6.6 0 0 0 0-1L8.9 4.7a.6.6 0 0 0-.9.5z" fill="currentColor" stroke="none"/></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" fill="currentColor" stroke="none"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
  };
  var reader = { slug: '', urls: [], loading: null };
  function itemInfo(it) {
    var t = $('.ev-tab-title', it), m = ($('.ev-meta', it) || {}).textContent || '', mm = m.match(/(\d+)\s*min/);
    return { slug: reader.slug, id: it.id.replace(/^soi-/, ''), title: t ? t.textContent.trim() : '', label: reader.label || '', min: mm ? +mm[1] : 0, audio: !!$('.ev-player audio[src]', it) };
  }
  function currentItem() {
    var a = now.audio; if (a && !a.paused && now.slug === reader.slug) { var ai = audioItem(a); if (ai) return ai; }
    var open = $$('#soi-app-read-body .ev-item.is-open'), best = null, mid = W.innerHeight * 0.4;
    open.forEach(function (it) { var r = it.getBoundingClientRect(); if (r.top < mid && r.bottom > 80) best = it; });
    return best || open[0] || null;
  }
  var saveT = 0;
  function remember(force) {
    if (!reader.slug) return; var n = Date.now(); if (!force && n - saveT < 1200) return; saveT = n;
    var a = now.audio, playingHere = a && now.slug === reader.slug && a.currentTime > 0, it = readerShown ? currentItem() : (playingHere ? audioItem(a) : null);
    if (!it) return;
    var info = itemInfo(it), prev = mem.progress(), p = { slug: reader.slug, id: info.id, title: info.title, label: info.label, min: info.min, at: n };
    if (readerShown) {
      var body = $('.ev-body', it) || it, r = body.getBoundingClientRect();
      p.frac = +Math.max(0, Math.min(1, (W.innerHeight * 0.5 - r.top) / Math.max(1, r.height))).toFixed(3);
      p.off = Math.round(-it.getBoundingClientRect().top);
      if (p.frac > 0.92 && r.bottom < W.innerHeight * 0.9) mem.markRead(reader.slug, info.id);
    } else if (prev && prev.slug === p.slug && prev.id === p.id) { p.frac = prev.frac; p.off = prev.off; }
    if (playingHere && audioItem(a) === it) { p.t = Math.floor(a.currentTime); p.dur = Math.floor(a.duration || 0); if (p.dur) p.frac = Math.max(p.frac || 0, +(p.t / p.dur).toFixed(3)); }
    else if (prev && prev.slug === p.slug && prev.id === p.id && prev.t) { p.t = prev.t; p.dur = prev.dur; }
    LS.set('soiProgress', p);
  }
  W.addEventListener('scroll', function () { if (readerShown) remember(false); }, { passive: true });
  D.addEventListener('visibilitychange', function () { if (D.hidden) remember(true); });
  W.addEventListener('pagehide', function () { remember(true); });
  function articleButtons(scope) {
    $$('.ev-item', scope).forEach(function (it) {
      var m = $('.ev-meta', it); if (!m || $('.soi-acts', it)) return;
      var info = itemInfo(it), on = mem.hasArticle(reader.slug, info.id), box = D.createElement('div'); box.className = 'soi-acts';
      box.innerHTML = '<button type="button" class="soi-act-save" aria-pressed="' + on + '" aria-label="Save this article">' + IC.save + '<span>' + (on ? 'Saved' : 'Save') + '</span></button>' +
        '<button type="button" class="soi-act-share" aria-label="Share this article">' + IC.share + '<span>Share</span></button>';
      box.addEventListener('click', function (e) {
        var b = e.target.closest('button'); if (!b) return; e.stopPropagation();
        if (b.classList.contains('soi-act-share')) { share(info.title, '/issues/' + reader.slug + '/#soi-' + info.id); return; }
        var v = mem.toggleArticle(itemInfo(it)); b.setAttribute('aria-pressed', v); $('span', b).textContent = v ? 'Saved' : 'Save'; tap('ok'); toast(v ? 'Saved' : 'Removed from Saved');
      });
      m.appendChild(box);
    });
  }
  function unloadReader() {
    stopAudio(); audios.length = 0;
    reader.urls.forEach(function (u) { try { URL.revokeObjectURL(u); } catch (e) {} }); reader.urls = [];
    var b = $('#soi-app-read-body'); if (b) b.innerHTML = '';
    var g = D.getElementById('soi-gotop'); if (g) g.remove();
    reader.slug = '';
  }
  function runScripts(scope) {
    $$('script', scope).forEach(function (old) {
      var s = D.createElement('script'); s.textContent = old.textContent; old.parentNode.replaceChild(s, old);
    });
  }
  function openArticle(id, off) {
    var it = D.getElementById('soi-' + id); if (!it) return;
    if (!it.classList.contains('is-open')) { var tab = $('.ev-tab', it); if (tab) tab.click(); }
    var tries = 0;
    (function settle() {                                           /* the block animates the article open; land after it */
      var y = it.getBoundingClientRect().top + W.scrollY + (off || 0) - (off ? 0 : 64);
      realScrollTo(0, Math.max(0, y));
      if (++tries < 6) setTimeout(settle, 160);
    })();
  }
  screens.read = {
    title: 'Reading', full: true,
    init: function (v) {
      v.innerHTML = '<header class="soi-app-nav" id="soi-app-read-nav"><button type="button" class="soi-app-ib" data-back aria-label="Back">' + IC.back + '</button>' +
        '<b id="soi-app-read-title" aria-live="polite"></b><button type="button" class="soi-app-ib" data-share aria-label="Share this issue">' + IC.share + '</button></header>' +
        '<div id="soi-app-read-head"></div><div id="soi-app-read-state" role="status"></div><div id="soi-app-read-body"></div>';
      v.addEventListener('click', function (e) {
        if (e.target.closest('[data-back]')) { remember(true); back(); }
        else if (e.target.closest('[data-share]')) share(reader.label || 'Spirit of Islam', '/issues/' + reader.slug + '/');
        else if (e.target.closest('[data-offline]')) saveFlow(reader.slug);
        else if (e.target.closest('[data-retry]')) screens.read.show(v, parse().q, {});
      });
      W.addEventListener('soi-offline', function (e) { if (e.detail && e.detail.slug === reader.slug) screens.read.head(); });
    },
    head: function () {
      var slug = reader.slug || (cur && cur.q.issue); if (!slug) return;
      issueOf(slug).then(function (it) {
        reader.label = label(it); $('#soi-app-read-title').textContent = reader.label;
        var j = job(slug), st = j ? (j.state === 'audio' ? 'Saving audio ' + j.done + ' of ' + j.total : 'Saving…') : hasAudio(slug) ? 'Text and audio on this phone' : hasText(slug) ? (it.audio ? 'Text on this phone' : 'On this phone') : 'Save for offline';
        var done = !j && (hasAudio(slug) || (hasText(slug) && !it.audio));
        $('#soi-app-read-head').innerHTML = '<div class="soi-app-readhead">' + cover(it, false, true) + '<div><p class="soi-app-kick">' + esc(it.number ? 'Issue ' + it.number : 'Spirit of Islam') + '</p><h1 data-focus tabindex="-1">' + esc(it.period) + '</h1>' +
          '<p class="soi-app-sub">' + (it.articles || '') + ' articles' + (it.audio ? ' · ' + it.audio + ' with audio' : '') + (mem.readCount(slug) ? ' · ' + mem.readCount(slug) + ' read' : '') + '</p>' +
          '<button type="button" class="soi-app-chipbtn' + (done ? ' is-done' : '') + '" data-offline' + (j ? ' disabled' : '') + '>' + (done ? IC.check : IC.down) + '<span>' + esc(st) + '</span></button></div></div>';
      });
    },
    show: function (v, q) {
      var slug = /^[\w-]+$/.test(q.issue || '') ? q.issue : '', state = $('#soi-app-read-state'), body = $('#soi-app-read-body');
      if (!slug) { go('home', {}, { replace: true }); return; }
      var art = q.art || (q.hash ? q.hash.replace(/^soi-/, '') : ''), p = mem.progress(), res = q.resume && p && p.slug === slug ? p : null;
      if (res) { art = res.id; resumeAt = res.t ? { id: res.id, t: res.t } : null; }
      mem.day();
      if (reader.slug === slug && body.firstChild) {              /* already open (audio may be playing): just show it */
        screens.read.head(); state.innerHTML = '';
        if (art) setTimeout(function () { openArticle(art, res ? res.off : 0); }, 60);
        return;
      }
      if (reader.used && reader.used !== slug) {                /* the magazine block starts only once per page: a different issue gets a fresh page */
        remember(true); stopAudio(); if (art && !q.resume) realReplace(history.state, '', location.pathname + location.search + '#soi-' + art); location.reload(); return;
      }
      reader.slug = slug; body.innerHTML = ''; v.dataset.y = '0'; screens.read.head();
      state.innerHTML = '<div class="soi-app-skel" aria-label="Opening the issue"><i></i><i></i><i></i><i></i></div>';
      var mine = reader.loading = {};
      Promise.all([pageOf(slug), store.audioOf(slug)]).then(function (x) {
        if (reader.loading !== mine || reader.slug !== slug) return;
        var html = blockOf(x[0]); if (!html) throw new Error('not an issue page');
        var local = {}; x[1].forEach(function (r) { var u = URL.createObjectURL(r.blob); reader.urls.push(u); local[r.url] = u; });
        html = html.replace(/(<audio\b[^>]*\bsrc=")([^"]+)(")/g, function (m, a, src, c) { var k = src.replace(/&amp;/g, '&'); return a + (local[k] || absUrl(k)) + c; });
        if (art) realReplace(history.state, '', location.pathname + location.search + '#soi-' + art);
        body.innerHTML = html; state.innerHTML = ''; reader.used = slug;
        runScripts(body); articleButtons(body);
        if (!index()[slug] || !index()[slug].of) { var n = audioList(x[0]).length; if (n || hasText(slug)) setIndex(slug, { of: n }); }
        screens.read.head();
        if (art) setTimeout(function () { openArticle(art, res ? res.off : 0); if (res && res.t) toast('Audio continues from ' + mmss(res.t)); }, 120);
        if (!packed(slug)) manifest(true).then(function (list) {   /* quietly pick up a corrected version for next time */
          var it = list.filter(function (i) { return i.slug === slug; })[0];
          store.getIssue(slug).then(function (rec) { if (rec && it && it.v && it.v !== rec.v) fetchPage(slug).catch(function () {}); });
        });
      }).catch(function () {
        if (reader.loading !== mine) return; reader.slug = '';
        state.innerHTML = '<div class="soi-app-empty"><h2>This issue is not on your phone yet</h2><p>It needs an internet connection the first time. Once opened, it stays on the phone and can be read offline.</p>' +
          '<button type="button" class="soi-app-btn" data-retry>Try again</button> <a class="soi-app-btn is-quiet" href="' + link('saved') + '" data-replace>See saved issues</a></div>';
      });
    },
    leave: function () { remember(true); }
  };

  /* ---------- mini player (every screen except the article that is playing) ---------- */
  function mini() {
    var el = $('#soi-app-mini'), s = player.state(), hide = !s || (readerShown && s.slug === reader.slug);
    D.body.classList.toggle('soi-app-hasmini', !hide);
    if (hide) { el.hidden = true; return; }
    if (el.hidden || el.dataset.id !== s.slug + '/' + s.id) {
      el.dataset.id = s.slug + '/' + s.id;
      el.innerHTML = '<button type="button" class="soi-app-mini-open" aria-label="Open the article that is playing: ' + esc(s.title) + '">' + cover({ slug: s.slug }, false, true) +
        '<span><b>' + esc(s.title || 'Playing') + '</b><small>' + esc(s.album || '') + '</small></span></button>' +
        '<button type="button" class="soi-app-ib" data-mini="toggle"></button><button type="button" class="soi-app-ib" data-mini="stop" aria-label="Stop and close the player">' + IC.close + '</button>' +
        '<span class="soi-app-mini-bar" role="progressbar" aria-label="Audio position" aria-valuemin="0" aria-valuemax="100"><i></i></span>';
      el.hidden = false;
    }
    var b = $('[data-mini="toggle"]', el); b.innerHTML = s.playing ? IC.pause : IC.play; b.setAttribute('aria-label', s.playing ? 'Pause' : 'Play');
    var pct = s.dur ? Math.min(100, s.t / s.dur * 100) : 0; $('.soi-app-mini-bar i', el).style.transform = 'scaleX(' + (pct / 100).toFixed(4) + ')'; $('.soi-app-mini-bar', el).setAttribute('aria-valuenow', Math.round(pct));
  }
  W.addEventListener('soi-audio', mini); W.addEventListener('soi-audio-time', mini);

  /* ---------- start ---------- */
  function start() {
    $('#soi-app-mini').addEventListener('click', function (e) {
      var b = e.target.closest('[data-mini]');
      if (b) { if (b.dataset.mini === 'toggle') player.toggle(); else { remember(true); player.stop(); } tap(); return; }
      if (e.target.closest('.soi-app-mini-open')) { var s = player.state(); if (s) go('read', { issue: s.slug, art: s.id }); }
    });
    if (AppP && AppP.addListener) {
      AppP.addListener('backButton', function () { if (!$('#soi-app-sheet').hidden) { var x = $('#soi-app-sheet [data-x]'); if (x) x.click(); } else if (history.state && history.state.n > 0) history.back(); else if (cur && cur.s !== 'home') go('home', {}, { replace: true }); else AppP.exitApp(); });
      AppP.addListener('appUrlOpen', function (e) {               /* a shared article link opened on a phone that has the app */
        try { var u = new URL(e.url), m = u.pathname.match(/^\/issues\/([\w-]+)\/?$/); if (m) go('read', { issue: m[1], art: u.hash.replace(/^#soi-/, '').replace(/^#/, '') }); } catch (x) {}
      });
    }
    var r = parse(); realReplace({ n: 0 }, '', location.href); show(r, 'none');
    root.classList.add('soi-app-ready');
    if (Splash) { try { Splash.hide({ fadeOutDuration: 250 }).catch(function () {}); } catch (e) {} }
    manifest(true);
  }
  W.soiApp = {
    screens: screens, go: go, back: back, link: link, parse: parse, esc: esc, $: $, $$: $$, LS: LS, IC: IC, toast: toast, tap: tap, sheet: sheet, cover: cover, label: label, shortPeriod: shortPeriod, mb: mb, mmss: mmss,
    cfg: function () { return CFG; }, manifest: manifest, issueOf: issueOf, mem: mem, share: share, quotes: quotes, quoteOfDay: quoteOfDay, quoteImage: quoteImage,
    offline: { index: index, job: job, save: saveIssue, saveFlow: saveFlow, removeAudio: removeAudio, removeIssue: removeIssue, hasText: hasText, hasAudio: hasAudio, packed: packed, used: storageUsed },
    player: player, prefs: function () { return prefs; }, setPref: setPref, isDark: isDark, native: native,
    route: function (href) { var u = new URL(href, location.href), m = u.pathname.match(/^\/issues\/([\w-]+)\//); return m ? link('read', { issue: m[1], art: u.hash.replace(/^#soi-/, '') }) : null; }
  };
  fetch('/assets/app-config.json').then(function (r) { return r.json(); }).then(function (c) { CFG = c; }).catch(function () {}).then(function () {
    if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', start); else start();
  });
})();
