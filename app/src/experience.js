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

  /* ================= 1. Welcome slides + sign-in =================
     One teal colour throughout. The logo first, then four illustrated slides that animate in,
     then sign-in. No Skip: readers go through every slide; "Not now – just read" is on the sign-in page. */
  var COV = ['2026-07', '2026-09', '2026-11'];
  function wave(n) { return '<span class="soi-w-wave">' + Array.apply(null, Array(n)).map(function (_, k) { return '<i style="height:' + (6 + Math.round(22 * Math.abs(Math.sin(k * 1.9) * Math.cos(k * .7)))) + 'px;animation-delay:' + (k % 5) * .12 + 's"></i>'; }).join('') + '</span>'; }
  function welcome(force) {
    if (!force && LSget('soiWelcomed', 0)) return;
    var w = document.createElement('div'); w.id = 'soi-x-welcome'; w.setAttribute('role', 'dialog'); w.setAttribute('aria-label', 'Welcome to Spirit of Islam');
    var arts = [
      '<div class="soi-w-logo"><img class="soi-w-dove" src="/assets/brand/Peogen-logo.png" alt=""><span class="soi-w-line"></span><img class="soi-w-mark" src="/assets/brand/soi-mark-white.svg" alt="Spirit of Islam">' +
        '<p class="soi-w-tag">Towards Global Peace &amp; Spiritual Living</p><p class="soi-w-type"><span>Read · Listen · Reflect</span></p></div>',
      '<div class="soi-w-stack">' + COV.map(function (c, k) { return '<span class="soi-w-cv s' + k + '" style="background-image:url(/assets/covers/' + c + '.webp)"></span>'; }).join('') + '</div>',
      '<div class="soi-w-listen"><span class="soi-w-cv" style="background-image:url(/assets/covers/' + COV[2] + '.webp)"></span><b>The Superior Solution</b>' + wave(15) + '<span class="soi-w-pp">' + I.pause + '</span></div>',
      '<div class="soi-w-quotes"><div class="soi-w-q a"><span>❝</span><p class="soi-w-qt1">A mistake turns into a virtue when it gives rise to humility within a person.</p><small>Share as a picture ›</small></div><div class="soi-w-q b"><span>❝</span><p class="soi-w-qt2">&nbsp;</p></div></div>',
      '<div class="soi-w-grow"><span class="soi-w-ring"><svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="50"/><circle class="soi-w-rf" cx="60" cy="60" r="50"/></svg><b>72%</b></span><span class="soi-w-gem">' + svg('<path d="M6.5 3.5h11l4 5.5L12 20.5 2.5 9z"/><path d="M2.5 9h19M9 3.5 7.5 9 12 20.5 16.5 9 15 3.5"/>') + '+40 gems this week</span></div>'
    ];
    var heads = [
      ['', ''],
      ['The archive', 'Every issue since 2013, in your pocket', 'Save any issue on your phone and read it without internet.'],
      ['Listen', 'Listen to every article', 'The text follows the voice, and it keeps playing with the screen off.'],
      ['Reflect', 'Wisdom to share', 'Quotes on beautiful pictures to keep and send to the people you love.'],
      ['Grow', 'Grow a little every day', 'Your progress, a short quiz after each issue, and gems as you go.']
    ];
    var n = arts.length;
    w.innerHTML = arts.map(function (art, k) {
      var h = heads[k];
      return '<section class="soi-x-slide' + (k === 0 ? ' soi-w-first' : '') + '"><div class="soi-w-panel"><div class="soi-w-art">' + art + '</div>' +
        (h[1] ? '<div class="soi-w-txt"><span class="soi-x-k">' + h[0] + '</span><h2>' + h[1] + '</h2><p>' + h[2] + '</p></div>' : '') + '</div></section>';
    }).join('') +
      '<section class="soi-x-slide soi-x-sign"><div class="soi-w-panel"><div class="soi-w-art"><div class="soi-w-logo is-small"><img class="soi-w-dove" src="/assets/brand/Peogen-logo.png" alt=""><span class="soi-w-line"></span><img class="soi-w-mark" src="/assets/brand/soi-mark-white.svg" alt="Spirit of Islam"></div></div>' +
      '<div class="soi-w-txt"><h2>Assalamu alaikum</h2><p>Sign in to keep your progress, saved articles and gems on every phone and on the website.</p>' +
      '<a class="soi-x-sbtn is-w" href="/profile.html?signin=google">' + I.google + 'Continue with Google</a>' +
      '<a class="soi-x-sbtn is-w" href="/profile.html?signin=apple">' + I.apple + 'Continue with Apple</a>' +
      '<a class="soi-x-sbtn is-d" href="/profile.html?signin=email">' + I.mail + 'Continue with email</a>' +
      '<button type="button" class="soi-x-notnow">Not now – just read</button></div></div></section>' +
      '<div class="soi-x-bars">' + arts.map(function () { return '<i><b></b></i>'; }).join('') + '</div>' +
      '<div class="soi-x-nav"><button type="button" class="soi-x-back" aria-label="Previous">' + I.prev + '</button><button type="button" class="soi-x-go">Continue</button><button type="button" class="soi-x-fwd" aria-label="Next">' + I.next + '</button></div>';
    document.body.appendChild(w); document.documentElement.classList.add('soi-x-lock');
    var at = 0, timer = null;
    fetch('/assets/quotes.json').then(function (r) { return r.json(); }).then(function (d) {    /* two real, short quotes */
      var short = d.quotes.filter(function (q) { return q.t.length < 60 && q.t.length > 25 && !q.hd; }); if (short.length < 2) return;
      var k = Math.floor(Date.now() / 864e5) % short.length;
      $('.soi-w-qt1', w).textContent = short[k].t; $('.soi-w-qt2', w).textContent = short[(k + 7) % short.length].t;
    }).catch(function () {});
    fetch('/issues.json').then(function (r) { return r.json(); }).then(function (j) {          /* the real number of issues */
      var c = (j.issues || []).length; if (c > 20) $('.soi-x-slide:nth-child(2) h2', w).textContent = c + ' issues since 2013, in your pocket';
    }).catch(function () {});
    function done() { LSset('soiWelcomed', 1); clearTimeout(timer); w.classList.add('is-out'); document.documentElement.classList.remove('soi-x-lock'); setTimeout(function () { w.remove(); }, 500); }
    function show(k) {
      at = Math.max(0, Math.min(n, k)); clearTimeout(timer);
      $$('.soi-x-slide', w).forEach(function (s, j) { s.classList.toggle('is-on', j === at); });
      $$('.soi-x-bars i', w).forEach(function (b, j) { b.className = j < at ? 'is-done' : j === at ? 'is-on' : ''; });
      w.classList.toggle('is-last', at === n); w.classList.toggle('is-first', at === 0);
      $('.soi-x-go', w).textContent = at === 0 ? 'Begin' : at === n - 1 ? 'Get started' : 'Continue';
      if (at < n) timer = setTimeout(function () { show(at + 1); }, at === 0 ? 4200 : 6500);
    }
    w.addEventListener('click', function (e) {
      if (e.target.closest('.soi-x-go') || e.target.closest('.soi-x-fwd')) show(at + 1);
      else if (e.target.closest('.soi-x-back')) show(at - 1);
      else if (e.target.closest('.soi-x-notnow')) done();
      else if (e.target.closest('.soi-x-sbtn')) LSset('soiWelcomed', 1);
    });
    var x0 = null;
    w.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    w.addEventListener('touchend', function (e) { if (x0 == null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null; if (Math.abs(dx) > 50) show(at + (dx < 0 ? 1 : -1)); });
    requestAnimationFrame(function () { show(0); });
  }

  /* ================= 2. Issue pages (light) =================
     Nature cover photo with a curved edge, the year's issues on the curve, title + issue number,
     tabs with icons (Read & Listen · Audio only · PDF · Quiz), article cards whose number sits inside a
     progress ring, a mini player with a close button, and the full player. */
  function artFrac(slug) { return (LSget('soiArtFrac', {})[slug]) || {}; }
  function setFrac(slug, id, f) { var m = LSget('soiArtFrac', {}); m[slug] = m[slug] || {}; if ((m[slug][id] || 0) < f) { m[slug][id] = Math.round(f * 100) / 100; LSset('soiArtFrac', m); } }
  function ring(n, f, done) {
    var C = 2 * Math.PI * 17, off = C * (1 - (done ? 1 : f));
    return '<span class="soi-x-ring' + (done ? ' is-done' : f > 0 ? ' is-part' : '') + '"><svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="17"/><circle class="p" cx="20" cy="20" r="17" style="stroke-dasharray:' + C.toFixed(1) + ';stroke-dashoffset:' + off.toFixed(1) + '"/></svg>' +
      '<b>' + (done ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>' : n) + '</b></span>';
  }
  var ICT = {
    read: svg('<path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5zM12 6.5v13"/>'),
    audio: svg('<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/>'),
    pdf: svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>'),
    quiz: svg('<path d="M2.5 9 12 4.5 21.5 9 12 13.5z"/><path d="M6.5 11v4.5c1.5 1.5 3.4 2.2 5.5 2.2s4-.7 5.5-2.2V11M21.5 9v5"/>')
  };
  function issuePage(meta) {
    var slug = meta.content, label = meta.getAttribute('data-label') || '', ev = $('.soi-ev');
    if (!ev || $('#soi-x-hero')) return;
    document.documentElement.classList.add('soi-x-issue');
    var head = $('.soi-issue-head'), kicker = head ? ($('.soi-kicker', head) || {}).textContent || '' : '', h1 = head ? $('h1', head) : null;
    var title = h1 && h1.firstChild ? h1.firstChild.textContent.trim() : label, num = (kicker.match(/\d+/) || [''])[0];
    var items = $$('.ev-item', ev), withAudio = items.filter(function (it) { return $('audio', it); });
    var year = (label.match(/(19|20)\d\d/) || [''])[0];
    var hero = document.createElement('section'); hero.id = 'soi-x-hero';
    hero.innerHTML = '<div class="soi-x-hph" style="background-image:url(/assets/covers/' + slug + '@2x.webp),url(/assets/covers/' + slug + '.webp)"></div>' +
      '<div class="soi-x-htop"><button type="button" class="soi-x-wbtn soi-x-hback" aria-label="Back">' + I.back + '</button><span></span>' +
      '<button type="button" class="soi-x-wbtn soi-x-hshare" aria-label="Share this issue">' + I.share + '</button><button type="button" class="soi-x-wbtn soi-x-hsave" aria-label="Save this issue on the phone">' + I.save + '</button></div>' +
      '<div class="soi-x-years" aria-label="Other issues of ' + year + '"></div>';
    var sheet = document.createElement('div'); sheet.id = 'soi-x-sheet';
    sheet.innerHTML = '<p class="soi-x-src"><img src="/assets/brand/Peogen-logo.png" alt="">Spirit of Islam' + (year ? ' · ' + year : '') + '</p>' +
      '<div class="soi-x-trow"><h1>' + esc(title) + '</h1><span class="soi-x-badge">' + (num ? '<b>' + num + '</b><small>Issue</small>' : '') + '</span></div>' +
      '<p class="soi-x-meta">' + items.length + ' articles · ' + withAudio.length + ' to listen</p>' +
      '<div class="soi-x-tabs" role="tablist"><button type="button" role="tab" aria-selected="true" data-tab="read">' + ICT.read + 'Read &amp; Listen</button>' +
      '<button type="button" role="tab" aria-selected="false" data-tab="audio">' + ICT.audio + 'Audio only</button>' +
      '<a class="soi-x-tpdf" href="#" hidden>' + ICT.pdf + 'PDF</a><button type="button" data-tab="quiz">' + ICT.quiz + 'Quiz</button></div>' +
      '<div class="soi-x-alist" role="list" hidden></div>';
    var main = $('main') || document.body, first = $('.soi-issue') || ev;
    main.insertBefore(hero, main.firstChild);
    first.parentNode.insertBefore(sheet, first);
    var fbar = document.createElement('div'); fbar.id = 'soi-x-fbar';
    fbar.innerHTML = '<button type="button" class="soi-x-wbtn soi-x-hback" aria-label="Back">' + I.back + '</button><b>' + esc(title) + '</b><button type="button" class="soi-x-wbtn soi-x-hshare" aria-label="Share this issue">' + I.share + '</button>';
    document.body.appendChild(fbar);
    function onScroll() { fbar.classList.toggle('is-on', window.scrollY > hero.offsetHeight - 60); }
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
    $$('.soi-x-hback').forEach(function (b) { b.addEventListener('click', function () { if (history.length > 1) history.back(); else location.href = '/index.html'; }); });
    $$('.soi-x-hshare').forEach(function (b) { b.addEventListener('click', function () { if (window.soi) window.soi.share(label, '/issues/' + slug + '/'); }); });
    $('.soi-x-hsave', hero).addEventListener('click', function () {
      var b = this; if (!window.soiApp || !window.soiApp.download) return; toast('Saving for offline…');
      window.soiApp.download(slug).then(function () { b.classList.add('is-on'); toast('Saved on this phone'); }, function () { toast('No internet – try again later'); });
    });
    if (window.soiApp) window.soiApp.manifest(false).then(function (l) {
      var same = l.filter(function (x) { return (x.period || '').indexOf(year) >= 0; }).slice(-6), it = l.filter(function (x) { return x.slug === slug; })[0];
      $('.soi-x-years', hero).innerHTML = same.map(function (x) { return '<a href="/issues/' + x.slug + '/" class="' + (x.slug === slug ? 'is-on' : '') + '" aria-label="' + esc(x.period) + '" style="background-image:url(/assets/covers/' + x.slug + '.webp)"></a>'; }).join('') +
        '<a href="/archive/" class="soi-x-yall" aria-label="All issues">All</a>';
      if (it && it.pdf) { var a = $('.soi-x-tpdf', sheet); a.href = abs(it.pdf); a.hidden = false; }
    }).catch(function () {});
    function paint() {
      var read = (LSget('soiRead', {})[slug]) || {}, fr = artFrac(slug), p = LSget('soiProgress', null);
      items.forEach(function (it, k) {
        var id = it.id.replace(/^soi-/, ''), done = !!read[id], f = fr[id] || (p && p.slug === slug && p.id === id ? p.frac || 0 : 0);
        var n = $('.ev-num', it); if (n) { var key = (done ? 'd' : '') + Math.round(f * 50); if (n.getAttribute('data-k') !== key) { n.setAttribute('data-k', key); n.innerHTML = ring(('0' + (k + 1)).slice(-2), f, done); } }
        it.setAttribute('data-x', done ? 'done' : f > 0 ? 'now' : '');
      });
      $$('.soi-x-arow', sheet).forEach(function (r) { var it = document.getElementById(r.getAttribute('data-id')), k = items.indexOf(it), id = it.id.replace(/^soi-/, ''); $('.soi-x-anum', r).innerHTML = ring(('0' + (k + 1)).slice(-2), fr[id] || 0, !!read[id]); r.setAttribute('data-x', read[id] ? 'done' : ''); });
    }
    $('.soi-x-alist', sheet).innerHTML = withAudio.map(function (it) {
      var dd = $('[data-duration]', it), d = dd ? +dd.getAttribute('data-duration') || 0 : 0;
      return '<div class="soi-x-arow" role="listitem" data-id="' + it.id + '"><span class="soi-x-anum"></span><span class="soi-x-at"><small>' + esc(($('.ev-kicker', it) || {}).textContent || '') + '</small><b>' + esc(($('.ev-tab-title', it) || {}).textContent || '') + '</b></span>' +
        '<span class="soi-x-adur">' + (d ? mmss(d) : '') + '</span><button type="button" class="soi-x-aplay" aria-label="Play">' + I.play + '</button></div>';
    }).join('');
    paint(); setInterval(paint, 3000);
    ev.classList.add('soi-x-cards');
    $('.soi-x-tabs', sheet).addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return; var t = b.getAttribute('data-tab');
      if (t === 'quiz') { var inv = $('#soi-quiz .z-invite'); if (inv && inv.getAttribute('aria-expanded') !== 'true') inv.click(); else document.documentElement.classList.add('soi-x-quiz', 'soi-x-lock'); return; }
      $$('button[role="tab"]', this).forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      $('.soi-x-alist', sheet).hidden = t !== 'audio'; document.documentElement.classList.toggle('soi-x-audioonly', t === 'audio');
    });
    $('.soi-x-alist', sheet).addEventListener('click', function (e) { var r = e.target.closest('.soi-x-arow'); if (r) playItem(document.getElementById(r.getAttribute('data-id')), true); });
    player(items, withAudio, slug, title, num, label);
    quizFull();
  }

  /* ----- the player. The page's own player makes the sound (one Audio element); this follows it and drives it ----- */
  var cur = null, openFull = function () {}, playItem = function () {};
  var PLPH = ['quote-4', 'guide2', 'topic-patience', 'quote-1', 'guide1', 'topic-peace', 'quote-2', 'hero', 'quote-6', 'topic-gratitude'];
  function player(items, withAudio, slug, issueTitle, num, label) {
    var cover = remote() + '/assets/covers/' + slug + '.webp';
    var mini = document.createElement('div'); mini.id = 'soi-x-mini'; mini.hidden = true;
    mini.innerHTML = '<span class="soi-x-mcv" style="background-image:url(/assets/covers/' + slug + '.webp)"></span><span class="soi-x-mt"><b></b><small></small></span>' +
      '<button type="button" class="soi-x-mpp" aria-label="Play or pause">' + I.pause + '</button><button type="button" class="soi-x-mx" aria-label="Stop and close">' + I.close + '</button><i class="soi-x-mbar"></i>';
    var full = document.createElement('div'); full.id = 'soi-x-full'; full.hidden = true;
    full.innerHTML = '<div class="soi-x-pbg"></div>' +
      '<div class="soi-x-ftop"><button type="button" class="soi-x-fclose" aria-label="Close player">' + I.down + '</button><small>' + (num ? 'Issue ' + num + ' · ' : '') + esc(issueTitle) + '</small><button type="button" class="soi-x-fshare" aria-label="Share">' + I.share + '</button></div>' +
      '<div class="soi-x-lyr" aria-live="polite"><div class="soi-x-lyr-in"></div></div>' +
      '<div class="soi-x-car"><div class="soi-x-car-in"></div></div>' +
      '<div class="soi-x-ft"><small></small><b></b><span></span></div>' +
      '<button type="button" class="soi-x-readbtn" aria-pressed="false"><span class="soi-x-rb-ic">' + svg('<path d="M4 6h16M4 10h16M4 14h10M4 18h7"/>') + '</span><span class="soi-x-rb-t"><b>Read along</b><small>See the words as they are spoken</small></span><i class="soi-x-sw"></i></button>' +
      '<div class="soi-x-prog"><input type="range" class="soi-x-seek" min="0" max="1000" value="0" aria-label="Position"><div class="soi-x-times"><span>0:00</span><span>0:00</span></div></div>' +
      '<div class="soi-x-ctl"><button type="button" class="soi-x-prev" aria-label="Previous article">' + svg('<path d="M18 6 9 12l9 6zM6 6v12"/>') + '</button><button type="button" class="soi-x-b15" aria-label="Back 15 seconds">' + svg('<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>') + '<i>15</i></button>' +
      '<button type="button" class="soi-x-big" aria-label="Play or pause">' + I.pause + '</button><button type="button" class="soi-x-f15" aria-label="Forward 15 seconds">' + svg('<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>') + '<i>15</i></button>' +
      '<button type="button" class="soi-x-next" aria-label="Next article">' + svg('<path d="m6 6 9 6-9 6zM18 6v12"/>') + '</button></div>' +
      '<div class="soi-x-row"><button type="button" class="soi-x-speed"><b>1×</b><small>Speed</small></button><button type="button" class="soi-x-timer"><b>' + svg('<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/>') + '</b><small>Sleep</small></button><button type="button" class="soi-x-goto"><b>' + svg('<path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5zM12 6.5v13"/>') + '</b><small>Article</small></button></div>' +
      '<div class="soi-x-sheet2" hidden><div class="soi-x-sh-in"><b class="soi-x-sh-t"></b><div class="soi-x-sh-opts"></div></div></div>';
    document.body.appendChild(mini); document.body.appendChild(full);
    var curItem = null, sents = [], lastS = -1;
    $('.soi-x-car-in', full).innerHTML = withAudio.map(function (it, k) {
      return '<button type="button" class="soi-x-card" data-k="' + k + '" aria-label="' + esc(($('.ev-tab-title', it) || {}).textContent || '') + '"><span class="soi-x-cimg" style="background-image:url(/assets/photos/' + PLPH[k % PLPH.length] + '.webp)"></span>' +
        '<span class="soi-x-cnum">' + ('0' + (items.indexOf(it) + 1)).slice(-2) + '</span><span class="soi-x-ckick">' + esc(($('.ev-kicker', it) || {}).textContent || '') + '</span></button>';
    }).join('');
    function idOfSrc(src) { var it = null; withAudio.some(function (x) { var a = $('audio', x), s = a && (a.getAttribute('src') || ''); if (s && src && (src === s || src.split('/').pop() === s.split('/').pop())) { it = x; return true; } }); return it; }
    function place() {
      var k = withAudio.indexOf(curItem);
      $$('.soi-x-card', full).forEach(function (c, j) { var d = j - k; c.style.setProperty('--d', d); c.classList.toggle('is-on', d === 0); c.hidden = Math.abs(d) > 2; });
      $('.soi-x-pbg', full).style.backgroundImage = 'url(/assets/photos/' + PLPH[Math.max(0, k) % PLPH.length] + '.webp)';
    }
    function info() {
      if (!curItem) return;
      var t = ($('.ev-tab-title', curItem) || {}).textContent || '', k = ($('.ev-kicker', curItem) || {}).textContent || '', who = (($('.ev-meta span', curItem) || {}).textContent || '');
      $('.soi-x-mt b', mini).textContent = t; $('.soi-x-ft b', full).textContent = t; $('.soi-x-ft small', full).textContent = k;
      $('.soi-x-ft span', full).textContent = (who && !/min/.test(who) ? who + ' · ' : '') + 'Article ' + (items.indexOf(curItem) + 1) + ' of ' + items.length;
      sents = $$('.ev-content .ev-s[data-t]', curItem).map(function (s) { return { t: +s.getAttribute('data-t'), x: s.textContent }; }); lastS = -1;
      place(); lyrics(true);
      try {                                                   /* lock screen: article title and the issue cover */
        if ('mediaSession' in navigator && window.MediaMetadata) setTimeout(function () { navigator.mediaSession.metadata = new MediaMetadata({ title: t, artist: 'Spirit of Islam', album: (num ? 'Issue ' + num + ' · ' : '') + label, artwork: [{ src: cover, sizes: '600x850', type: 'image/webp' }] }); }, 80);
      } catch (e) {}
    }
    function lyrics(force) {
      if (!cur || !full.classList.contains('is-read')) return;
      if (!sents.length) { $('.soi-x-lyr-in', full).innerHTML = '<p class="is-on">The words of this article appear here as they are read.</p>'; return; }
      var t = cur.currentTime, k = 0; for (var i = 0; i < sents.length; i++) { if (sents[i].t <= t) k = i; else break; }
      if (k === lastS && !force) return; lastS = k;
      var from = Math.max(0, k - 1);
      $('.soi-x-lyr-in', full).innerHTML = sents.slice(from, k + 4).map(function (s, j) { return '<p class="' + (from + j === k ? 'is-on' : from + j < k ? 'is-past' : '') + '">' + esc(s.x) + '</p>'; }).join('');
    }
    var seeking = false;
    function tick() {
      if (!cur) return; var d = isFinite(cur.duration) ? cur.duration : 0, p = d ? cur.currentTime / d : 0;
      $('.soi-x-mbar', mini).style.width = (p * 100) + '%'; $('.soi-x-mt small', mini).textContent = mmss(cur.currentTime) + (d ? ' / ' + mmss(d) : '');
      if (curItem && p > 0) setFrac(slug, curItem.id.replace(/^soi-/, ''), p > .97 ? 1 : p);
      if (!full.hidden) {
        var seek = $('.soi-x-seek', full);
        if (!seeking) { seek.value = Math.round(p * 1000); seek.style.setProperty('--p', (p * 100) + '%'); }
        var ts = $$('.soi-x-times span', full); ts[0].textContent = mmss(cur.currentTime); ts[1].textContent = d ? '-' + mmss(d - cur.currentTime) : '';
        lyrics();
      }
    }
    function state() {
      var on = !!(cur && !cur.paused && !cur.ended);
      if (mini.getAttribute('data-on') !== String(on)) { mini.setAttribute('data-on', on); $('.soi-x-mpp', mini).innerHTML = on ? I.pause : I.play; $('.soi-x-big', full).innerHTML = on ? I.pause : I.play; }
      full.classList.toggle('is-playing', on);
    }
    var bound = [];
    function adopt(a) {
      if (!a || a.tagName !== 'AUDIO') return;
      var it = a.closest ? a.closest('.ev-item') : null; it = it || idOfSrc(a.currentSrc || a.src); if (!it) return;
      if (cur && cur !== a && !cur.paused) cur.pause();
      cur = a; if (curItem !== it) { curItem = it; info(); }
      mini.hidden = false; document.body.classList.add('soi-x-has-mini');
      if (bound.indexOf(a) < 0) { bound.push(a); ['play', 'pause', 'ended', 'playing', 'waiting'].forEach(function (n) { a.addEventListener(n, function () { if (a === cur) state(); }); }); a.addEventListener('timeupdate', function () { if (a === cur) tick(); }); a.addEventListener('ended', function () { if (a === cur && !full.hidden && LSget('soiAutoNext', 1)) jump(1); }); }
      state(); tick();
    }
    document.addEventListener('play', function (e) { adopt(e.target); }, true);
    document.addEventListener('soi-audio-play', function (e) { adopt(e.detail); });
    setInterval(function () { if (cur) { state(); if (!document.hidden) tick(); } }, 700);    /* keeps the buttons true even when the lock screen controls are used */
    function sitePlay(it) {                                   /* press the article's own play button, so the page player, the lock screen and progress stay in step */
      var b = $('.ev-pl-play', it); if (b) { b.click(); return true; }
      var a = $('audio', it); if (a) { a.play().catch(function () { toast('Audio needs internet'); }); return true; }
      return false;
    }
    playItem = function (it, show) { if (!it) return; if (cur && !cur.paused) cur.pause(); curItem = it; info(); sitePlay(it); mini.hidden = false; document.body.classList.add('soi-x-has-mini'); if (show) openFull(); };
    openFull = function () { full.hidden = false; document.documentElement.classList.add('soi-x-lock'); requestAnimationFrame(function () { full.classList.add('is-open'); }); place(); tick(); lyrics(true); };
    function btn(sel, fn) { $(sel, full).addEventListener('click', fn); }
    function toggle() { if (!cur) { if (curItem) sitePlay(curItem); return; } if (cur.paused) cur.play().catch(function () {}); else cur.pause(); setTimeout(state, 60); }
    $('.soi-x-mpp', mini).addEventListener('click', function (e) { e.stopPropagation(); toggle(); });
    $('.soi-x-mx', mini).addEventListener('click', function (e) { e.stopPropagation(); if (cur) cur.pause(); mini.hidden = true; document.body.classList.remove('soi-x-has-mini'); });
    mini.addEventListener('click', openFull);
    function close() { full.classList.remove('is-open'); document.documentElement.classList.remove('soi-x-lock'); setTimeout(function () { full.hidden = true; }, 350); }
    btn('.soi-x-fclose', close);
    btn('.soi-x-big', toggle);
    btn('.soi-x-b15', function () { if (cur) cur.currentTime = Math.max(0, cur.currentTime - 15); });
    btn('.soi-x-f15', function () { if (cur) cur.currentTime = Math.min(cur.duration || 0, cur.currentTime + 15); });
    btn('.soi-x-prev', function () { jump(-1); }); btn('.soi-x-next', function () { jump(1); });
    btn('.soi-x-readbtn', function () { var on = full.classList.toggle('is-read'); this.setAttribute('aria-pressed', on); LSset('soiReadAlong', on ? 1 : 0); lastS = -1; lyrics(true); });
    if (LSget('soiReadAlong', 0)) { full.classList.add('is-read'); $('.soi-x-readbtn', full).setAttribute('aria-pressed', 'true'); }
    btn('.soi-x-goto', function () { close(); if (curItem) setTimeout(function () { var tab = $('.ev-tab', curItem); if (tab && tab.getAttribute('aria-expanded') !== 'true') tab.click(); curItem.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 360); });
    btn('.soi-x-fshare', function () { if (window.soi && curItem) window.soi.share(($('.ev-tab-title', curItem) || {}).textContent || issueTitle, '/issues/' + slug + '/#' + curItem.id); });
    /* a small sheet for Speed and Sleep, with words, so nobody has to guess what "1×" means */
    var sh = $('.soi-x-sheet2', full), sleepT = null;
    function choose(title, opts, onPick) {
      $('.soi-x-sh-t', sh).textContent = title;
      $('.soi-x-sh-opts', sh).innerHTML = opts.map(function (o, k) { return '<button type="button" data-k="' + k + '" aria-pressed="' + !!o[2] + '"><b>' + o[0] + '</b><small>' + o[1] + '</small></button>'; }).join('');
      sh.hidden = false; requestAnimationFrame(function () { sh.classList.add('is-open'); });
      sh.onclick = function (e) { var b = e.target.closest('button'); if (b) onPick(+b.getAttribute('data-k')); if (b || e.target === sh) { sh.classList.remove('is-open'); setTimeout(function () { sh.hidden = true; }, 250); } };
    }
    btn('.soi-x-speed', function () {
      var r = cur ? cur.playbackRate : 1, S = [[.75, 'Slower'], [1, 'Normal'], [1.25, 'A little faster'], [1.5, 'Faster'], [2, 'Twice as fast']];
      choose('Reading speed', S.map(function (x) { return [x[0] + '×', x[1], x[0] === r]; }), function (k) { if (cur) cur.playbackRate = S[k][0]; $('.soi-x-speed b', full).textContent = S[k][0] + '×'; });
    });
    btn('.soi-x-timer', function () {
      var T = [[0, 'Off'], [10, '10 minutes'], [20, '20 minutes'], [30, '30 minutes'], [-1, 'End of this article']];
      choose('Sleep timer', T.map(function (x) { return [x[1], x[0] > 0 ? 'Stop playing after ' + x[1] : x[0] < 0 ? 'Stop when this article ends' : 'Keep playing', false]; }), function (k) {
        clearTimeout(sleepT); LSset('soiAutoNext', T[k][0] < 0 ? 0 : 1); var bt = $('.soi-x-timer', full); bt.classList.toggle('is-on', T[k][0] !== 0);
        if (T[k][0] > 0) { sleepT = setTimeout(function () { if (cur) cur.pause(); bt.classList.remove('is-on'); }, T[k][0] * 60000); toast('Stops in ' + T[k][1]); }
        else if (T[k][0] < 0) toast('Stops at the end of this article');
      });
    });
    function jump(dir) { var k = withAudio.indexOf(curItem) + dir; if (withAudio[k]) playItem(withAudio[k], false); }
    $('.soi-x-car-in', full).addEventListener('click', function (e) { var c = e.target.closest('.soi-x-card'); if (!c) return; var k = +c.getAttribute('data-k'); if (withAudio[k] !== curItem) playItem(withAudio[k], false); });
    var seek = $('.soi-x-seek', full);
    seek.addEventListener('input', function () { seeking = true; seek.style.setProperty('--p', seek.value / 10 + '%'); });
    seek.addEventListener('change', function () { seeking = false; if (cur && cur.duration) cur.currentTime = seek.value / 1000 * cur.duration; });
    var x0 = null, y0 = null;
    full.addEventListener('touchstart', function (e) { if (e.target.closest('input,.soi-x-lyr')) { x0 = null; return; } x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    full.addEventListener('touchend', function (e) {
      if (x0 == null) return; var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null;
      if (dy > 110 && Math.abs(dx) < 60) close(); else if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) && e.target.closest('.soi-x-car')) jump(dx < 0 ? 1 : -1);
    });
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

  /* home: the top bar floats over the sky and takes its colour, so the two read as one */
  function homeTop() {
    var tries = 0;
    (function wait() {
      var sky = $('.soi-h-sky'), top = $('#soi-app-top');
      if (!sky || !top) { if (tries++ < 40) setTimeout(wait, 50); return; }
      document.documentElement.classList.add('soi-x-home'); document.documentElement.setAttribute('data-tod', sky.getAttribute('data-tod'));
      function on() { top.classList.toggle('is-solid', window.scrollY > 24); }
      window.addEventListener('scroll', on, { passive: true }); on();
    })();
  }

  /* ================= start ================= */
  window.soiExp = function () {
    var meta = $('meta[name="soi-issue"]'), screen = document.body && document.body.getAttribute('data-screen');
    if (meta) issuePage(meta);
    else if (/^\/quotes\/(index\.html)?$/.test(location.pathname)) quotesPage();
    if (screen === 'home') homeTop();
    if (screen === 'home') { var f = /[?&]welcome=1/.test(location.search); welcome(f); }
  };
  window.soiWelcome = function () { welcome(true); };
})();
