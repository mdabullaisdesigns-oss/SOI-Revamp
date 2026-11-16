/* Spirit of Islam app – the screens: Home, Search, Saved, Profile, Gems & leaderboard, All issues, Quotes.
   Real on this phone: issues, Continue reading, saved issues/articles/quotes, offline text and audio, search,
   quote of the day, theme and text size. Sample data (marked on screen) until sign-in exists: name, gems, rank,
   leaderboard and the "My reading" figures. */
(function () {
  'use strict';
  var A = window.soiApp, S = A.screens, esc = A.esc, $ = A.$, $$ = A.$$, IC = A.IC, O = A.offline, M = A.mem;
  var SAMPLE = {
    name: 'Aisha', gems: 1240, rankWeek: 18, rankAll: 240, since: 'November 2026',
    streak: 12, finished: 34, listened: '5 h 20 m', quiz: '8.2 / 10', days: [1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    boards: {
      'This week': [['1', 'Yusuf', '2,980'], ['2', 'Maryam', '2,640'], ['3', 'Imran', '2,410'], ['18', 'Aisha (you)', '1,240'], ['19', 'Sana', '1,210']],
      'This issue': [['1', 'Maryam', '410'], ['2', 'Bilal', '385'], ['3', 'Yusuf', '360'], ['9', 'Aisha (you)', '245'], ['10', 'Hamza', '240']],
      'All time': [['1', 'Imran', '48,200'], ['2', 'Yusuf', '45,930'], ['3', 'Fatima', '44,100'], ['240', 'Aisha (you)', '1,240'], ['241', 'Zaid', '1,235']]
    },
    earn: [['Finish an article (read or listen)', '+10'], ['Each correct quiz answer', '+5'], ['Quiz score 7 or more', '+20'], ['Daily reading streak', '+5 a day'], ['Finish a whole issue', '+50']]
  };
  var GEM = '<svg viewBox="0 0 24 24" aria-hidden="true" class="soi-app-gem"><path d="M12 2l4 6-4 14-4-14z"/><path d="M4 8h16l-8 14z" opacity=".55"/></svg>';
  var I = {
    search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>',
    chev: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>',
    film: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor" stroke="none"/></svg>',
    quote: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 11H6.5A1.5 1.5 0 0 1 5 9.5v-2A1.5 1.5 0 0 1 6.5 6h2A1.5 1.5 0 0 1 10 7.5V13a4 4 0 0 1-4 4M19 11h-3.500A1.5 1.5 0 0 1 14 9.5v-2A1.5 1.5 0 0 1 15.5 6h2A1.5 1.500 0 0 1 19 7.5V13a4 4 0 0 1-4 4"/></svg>',
    books: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h4v16H5zM10.500 4h4v16h-4zM16.200 6.200l3.700-1 3 13.600-3.700 1z" transform="translate(-1 0)"/></svg>',
    bell: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 16v-5a6 6 0 0 1 12 0v5l1.800 2H4.200zM10 21h4"/></svg>',
    quiz: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.300 9.500a2.800 2.800 0 1 1 4.200 2.400c-.900.600-1.500 1.100-1.500 2.100M12 17.200h.01"/></svg>',
    trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M10 7V4.500h4V7M7 7l.8 12.500h8.400L17 7"/></svg>',
    wave: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10v4M8 6.500v11M12 4v16M16 7.500v9M20 10v4"/></svg>'
  };
  var GUIDES = ['Listen with read-along', 'Save issues for offline', 'Earn gems with quizzes', 'Share an article'];
  function sample(t) { return '<span class="soi-app-sample">' + (t || 'Sample') + '</span>'; }
  function soon() { A.toast('Coming with sign-in'); }
  function title(t, extra) { return '<header class="soi-app-large"><h1 data-focus tabindex="-1">' + t + '</h1>' + (extra || '') + '</header>'; }
  function segs(id, names, on) {
    return '<div class="soi-app-seg" role="tablist" id="' + id + '">' + names.map(function (l) { var k = l.toLowerCase().replace(/\s+/g, '-'); return '<button type="button" role="tab" data-seg="' + k + '" aria-selected="' + (k === on) + '" tabindex="' + (k === on ? 0 : -1) + '">' + l + '</button>'; }).join('') + '</div>';
  }
  function segKeys(el, pick) {                                     /* arrow keys move between the tabs, as on a native control */
    el.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return; var b = $$('[role="tab"]', el), i = b.indexOf(document.activeElement); if (i < 0) return;
      e.preventDefault(); var n = b[(i + (e.key === 'ArrowRight' ? 1 : b.length - 1)) % b.length]; n.focus(); pick(n.dataset.seg);
    });
  }
  function ring(pct) { var c = 2 * Math.PI * 9; return '<svg class="soi-app-ring" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="9" stroke-dasharray="' + c.toFixed(1) + '" stroke-dashoffset="' + (c * (1 - Math.max(0.03, Math.min(1, pct)))).toFixed(1) + '"/></svg>'; }

  /* ================= Home ================= */
  S.home = {
    title: 'Home',
    init: function (v) {
      v.innerHTML = '<div class="soi-app-pad"><div class="soi-app-top"><a class="soi-app-searchbar" href="' + A.link('search', { focus: 1 }) + '" aria-label="Search the magazine">' + I.search + '<span>Search “patience”</span></a>' +
        '<a class="soi-app-gempill" href="' + A.link('gems') + '" aria-label="Your gems, sample figure: ' + SAMPLE.gems.toLocaleString() + '">' + GEM + SAMPLE.gems.toLocaleString() + '</a></div>' +
        '<div class="soi-app-hello"><img src="/assets/brand/Peogen-logo.png" alt="" width="40" height="39"><div><p>Assalamu alaikum</p><h1 data-focus tabindex="-1">Spirit of Islam</h1></div></div>' +
        '<div id="soi-app-cont"></div>' +
        '<section aria-labelledby="soi-app-h-latest"><div class="soi-app-hrow"><h2 id="soi-app-h-latest">Latest issue</h2></div><div id="soi-app-latest"></div></section>' +
        '<section aria-labelledby="soi-app-h-new"><div class="soi-app-hrow"><h2 id="soi-app-h-new">Newest issues</h2><a href="' + A.link('library') + '">All issues</a></div><div class="soi-app-row3" id="soi-app-newest"></div></section>' +
        '<section aria-labelledby="soi-app-h-art"><div class="soi-app-hrow"><h2 id="soi-app-h-art">In this issue</h2></div><div class="soi-app-list" id="soi-app-arts"></div></section>' +
        '<section aria-labelledby="soi-app-h-how"><div class="soi-app-hrow"><h2 id="soi-app-h-how">How to use the app</h2></div><div class="soi-app-scroll" id="soi-app-guides">' +
        GUIDES.map(function (g, k) { return '<div class="soi-app-guide soi-app-guide-' + (k % 4) + '">' + I.film + '<b>' + esc(g) + '</b><small>Video coming soon</small></div>'; }).join('') + '</div></section>' +
        '<section class="soi-app-quote" id="soi-app-qotd" aria-labelledby="soi-app-h-q"><p class="soi-app-kick" id="soi-app-h-q">Quote of the day</p><blockquote>&nbsp;</blockquote><p class="soi-app-quote-src"></p>' +
        '<div class="soi-app-quote-acts"><button type="button" data-q="save">Save</button><button type="button" data-q="img">Share as picture</button><a href="' + A.link('quotes') + '">All quotes</a></div></section></div>';
      v.addEventListener('click', function (e) {
        var b = e.target.closest('[data-save]'); if (b) { O.saveFlow(b.dataset.save); return; }
        var q = e.target.closest('[data-q]'); if (q && S.home.q) { if (q.dataset.q === 'img') A.quoteImage(S.home.q); else { var on = M.toggleQuote(S.home.q); q.textContent = on ? 'Saved' : 'Save'; q.setAttribute('aria-pressed', on); A.tap('ok'); A.toast(on ? 'Quote saved' : 'Removed from Saved'); } }
      });
      window.addEventListener('soi-offline', function () { if (!v.hidden) S.home.draw(); });
      A.quoteOfDay().then(function (q) {
        S.home.q = q; var box = $('#soi-app-qotd', v); $('blockquote', box).textContent = '“' + q.t + '”';
        $('.soi-app-quote-src', box).innerHTML = '<a href="/issues/' + q.s + '/#soi-' + q.a + '">' + esc(q.at) + '</a> · Issue ' + q.n;
        var sb = $('[data-q="save"]', box), on = M.hasQuote(q); sb.textContent = on ? 'Saved' : 'Save'; sb.setAttribute('aria-pressed', on);
      }).catch(function () {});
      A.manifest(true).then(function () { if (!v.hidden) S.home.draw(); });
    },
    show: function () { S.home.draw(); },
    draw: function () {
      A.manifest(false).then(function (list) {
        var latest = list[list.length - 1], three = list.slice(-3).reverse(), p = M.progress(), c = $('#soi-app-cont');
        if (p) {
          var left = p.min ? Math.max(1, Math.round(p.min * (1 - (p.frac || 0)))) : 0, pct = Math.round((p.frac || 0) * 100);
          c.innerHTML = '<a class="soi-app-cont" href="/issues/' + p.slug + '/?resume=1#soi-' + p.id + '" aria-label="Continue reading ' + esc(p.title) + ', ' + pct + ' percent read' + (p.t ? ', audio paused at ' + A.mmss(p.t) : '') + '">' +
            A.cover({ slug: p.slug }, false, true) + '<span class="soi-app-cont-t"><small>Continue reading</small><b>' + esc(p.title) + '</b><i>' + esc([p.label, left ? left + ' min left' : '', p.t ? 'paused at ' + A.mmss(p.t) : ''].filter(Boolean).join(' · ')) + '</i>' +
            '<span class="soi-app-bar"><i style="transform:scaleX(' + (pct / 100) + ')"></i></span></span><span class="soi-app-cont-play" aria-hidden="true">' + IC.play + '</span></a>';
        } else c.innerHTML = '';
        var a0 = (latest.arts || []).filter(function (a) { return a[4]; })[0], j = O.job(latest.slug), full = O.hasAudio(latest.slug) || (O.hasText(latest.slug) && !latest.audio);
        $('#soi-app-latest').innerHTML = '<div class="soi-app-hero">' + A.cover(latest, true, true) + '<div class="soi-app-hero-t"><div class="soi-app-hero-txt"><p class="soi-app-kick">' + esc(A.label(latest)) + '</p>' +
          (latest.line ? '<p class="soi-app-hero-line">' + esc(latest.line) + '</p>' : '') +
          '<p class="soi-app-sub">' + latest.articles + ' articles' + (latest.audio ? ' · ' + latest.audio + ' with audio' : '') + '</p></div>' +
          '<div class="soi-app-hero-btns"><a class="soi-app-btn" href="/issues/' + latest.slug + '/">Read</a>' + (a0 ? '<a class="soi-app-btn is-gold" href="/issues/' + latest.slug + '/#soi-' + a0[0] + '">Listen</a>' : '') +
          '<button type="button" class="soi-app-ib is-ring' + (full ? ' is-on' : '') + '" data-save="' + latest.slug + '" aria-label="' + (full ? 'Saved for offline' : j ? 'Saving for offline' : 'Save this issue for offline') + '">' + (j ? ring(j.total ? j.done / j.total : .1) : full ? IC.check : IC.down) + '</button></div></div></div>';
        $('#soi-app-newest').innerHTML = three.map(function (i) { return '<a href="/issues/' + i.slug + '/" aria-label="' + esc(A.label(i)) + '">' + A.cover(i, false, true) + '<b>' + esc(A.shortPeriod(i.period).replace(/ \d{4}$/, '')) + '</b><small>' + (i.number ? 'Issue ' + i.number : i.year) + '</small></a>'; }).join('');
        $('#soi-app-arts').innerHTML = (latest.arts || []).slice(0, 4).map(function (a, k) {
          return '<a href="/issues/' + latest.slug + '/#soi-' + a[0] + '"><span class="soi-app-n" aria-hidden="true">' + (k + 1) + '</span><span class="soi-app-at"><small>' + esc(a[2] || 'Article') + '</small><b>' + esc(a[1]) + '</b></span><span class="soi-app-min">' + a[3] + ' min' + (a[4] ? I.wave : '') + '</span></a>';
        }).join('') + '<a class="soi-app-more" href="/issues/' + latest.slug + '/">All ' + latest.articles + ' articles</a>';
      }).catch(function () {});
    }
  };

  /* ================= Search ================= */
  var POP = ['The purpose of life', 'Patience', 'Peace and reconciliation', 'Your Questions Answered', 'The Word of God'];
  S.search = {
    title: 'Search',
    init: function (v) {
      v.innerHTML = '<div class="soi-app-pad">' + title('Search') +
        '<div class="soi-app-searchbox" role="search">' + I.search + '<input id="soi-app-q" type="search" enterkeyhint="search" autocomplete="off" autocapitalize="none" spellcheck="false" aria-label="Search every article" placeholder="What would you like to read?"><button type="button" class="soi-app-ib" id="soi-app-qx" aria-label="Clear search" hidden>' + IC.close + '</button></div>' +
        '<button type="button" class="soi-app-quran"><span aria-hidden="true">51:56</span><b>Search by Quran reference</b>' + I.chev + '</button>' +
        '<div id="soi-app-idle"><div id="soi-app-recent"></div><h2 class="soi-app-cap">Popular</h2><div class="soi-app-pop">' + POP.map(function (q) { return '<button type="button" data-q="' + esc(q) + '">' + I.search + '<b>' + esc(q) + '</b>' + I.chev + '</button>'; }).join('') + '</div></div>' +
        '<div id="soi-app-results" aria-live="polite"></div></div>';
      var input = $('#soi-app-q', v), idle = $('#soi-app-idle', v), out = $('#soi-app-results', v), clear = $('#soi-app-qx', v), pf = null, seq = 0, timer = 0;
      function recent() { var r = A.LS.get('soiRecent', []); $('#soi-app-recent', v).innerHTML = r.length ? '<h2 class="soi-app-cap">Recent</h2><div class="soi-app-chips">' + r.map(function (q) { return '<button type="button" data-q="' + esc(q) + '">' + esc(q) + '</button>'; }).join('') + '</div>' : ''; }
      function keep(q) { var r = A.LS.get('soiRecent', []).filter(function (x) { return x.toLowerCase() !== q.toLowerCase(); }); r.unshift(q); A.LS.set('soiRecent', r.slice(0, 6)); }
      function engine() { if (!pf) pf = import('/pagefind/pagefind.js').then(function (m) { return (m.options ? m.options({ baseUrl: '/' }) : Promise.resolve()).then(function () { return m; }); }); return pf; }
      function run(q, remember) {
        q = q.trim().replace(/(\d{1,3})\s*:\s*(\d{1,3})/g, '$1:$2'); var my = ++seq; clear.hidden = !input.value;
        if (!q) { idle.hidden = false; out.innerHTML = ''; return; }
        idle.hidden = true; if (!out.innerHTML) out.innerHTML = '<p class="soi-app-cap">Searching…</p>';
        engine().then(function (m) { return m.search(q); }).then(function (r) { return Promise.all(r.results.slice(0, 30).map(function (x) { return x.data(); })).then(function (d) { return { n: r.results.length, d: d }; }); }).then(function (r) {
          if (my !== seq) return; if (remember && r.n) { keep(q); recent(); }
          out.innerHTML = '<h2 class="soi-app-cap">' + (r.n ? r.n + (r.n === 1 ? ' article' : ' articles') : 'Nothing found for “' + esc(q) + '”') + '</h2>' + r.d.map(function (x) {
            return '<a class="soi-app-res" href="' + esc(x.url) + '"><b>' + esc(x.meta.title) + '</b><small>' + esc(x.meta.issue || '') + '</small><span>' + x.excerpt + '</span></a>'; }).join('');
        }).catch(function () { if (my === seq) out.innerHTML = '<p class="soi-app-cap">Search could not start. Please try again.</p>'; });
      }
      S.search.run = function (q) { input.value = q; run(q, true); };
      input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(function () { run(input.value, false); }, 200); });
      input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { clearTimeout(timer); run(input.value, true); input.blur(); } });
      clear.addEventListener('click', function () { input.value = ''; run(''); input.focus(); });
      out.addEventListener('click', function (e) { if (e.target.closest('a') && input.value.trim()) keep(input.value.trim()); });
      v.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-q]'); if (b) { input.value = b.dataset.q; run(input.value, true); return; }
        if (e.target.closest('.soi-app-quran')) { input.value = ''; input.placeholder = 'Chapter:verse, for example 51:56'; input.focus(); run(''); }
      });
      S.search.recent = recent;
    },
    show: function (v, q, how) {
      S.search.recent();
      if (q.q) S.search.run(q.q); else if (q.focus && !how.back) setTimeout(function () { $('#soi-app-q', v).focus(); }, 350);
    }
  };

  /* ================= Saved ================= */
  S.saved = {
    title: 'Saved', seg: 'issues',
    init: function (v) {
      v.innerHTML = '<div class="soi-app-pad">' + title('Saved') + segs('soi-app-savedseg', ['Issues', 'Articles', 'Quotes'], 'issues') + '<div id="soi-app-pane" role="tabpanel" aria-labelledby="soi-app-savedseg"></div></div>';
      var busyAll = false;
      function pick(s) { S.saved.seg = s; $$('#soi-app-savedseg button', v).forEach(function (b) { var on = b.dataset.seg === s; b.setAttribute('aria-selected', on); b.tabIndex = on ? 0 : -1; }); S.saved.draw(); }
      S.saved.pick = pick; segKeys($('#soi-app-savedseg', v), pick);
      v.addEventListener('click', function (e) {
        var b = e.target.closest('button'); if (!b) return;
        if (b.dataset.seg) { A.tap(); pick(b.dataset.seg); return; }
        var slug = b.dataset.slug;
        if (b.dataset.act === 'menu') {
          A.issueOf(slug).then(function (it) {
            var ch = [], x = O.index()[slug] || {};
            if (it.audio && !O.hasAudio(slug)) ch.push({ label: x.have ? 'Finish saving the audio' : 'Save the audio too', note: (x.have || 0) + ' of ' + (x.of || it.audio) + ' recordings on this phone', value: 'audio', kind: 'is-main' });
            if (x.have) ch.push({ label: 'Remove the audio', note: 'Frees ' + A.mb(x.audio) + '; the text stays', value: 'rmaudio' });
            if (!O.packed(slug) && x.text) ch.push({ label: 'Remove from this phone', note: 'Frees ' + A.mb((x.text || 0) + (x.audio || 0)), value: 'rm', kind: 'is-danger' });
            if (!ch.length) { A.toast('This issue comes with the app'); return; }
            A.sheet(A.label(it), '', ch).then(function (c) {
              if (c === 'audio') O.save(slug, true).then(function () { A.tap('ok'); A.toast('Audio saved'); }, function (er) { A.toast(/cancel/.test(er.message) ? 'Stopped' : /could not/.test(er.message) ? er.message : 'No internet – try again later'); });
              else if (c === 'rmaudio') O.removeAudio(slug).then(function () { A.toast('Audio removed'); });
              else if (c === 'rm') O.removeIssue(slug).then(function () { A.toast('Removed'); });
            });
          });
        } else if (b.dataset.act === 'cancel') { var j = O.job(slug); if (j) j.cancel(); }
        else if (b.dataset.act === 'all' && !busyAll) {
          A.sheet('Save every issue', 'The text of all issues, to read without internet. Audio is saved one issue at a time.', [{ label: 'Save all issues', note: b.dataset.size, value: 1, kind: 'is-main' }]).then(function (ok) {
            if (!ok) return; busyAll = true;
            A.manifest(false).then(function (all) {
              var todo = all.filter(function (i) { return !O.hasText(i.slug); }).reverse(), total = todo.length, done = 0, failed = 0;
              function next() { var it = todo.shift(); if (!it) return Promise.resolve(); return O.save(it.slug, false).then(function () { done++; }, function () { failed++; }).then(function () { S.saved.allNote = 'Saving ' + (done + failed) + ' of ' + total + '…'; S.saved.draw(); return next(); }); }
              return Promise.all([next(), next(), next()]).then(function () { busyAll = false; S.saved.allNote = ''; S.saved.draw(); A.tap('ok'); A.toast(failed ? failed + ' could not be saved – check your connection' : 'All issues saved'); });
            });
          });
        } else if (b.dataset.act === 'unsave') { var l = M.articles().filter(function (a) { return !(a.slug === slug && a.id === b.dataset.id); }); A.LS.set('soiSavedArticles', l); S.saved.draw(); A.toast('Removed'); }
        else if (b.dataset.act === 'unquote') { var qs = M.quotes(); qs.splice(+b.dataset.k, 1); A.LS.set('soiSavedQuotes', qs); S.saved.draw(); A.toast('Removed'); }
        else if (b.dataset.act === 'qimg') A.quoteImage(M.quotes()[+b.dataset.k]);
      });
      var t = 0; window.addEventListener('soi-offline', function () { if (v.hidden || S.saved.seg !== 'issues') return; clearTimeout(t); t = setTimeout(S.saved.draw, 120); });
    },
    show: function (v, q) { if (q.tab && ['issues', 'articles', 'quotes'].indexOf(q.tab) >= 0) S.saved.pick(q.tab); else S.saved.draw(); },
    draw: function () {
      var pane = $('#soi-app-pane'), seg = S.saved.seg; if (!pane) return;
      if (seg === 'articles') {
        var l = M.articles();
        pane.innerHTML = l.length ? '<div class="soi-app-cards">' + l.map(function (a) {
          return '<div class="soi-app-card soi-app-acard"><a href="/issues/' + a.slug + '/#soi-' + a.id + '">' + A.cover({ slug: a.slug }) + '<span><b>' + esc(a.title) + '</b><small>' + esc([a.label, a.min ? a.min + ' min' : '', a.audio ? 'audio' : ''].filter(Boolean).join(' · ')) + '</small></span></a>' +
            '<button type="button" class="soi-app-ib" data-act="unsave" data-slug="' + a.slug + '" data-id="' + a.id + '" aria-label="Remove ' + esc(a.title) + ' from Saved">' + I.trash + '</button></div>'; }).join('') + '</div>'
          : '<div class="soi-app-empty">' + IC.save + '<h2>No articles saved yet</h2><p>Open any article and press Save under its title.</p></div>';
        return;
      }
      if (seg === 'quotes') {
        var qs = M.quotes();
        pane.innerHTML = qs.length ? '<div class="soi-app-quotes">' + qs.map(function (q, k) {
          return '<figure class="soi-app-qcard"><blockquote>“' + esc(q.t) + '”</blockquote><figcaption><a href="/issues/' + q.s + '/#soi-' + q.a + '">' + esc(q.at) + '</a> · Issue ' + q.n + '</figcaption>' +
            '<div><button type="button" data-act="qimg" data-k="' + k + '">Share as picture</button><button type="button" data-act="unquote" data-k="' + k + '">Remove</button></div></figure>'; }).join('') + '</div>'
          : '<div class="soi-app-empty">' + I.quote + '<h2>No quotes saved yet</h2><p>Save the quote of the day, or any quote in the quotes library.</p><a class="soi-app-btn" href="' + A.link('quotes') + '">Open the quotes library</a></div>';
        return;
      }
      A.manifest(false).then(function (all) {
        if (S.saved.seg !== 'issues') return;
        var ix = O.index(), mine = all.filter(function (i) { return O.hasText(i.slug) || O.job(i.slug) || M.readCount(i.slug); }).reverse(), used = O.used();
        var missing = all.filter(function (i) { return !O.hasText(i.slug); }), size = missing.reduce(function (a, i) { return a + (i.bytes || 0); }, 0);
        pane.innerHTML = '<div class="soi-app-card soi-app-storage" role="group" aria-label="Storage used on this phone"><div><p class="soi-app-kick">On this phone</p><p class="soi-app-big">' + A.mb(used.total) + '</p>' +
          '<p class="soi-app-sub">' + (used.issues + A.cfg().bundled.length) + ' issues · ' + used.withAudio + ' with audio</p></div>' +
          '<div class="soi-app-storebar" aria-hidden="true"><i style="flex:' + Math.max(used.text, 1) + '"></i><i class="is-audio" style="flex:' + (used.audio || 0) + '"></i></div>' +
          '<p class="soi-app-legend"><span><i></i>Text ' + A.mb(used.text) + '</span><span><i class="is-audio"></i>Audio ' + A.mb(used.audio) + '</span></p>' +
          (missing.length ? '<button type="button" class="soi-app-btn is-quiet" data-act="all" data-size="' + missing.length + ' issues · about ' + A.mb(size) + '">' + (S.saved.allNote || 'Save all issues (text, ' + A.mb(size) + ')') + '</button>' : '<p class="soi-app-sub">Every issue is on this phone.</p>') + '</div>' +
          '<div class="soi-app-ilist">' + mine.map(function (i) {
            var n = M.readCount(i.slug), tot = i.articles || 1, pct = Math.min(1, n / tot), x = ix[i.slug] || {}, j = O.job(i.slug), text = O.hasText(i.slug), aud = O.hasAudio(i.slug);
            var st = j ? (j.state === 'audio' ? 'Saving audio ' + j.done + ' of ' + j.total + (j.bytes ? ' · ' + A.mb(j.bytes) : '') : 'Saving text…')
              : aud ? 'Text and audio · ' + A.mb((x.text || 0) + (x.audio || 0)) : text ? (x.have ? 'Text · audio ' + x.have + ' of ' + x.of + ' · ' + A.mb((x.text || 0) + (x.audio || 0)) : O.packed(i.slug) ? 'Text · comes with the app' : 'Text · ' + A.mb(x.text)) : 'Not on this phone';
            return '<div class="soi-app-card soi-app-irow"><a href="/issues/' + i.slug + '/" aria-label="' + esc(A.label(i)) + '">' + A.cover(i) + '</a><div class="soi-app-irow-t"><a href="/issues/' + i.slug + '/"><b>' + esc(A.shortPeriod(i.period)) + '</b></a>' +
              '<p class="soi-app-status' + (text ? ' is-off' : '') + '">' + (j ? '' : aud ? I.wave : text ? IC.check : '') + '<span>' + esc(st) + '</span></p>' +
              (j && j.total ? '<span class="soi-app-bar is-gold" role="progressbar" aria-label="Saving audio" aria-valuemin="0" aria-valuemax="' + j.total + '" aria-valuenow="' + j.done + '"><i style="transform:scaleX(' + (j.done / j.total).toFixed(3) + ')"></i></span>'
                : '<span class="soi-app-bar" role="progressbar" aria-label="Articles read" aria-valuemin="0" aria-valuemax="' + tot + '" aria-valuenow="' + n + '"><i style="transform:scaleX(' + pct.toFixed(3) + ')"></i></span>') +
              '<small>' + (n >= tot ? 'Finished' : n ? n + ' of ' + tot + ' read' : 'Not started') + '</small></div>' +
              (j ? '<button type="button" class="soi-app-ib" data-act="cancel" data-slug="' + i.slug + '" aria-label="Stop saving ' + esc(A.shortPeriod(i.period)) + '">' + IC.close + '</button>'
                : '<button type="button" class="soi-app-ib" data-act="menu" data-slug="' + i.slug + '" aria-label="Offline options for ' + esc(A.shortPeriod(i.period)) + '"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1.600" fill="currentColor"/><circle cx="12" cy="12" r="1.600" fill="currentColor"/><circle cx="19" cy="12" r="1.600" fill="currentColor"/></svg></button>') + '</div>';
          }).join('') + '</div>';
      });
    }
  };

  /* ================= All issues ================= */
  S.library = {
    title: 'All issues',
    init: function (v) {
      v.innerHTML = '<header class="soi-app-nav"><button type="button" class="soi-app-ib" data-back aria-label="Back">' + IC.back + '</button><b>All issues</b><span class="soi-app-ib" aria-hidden="true"></span></header>' +
        '<div class="soi-app-pad">' + title('All issues', '<p class="soi-app-sub" id="soi-app-libcount"></p>') + '<div class="soi-app-scroll soi-app-years" id="soi-app-years" role="tablist" aria-label="Year"></div><div class="soi-app-grid3" id="soi-app-lib"></div></div>';
      v.addEventListener('click', function (e) { if (e.target.closest('[data-back]')) A.back(); var b = e.target.closest('[data-year]'); if (b) { S.library.year = +b.dataset.year; A.tap(); S.library.draw(); } });
    },
    show: function () { S.library.draw(); },
    draw: function () {
      A.manifest(false).then(function (all) {
        var years = []; all.forEach(function (i) { if (years.indexOf(i.year) < 0) years.push(i.year); }); years.sort(function (a, b) { return b - a; });
        var y = S.library.year || years[0];
        $('#soi-app-libcount').textContent = all.length + ' issues since ' + years[years.length - 1];
        $('#soi-app-years').innerHTML = years.map(function (x) { return '<button type="button" role="tab" data-year="' + x + '" aria-selected="' + (x === y) + '">' + x + '</button>'; }).join('');
        $('#soi-app-lib').innerHTML = all.filter(function (i) { return i.year === y; }).reverse().map(function (i) {
          return '<a href="/issues/' + i.slug + '/" aria-label="' + esc(A.label(i)) + (O.hasText(i.slug) ? ', on this phone' : '') + '">' + A.cover(i) + (O.hasText(i.slug) ? '<span class="soi-app-dot" aria-hidden="true">' + IC.check + '</span>' : '') +
            '<b>' + esc(A.shortPeriod(i.period).replace(/ \d{4}$/, '')) + '</b><small>' + (i.number ? 'Issue ' + i.number : '') + '</small></a>'; }).join('');
        var on = $('#soi-app-years [aria-selected="true"]'); if (on && on.scrollIntoView) on.parentNode.scrollLeft = Math.max(0, on.offsetLeft - 20);
      });
    }
  };

  /* ================= Quotes ================= */
  S.quotes = {
    title: 'Quotes', topic: '', n: 30,
    init: function (v) {
      v.innerHTML = '<header class="soi-app-nav"><button type="button" class="soi-app-ib" data-back aria-label="Back">' + IC.back + '</button><b>Quotes</b><span class="soi-app-ib" aria-hidden="true"></span></header>' +
        '<div class="soi-app-pad">' + title('Quotes', '<p class="soi-app-sub" id="soi-app-qcount"></p>') + '<div class="soi-app-scroll soi-app-years" id="soi-app-topics" role="tablist" aria-label="Topic"></div><div class="soi-app-quotes" id="soi-app-qlist"></div><button type="button" class="soi-app-btn is-quiet" id="soi-app-qmore">Show more</button></div>';
      v.addEventListener('click', function (e) {
        if (e.target.closest('[data-back]')) return A.back();
        var b = e.target.closest('button'); if (!b) return;
        if (b.dataset.topic != null) { S.quotes.topic = b.dataset.topic; S.quotes.n = 30; A.tap(); S.quotes.draw(); }
        else if (b.id === 'soi-app-qmore') { S.quotes.n += 30; S.quotes.draw(); }
        else if (b.dataset.k != null) { var q = S.quotes.shown[+b.dataset.k]; if (b.dataset.act === 'img') A.quoteImage(q); else { var on = M.toggleQuote(q); b.textContent = on ? 'Saved' : 'Save'; b.setAttribute('aria-pressed', on); A.tap('ok'); A.toast(on ? 'Quote saved' : 'Removed from Saved'); } }
      });
    },
    show: function () { S.quotes.draw(); },
    draw: function () {
      A.quotes().then(function (d) {
        var t = S.quotes.topic, list = d.quotes.filter(function (q) { return !t || (q.tp || []).indexOf(t) >= 0; });
        $('#soi-app-qcount').textContent = list.length.toLocaleString() + ' quotes' + (t ? ' on ' + t : ' from every issue');
        $('#soi-app-topics').innerHTML = [''].concat(d.topics || []).map(function (x) { return '<button type="button" role="tab" data-topic="' + esc(x) + '" aria-selected="' + (x === t) + '">' + esc(x || 'All') + '</button>'; }).join('');
        S.quotes.shown = list.slice(0, S.quotes.n);
        $('#soi-app-qlist').innerHTML = S.quotes.shown.map(function (q, k) {
          var on = M.hasQuote(q);
          return '<figure class="soi-app-qcard"><blockquote>“' + esc(q.t) + '”</blockquote><figcaption><a href="/issues/' + q.s + '/#soi-' + q.a + '">' + esc(q.at) + '</a> · Issue ' + q.n + '</figcaption>' +
            '<div><button type="button" data-k="' + k + '" data-act="save" aria-pressed="' + on + '">' + (on ? 'Saved' : 'Save') + '</button><button type="button" data-k="' + k + '" data-act="img">Share as picture</button></div></figure>'; }).join('');
        $('#soi-app-qmore').hidden = list.length <= S.quotes.n;
      }).catch(function () { $('#soi-app-qlist').innerHTML = '<p class="soi-app-sub">The quotes could not be opened.</p>'; });
    }
  };

  /* ================= Profile (sample data + real settings) ================= */
  S.profile = {
    title: 'Profile',
    init: function (v) {
      v.addEventListener('click', function (e) {
        var b = e.target.closest('[data-soon]'); if (b) { e.preventDefault(); soon(); return; }
        var t = e.target.closest('[data-theme]'); if (t) { A.setPref('theme', t.dataset.theme); A.tap(); S.profile.draw(v); return; }
        var z = e.target.closest('[data-text]'); if (z) { A.setPref('text', +z.dataset.text); A.tap(); S.profile.draw(v); }
      });
    },
    show: function (v) { S.profile.draw(v); },
    draw: function (v) {
      var p = A.prefs(), used = O.used(), R = A.cfg().remote;
      var tiles = [['Saved', A.link('saved'), IC.save], ['Downloads', A.link('saved', { tab: 'issues' }), IC.down], ['Quizzes', '', I.quiz], ['Alerts', '', I.bell]];
      var sizes = [[0.9, 'Small'], [1, 'Default'], [1.15, 'Large'], [1.3, 'Larger']];
      v.innerHTML = '<div class="soi-app-pad">' + title('Profile') +
        '<p class="soi-app-note">' + sample('Sample data') + ' The name, gems, rank and “My reading” are example figures. They become yours when sign-in is added.</p>' +
        '<div class="soi-app-card"><div class="soi-app-who"><span class="soi-app-avatar" aria-hidden="true">' + SAMPLE.name.charAt(0) + '</span><span><b>' + SAMPLE.name + '</b><small>Reading since ' + SAMPLE.since + '</small></span><button type="button" class="soi-app-chipbtn" data-soon>Sign in</button></div>' +
        '<a class="soi-app-rank" href="' + A.link('gems') + '">' + GEM + '<span><b>' + SAMPLE.gems.toLocaleString() + ' gems</b><small>Rank #' + SAMPLE.rankWeek + ' this week</small></span><i>Leaderboard</i>' + I.chev + '</a></div>' +
        '<div class="soi-app-tiles">' + tiles.map(function (t) { return t[1] ? '<a class="soi-app-card" href="' + t[1] + '">' + t[2] + '<span>' + t[0] + '</span></a>' : '<button type="button" class="soi-app-card" data-soon>' + t[2] + '<span>' + t[0] + '</span></button>'; }).join('') + '</div>' +
        '<section class="soi-app-card soi-app-dash" aria-labelledby="soi-app-h-dash"><div class="soi-app-dash-h"><h2 id="soi-app-h-dash">My reading</h2>' + sample() + '</div><div class="soi-app-stats">' +
        '<div class="is-main"><b>' + SAMPLE.streak + ' days</b><span>Reading streak</span></div><div><b>' + SAMPLE.finished + '</b><span>Articles finished</span></div>' +
        '<div><b>' + SAMPLE.listened + '</b><span>Listened</span></div><div><b>' + SAMPLE.quiz + '</b><span>Average quiz score</span></div></div>' +
        '<p class="soi-app-sub">Last 14 days</p><div class="soi-app-cal" role="img" aria-label="Sample reading calendar: 13 of the last 14 days">' + SAMPLE.days.map(function (d) { return '<span' + (d ? ' class="is-on"' : '') + '></span>'; }).join('') + '</div></section>' +
        '<section class="soi-app-card soi-app-set" aria-labelledby="soi-app-h-look"><h2 id="soi-app-h-look">Appearance</h2>' +
        '<div class="soi-app-setrow"><span id="soi-app-l-theme">Theme</span><div class="soi-app-seg is-small" role="group" aria-labelledby="soi-app-l-theme">' + [['system', 'Auto'], ['light', 'Light'], ['dark', 'Dark']].map(function (t) { return '<button type="button" data-theme="' + t[0] + '" aria-pressed="' + (p.theme === t[0]) + '">' + t[1] + '</button>'; }).join('') + '</div></div>' +
        '<div class="soi-app-setrow is-col"><span id="soi-app-l-text">Text size</span><div class="soi-app-seg is-small" role="group" aria-labelledby="soi-app-l-text">' + sizes.map(function (s) { return '<button type="button" data-text="' + s[0] + '" aria-pressed="' + (p.text === s[0]) + '" aria-label="' + s[1] + '"><span style="font-size:' + (0.8 * s[0]) + 'rem">A</span></button>'; }).join('') + '</div>' +
        '<p class="soi-app-preview">The art of living is to turn every experience into a lesson.</p><small>Follows your phone’s text size as well.</small></div></section>' +
        '<section class="soi-app-card soi-app-set" aria-labelledby="soi-app-h-more"><h2 id="soi-app-h-more">More</h2>' +
        '<a href="' + A.link('saved', { tab: 'issues' }) + '"><span>Downloads &amp; storage</span><small>' + A.mb(used.total) + '</small>' + I.chev + '</a>' +
        '<a href="' + A.link('quotes') + '"><span>Quotes library</span>' + I.chev + '</a><a href="' + A.link('library') + '"><span>All issues</span>' + I.chev + '</a>' +
        '<button type="button" data-soon><span>Notifications for new issues</span>' + I.chev + '</button>' +
        '<a href="' + R + '/about/" target="_blank" rel="noopener"><span>About Spirit of Islam</span><small>Opens the website</small>' + I.chev + '</a>' +
        '<a href="' + R + '/contact/" target="_blank" rel="noopener"><span>Contact us</span><small>Opens the website</small>' + I.chev + '</a></section>' +
        '<div class="soi-app-brand"><img src="/assets/brand/Peogen-logo.png" alt="" width="54" height="52"><img class="soi-app-brand-logo" src="/assets/brand/Spirit-of-Islam-Logo.png" alt="Spirit of Islam" width="220" height="23"><p>Towards Global Peace &amp; Spiritual Living</p></div></div>';
    }
  };

  /* ================= Gems & leaderboard (sample data) ================= */
  S.gems = {
    title: 'Gems and leaderboard', full: true, seg: 'This week',
    init: function (v) {
      v.innerHTML = '<header class="soi-app-nav"><button type="button" class="soi-app-ib" data-back aria-label="Back">' + IC.back + '</button><b>SOI Gems</b><button type="button" class="soi-app-ib" data-soon aria-label="Share my progress">' + IC.share + '</button></header>' +
        '<div class="soi-app-pad"><div class="soi-app-ghead">' + GEM + '<h1 data-focus tabindex="-1">' + SAMPLE.gems.toLocaleString() + '</h1><p>gems · ' + SAMPLE.name + '</p><p>' + sample('Sample data – real points come with sign-in') + '</p></div>' +
        '<div class="soi-app-gstats"><div><b>#' + SAMPLE.rankWeek + '</b><span>This week</span></div><div><b>#' + SAMPLE.rankAll + '</b><span>All time</span></div><div><b>' + SAMPLE.streak + '</b><span>Day streak</span></div></div>' +
        '<h2 class="soi-app-cap">Leaderboard</h2>' + segs('soi-app-gseg', Object.keys(SAMPLE.boards), 'this-week') + '<ol id="soi-app-board" role="tabpanel" aria-labelledby="soi-app-gseg"></ol>' +
        '<section class="soi-app-earn" aria-labelledby="soi-app-h-earn"><h2 id="soi-app-h-earn">How to earn gems <span>Proposed</span></h2>' + SAMPLE.earn.map(function (e) { return '<div><span>' + esc(e[0]) + '</span><strong>' + e[1] + '</strong></div>'; }).join('') + '</section>' +
        '<a class="soi-app-btn is-gold is-wide" href="' + A.link('home') + '" data-replace>Keep reading</a></div>';
      function board(k) {
        var name = Object.keys(SAMPLE.boards).filter(function (n) { return n.toLowerCase().replace(/\s+/g, '-') === k; })[0] || 'This week'; S.gems.seg = name;
        $$('#soi-app-gseg button', v).forEach(function (b) { var on = b.dataset.seg === k; b.setAttribute('aria-selected', on); b.tabIndex = on ? 0 : -1; });
        $('#soi-app-board', v).innerHTML = SAMPLE.boards[name].map(function (r) { var you = r[1].indexOf('you') > -1; return '<li class="' + (you ? 'is-you' : '') + '"' + (+r[0] > 3 && you ? ' data-gap' : '') + '><span class="soi-app-brank">' + r[0] + '</span><span class="soi-app-bini" aria-hidden="true">' + r[1].charAt(0) + '</span><span class="soi-app-bname">' + esc(r[1]) + '</span><span class="soi-app-bgems">' + r[2] + '<span class="soi-app-vh"> gems</span></span></li>'; }).join('');
      }
      segKeys($('#soi-app-gseg', v), board);
      v.addEventListener('click', function (e) { if (e.target.closest('[data-back]')) return A.back(); if (e.target.closest('[data-soon]')) return soon(); var b = e.target.closest('[data-seg]'); if (b) { A.tap(); board(b.dataset.seg); } });
      board('this-week');
    }
  };
})();
