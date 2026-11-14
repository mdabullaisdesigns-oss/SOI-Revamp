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
<section class="soi-wrap soi-page-head">
  <h1>Quotes</h1>
  <p>__N__ reflections from __ISSUES__ issues — the thought that closes each article, and the In Focus words of Maulana Wahiduddin Khan. Each one opens the article it comes from.</p>
</section>
<section class="soi-wrap soi-block" id="soi-qotd-wrap">
  <h2 class="soi-h2"><span>Quote of the day</span></h2>
  <div id="soi-qotd"></div>
</section>
<section class="soi-wrap soi-block">
  <h2 class="soi-h2"><span>All quotes</span><small id="soi-q-count"></small></h2>
  <div class="soi-q-tools">
    <label class="soi-q-find"><span class="soi-vh">Find a quote</span><input id="soi-q-find" type="search" placeholder="Find a word, e.g. patience" autocomplete="off"></label>
    <div class="soi-dd" id="soi-q-year"><span class="soi-vh" id="soi-q-year-l">Year</span><button class="soi-dd-btn" type="button" aria-haspopup="listbox" aria-expanded="false" aria-labelledby="soi-q-year-l"><span>All years</span></button><ul class="soi-dd-list" role="listbox" aria-labelledby="soi-q-year-l" hidden></ul></div>
  </div>
  <div class="soi-q-topics" id="soi-q-topics" role="group" aria-label="Topic"></div>
  <div class="soi-q-list" id="soi-q-list"></div>
  <p class="soi-q-more"><button class="soi-btn" id="soi-q-more" type="button">Show more</button></p>
</section>
<div class="soi-q-toast" id="soi-q-toast" role="status" aria-live="polite"></div>
<script>
(function(){
  var ALL=[],shown=0,STEP=24,list=document.getElementById('soi-q-list'),find=document.getElementById('soi-q-find'),
      yearEl=document.getElementById('soi-q-year'),year=null,topics=document.getElementById('soi-q-topics'),more=document.getElementById('soi-q-more'),
      count=document.getElementById('soi-q-count'),toast=document.getElementById('soi-q-toast'),topic='',cur=[];
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function link(q){return location.origin+'/issues/'+q.s+'/#soi-'+q.a}
  function say(t){toast.textContent=t;toast.classList.add('is-on');clearTimeout(say.t);say.t=setTimeout(function(){toast.classList.remove('is-on')},2200)}
  function card(q,big){
    var el=document.createElement('article');el.className='soi-q'+(big?' soi-q-big':'');
    el.innerHTML='<blockquote><p>'+esc(q.t)+'</p></blockquote>'+
      '<p class="soi-q-src">'+(q.by?esc(q.by)+' · ':'')+'<a href="/issues/'+q.s+'/#soi-'+q.a+'">'+esc(q.at)+'</a> · Issue '+q.n+', '+esc(q.p)+'</p>'+
      '<p class="soi-q-tags">'+q.tp.map(function(t){return '<i>'+esc(t)+'</i>'}).join('')+'</p>'+
      '<p class="soi-q-act"><button type="button" data-act="save" aria-pressed="'+(window.soi&&soi.store.hasQuote(q))+'">'+(window.soi&&soi.store.hasQuote(q)?'Saved':'Save')+'</button><button type="button" data-act="img">Share as image</button><button type="button" data-act="wa">WhatsApp</button><button type="button" data-act="copy">Copy</button></p>';
    el.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;if(b.getAttribute('data-act')==='save'){var on=soi.store.toggleQuote(q);b.textContent=on?'Saved':'Save';b.setAttribute('aria-pressed',on);say(on?'Saved to this device':'Removed from Saved');return}act(b.getAttribute('data-act'),q)});
    return el;
  }
  function text(q){return '“'+q.t+'”\n— Spirit of Islam, Issue '+q.n+' ('+q.p+')\n'+link(q)}
  function act(a,q){
    if(a==='wa'){window.open('https://wa.me/?text='+encodeURIComponent(text(q)),'_blank','noopener');return}
    if(a==='copy'){(navigator.clipboard?navigator.clipboard.writeText(text(q)):Promise.reject()).then(function(){say('Copied')},function(){say('Could not copy')});return}
    image(q);
  }
  function wrap(ctx,t,max){var w=t.split(' '),lines=[],l='';w.forEach(function(x){var n=l?l+' '+x:x;if(ctx.measureText(n).width>max&&l){lines.push(l);l=x}else l=n});if(l)lines.push(l);return lines}
  function image(q){
    var W=1080,H=1350,c=document.createElement('canvas');c.width=W;c.height=H;var x=c.getContext('2d');
    function draw(){
      x.fillStyle='#204E60';x.fillRect(0,0,W,H);x.strokeStyle='#D4CC73';x.lineWidth=3;x.strokeRect(48,48,W-96,H-96);
      x.fillStyle='#D4CC73';x.save();x.translate(W/2,170);x.rotate(Math.PI/4);x.fillRect(-13,-13,26,26);x.restore();
      var size=q.t.length>330?40:q.t.length>220?46:q.t.length>120?54:64,lines;
      x.fillStyle='#EEEEE5';x.textAlign='center';x.textBaseline='middle';
      do{x.font='italic '+size+'px "Cita Pro Ita","Cita Pro",Georgia,serif';lines=wrap(x,'“'+q.t+'”',W-240);size-=2}while(lines.length*(size*1.42)>H-560&&size>26);
      var lh=(size+2)*1.42,y=H/2-((lines.length-1)*lh)/2-30;lines.forEach(function(l,i){x.fillText(l,W/2,y+i*lh)});
      x.fillStyle='#D4CC73';x.fillRect(W/2-60,H-330,120,3);
      x.fillStyle='#EEEEE5';x.font='600 30px "Plus Jakarta Sans",Arial,sans-serif';x.fillText('Spirit of Islam',W/2,H-270);
      x.globalAlpha=.8;x.font='26px "Plus Jakarta Sans",Arial,sans-serif';x.fillText('Issue '+q.n+' · '+q.p,W/2,H-225);
      x.fillText(location.host,W/2,H-150);x.globalAlpha=1;
      c.toBlob(function(b){
        var f=new File([b],'spirit-of-islam-quote.png',{type:'image/png'});
        if(navigator.canShare&&navigator.canShare({files:[f]})){navigator.share({files:[f],text:link(q)}).catch(function(){});return}
        var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=f.name;document.body.appendChild(a);a.click();a.remove();say('Image saved');
      },'image/png');
    }
    (document.fonts&&document.fonts.load?document.fonts.load('italic 40px "Cita Pro Ita"').then(draw,draw):draw());
  }
  function apply(){
    var w=find.value.trim().toLowerCase(),y=year?year.value:'';
    cur=ALL.filter(function(q){return (!y||String(q.y)===y)&&(!topic||q.tp.indexOf(topic)>-1)&&(!w||q.t.toLowerCase().indexOf(w)>-1||q.at.toLowerCase().indexOf(w)>-1)});
    list.innerHTML='';shown=0;count.textContent=cur.length.toLocaleString()+(cur.length===1?' quote':' quotes');grow();
    if(!cur.length)list.innerHTML='<p class="soi-q-none">No quote matches. Try another word or clear the filters.</p>';
  }
  function grow(){cur.slice(shown,shown+STEP).forEach(function(q){list.appendChild(card(q))});shown=Math.min(cur.length,shown+STEP);more.hidden=shown>=cur.length}
  more.addEventListener('click',grow);find.addEventListener('input',apply);
  topics.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;topic=topic===b.dataset.t?'':b.dataset.t;
    [].forEach.call(topics.children,function(c){c.setAttribute('aria-pressed',c.dataset.t===topic?'true':'false')});apply()});
  fetch('/assets/quotes.json').then(function(r){return r.json()}).then(function(d){
    ALL=d.quotes;
    d.topics.forEach(function(t){var b=document.createElement('button');b.type='button';b.dataset.t=t;b.textContent=t;b.setAttribute('aria-pressed','false');topics.appendChild(b)});
    var ys={};ALL.forEach(function(q){ys[q.y]=1});year=soiDropdown(yearEl,[['','All years']].concat(Object.keys(ys).sort().reverse().map(function(y){return [y,y]})),apply);
    var pool=ALL.filter(function(q){return q.t.length<260}),day=Math.floor(Date.now()/864e5-new Date().getTimezoneOffset()/1440);
    document.getElementById('soi-qotd').appendChild(card(pool[(day*7919)%pool.length],true));
    var m=location.hash.match(/^#t=(.+)$/);if(m){topic=decodeURIComponent(m[1]);[].forEach.call(topics.children,function(c){c.setAttribute('aria-pressed',c.dataset.t===topic?'true':'false')})}
    apply();
  }).catch(function(){list.innerHTML='<p class="soi-q-none">The quotes could not be loaded. Please reload the page.</p>'});
})();
</script>
"""


def build(root, out_dir, issues, page, write):
    quotes, dropped = collect(root, issues)
    quotes.sort(key=lambda q: (q["s"], q["a"]), reverse=True)
    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    json.dump({"topics": [t[0] for t in TOPICS], "quotes": quotes}, open(os.path.join(out_dir, "assets", "quotes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    body = PAGE.replace("__N__", f"{len(quotes):,}").replace("__ISSUES__", str(len({q['s'] for q in quotes})))
    write("quotes/index.html", page("Quotes – Spirit of Islam", body, cls="soi-quotes", current="quotes",
                                    desc="Reflections from every issue of Spirit of Islam: the closing thought of each article and the In Focus words of Maulana Wahiduddin Khan."))
    return len(quotes), dropped
