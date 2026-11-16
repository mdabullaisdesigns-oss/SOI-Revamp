// Contact form -> email to the SOI developer address, with strict spam protection:
//  1. Cloudflare Turnstile (invisible check that a person, not a bot, sent it)
//  2. a hidden "website" field that only bots fill in
//  3. a minimum time on the page (bots submit instantly)
//  4. at most 3 messages per visitor per hour (by IP, kept in the edge cache)
//  5. messages with more than 2 links, or too short/long, are refused
// Settings (Cloudflare Pages -> soi-preview -> Settings -> Variables and secrets):
//   TURNSTILE_SECRET  secret key of the Turnstile widget
//   RESEND_API_KEY    key from resend.com (domain spiritofislam.co.in verified there)
//   CONTACT_TO        optional, default developer@spiritofislam.co.in
//   CONTACT_FROM      optional, default "Spirit of Islam website <website@spiritofislam.co.in>"
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });

export async function onRequestPost({ request, env }) {
  let f;
  try { f = await request.formData(); } catch { return json({ ok: false, error: 'Please try again.' }, 400); }
  const get = (k) => String(f.get(k) || '').trim();
  const name = get('name').slice(0, 120), email = get('email').slice(0, 200), subject = get('subject').slice(0, 160), msg = get('message');
  if (get('website')) return json({ ok: true });                                   // bot filled the hidden field: pretend success
  if (Date.now() - Number(get('t') || 0) < 4000) return json({ ok: false, error: 'Please take a moment and send again.' }, 400);
  if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email) || msg.length < 10 || msg.length > 5000)
    return json({ ok: false, error: 'Please fill in your name, a valid email and a message (10–5000 characters).' }, 400);
  if ((msg.match(/https?:\/\/|www\./gi) || []).length > 2) return json({ ok: false, error: 'Please include no more than two links.' }, 400);

  const ip = request.headers.get('cf-connecting-ip') || '';
  if (!env.TURNSTILE_SECRET) return json({ ok: false, error: 'The form is not switched on yet. Please write to us by email.' }, 503);
  const v = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST', body: new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: get('cf-turnstile-response'), remoteip: ip }) }).then(r => r.json()).catch(() => ({}));
  if (!v.success) return json({ ok: false, error: 'The spam check did not pass. Please reload the page and try again.' }, 400);

  const cache = caches.default, key = new Request('https://rate.soi/contact/' + encodeURIComponent(ip));
  const seen = Number((await cache.match(key).then(r => r && r.text())) || 0);
  if (seen >= 3) return json({ ok: false, error: 'You have sent several messages already. Please try again in an hour.' }, 429);
  await cache.put(key, new Response(String(seen + 1), { headers: { 'cache-control': 'max-age=3600' } }));

  if (!env.RESEND_API_KEY) return json({ ok: false, error: 'The form is not switched on yet. Please write to us by email.' }, 503);
  const esc = (s) => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST', headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.CONTACT_FROM || 'Spirit of Islam website <website@spiritofislam.co.in>',
      to: [env.CONTACT_TO || 'developer@spiritofislam.co.in'], reply_to: email,
      subject: '[SOI website] ' + (subject || 'Message from ' + name),
      html: `<p><b>${esc(name)}</b> &lt;${esc(email)}&gt; wrote:</p><p style="white-space:pre-wrap">${esc(msg)}</p><hr><p style="color:#777;font-size:12px">Sent from the contact form on spiritofislam.co.in</p>` }) });
  if (!r.ok) return json({ ok: false, error: 'Sorry, the message could not be sent. Please try again later.' }, 502);
  return json({ ok: true });
}
