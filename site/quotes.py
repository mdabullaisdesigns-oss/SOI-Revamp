"""Quotes library: every closing reflection (the quotation that ends an article) and every In Focus
quotation, from all issues.  Written to dist/assets/quotes.json and shown at /quotes/."""
import html, json, os, re

TOPICS = [  # (name, words that put a quotation under it)
    ("Peace", r"\bpeace|peaceful|non-?violen|reconcil|harmony|conflict|violence|\bwar\b"),
    ("Patience", r"\bpatien|\bsabr\b|forbear|endur|tolera|restraint|provocation"),
    ("God", r"\bGod\b|Creator|\bLord\b|\bAllah\b|divine|Almighty"),
    ("Prayer & Worship", r"\bpray|worship|\bdua\b|supplicat|fasting|\bhajj\b|remembrance|\bzikr\b"),
    ("Gratitude", r"gratitude|grateful|thankful|\bshukr\b|blessing|acknowledg"),
    ("Knowledge & Wisdom", r"knowledge|wisdom|\bwise\b|learn|intellect|thinking|reflect|contemplat|reason|realiz|discover"),
    ("Hereafter", r"hereafter|paradise|death|\bdie\b|eternal|eternity|afterlife|judg(e)?ment|accountab|\bhell\b"),
    ("Character", r"character|humility|humble|modest|honest|sincer|truth|arrogan|\bego\b|anger|forgiv|moral|ethic|virtue"),
    ("Positive Thinking", r"positiv|negativ|optimis|\bhope|opportunit|failure|success|problem|challenge|adversit|difficult"),
    ("Quran & the Prophet", r"quran|prophet|hadith|sunnah|\bislam\b|muslim"),
    ("Society & Family", r"society|famil|parent|child|marriage|neighbo|women|humanity|mankind|human being"),
    ("Life's Purpose", r"purpose|mission|test\b|trial|\bworld\b|creation|destiny|spiritual"),
]


def plain(runs):
    return re.sub(r"\s+", " ", "".join(r[1] for r in runs)).strip()


def good(t):
    n = len(t.split())
    return 6 <= n <= 75 and re.match(r"[“\"‘'(]?[A-Z]", t) and re.search(r"[.!?”’\")]$", t)


def collect(root, issues):
    out, seen, dropped = [], {}, 0
    label = {i["slug"]: (i["number"], i["period"]) for i in issues}

    def add(slug, a_id, a_title, text, kind, by=""):
        nonlocal dropped
        text = re.sub(r"\s*❑\s*$", "", text).strip()
        if not good(text):
            dropped += 1
            return
        key = re.sub(r"[^a-z0-9]", "", text.lower())
        if key in seen:
            seen[key]["also"] += 1
            return
        q = {"t": text, "s": slug, "n": label[slug][0], "p": label[slug][1], "a": a_id, "at": a_title, "k": kind, "by": by, "also": 0,
             "y": int(slug[:4]), "tp": [name for name, rx in TOPICS if re.search(rx, text, re.I)][:3]}
        seen[key] = q
        out.append(q)

    for i in issues:
        p = os.path.join(root, "issues", i["slug"], "issue.json")
        if os.path.exists(p):
            for a in json.load(open(p, encoding="utf-8"))["articles"]:
                its = a["items"]
                for k, x in enumerate(its):
                    if x["k"] == "thought":
                        add(i["slug"], a["id"], a["title"], plain(x["runs"]), "Closing reflection")
                    if x["k"] == "filler_sig" and k and its[k - 1]["k"] == "filler_p" and \
                            any(y["k"] == "filler_h" and re.fullmatch(r"\s*in focus\s*", plain(y["runs"]), re.I) for y in its[:k]):
                        add(i["slug"], a["id"], a["title"], plain(its[k - 1]["runs"]), "In Focus", plain(x["runs"]).strip(" -–—"))
        else:                                        # Issue 133, the hand-finished page
            for m in re.finditer(r'<section class="ev-item" id="soi-([\w-]+)".*?</section>', i["block"], re.S):
                title = next((a["title"] for a in i["articles"] if a["id"] == m.group(1)), "")
                for b in re.finditer(r'<blockquote class="ev-thought">(.*?)</blockquote>', m.group(0), re.S):
                    add(i["slug"], m.group(1), title, html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", b.group(1)))).strip(), "Closing reflection")
    return out, dropped


PAGE = r"""
<section class="soi-wrap soi-sec soi-page-head soi-q2-head">
  <p class="soi-kicker">Quotes</p>
  <h1>Words to carry with you</h1>
  <p>__N__ reflections from __ISSUES__ issues: the thought that closes each article, and the In Focus words of Maulana Wahiduddin Khan. Listen to them, share them as a picture, or open the article they come from.</p>
</section>
<section class="soi-wrap soi-q2">
  <div class="soi-q2-tools">
    <label class="soi-q2-find"><svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M10 2a8 8 0 1 0 4.9 14.3l5.4 5.4 1.4-1.4-5.4-5.4A8 8 0 0 0 10 2m0 2a6 6 0 1 1 0 12 6 6 0 0 1 0-12"/></svg><span class="soi-vh">Find a quote</span><input id="soi-q-find" type="search" placeholder="Find a word, e.g. patience" autocomplete="off"></label>
    <div class="soi-dd" id="soi-q-topic"><span class="soi-vh" id="soi-q-topic-l">Topic</span><button class="soi-dd-btn" type="button" aria-haspopup="listbox" aria-expanded="false" aria-labelledby="soi-q-topic-l"><span>All topics</span></button><ul class="soi-dd-list" role="listbox" aria-labelledby="soi-q-topic-l" hidden></ul></div>
    <div class="soi-dd" id="soi-q-year"><span class="soi-vh" id="soi-q-year-l">Year</span><button class="soi-dd-btn" type="button" aria-haspopup="listbox" aria-expanded="false" aria-labelledby="soi-q-year-l"><span>All years</span></button><ul class="soi-dd-list" role="listbox" aria-labelledby="soi-q-year-l" hidden></ul></div>
    <button class="soi-q2-btn" id="soi-q-rand" type="button">Surprise me</button>
  </div>
  <p class="soi-q2-count" id="soi-q-count" aria-live="polite"></p>
  <div id="soi-q-list" class="soi-q3-grid"></div>
  <p class="soi-q-more"><button class="soi-btn" id="soi-q-more" type="button">Show more</button></p>
</section>
<div class="soi-q-toast" id="soi-q-toast" role="status" aria-live="polite"></div>
<script>
(function(){
  var ALL=[],PH=[],cur=[],shown=0,STEP=22,topic=null,year=null,speaking=null,DAY=-1,
      $=function(i){return document.getElementById(i)},list=$('soi-q-list'),find=$('soi-q-find'),more=$('soi-q-more'),count=$('soi-q-count'),toast=$('soi-q-toast');
  var I={listen:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9v6h4l5 4V5L7 9zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4M14 3.2v2.1a7 7 0 0 1 0 13.4v2.1a9 9 0 0 0 0-17.6"/></svg>',
    stop:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6h12v12H6z"/></svg>',
    img:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2m0 16H5v-1.6l4-4 3 3 4-4 3 3zm0-5.4-3-3-4 4-3-3-4 4V5h14zM8.5 10A1.5 1.5 0 1 0 8.5 7a1.5 1.5 0 0 0 0 3"/></svg>',
    wa:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2m0 2a8 8 0 1 1-4.2 14.8l-.3-.2-2.9.8.8-2.8-.2-.3A8 8 0 0 1 12 4"/></svg>',
    copy:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 8h-9a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h9a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1m-1 11h-7v-9h7zM4 3h9a1 1 0 0 1 1 1v2h-2V5H5v9h1v2H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1"/></svg>',
    save:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M17 2H7a2 2 0 0 0-2 2v17.4a.6.6 0 0 0 .95.5L12 18l6.05 3.9a.6.6 0 0 0 .95-.5V4a2 2 0 0 0-2-2m0 16.5-5-3.2-5 3.2V4h10z"/></svg>',
    prev:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="M15.4 5.4 14 4l-8 8 8 8 1.4-1.4L8.8 12z"/></svg>',
    next:'<svg class="soi-fi" viewBox="0 0 24 24" aria-hidden="true"><path d="m8.6 18.6 1.4 1.4 8-8-8-8-1.4 1.4 6.6 6.6z"/></svg>'};
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function say(t){toast.textContent=t;toast.classList.add('is-on');clearTimeout(say.t);say.t=setTimeout(function(){toast.classList.remove('is-on')},2200)}
  function photo(q){return PH.length?PH[(cur.indexOf(q)+PH.length)%PH.length]:''}
  function saved(q){return !!(window.soi&&soi.store.hasQuote(q))}
  var canSpeak='speechSynthesis' in window,SITE='spiritofislam.co.in';
  function text(q){return '“'+q.t+'”\n— Spirit of Islam Magazine · '+SITE}
  function src(q){return (q.by?esc(q.by)+' · ':'')+'<a href="/issues/'+q.s+'/#soi-'+q.a+'">'+esc(q.at)+'</a> · Issue '+q.n+', '+esc(q.p)}
  function acts(q){
    return '<p class="soi-q2-act">'+
      (canSpeak?'<button type="button" data-act="listen" aria-label="Listen to this quote">'+I.listen+'<span>Listen</span></button>':'')+
      '<button type="button" data-act="img" aria-label="Share as a picture">'+I.img+'<span>Picture</span></button>'+
      '<button type="button" data-act="wa" aria-label="Share on WhatsApp">'+I.wa+'<span>WhatsApp</span></button>'+
      '<button type="button" data-act="copy" aria-label="Copy">'+I.copy+'<span>Copy</span></button>'+
      '<button type="button" data-act="save" aria-pressed="'+saved(q)+'" aria-label="Save">'+I.save+'<span>'+(saved(q)?'Saved':'Save')+'</span></button></p>';
  }
  function card(q,k){
    var el=document.createElement('article'),ph=PH.length?PH[k%PH.length]:'';
    el.className='soi-q3';
    el.innerHTML='<div class="soi-q3-in">'+(ph?'<img class="soi-q3-img" src="'+ph+'" alt="" loading="lazy">':'')+
      '<div class="soi-q3-body">'+(k===0&&isDefault()?'<p class="soi-q3-day">Quote of the day</p>':'')+'<blockquote><p>'+esc(q.t)+'</p></blockquote><p class="soi-q2-src">'+src(q)+'</p>'+acts(q)+'</div></div>';
    el.addEventListener('click',function(e){var b=e.target.closest('button[data-act]');if(b)act(b,q,ph)});return el;
  }
  function stopSpeak(){if(canSpeak&&speaking){speechSynthesis.cancel();setBtn(speaking,false);speaking=null}}
  function setBtn(b,on){if(!b||!b.isConnected)return;b.innerHTML=(on?I.stop:I.listen)+'<span>'+(on?'Stop':'Listen')+'</span>';b.classList.toggle('is-on',on)}
  function act(b,q,ph){
    var a=b.getAttribute('data-act');
    if(a==='listen'){if(speaking===b){stopSpeak();return}stopSpeak();var u=new SpeechSynthesisUtterance(q.t);u.lang='en';u.rate=.95;
      var v=speechSynthesis.getVoices().filter(function(x){return /^en/i.test(x.lang)});var pick=v.filter(function(x){return /male|daniel|alex|google uk english male/i.test(x.name)})[0]||v[0];if(pick)u.voice=pick;
      u.onend=u.onerror=function(){if(speaking===b){setBtn(b,false);speaking=null}};speaking=b;setBtn(b,true);speechSynthesis.speak(u);return}
    if(a==='save'){var on=soi.store.toggleQuote(q);b.setAttribute('aria-pressed',on);b.querySelector('span').textContent=on?'Saved':'Save';say(on?'Saved to this device':'Removed from Saved');return}
    if(a==='copy'){(navigator.clipboard?navigator.clipboard.writeText(text(q)):Promise.reject()).then(function(){say('Copied')},function(){say('Could not copy')});return}
    image(q,a==='wa'?'wa':'',ph);
  }
  function wrap(ctx,t,max){var w=t.split(' '),lines=[],l='';w.forEach(function(x){var n=l?l+' '+x:x;if(ctx.measureText(n).width>max&&l){lines.push(l);l=x}else l=n});if(l)lines.push(l);return lines}
  function image(q,how,phOverride){
    var W=1080,H=1350,c=document.createElement('canvas');c.width=W;c.height=H;var x=c.getContext('2d'),bg=new Image(),ph=phOverride||photo(q);
    function draw(){
      x.fillStyle='#204E60';x.fillRect(0,0,W,H);
      if(bg.naturalWidth){var r=Math.max(W/bg.naturalWidth,H/bg.naturalHeight),bw=bg.naturalWidth*r,bh=bg.naturalHeight*r;x.drawImage(bg,(W-bw)/2,(H-bh)/2,bw,bh);
        var g=x.createLinearGradient(0,0,0,H);g.addColorStop(0,'rgba(23,58,72,.55)');g.addColorStop(.5,'rgba(23,58,72,.72)');g.addColorStop(1,'rgba(23,58,72,.92)');x.fillStyle=g;x.fillRect(0,0,W,H)}
      x.strokeStyle='#D4CC73';x.lineWidth=3;x.strokeRect(48,48,W-96,H-96);
      x.fillStyle='#D4CC73';x.save();x.translate(W/2,170);x.rotate(Math.PI/4);x.fillRect(-13,-13,26,26);x.restore();
      var size=q.t.length>330?40:q.t.length>220?46:q.t.length>120?54:64,lines;x.fillStyle='#FFFFFF';x.textAlign='center';x.textBaseline='middle';
      do{x.font='italic '+size+'px "Cita Pro Ita","Cita Pro",Georgia,serif';lines=wrap(x,'“'+q.t+'”',W-240);size-=2}while(lines.length*(size*1.42)>H-560&&size>26);
      var lh=(size+2)*1.42,y=H/2-((lines.length-1)*lh)/2-30;x.shadowColor='rgba(0,0,0,.35)';x.shadowBlur=12;lines.forEach(function(l,i){x.fillText(l,W/2,y+i*lh)});x.shadowBlur=0;
      x.fillStyle='#D4CC73';x.fillRect(W/2-60,H-330,120,3);
      if(logo.naturalWidth){var lw=230,lh=lw*51.17/79.08;x.drawImage(logo,W/2-lw/2,H-290,lw,lh)}
      x.fillStyle='#FFFFFF';x.globalAlpha=.9;x.font='600 28px "Plus Jakarta Sans",Arial,sans-serif';x.fillText(SITE,W/2,H-105);x.globalAlpha=1;
      c.toBlob(function(b){var f=new File([b],'spirit-of-islam-quote.png',{type:'image/png'});
        function dl(){if(how==='wa'){window.open('https://wa.me/?text='+encodeURIComponent(text(q)),'_blank','noopener');return}var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=f.name;document.body.appendChild(a);a.click();a.remove();say('Picture saved')}
        if(navigator.canShare&&navigator.canShare({files:[f]})){navigator.share({files:[f],text:SITE}).catch(function(e){if(!e||e.name!=='AbortError')dl()});return}
        dl()},'image/png');
    }
    var logo=new Image();
    var fonts=document.fonts&&document.fonts.load?document.fonts.load('italic 40px "Cita Pro Ita"'):Promise.resolve();
    fonts.then(function(){logo.onload=logo.onerror=function(){if(!ph)return draw();bg.onload=draw;bg.onerror=draw;bg.src=ph};logo.src='/assets/brand/soi-mark-white.svg'},draw);
  }
  function isDefault(){return !find.value.trim()&&!(topic&&topic.value)&&!(year&&year.value)}
  function apply(shuffle){
    var w=find.value.trim().toLowerCase(),y=year?year.value:'',t=topic?topic.value:'';
    cur=ALL.filter(function(q){return (!y||String(q.y)===y)&&(!t||q.tp.indexOf(t)>-1)&&(!w||q.t.toLowerCase().indexOf(w)>-1||q.at.toLowerCase().indexOf(w)>-1)});
    if(shuffle){for(var i=cur.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),x=cur[i];cur[i]=cur[j];cur[j]=x}}
    else if(isDefault()&&DAY>-1){var d=cur.splice(DAY,1)[0];if(d)cur.unshift(d)}
    stopSpeak();count.textContent=cur.length.toLocaleString()+(cur.length===1?' quote':' quotes');list.innerHTML='';shown=0;grow();
    if(!cur.length)list.innerHTML='<p class="soi-q-none">No quote matches. Try another word or clear the filters.</p>';
  }
  function grow(){cur.slice(shown,shown+STEP).forEach(function(q,k){list.appendChild(card(q,shown+k))});shown=Math.min(cur.length,shown+STEP);more.hidden=shown>=cur.length}
  $('soi-q-rand').addEventListener('click',function(){apply(true)});
  more.addEventListener('click',grow);find.addEventListener('input',function(){apply()});
  fetch('/assets/quotes.json').then(function(r){return r.json()}).then(function(d){
    ALL=d.quotes;PH=d.photos||[];
    var ys={};ALL.forEach(function(q){ys[q.y]=1});
    year=soiDropdown($('soi-q-year'),[['','All years']].concat(Object.keys(ys).sort().reverse().map(function(y){return [y,y]})),function(){apply()});
    var m=location.hash.match(/^#t=(.+)$/),pre=m?decodeURIComponent(m[1]):'';
    topic=soiDropdown($('soi-q-topic'),[['','All topics']].concat(d.topics.map(function(t){return [t,t]})),function(){apply()});
    if(pre){var li=[].filter.call(document.querySelectorAll('#soi-q-topic li'),function(l){return l.dataset.v===pre})[0];if(li)li.click()}
    var pool=ALL.map(function(q,i){return [q,i]}).filter(function(x){return x[0].t.length<260}),day=Math.floor(Date.now()/864e5-new Date().getTimezoneOffset()/1440);
    DAY=pool.length?pool[(day*7919)%pool.length][1]:-1;
    apply();
  }).catch(function(){list.innerHTML='<p class="soi-q-none">The quotes could not be loaded. Please reload the page.</p>'});
})();
</script>
"""


def MENU_PHOTOS(root):
    m = json.load(open(os.path.join(root, "site", "menu.json"), encoding="utf-8"))
    return [f for f in m.get("quote_photos", []) if os.path.exists(os.path.join(root, "site", "photos", f))]


def build(root, out_dir, issues, page, write):
    quotes, dropped = collect(root, issues)
    quotes.sort(key=lambda q: (q["s"], q["a"]), reverse=True)
    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    photos = ["/assets/photos/" + f for f in sorted(os.listdir(os.path.join(root, "site", "photos"))) if f.endswith(".webp")]
    json.dump({"topics": [t[0] for t in TOPICS], "photos": photos, "quotes": quotes}, open(os.path.join(out_dir, "assets", "quotes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    body = PAGE.replace("__N__", f"{len(quotes):,}").replace("__ISSUES__", str(len({q['s'] for q in quotes})))
    write("quotes/index.html", page("Quotes – Spirit of Islam", body, cls="soi-quotes", current="quotes",
                                    desc="Reflections from every issue of Spirit of Islam: the closing thought of each article and the In Focus words of Maulana Wahiduddin Khan."))
    return len(quotes), dropped
