// Contact form, two steps, with strict spam protection:
//   step "code": checks the form (Turnstile, hidden field, time on page, link limit, promotional words,
//                rate limit) and emails a 6-digit code to the sender. Nothing is sent to SOI yet.
//   step "send": the sender types the code; only then is the message emailed to SOI.
// The code is not stored anywhere: the browser holds a signed token (HMAC) that ties the code to this
// email address and this exact message for 15 minutes.
// Settings (Cloudflare Pages -> soi-preview -> Settings -> Variables and secrets):
//   TURNSTILE_SECRET, RESEND_API_KEY, OTP_SECRET (any long random text)
//   CONTACT_TO (default developer@spiritofislam.co.in), CONTACT_FROM (default website@spiritofislam.co.in)
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });
const enc = new TextEncoder();
const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
async function hmac(key, text) { const k = await crypto.subtle.importKey('raw', enc.encode(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']); return b64(await crypto.subtle.sign('HMAC', k, enc.encode(text))); }
async function sha(text) { return b64(await crypto.subtle.digest('SHA-256', enc.encode(text))); }
const esc = (s) => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const PROMO = /\b(seo|backlinks?|guest post|crypto|bitcoin|forex|casino|betting|loan offer|web ?design services|rank (your|on) google|marketing services|increase (your )?traffic|buy followers|whatsapp me|telegram me|discount offer)\b/i;
const SUBJECTS = ['A question about an article', 'The magazine or a subscription', 'Audio or the website', 'Children’s Corner', 'Feedback or a suggestion', 'Something else'];

async function mail(env, to, subject, html, replyTo) {
  const r = await fetch('https://api.resend.com/emails', { method: 'POST', headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({ from: env.CONTACT_FROM || 'Spirit of Islam website <website@spiritofislam.co.in>', to: [to], subject, html, ...(replyTo ? { reply_to: replyTo } : {}) }) });
  return r.ok;
}

export async function onRequestPost({ request, env }) {
  let f; try { f = await request.formData(); } catch { return json({ ok: false, error: 'Please try again.' }, 400); }
  const get = (k) => String(f.get(k) || '').trim();
  const step = get('step') || 'code', name = get('name').slice(0, 120), email = get('email').slice(0, 200).toLowerCase(), subject = get('subject'), msg = get('message');
  if (!env.TURNSTILE_SECRET || !env.RESEND_API_KEY || !env.OTP_SECRET) return json({ ok: false, error: 'The form is not switched on yet. Please write to us by email.' }, 503);
  if (get('website')) return json({ ok: true, step });                                         // a bot filled the hidden field
  if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email) || msg.length < 10 || msg.length > 3000)
    return json({ ok: false, error: 'Please give your name, a valid email and a message (10–3000 characters).' }, 400);
  if (!SUBJECTS.includes(subject)) return json({ ok: false, error: 'Please choose what your message is about.' }, 400);
  if ((msg.match(/https?:\/\/|www\./gi) || []).length > 2) return json({ ok: false, error: 'Messages with more than two links are not accepted.' }, 400);
  if (PROMO.test(msg) || PROMO.test(name)) return json({ ok: false, error: 'This looks like a promotional message, which this form does not accept.' }, 400);
  const fp = await sha([name, email, subject, msg].join('\n'));                               // ties the code to this exact message

  if (step === 'code') {
    if (Date.now() - Number(get('t') || 0) < 4000) return json({ ok: false, error: 'Please take a moment and try again.' }, 400);
    const ip = request.headers.get('cf-connecting-ip') || '';
    const v = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: get('cf-turnstile-response'), remoteip: ip }) }).then(r => r.json()).catch(() => ({}));
    if (!v.success) return json({ ok: false, error: 'The security check did not pass. Please reload the page and try again.' }, 400);
    const cache = caches.default;
    for (const id of ['ip/' + ip, 'mail/' + email]) {                                          // at most 3 codes an hour per visitor and per address
      const key = new Request('https://rate.soi/contact/' + encodeURIComponent(id)), n = Number((await cache.match(key).then(r => r && r.text())) || 0);
      if (n >= 3) return json({ ok: false, error: 'Too many attempts. Please try again in an hour.' }, 429);
      await cache.put(key, new Response(String(n + 1), { headers: { 'cache-control': 'max-age=3600' } }));
    }
    const code = String(crypto.getRandomValues(new Uint32Array(1))[0] % 1000000).padStart(6, '0'), exp = Date.now() + 15 * 60 * 1000;
    const token = exp + '.' + await hmac(env.OTP_SECRET, [exp, email, fp, code].join('|'));
    const ok = await mail(env, email, 'Your Spirit of Islam code: ' + code,
      `<p>Assalamu alaikum ${esc(name)},</p><p>Your code to send your message to Spirit of Islam is:</p><p style="font-size:28px;font-weight:700;letter-spacing:6px">${code}</p><p>It works for 15 minutes. If you did not write to us, you can ignore this email.</p>`);
    if (!ok) return json({ ok: false, error: 'We could not send the code to that address. Please check it and try again.' }, 502);
    return json({ ok: true, step: 'code', token });
  }

  const [exp, sig] = get('token').split('.'), code = get('code').replace(/\D/g, '');
  if (!exp || Date.now() > Number(exp)) return json({ ok: false, error: 'The code has expired. Please ask for a new one.' }, 400);
  if (sig !== await hmac(env.OTP_SECRET, [exp, email, fp, code].join('|'))) return json({ ok: false, error: 'That code is not right. Please check the email and try again.' }, 400);
  const ok = await mail(env, env.CONTACT_TO || 'developer@spiritofislam.co.in', '[SOI website] ' + subject + ' – ' + name,
    `<p><b>${esc(name)}</b> &lt;${esc(email)}&gt; (email address confirmed with a code)</p><p><b>About:</b> ${esc(subject)}</p><p style="white-space:pre-wrap">${esc(msg)}</p><hr><p style="color:#777;font-size:12px">Sent from the contact form on spiritofislam.co.in</p>`, email);
  if (!ok) return json({ ok: false, error: 'Sorry, the message could not be sent. Please try again later.' }, 502);
  return json({ ok: true, step: 'send' });
}
