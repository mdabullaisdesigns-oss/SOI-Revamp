// Mailing list sign-up -> Kit (kit.com). Kit sends the confirmation email (double opt-in) and handles unsubscribes.
// Settings (Cloudflare Pages -> soi-preview -> Variables and secrets): KIT_API_KEY (v4 API key), KIT_FORM_ID, TURNSTILE_SECRET
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });
export async function onRequestPost({ request, env }) {
  let f; try { f = await request.formData(); } catch { return json({ ok: false, error: 'Please try again.' }, 400); }
  const get = (k) => String(f.get(k) || '').trim();
  if (get('website')) return json({ ok: true });
  const email = get('email').slice(0, 200), name = get('name').slice(0, 100);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return json({ ok: false, error: 'Please enter a valid email address.' }, 400);
  if (!env.KIT_API_KEY || !env.KIT_FORM_ID || !env.TURNSTILE_SECRET) return json({ ok: false, error: 'Subscriptions open soon. Thank you for your patience.' }, 503);
  const v = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST',
    body: new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: get('cf-turnstile-response'), remoteip: request.headers.get('cf-connecting-ip') || '' }) }).then(r => r.json()).catch(() => ({}));
  if (!v.success) return json({ ok: false, error: 'The spam check did not pass. Please reload and try again.' }, 400);
  const h = { 'X-Kit-Api-Key': env.KIT_API_KEY, 'content-type': 'application/json' };
  const s = await fetch('https://api.kit.com/v4/subscribers', { method: 'POST', headers: h, body: JSON.stringify({ email_address: email, first_name: name || undefined, state: 'inactive' }) });
  if (!s.ok) return json({ ok: false, error: 'Sorry, that did not work. Please try again later.' }, 502);
  const a = await fetch(`https://api.kit.com/v4/forms/${env.KIT_FORM_ID}/subscribers`, { method: 'POST', headers: h, body: JSON.stringify({ email_address: email }) });
  if (!a.ok) return json({ ok: false, error: 'Sorry, that did not work. Please try again later.' }, 502);
  return json({ ok: true });
}
