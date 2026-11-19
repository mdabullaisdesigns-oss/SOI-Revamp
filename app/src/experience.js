/* Spirit of Islam app – the "experience" layer (19 Nov design round), joined onto app.js at build time.
   1. Welcome slides on the first launch, ending with sign-in (Google, Apple, email, or "Not now").
   2. Issue pages: full-bleed cover hero with glass back/share, a reading path (done / in progress / not started),
      a bottom bar (Play all, PDF), a mini player and a full-screen player, and the quiz on its own full page.
   3. Quotes: one quote at a time on a nature photo; Random in the middle, previous/next either side;
      listen, share as a picture, save, read the article. The full list is one tap away.
   Nature photos only (site/photos), no people. Everything prefixed soi. */
(function () {
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function LSget(k, d) { try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } }
  function LSset(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function remote() { var c = window.soiApp && window.soiApp.cfg ? window.soiApp.cfg() : {}; return (c && c.remote) || ''; }
  function abs(u) { return !u ? u : /^https?:/.test(u) ? u : remote() + u; }
  function mmss(t) { t = Math.max(0, Math.floor(t || 0)); return Math.floor(t / 60) + ':' + ('0' + t % 60).slice(-2); }
  function svg(d, cls) { return '<svg' + (cls ? ' class="' + cls + '"' : '') + ' viewBox="0 0 24 24" aria-hidden="true">' + d + '</svg>'; }
  var I = {
    back: svg('<path d="M15 5l-7 7 7 7"/>'), share: svg('<path d="M12 3v12M7 8l5-5 5 5"/><path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/>'),
    next: svg('<path d="M9 5l7 7-7 7"/>'), prev: svg('<path d="M15 5l-7 7 7 7"/>'), close: svg('<path d="M6 6l12 12M18 6 6 18"/>'), down: svg('<path d="M6 9l6 6 6-6"/>'),
    play: svg('<path class="f" d="M8 5v14l11-7z"/>'), pause: svg('<path class="f" d="M7 5h4v14H7zM13 5h4v14h-4z"/>'),
    shuffle: svg('<path d="M3 7h3.5c2.2 0 3.6 1 4.8 3l1.4 2.2c1.2 2 2.6 3 4.8 3H21M17.5 12 21 15.5 17.5 19M3 17h3.5c1.4 0 2.5-.4 3.4-1.3M14.1 8.3c.9-.9 2-1.3 3.4-1.3H21M17.5 3.5 21 7l-3.5 3.5"/>'),
    head: svg('<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/>'),
    save: svg('<path d="M6 3.5h12a1 1 0 0 1 1 1v16l-7-4.5-7 4.5v-16a1 1 0 0 1 1-1z"/>'), book: svg('<path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5zM12 6.5v13"/>'),
    list: svg('<path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01"/>'), pdf: svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>'),
    check: svg('<path d="M5 12l5 5 9-10"/>'), mail: svg('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>'),
    google: '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.5l6.7-6.7C35.6 2.4 30.2 0 24 0 14.6 0 6.6 5.4 2.6 13.2l7.8 6c1.9-5.6 7.2-9.7 13.6-9.7z"/><path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.6 5.9c4.4-4.1 7-10.1 7-17.6z"/><path fill="#FBBC05" d="M10.4 28.8c-.5-1.4-.8-3-.8-4.8s.3-3.3.8-4.8l-7.8-6C1 16.5 0 20.1 0 24s1 7.5 2.6 10.8z"/><path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.6-5.9c-2.1 1.4-4.9 2.3-8.3 2.3-6.4 0-11.8-4.3-13.7-10l-7.8 6C6.6 42.6 14.6 48 24 48z"/></svg>',
    apple: '<svg viewBox="0 0 17 20" aria-hidden="true"><path fill="currentColor" d="M14.1 10.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.4-.9C3.6 4.8 2 5.8 1.1 7.4c-1.8 3.2-.5 7.9 1.3 10.5.9 1.3 1.9 2.7 3.2 2.6 1.3-.1 1.8-.8 3.3-.8s2 .8 3.4.8c1.4 0 2.3-1.3 3.1-2.6 1-1.5 1.4-2.9 1.4-3-.1 0-2.7-1-2.7-4.3zM11.6 3c.7-.9 1.2-2 1.1-3.2-1 0-2.3.7-3 1.5-.7.8-1.2 2-1.1 3.1 1.2.1 2.3-.6 3-1.4z"/></svg>'
  };
  var LOGO = '<img src="/assets/brand/Peogen-logo.png" alt="" width="470" height="453"><span class="soi-x-rule"></span><img src="/assets/brand/soi-mark-white.svg" alt="Spirit of Islam" width="790" height="511">';
  function toast(t) { if (window.soi && window.soi.toast) window.soi.toast(t); }

  /* ================= 1. Welcome slides + sign-in ================= */
  var SLIDES = [
    { ph: 'hero', k: 'Spirit of Islam', t: 'A magazine for the journey of life', p: 'The English bimonthly of CPS International, inspired by the teachings of Maulana Wahiduddin Khan: peace, spirituality and positive thinking.' },
    { ph: 'quote-4', k: 'The archive', t: 'Every issue since 2013, in your pocket', p: 'Save any issue on your phone and read it without internet.' },
    { ph: 'guide2', k: 'Listen', t: 'Hear every article, read aloud', p: 'The text follows the voice, and it keeps playing with the screen off.' },
    { ph: 'quote-7', k: 'Reflect', t: 'Wisdom to keep and to share', p: 'Quotes on beautiful pictures, a short quiz after each issue, and gems as you grow.' }
  ];
  function welcome(force) {
    if (!force && LSget('soiWelcomed', 0)) return;
    var w = document.createElement('div'); w.id = 'soi-x-welcome'; w.setAttribute('role', 'dialog'); w.setAttribute('aria-label', 'Welcome to Spirit of Islam');
    var n = SLIDES.length, at = 0, timer = null;
    w.innerHTML = SLIDES.map(function (s, k) {
      return '<section class="soi-x-slide" data-k="' + k + '"><div class="soi-x-ph" style="background-image:url(/assets/photos/' + s.ph + '.webp)"></div>' +
        '<div class="soi-x-txt"><span class="soi-x-k">' + esc(s.k) + '</span><h2>' + esc(s.t) + '</h2><p>' + esc(s.p) + '</p></div></section>';
    }).join('') +
      '<section class="soi-x-slide soi-x-sign" data-k="' + n + '"><div class="soi-x-ph" style="background-image:url(/assets/photos/quote-5.webp)"></div>' +
      '<div class="soi-x-txt"><span class="soi-x-logo">' + LOGO + '</span><h2>Assalamu alaikum</h2><p>Sign in to keep your progress, saved articles and gems on every phone and on the website.</p>' +
      '<a class="soi-x-sbtn is-w" href="/profile.html?signin=google">' + I.google + 'Continue with Google</a>' +
      '<a class="soi-x-sbtn is-w" href="/profile.html?signin=apple">' + I.apple + 'Continue with Apple</a>' +
      '<a class="soi-x-sbtn is-d" href="/profile.html?signin=email">' + I.mail + 'Continue with email</a>' +
      '<button type="button" class="soi-x-notnow">Not now – just read</button></div></section>' +
      '<div class="soi-x-bars">' + SLIDES.map(function () { return '<i><b></b></i>'; }).join('') + '</div>' +
      '<button type="button" class="soi-x-skip">Skip</button>' +
      '<div class="soi-x-nav"><button type="button" class="soi-x-back" aria-label="Back">' + I.prev + '</button><button type="button" class="soi-x-go"><span>Continue</span><i>' + I.next + '</i></button></div>';
    document.body.appendChild(w); document.documentElement.classList.add('soi-x-lock');
    function done() { LSset('soiWelcomed', 1); clearTimeout(timer); w.classList.add('is-out'); document.documentElement.classList.remove('soi-x-lock'); setTimeout(function () { w.remove(); }, 500); }
    function show(k) {
      at = Math.max(0, Math.min(n, k)); clearTimeout(timer);
      $$('.soi-x-slide', w).forEach(function (s, j) { s.classList.toggle('is-on', j === at); s.classList.toggle('is-past', j < at); });
      $$('.soi-x-bars i', w).forEach(function (b, j) { b.className = j < at ? 'is-done' : j === at ? 'is-on' : ''; });
      w.classList.toggle('is-last', at === n); w.classList.toggle('is-first', at === 0);
      $('.soi-x-go span', w).textContent = at === n - 1 ? 'Get started' : 'Continue';
      if (at < n) timer = setTimeout(function () { show(at + 1); }, 6000);
    }
    w.addEventListener('click', function (e) {
      if (e.target.closest('.soi-x-go')) show(at + 1);
      else if (e.target.closest('.soi-x-back')) show(at - 1);
      else if (e.target.closest('.soi-x-skip')) show(n);
      else if (e.target.closest('.soi-x-notnow')) done();
      else if (e.target.closest('.soi-x-sbtn')) LSset('soiWelcomed', 1);
    });
    var x0 = null;
    w.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    w.addEventListener('touchend', function (e) { if (x0 == null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null; if (Math.abs(dx) > 50) show(at + (dx < 0 ? 1 : -1)); });
    requestAnimationFrame(function () { show(0); });
  }

  /* ================= 2. Issue pages ================= */
  function issuePage(meta) {
    var slug = meta.content, label = meta.getAttribute('data-label') || '', ev = $('.soi-ev');
    if (!ev || $('#soi-x-hero')) return;
    document.documentElement.classList.add('soi-x-issue');
    var head = $('.soi-issue-head'), kicker = head ? ($('.soi-kicker', head) || {}).textContent || '' : '', title = head ? ($('h1', head) || {}).firstChild : null;
    title = title ? title.textContent : label;
    var items = $$('.ev-item', ev), audioN = items.filter(function (it) { return $('audio', it); }).length;
    var year = (label.match(/(19|20)\d\d/) || [''])[0];
    var hero = document.createElement('section'); hero.id = 'soi-x-hero';
    hero.innerHTML = '<div class="soi-x-hph" style="background-image:url(/assets/covers/' + slug + '@2x.webp),url(/assets/covers/' + slug + '.webp)"></div>' +
      '<div class="soi-x-htop"><button type="button" class="soi-x-glass soi-x-hback" aria-label="Back">' + I.back + '</button><span class="soi-x-hlogo"><img src="/assets/brand/Peogen-logo.png" alt=""></span>' +
      '<button type="button" class="soi-x-glass soi-x-hshare" aria-label="Share this issue">' + I.share + '</button></div>' +
      '<div class="soi-x-htxt"><span>' + esc(kicker) + '</span><h1>' + esc(title) + '</h1><p>' + items.length + ' articles' + (audioN ? ' · ' + audioN + ' with audio' : '') + '</p></div>';
    var sheet = document.createElement('div'); sheet.id = 'soi-x-sheet';
    sheet.innerHTML = '<div class="soi-x-grab"></div><div class="soi-x-chips">' + (year ? '<a href="/archive/#y' + year + '">' + year + ' issues</a>' : '') + '<a href="/archive/">All issues</a><a href="#soi-quiz" class="soi-x-qz">Quiz</a></div>' +
      '<div class="soi-x-ptitle"><b>Your path through this issue</b><span id="soi-x-pcount"></span></div>';
    var main = $('main') || document.body, first = $('.soi-issue') || ev;
    main.insertBefore(hero, main.firstChild);
    first.parentNode.insertBefore(sheet, first);
    /* fixed bar that turns solid after the hero */
    var fbar = document.createElement('div'); fbar.id = 'soi-x-fbar';
    fbar.innerHTML = '<button type="button" class="soi-x-glass soi-x-hback" aria-label="Back">' + I.back + '</button><b>' + esc(kicker ? kicker + ' · ' : '') + esc(title) + '</b><button type="button" class="soi-x-glass soi-x-hshare" aria-label="Share this issue">' + I.share + '</button>';
    document.body.appendChild(fbar);
    function onScroll() { fbar.classList.toggle('is-on', window.scrollY > hero.offsetHeight - 70); }
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
    $$('.soi-x-hback').forEach(function (b) { b.addEventListener('click', function () { if (history.length > 1) history.back(); else location.href = '/index.html'; }); });
    $$('.soi-x-hshare').forEach(function (b) { b.addEventListener('click', function () { if (window.soi) window.soi.share(label, '/issues/' + slug + '/'); }); });
    /* reading path: done / in progress / not started */
    function paint() {
      var read = (LSget('soiRead', {})[slug]) || {}, p = LSget('soiProgress', null), done = 0;
      items.forEach(function (it) {
        var id = it.id.replace(/^soi-/, ''), st = read[id] ? 'done' : (p && p.slug === slug && p.id === id ? 'now' : '');
        if (st === 'done') done++;
        it.setAttribute('data-x', st);
        var dot = $('.soi-x-dot', it); if (!dot) { dot = document.createElement('span'); dot.className = 'soi-x-dot'; dot.setAttribute('aria-hidden', 'true'); it.insertBefore(dot, it.firstChild); }
        dot.innerHTML = st === 'done' ? I.check : '';
      });
      var c = $('#soi-x-pcount'); if (c) c.textContent = done + ' of ' + items.length + ' done';
    }
    paint(); setInterval(paint, 4000);
    ev.classList.add('soi-x-path');
    /* bottom bar: Play all + PDF */
    var dock = document.createElement('div'); dock.id = 'soi-x-dock';
    dock.innerHTML = '<button type="button" class="soi-x-playall">' + I.play + '<span>Play all</span></button><a class="soi-x-pdf" href="#" hidden>' + I.pdf + '<span>PDF</span></a>';
    document.body.appendChild(dock); document.body.classList.add('soi-x-has-dock');
    if (window.soiApp) window.soiApp.manifest(false).then(function (l) { var it = l.filter(function (x) { return x.slug === slug; })[0]; if (it && it.pdf) { var a = $('.soi-x-pdf', dock); a.href = abs(it.pdf); a.hidden = false; } }).catch(function () {});
    $('.soi-x-playall', dock).addEventListener('click', function () {
      if (cur && !cur.paused) { cur.pause(); return; }
      if (cur) { cur.play(); return; }
      var read = (LSget('soiRead', {})[slug]) || {};
      var t = items.filter(function (it) { return $('audio', it) && !read[it.id.replace(/^soi-/, '')]; })[0] || items.filter(function (it) { return $('audio', it); })[0];
      if (!t) return;
      var tab = $('.ev-tab', t); if (tab && tab.getAttribute('aria-expanded') !== 'true') tab.click();
      setTimeout(function () { var b = $('.ev-pl-play', t); if (b) b.click(); }, 350);
    });
    player(items, slug, title, dock);
    quizFull();
  }

  /* mini player + full-screen player, following whichever article audio is playing */
  var cur = null;
  function player(items, slug, issueTitle, dock) {
    var mini = document.createElement('div'); mini.id = 'soi-x-mini'; mini.hidden = true;
    mini.innerHTML = '<span class="soi-x-mcv" style="background-image:url(/assets/covers/' + slug + '.webp)"></span><span class="soi-x-mt"><b></b><small></small></span>' +
      '<button type="button" class="soi-x-mpp" aria-label="Play or pause">' + I.pause + '</button><i class="soi-x-mbar"></i>';
    var full = document.createElement('div'); full.id = 'soi-x-full'; full.hidden = true;
    full.innerHTML = '<div class="soi-x-fbg" style="background-image:url(/assets/covers/' + slug + '.webp)"></div>' +
      '<div class="soi-x-ftop"><button type="button" class="soi-x-fclose" aria-label="Close player">' + I.down + '</button><small>NOW PLAYING · ' + esc(issueTitle.toUpperCase()) + '</small><button type="button" class="soi-x-fshare" aria-label="Share">' + I.share + '</button></div>' +
      '<div class="soi-x-fcv" style="background-image:url(/assets/covers/' + slug + '@2x.webp),url(/assets/covers/' + slug + '.webp)"></div>' +
      '<div class="soi-x-ft"><small></small><b></b></div>' +
      '<div class="soi-x-wave">' + Array.apply(null, Array(36)).map(function (_, k) { return '<i style="height:' + (8 + Math.round(26 * Math.abs(Math.sin(k * 1.7) * Math.cos(k * .6)))) + 'px"></i>'; }).join('') + '</div>' +
      '<input type="range" class="soi-x-seek" min="0" max="1000" value="0" aria-label="Position"><div class="soi-x-times"><span>0:00</span><span>0:00</span></div>' +
      '<div class="soi-x-ctl"><button type="button" class="soi-x-prev" aria-label="Previous article">' + I.prev + '</button><button type="button" class="soi-x-b15" aria-label="Back 15 seconds">15</button>' +
      '<button type="button" class="soi-x-big" aria-label="Play or pause">' + I.pause + '</button><button type="button" class="soi-x-f15" aria-label="Forward 15 seconds">15</button><button type="button" class="soi-x-next" aria-label="Next article">' + I.next + '</button></div>' +
      '<div class="soi-x-row"><button type="button" class="soi-x-speed">1×</button><button type="button" class="soi-x-read">' + I.book + 'Read along</button></div>';
    document.body.appendChild(mini); document.body.appendChild(full);
    var curItem = null;
    function itemOf(a) { return a.closest('.ev-item'); }
    function info() {
      if (!curItem) return;
      var t = ($('.ev-tab-title', curItem) || {}).textContent || '', k = ($('.ev-kicker', curItem) || {}).textContent || '';
      $('.soi-x-mt b', mini).textContent = t; $('.soi-x-ft b', full).textContent = t; $('.soi-x-ft small', full).textContent = k.toUpperCase();
    }
    function tick() {
      if (!cur) return; var d = cur.duration || 0, p = d ? cur.currentTime / d : 0;
      $('.soi-x-mbar', mini).style.width = (p * 100) + '%'; $('.soi-x-mt small', mini).textContent = mmss(cur.currentTime) + ' / ' + mmss(d);
      if (!full.hidden) {
        if (!seeking) $('.soi-x-seek', full).value = Math.round(p * 1000);
        var ts = $$('.soi-x-times span', full); ts[0].textContent = mmss(cur.currentTime); ts[1].textContent = '-' + mmss(d - cur.currentTime);
        $$('.soi-x-wave i', full).forEach(function (w, j, all) { w.classList.toggle('on', j / all.length <= p); });
      }
    }
    function state() {
      var on = cur && !cur.paused;
      $('.soi-x-mpp', mini).innerHTML = on ? I.pause : I.play; $('.soi-x-big', full).innerHTML = on ? I.pause : I.play;
      full.classList.toggle('is-playing', !!on);
      var pa = $('.soi-x-playall', dock); if (pa) pa.innerHTML = (on ? I.pause : I.play) + '<span>' + (on ? 'Pause' : cur ? 'Resume' : 'Play all') + '</span>';
    }
    document.addEventListener('play', function (e) {
      var a = e.target; if (!a || a.tagName !== 'AUDIO' || !itemOf(a)) return;
      cur = a; curItem = itemOf(a); mini.hidden = false; document.body.classList.add('soi-x-has-mini'); info(); state(); tick();
    }, true);
    ['pause', 'ended'].forEach(function (n) { document.addEventListener(n, function (e) { if (e.target === cur) state(); }, true); });
    document.addEventListener('timeupdate', function (e) { if (e.target === cur) tick(); }, true);
    function btn(sel, fn) { $(sel, full).addEventListener('click', fn); }
    $('.soi-x-mpp', mini).addEventListener('click', function (e) { e.stopPropagation(); if (cur) { if (cur.paused) cur.play(); else cur.pause(); } });
    mini.addEventListener('click', function () { full.hidden = false; document.documentElement.classList.add('soi-x-lock'); requestAnimationFrame(function () { full.classList.add('is-open'); }); tick(); });
    function close() { full.classList.remove('is-open'); document.documentElement.classList.remove('soi-x-lock'); setTimeout(function () { full.hidden = true; }, 350); }
    btn('.soi-x-fclose', close);
    btn('.soi-x-big', function () { if (cur) { if (cur.paused) cur.play(); else cur.pause(); } });
    btn('.soi-x-b15', function () { if (cur) cur.currentTime = Math.max(0, cur.currentTime - 15); });
    btn('.soi-x-f15', function () { if (cur) cur.currentTime = Math.min(cur.duration || 0, cur.currentTime + 15); });
    var SP = [1, 1.25, 1.5, 1.75, 2, 0.75];
    btn('.soi-x-speed', function () { if (!cur) return; var k = (SP.indexOf(cur.playbackRate) + 1) % SP.length; cur.playbackRate = SP[k]; this.textContent = SP[k] + '×'; });
    function jump(dir) {
      if (!curItem) return; var list = items.filter(function (it) { return $('audio', it); }), k = list.indexOf(curItem) + dir, t = list[k]; if (!t) return;
      if (cur) cur.pause(); var tab = $('.ev-tab', t); if (tab && tab.getAttribute('aria-expanded') !== 'true') tab.click();
      setTimeout(function () { var b = $('.ev-pl-play', t); if (b) b.click(); }, 350);
    }
    btn('.soi-x-prev', function () { jump(-1); }); btn('.soi-x-next', function () { jump(1); });
    btn('.soi-x-read', function () { close(); if (curItem) setTimeout(function () { curItem.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 360); });
    btn('.soi-x-fshare', function () { if (window.soi && curItem) window.soi.share(($('.ev-tab-title', curItem) || {}).textContent || issueTitle, '/issues/' + slug + '/#' + curItem.id); });
    var seek = $('.soi-x-seek', full), seeking = false;
    seek.addEventListener('input', function () { seeking = true; });
    seek.addEventListener('change', function () { seeking = false; if (cur && cur.duration) cur.currentTime = seek.value / 1000 * cur.duration; });
    var y0 = null;
    full.addEventListener('touchstart', function (e) { if (e.target.closest('input')) return; y0 = e.touches[0].clientY; }, { passive: true });
    full.addEventListener('touchend', function (e) { if (y0 != null && e.changedTouches[0].clientY - y0 > 90) close(); y0 = null; });
  }

  /* the quiz on its own full page */
  function quizFull() {
    var q = $('#soi-quiz'); if (!q || $('.soi-x-qclose')) return;
    var inv = $('.z-invite', q), x = document.createElement('button'); x.type = 'button'; x.className = 'soi-x-qclose'; x.setAttribute('aria-label', 'Close quiz'); x.innerHTML = I.close;
    q.appendChild(x);
    function open() { document.documentElement.classList.add('soi-x-quiz', 'soi-x-lock'); q.scrollTop = 0; LSset('soiQuizDay', new Date().toISOString().slice(0, 10)); }
    function shut() { document.documentElement.classList.remove('soi-x-quiz', 'soi-x-lock'); if (inv && inv.getAttribute('aria-expanded') === 'true') inv.click(); q.scrollIntoView({ block: 'start' }); }
    if (inv) inv.addEventListener('click', function () { setTimeout(function () { if (inv.getAttribute('aria-expanded') === 'true') open(); else document.documentElement.classList.remove('soi-x-quiz', 'soi-x-lock'); }, 30); });
    x.addEventListener('click', shut);
    var qz = $('.soi-x-qz'); if (qz) qz.addEventListener('click', function (e) { e.preventDefault(); if (inv && inv.getAttribute('aria-expanded') !== 'true') inv.click(); else open(); });
  }

  /* ================= 3. Quotes, one at a time ================= */
  function quotesPage() {
    if ($('#soi-x-quote')) return;
    var box = document.createElement('section'); box.id = 'soi-x-quote';
    box.innerHTML = '<div class="soi-x-qbg"></div><div class="soi-x-qbg soi-x-qbg2"></div><div class="soi-x-qshade"></div>' +
      '<div class="soi-x-qtop"><button type="button" class="soi-x-glass soi-x-qback" aria-label="Back">' + I.back + '</button><div class="soi-x-qtopics" role="tablist"></div><button type="button" class="soi-x-glass soi-x-qlist" aria-label="All quotes as a list">' + I.list + '</button></div>' +
      '<div class="soi-x-qmid"><span class="soi-x-qmark">' + svg('<path d="M5 6.5A1.5 1.5 0 0 1 6.5 5h2A1.5 1.5 0 0 1 10 6.5V11c0 3.4-1.5 5.8-4.6 7.2M14 6.5A1.5 1.5 0 0 1 15.5 5h2A1.5 1.5 0 0 1 19 6.5V11c0 3.4-1.5 5.8-4.6 7.2M5 11h5M14 11h5"/>') + '</span>' +
      '<blockquote class="soi-x-qt"></blockquote><p class="soi-x-qhd"></p><a class="soi-x-qsrc" href="#"></a></div>' +
      '<div class="soi-x-qctl"><button type="button" class="soi-x-glass soi-x-qprev" aria-label="Previous quote">' + I.prev + '</button>' +
      '<button type="button" class="soi-x-qrand" aria-label="A random quote">' + I.shuffle + '<span>Random</span></button>' +
      '<button type="button" class="soi-x-glass soi-x-qnext" aria-label="Next quote">' + I.next + '</button></div>' +
      '<div class="soi-x-qacts"><button type="button" class="soi-x-qlisten">' + I.head + '<span>Listen</span></button><button type="button" class="soi-x-qshare">' + I.share + '<span>Share</span></button>' +
      '<button type="button" class="soi-x-qsave">' + I.save + '<span>Save</span></button><a class="soi-x-qread" href="#">' + I.book + '<span>Article</span></a></div>';
    document.body.appendChild(box); document.documentElement.classList.add('soi-x-qmode', 'soi-x-lock'); LSset('soiQuoteDay', new Date().toISOString().slice(0, 10));
    var all = [], list = [], photos = [], at = 0, topic = '', hist = [], audio = null, flip = false;
    function hash(q) { var h = 0, s = q.s + q.a + q.t; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }
    function photo(q) { return photos.length ? photos[hash(q) % photos.length] : ''; }
    function draw(q, dir) {
      if (!q) return;
      var bgs = $$('.soi-x-qbg', box); flip = !flip; var on = bgs[flip ? 1 : 0], off = bgs[flip ? 0 : 1];
      on.style.backgroundImage = 'url(' + photo(q) + ')'; on.classList.add('is-on'); off.classList.remove('is-on');
      var mid = $('.soi-x-qmid', box); mid.classList.remove('is-in', 'from-l', 'from-r'); void mid.offsetWidth; mid.classList.add('is-in', dir < 0 ? 'from-l' : 'from-r');
      var t = q.t.replace(/^\s*["“”']+|["“”']+\s*$/g, '');
      var qt = $('.soi-x-qt', box); qt.textContent = t; qt.className = 'soi-x-qt' + (t.length > 260 ? ' is-xl' : t.length > 150 ? ' is-l' : '');
      $('.soi-x-qhd', box).textContent = q.hd === 'saying' ? '— Prophet Muhammad ﷺ' + (q.ref ? ' (' + q.ref + ')' : '') : '';
      var src = $('.soi-x-qsrc', box); src.innerHTML = I.book + '<span>' + esc((q.hd === 'saying' ? 'Quoted in “' : '“') + q.at + '” · ' + q.p) + '</span>';
      src.href = '/issues/' + q.s + '/#soi-' + q.a; $('.soi-x-qread', box).href = src.href;
      var saved = window.soi && window.soi.store.hasQuote(q); $('.soi-x-qsave', box).classList.toggle('is-on', !!saved); $('.soi-x-qsave span', box).textContent = saved ? 'Saved' : 'Save';
      $('.soi-x-qlisten', box).hidden = !q.au; stopAudio();
    }
    function curQ() { return list[at]; }
    function go(k, dir) { if (!list.length) return; at = (k + list.length) % list.length; draw(curQ(), dir); }
    function random() { if (!list.length) return; var k; do { k = Math.floor(Math.random() * list.length); } while (list.length > 1 && k === at); hist.push(at); go(k, 1); }
    function filter(tp) {
      topic = tp; list = tp ? all.filter(function (q) { return (q.tp || []).indexOf(tp) >= 0; }) : all.slice();
      $$('.soi-x-qtopics button', box).forEach(function (b) { b.setAttribute('aria-selected', b.getAttribute('data-t') === tp ? 'true' : 'false'); });
      random();
    }
    function stopAudio() { if (audio) { audio.pause(); audio = null; } $('.soi-x-qlisten', box).classList.remove('is-on'); $('.soi-x-qlisten span', box).textContent = 'Listen'; }
    fetch('/assets/quotes.json').then(function (r) { return r.json(); }).then(function (d) {
      all = d.quotes.filter(function (q) { return q.t && q.t.length < 420; }); photos = d.photos || [];
      $('.soi-x-qtopics', box).innerHTML = '<button type="button" role="tab" data-t="" aria-selected="true">All</button>' + (d.topics || []).map(function (t) { return '<button type="button" role="tab" data-t="' + esc(t) + '" aria-selected="false">' + esc(t) + '</button>'; }).join('');
      list = all.slice();
      var day = Math.floor(Date.now() / 864e5); at = day % list.length; draw(curQ(), 1);
    }).catch(function () { $('.soi-x-qt', box).textContent = 'Quotes could not load. Please check your internet.'; });
    box.addEventListener('click', function (e) {
      var t = e.target.closest('button,a'); if (!t) return;
      if (t.classList.contains('soi-x-qprev')) go(at - 1, -1);
      else if (t.classList.contains('soi-x-qnext')) go(at + 1, 1);
      else if (t.classList.contains('soi-x-qrand')) { t.classList.remove('spin'); void t.offsetWidth; t.classList.add('spin'); random(); }
      else if (t.getAttribute('role') === 'tab') filter(t.getAttribute('data-t'));
      else if (t.classList.contains('soi-x-qback')) { if (history.length > 1) history.back(); else location.href = '/index.html'; }
      else if (t.classList.contains('soi-x-qlist')) { stopAudio(); document.documentElement.classList.remove('soi-x-qmode', 'soi-x-lock'); box.hidden = true; showOpen(); }
      else if (t.classList.contains('soi-x-qshare')) { var q = curQ(); if (q && window.soi) window.soi.quoteImage(q, photo(q)); }
      else if (t.classList.contains('soi-x-qsave')) { var q2 = curQ(); if (q2 && window.soi) { var on = window.soi.store.toggleQuote(q2); t.classList.toggle('is-on', !!on); $('span', t).textContent = on ? 'Saved' : 'Save'; toast(on ? 'Quote saved' : 'Removed from saved'); } }
      else if (t.classList.contains('soi-x-qlisten')) {
        if (audio) { stopAudio(); return; }
        var q3 = curQ(); if (!q3 || !q3.au) return;
        audio = new Audio(abs(q3.au)); var a0 = q3.a0 || 0, a1 = q3.a1 || 0;
        audio.addEventListener('loadedmetadata', function () { if (a0) audio.currentTime = a0; });
        audio.addEventListener('timeupdate', function () { if (a1 && audio && audio.currentTime >= a1) stopAudio(); });
        audio.addEventListener('ended', stopAudio);
        audio.play().catch(function () { stopAudio(); toast('Audio needs internet'); });
        t.classList.add('is-on'); $('span', t).textContent = 'Stop';
      }
    });
    var x0 = null, y0 = null;
    box.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    box.addEventListener('touchend', function (e) {
      if (x0 == null || e.target.closest('.soi-x-qtopics')) { x0 = null; return; }
      var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null;
      if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) go(at + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
    });
    function showOpen() {                                  /* list mode: a floating button returns to one-at-a-time */
      if ($('#soi-x-qopen')) { $('#soi-x-qopen').hidden = false; return; }
      var b = document.createElement('button'); b.type = 'button'; b.id = 'soi-x-qopen'; b.innerHTML = I.shuffle + '<span>One at a time</span>';
      b.addEventListener('click', function () { b.hidden = true; box.hidden = false; document.documentElement.classList.add('soi-x-qmode', 'soi-x-lock'); });
      document.body.appendChild(b);
    }
  }

  /* ================= start ================= */
  window.soiExp = function () {
    var meta = $('meta[name="soi-issue"]'), screen = document.body && document.body.getAttribute('data-screen');
    if (meta) issuePage(meta);
    else if (/^\/quotes\/(index\.html)?$/.test(location.pathname)) quotesPage();
    if (screen === 'home') { var f = /[?&]welcome=1/.test(location.search); welcome(f); }
  };
  window.soiWelcome = function () { welcome(true); };
})();
