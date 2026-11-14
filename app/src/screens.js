/* Spirit of Islam app – the four tab screens and the gems page (approved canvas "SOI Redesign").
   Real on this phone: latest issue, Continue where you left, saved issues/articles/quotes, search, quote of the day.
   Sample data until sign-in exists (Firebase, later): the name, gems, rank, leaderboard and the reading dashboard. */
window.soiScreens = function () {
  var A = window.soiApp, S = window.soi, esc = A.esc, CFG = A.cfg();
  var screen = document.body.getAttribute('data-screen'), root = document.getElementById('soi-app-screen');
  if (!screen || !root) return;
  var SAMPLE = {
    name: 'Aisha', gems: 1240, rankWeek: 18, rankAll: 240, since: 'November 2026',
    streak: 12, finished: 34, listened: '5 h 20 m', quiz: '8.2 / 10', days: [1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    boards: {
      'This week': [['1', 'Yusuf', '2,980'], ['2', 'Maryam', '2,640'], ['3', 'Imran', '2,410'], ['…', '', ''], ['18', 'Aisha (you)', '1,240'], ['19', 'Sana', '1,210']],
      'This issue': [['1', 'Maryam', '410'], ['2', 'Bilal', '385'], ['3', 'Yusuf', '360'], ['…', '', ''], ['9', 'Aisha (you)', '245'], ['10', 'Hamza', '240']],
      'All time': [['1', 'Imran', '48,200'], ['2', 'Yusuf', '45,930'], ['3', 'Fatima', '44,100'], ['…', '', ''], ['240', 'Aisha (you)', '1,240'], ['241', 'Zaid', '1,235']]
    },
    earn: [['Finish an article (read or listen)', '+10'], ['Each correct quiz answer', '+5'], ['Quiz score 7 or more', '+20'], ['Daily reading streak', '+5 a day'], ['Finish a whole issue', '+50']]
  };
  var GEM = '<svg viewBox="0 0 24 24" aria-hidden="true" class="soi-gem"><path d="M12 2l4 6-4 14-4-14z"/><path d="M4 8h16l-8 14z" opacity=".6"/></svg>';
  var PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l13 8-13 8z"/></svg>';
  var SAVE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg>';
  var GUIDES = ['Listen with read-along', 'Save issues for offline', 'Earn gems with quizzes'];
  function short(p) { return p.replace(/January|February|March|April|June|July|August|September|October|November|December/g, function (m) { return m === 'June' || m === 'July' ? m.slice(0, 3) : m.slice(0, 3); }); }
  function lab(i) { return (i.number ? 'Issue ' + i.number + ' · ' : '') + short(i.period); }
  function cover(i, big) {
    return '<span class="soi-cover"><span class="soi-cover-fb" aria-hidden="true"><b>Spirit of Islam</b><i>' + esc(i.period) + '</i></span>' +
      '<img alt="" loading="lazy" src="/assets/covers/' + i.slug + (big ? '@2x' : '') + '.webp" onerror="if(this.dataset.f){this.remove()}else{this.dataset.f=1;this.src=\'/assets/covers/' + i.slug + '.webp\'}"></span>';
  }
  function sample(t) { return '<span class="soi-app-sample">' + (t || 'Sample') + '</span>'; }
  function soon(e) { if (e) e.preventDefault(); S.toast('Coming with sign-in'); }
  function offline(slug, have) { return CFG.bundled.indexOf(slug) >= 0 || !!have[slug]; }
  function haveMap() { return A.store.keys().then(function (k) { var h = {}; k.forEach(function (s) { h[s] = 1; }); return h; }); }
  function readCount(i) { var r = S.store.read()[i.slug] || {}; return Object.keys(r).length; }

  /* ================= Home ================= */
  function home() {
    root.innerHTML =
      '<div class="soi-app-top"><a class="soi-app-searchbar" href="/search.html?focus=1">' + '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg><span>Search “patience”</span></a>' +
      '<a class="soi-app-gempill" href="/gems.html" aria-label="Your gems (sample): ' + SAMPLE.gems.toLocaleString() + '">' + GEM + SAMPLE.gems.toLocaleString() + '</a></div>' +
      '<p class="soi-app-hello">Assalamu alaikum</p>' +
      '<div id="soi-app-cont"></div>' +
      '<div class="soi-app-hrow"><h2>Latest issue</h2><a href="/archive/">All issues</a></div>' +
      '<div class="soi-app-carousel" id="soi-app-latest"></div><div class="soi-app-dots" id="soi-app-dots" aria-hidden="true"></div>' +
      '<div class="soi-app-hrow"><h2>How to use SOI</h2></div>' +
      '<div class="soi-app-guides">' + GUIDES.map(function (g, k) { return '<div class="soi-app-guide"><span class="soi-ph soi-ph-wait soi-ph-' + k + '"></span><span class="soi-app-guide-play" aria-hidden="true">' + PLAY + '</span><b>' + esc(g) + '</b><small>Video coming soon</small></div>'; }).join('') + '</div>' +
      '<div class="soi-app-hrow"><h2>In this issue</h2></div><div class="soi-app-list" id="soi-app-arts"></div>' +
      '<div class="soi-app-quote" id="soi-app-qotd"><p class="soi-app-kick">Quote of the day</p><p class="soi-app-quote-t">&nbsp;</p><button type="button">Share as image →</button></div>';
    var p = S.store.progress();
    A.manifest(false).then(function (list) { draw(list); return A.manifest(true); }).then(draw).catch(function () {});
    function draw(list) {
      var latest = list.slice(-3).reverse(), first = latest[0];
      haveMap().then(function (have) {
        document.getElementById('soi-app-latest').innerHTML = latest.map(function (i) {
          var a0 = (i.arts || []).filter(function (a) { return a[4]; })[0];
          return '<div class="soi-app-issue" data-slug="' + i.slug + '">' + cover(i, true) +
            '<div class="soi-app-issue-btns"><a class="soi-app-b-read" href="/issues/' + i.slug + '/">Read</a>' +
            (a0 ? '<a class="soi-app-b-listen" href="/issues/' + i.slug + '/#soi-' + a0[0] + '">Listen</a>' : '') +
            '<button type="button" class="soi-app-b-save" aria-label="Save ' + esc(i.period) + ' for offline" aria-pressed="' + offline(i.slug, have) + '">' + SAVE + '</button></div></div>';
        }).join('');
        document.getElementById('soi-app-dots').innerHTML = latest.map(function (x, k) { return '<span' + (k ? '' : ' class="is-on"') + '></span>'; }).join('');
      });
      document.getElementById('soi-app-arts').innerHTML = (first.arts || []).slice(0, 4).map(function (a, k) {
        return '<a href="/issues/' + first.slug + '/#soi-' + a[0] + '"><span class="soi-app-n">' + (k + 1) + '</span><span class="soi-app-at"><small>' + esc(a[2] || 'Article') + '</small><b>' + esc(a[1]) + '</b></span><span class="soi-app-min">' + a[3] + ' min</span></a>';
      }).join('') + '<a class="soi-app-more" href="/issues/' + first.slug + '/">All ' + first.articles + ' articles →</a>';
      var c = document.getElementById('soi-app-cont');
      if (p) {
        var left = p.min ? Math.max(1, Math.round(p.min * (1 - (p.frac || 0)))) : 0, it = list.filter(function (x) { return x.slug === p.slug; })[0] || { slug: p.slug, period: '' };
        c.innerHTML = '<a class="soi-app-cont" href="/issues/' + p.slug + '/?resume=1#soi-' + p.id + '"><span class="soi-app-cont-row">' + cover(it) +
          '<span class="soi-app-cont-t"><small>Continue where you left</small><b>' + esc(p.title) + '</b><i>' + esc([p.label, left ? left + ' min left' : '', p.t ? 'paused at ' + S.mmss(p.t) : ''].filter(Boolean).join(' · ')) + '</i></span>' +
          '<span class="soi-app-cont-play" aria-hidden="true">' + PLAY + '</span></span><span class="soi-app-bar"><i style="width:' + Math.round((p.frac || 0) * 100) + '%"></i></span></a>';
      }
    }
    var car = document.getElementById('soi-app-latest');
    car.addEventListener('scroll', function () {
      var k = Math.round(car.scrollLeft / Math.max(1, car.clientWidth * 0.86));
      [].forEach.call(document.getElementById('soi-app-dots').children, function (d, j) { d.classList.toggle('is-on', j === k); });
    }, { passive: true });
    car.addEventListener('click', function (e) {
      var b = e.target.closest('.soi-app-b-save'); if (!b) return;
      var slug = b.closest('.soi-app-issue').dataset.slug;
      if (b.getAttribute('aria-pressed') === 'true') { S.toast('Already on this phone'); return; }
      b.disabled = true; S.toast('Saving for offline…');
      A.download(slug).then(function () { b.setAttribute('aria-pressed', 'true'); S.toast('Saved for offline'); }, function () { S.toast('No internet – try again later'); }).then(function () { b.disabled = false; });
    });
    S.quoteOfDay().then(function (q) {
      var box = document.getElementById('soi-app-qotd'); box.querySelector('.soi-app-quote-t').textContent = '“' + q.t + '”';
      box.querySelector('button').addEventListener('click', function () { S.quoteImage(q); });
    }).catch(function () {});
  }

  /* ================= Search ================= */
  function search() {
    var POP = ['The purpose of life', 'Patience', 'Peace and reconciliation', 'Your Questions Answered', 'The Word of God'];
    root.innerHTML =
      '<label class="soi-app-searchbox"><a href="/index.html" aria-label="Back"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12H5M11 6l-6 6 6 6"/></svg></a>' +
      '<input id="soi-app-q" type="search" enterkeyhint="search" autocomplete="off" aria-label="Search" placeholder="What would you like to read?"></label>' +
      '<button type="button" class="soi-app-quran"><span>51:56</span><b>Search by Quran reference</b><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 4l10 8-10 8z"/></svg></button>' +
      '<div id="soi-app-idle"><div id="soi-app-recent"></div><p class="soi-app-cap">Popular on SOI</p><div class="soi-app-pop">' +
      POP.map(function (q, k) { return '<button type="button" data-q="' + esc(q) + '"><span class="soi-ph soi-ph-wait soi-ph-' + (k % 4) + '"></span><b>' + esc(q) + '</b><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17 17L7 7M7 15V7h8"/></svg></button>'; }).join('') +
      '</div></div><div id="soi-app-results" aria-live="polite"></div>';
    var input = document.getElementById('soi-app-q'), idle = document.getElementById('soi-app-idle'), out = document.getElementById('soi-app-results'), pf = null, seq = 0, timer = 0;
    function recent() {
      var r = S.LS.get('soiRecent', []);
      document.getElementById('soi-app-recent').innerHTML = r.length ? '<p class="soi-app-cap">Recent</p><div class="soi-app-chips">' + r.map(function (q) { return '<button type="button" data-q="' + esc(q) + '">' + esc(q) + '</button>'; }).join('') + '</div>' : '';
    }
    function keep(q) { var r = S.LS.get('soiRecent', []).filter(function (x) { return x.toLowerCase() !== q.toLowerCase(); }); r.unshift(q); S.LS.set('soiRecent', r.slice(0, 6)); }
    function engine() { if (!pf) pf = import('/pagefind/pagefind.js').then(function (m) { return (m.options ? m.options({ baseUrl: '/' }) : Promise.resolve()).then(function () { return m; }); }); return pf; }
    function run(q, remember) {
      q = q.trim().replace(/(\d{1,3})\s*:\s*(\d{1,3})/g, '$1:$2'); var my = ++seq;
      if (!q) { idle.hidden = false; out.innerHTML = ''; return; }
      idle.hidden = true; if (!out.innerHTML) out.innerHTML = '<p class="soi-app-cap">Searching…</p>';
      engine().then(function (m) { return m.search(q); }).then(function (r) {
        return Promise.all(r.results.slice(0, 25).map(function (x) { return x.data(); })).then(function (d) { return { n: r.results.length, d: d }; });
      }).then(function (r) {
        if (my !== seq) return;
        if (remember && r.n) { keep(q); recent(); }
        out.innerHTML = '<p class="soi-app-cap">' + (r.n ? r.n + (r.n === 1 ? ' article' : ' articles') : 'Nothing found for “' + esc(q) + '”') + '</p>' + r.d.map(function (x) {
          return '<a class="soi-app-res" href="' + esc(x.url) + '"><b>' + esc(x.meta.title) + '</b><small>' + esc(x.meta.issue || '') + '</small><span>' + x.excerpt + '</span></a>';
        }).join('');
      }).catch(function () { if (my === seq) out.innerHTML = '<p class="soi-app-cap">Search could not start. Please try again.</p>'; });
    }
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(function () { run(input.value, false); }, 220); });
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { clearTimeout(timer); run(input.value, true); input.blur(); } });
    out.addEventListener('click', function (e) { if (e.target.closest('a') && input.value.trim()) keep(input.value.trim()); });
    root.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-q]'); if (b) { input.value = b.dataset.q; run(input.value, true); return; }
      if (e.target.closest('.soi-app-quran')) { input.value = ''; input.placeholder = 'Chapter:verse, for example 51:56'; input.setAttribute('inputmode', 'text'); input.focus(); run(''); }
    });
    recent();
    var q0 = new URLSearchParams(location.search);
    if (q0.get('q')) { input.value = q0.get('q'); run(input.value, true); } else if (q0.get('focus')) input.focus();
  }

  /* ================= Saved ================= */
  function saved() {
    var seg = (location.hash || '#issues').slice(1); if (['issues', 'articles', 'quotes'].indexOf(seg) < 0) seg = 'issues';
    root.innerHTML = '<h1 class="soi-app-h1">Saved</h1><div class="soi-app-seg" role="tablist">' + ['Issues', 'Articles', 'Quotes'].map(function (l) {
      return '<button type="button" role="tab" data-seg="' + l.toLowerCase() + '">' + l + '</button>'; }).join('') + '</div><div id="soi-app-pane"></div>';
    var pane = document.getElementById('soi-app-pane'), all = [], busy = false;
    function mb(n) { return Math.max(1, Math.round(n / 1048576)) + ' MB'; }
    function pick(s) {
      seg = s; history.replaceState(null, '', '#' + s);
      [].forEach.call(root.querySelectorAll('.soi-app-seg button'), function (b) { b.setAttribute('aria-selected', b.dataset.seg === s ? 'true' : 'false'); });
      if (s === 'issues') issues(); else if (s === 'articles') articles(); else quotes();
    }
    function issues() {
      haveMap().then(function (have) {
        if (seg !== 'issues') return;
        var mine = all.filter(function (i) { return offline(i.slug, have) || readCount(i); }).reverse();
        var down = mine.filter(function (i) { return offline(i.slug, have); }).length;
        var missing = all.filter(function (i) { return !offline(i.slug, have); }), size = missing.reduce(function (a, i) { return a + (i.bytes || 0); }, 0);
        pane.innerHTML = '<div class="soi-app-savedhead"><span>' + mine.length + ' issues · ' + down + ' downloaded for offline</span>' +
          (missing.length ? '<button type="button" id="soi-app-all">Save all (' + mb(size) + ')</button>' : '<span>All ' + all.length + ' issues are on this phone</span>') + '</div>' +
          '<div class="soi-app-grid">' + mine.map(function (i) {
            var n = readCount(i), tot = i.articles || 1, pct = Math.min(100, Math.round(n / tot * 100)), off = offline(i.slug, have), packed = CFG.bundled.indexOf(i.slug) >= 0;
            return '<div class="soi-app-si"><a href="/issues/' + i.slug + '/">' + cover(i) + '<span class="soi-app-badge' + (off ? '' : ' is-online') + '">' + (off ? 'Offline' : 'Online') + '</span></a>' +
              '<b>' + esc(short(i.period)) + '</b><span class="soi-app-bar"><i style="width:' + pct + '%"></i></span>' +
              '<small>' + (n >= tot ? 'Finished' : n ? n + ' of ' + tot + ' read' : 'Not started') + '</small>' +
              (off && !packed ? '<button type="button" class="soi-app-rm" data-slug="' + i.slug + '" aria-label="Remove ' + esc(i.period) + ' from this phone">Remove</button>' :
                !off ? '<button type="button" class="soi-app-get" data-slug="' + i.slug + '" aria-label="Save ' + esc(i.period) + ' for offline">Save offline</button>' : '') + '</div>';
          }).join('') + '</div>';
      });
    }
    function articles() {
      var l = S.store.articles();
      pane.innerHTML = l.length ? '<div class="soi-app-cards">' + l.map(function (a) {
        return '<a href="/issues/' + a.slug + '/#soi-' + a.id + '">' + cover({ slug: a.slug, period: '' }) + '<span><b>' + esc(a.title) + '</b><small>' + esc([a.label, a.min ? a.min + ' min' : '', a.audio ? 'audio' : ''].filter(Boolean).join(' · ')) + '</small></span></a>';
      }).join('') + '</div>' : '<p class="soi-app-empty">No articles saved yet. Open any article and press <b>Save</b> under its title.</p>';
    }
    function quotes() {
      var l = S.store.quotes();
      pane.innerHTML = l.length ? '<div class="soi-app-quotes">' + l.map(function (q, k) {
        return '<a class="' + (k % 2 ? 'is-light' : '') + '" href="/issues/' + q.s + '/#soi-' + q.a + '"><p>“' + esc(q.t) + '”</p><small>' + esc(q.at) + ' · Issue ' + q.n + '</small></a>';
      }).join('') + '</div>' : '<p class="soi-app-empty">No quotes saved yet. Press <b>Save</b> on any quote in the <a href="/quotes/">quotes library</a>.</p>';
    }
    root.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      if (b.dataset.seg) { pick(b.dataset.seg); return; }
      if (b.classList.contains('soi-app-rm')) { A.store.del(b.dataset.slug).then(issues); return; }
      if (b.classList.contains('soi-app-get')) { b.disabled = true; b.textContent = 'Saving…'; A.download(b.dataset.slug).then(issues, function () { b.disabled = false; b.textContent = 'Try again'; S.toast('No internet'); }); return; }
      if (b.id === 'soi-app-all' && !busy) {
        busy = true; b.disabled = true;
        if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(function () {});
        haveMap().then(function (have) {
          var todo = all.filter(function (i) { return !offline(i.slug, have); }).reverse(), total = todo.length, done = 0, failed = 0;
          function next() { var it = todo.shift(); if (!it) return Promise.resolve(); return A.download(it.slug, it.v).then(function () { done++; }, function () { failed++; }).then(function () { b.textContent = 'Saving… ' + (done + failed) + ' of ' + total; return next(); }); }
          return Promise.all([next(), next(), next()]).then(function () { busy = false; issues(); if (failed) S.toast(failed + ' could not be saved – check your connection'); else S.toast('All issues saved for offline'); });
        });
      }
    });
    A.manifest(false).then(function (l) { all = l; pick(seg); return A.manifest(true); }).then(function (l) { all = l; if (seg === 'issues' && !busy) issues(); }).catch(function () { pick(seg); });
  }

  /* ================= Profile (sample data) ================= */
  function profile() {
    var tiles = [['Saved', '/saved.html', '<path d="M6 3h12v18l-6-4-6 4z"/>'], ['Downloads', '/saved.html#issues', '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>'],
      ['Quizzes', '', '<path d="M9 9a3 3 0 115 2c-1 .7-2 1.3-2 3M12 18h.01"/><circle cx="12" cy="12" r="9"/>'], ['Alerts', '', '<path d="M6 16V11a6 6 0 0112 0v5l2 2H4zM10 21h4"/>']];
    var rows = [['Reading theme & text size', ''], ['Notifications for new issues', ''], ['Downloads & storage', '/saved.html#issues'], ['How to use SOI', ''], ['About Spirit of Islam', '/about/our-mission/'], ['Rate the app', ''], ['Log out', '']];
    root.innerHTML = '<h1 class="soi-app-h1">Profile</h1>' +
      '<p class="soi-app-note">' + sample('Sample data') + ' Name, gems, rank and the dashboard show example figures. They become yours when sign-in is added.</p>' +
      '<div class="soi-app-card"><div class="soi-app-who"><span class="soi-app-avatar" aria-hidden="true">' + SAMPLE.name.charAt(0) + '</span><span><b>Hi ' + SAMPLE.name + '!</b><a href="#" data-soon>Edit profile ›</a></span></div>' +
      '<a class="soi-app-rank" href="/gems.html"><span>' + SAMPLE.gems.toLocaleString() + ' gems · <strong>Rank #' + SAMPLE.rankWeek + '</strong> this week</span><b>Leaderboard ›</b></a></div>' +
      '<div class="soi-app-tiles">' + tiles.map(function (t) { return '<a class="soi-app-card" href="' + (t[1] || '#') + '"' + (t[1] ? '' : ' data-soon') + '><svg viewBox="0 0 24 24" aria-hidden="true">' + t[2] + '</svg>' + t[0] + '</a>'; }).join('') + '</div>' +
      '<div class="soi-app-card soi-app-dash"><div class="soi-app-dash-h"><h2>My reading</h2><span>This month</span></div><div class="soi-app-stats">' +
      '<div class="is-main"><b>' + SAMPLE.streak + ' days</b><span>Reading streak</span></div><div><b>' + SAMPLE.finished + '</b><span>Articles finished</span></div>' +
      '<div><b>' + SAMPLE.listened + '</b><span>Listened</span></div><div><b>' + SAMPLE.quiz + '</b><span>Average quiz score</span></div></div>' +
      '<p class="soi-app-cap">Last 14 days</p><div class="soi-app-cal" role="img" aria-label="Reading streak calendar: 13 of the last 14 days">' + SAMPLE.days.map(function (d) { return '<span' + (d ? ' class="is-on"' : '') + '></span>'; }).join('') + '</div></div>' +
      '<div class="soi-app-card soi-app-settings"><h2>Settings</h2>' + rows.map(function (r) { return '<a href="' + (r[1] || '#') + '"' + (r[1] ? '' : ' data-soon') + (r[0] === 'Log out' ? ' class="is-out"' : '') + '>' + esc(r[0]) + '<span aria-hidden="true">›</span></a>'; }).join('') + '</div>';
    root.addEventListener('click', function (e) { if (e.target.closest('[data-soon]')) soon(e); });
  }

  /* ================= Gems & leaderboard (sample data) ================= */
  function gems() {
    var seg = 'This week';
    root.innerHTML = '<div class="soi-app-gtop"><a href="/profile.html" aria-label="Back"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12H5M11 6l-6 6 6 6"/></svg></a>' +
      '<button type="button" id="soi-app-gshare" aria-label="Share my progress"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v13M7 8l5-5 5 5M5 14v6h14v-6"/></svg></button></div>' +
      '<div class="soi-app-ghead"><p class="soi-app-gtitle">SOI Gems</p><p class="soi-app-gname">' + SAMPLE.name.toUpperCase() + '</p><p>Reading since ' + SAMPLE.since + '</p><p>' + sample('Sample data – real points come with sign-in') + '</p></div>' +
      '<div class="soi-app-gtotal"><span class="soi-app-gicon">' + GEM + '</span><span><b>Total gems</b><small>Rank #' + SAMPLE.rankWeek + ' this week · #' + SAMPLE.rankAll + ' all time</small></span><strong>' + SAMPLE.gems.toLocaleString() + '</strong></div>' +
      '<div class="soi-app-gseg" role="tablist">' + Object.keys(SAMPLE.boards).map(function (l) { return '<button type="button" role="tab" data-b="' + l + '">' + l + '</button>'; }).join('') + '</div><div id="soi-app-board"></div>' +
      '<div class="soi-app-earn"><h2>How to earn gems <span>PROPOSED</span></h2>' + SAMPLE.earn.map(function (e) { return '<div><span>' + esc(e[0]) + '</span><strong>' + e[1] + '</strong></div>'; }).join('') + '</div>' +
      '<a class="soi-app-keep" href="/index.html">Keep reading</a>';
    function board() {
      [].forEach.call(root.querySelectorAll('.soi-app-gseg button'), function (b) { b.setAttribute('aria-selected', b.dataset.b === seg ? 'true' : 'false'); });
      document.getElementById('soi-app-board').innerHTML = SAMPLE.boards[seg].map(function (r) {
        return '<div class="' + (r[1].indexOf('you') > -1 ? 'is-you' : '') + '"><span class="soi-app-brank">' + r[0] + '</span><span class="soi-app-bini" aria-hidden="true">' + (r[1] ? r[1].charAt(0) : '·') + '</span><span class="soi-app-bname">' + esc(r[1]) + '</span><span class="soi-app-bgems">' + r[2] + '</span></div>';
      }).join('');
    }
    root.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      if (b.dataset.b) { seg = b.dataset.b; board(); } else if (b.id === 'soi-app-gshare') soon();
    });
    board();
  }

  ({ home: home, search: search, saved: saved, profile: profile, gems: gems }[screen] || function () {})();
};
