// Serves the magazine audio (and PDFs) from the R2 bucket on the site's own address:
//   /media/audio/2018/SOI-2018-07-<article>.mp3  ->  R2 soi-media: audio/2018/SOI-2018-07-<article>.mp3
// Supports Range requests so the player can seek, and lets browsers/CDN cache for a year.
export async function onRequest({ params, request, env }) {
  if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method not allowed', { status: 405 });
  const key = (params.path || []).join('/');
  if (!/^(audio|pdfs|pages)\/[\w.\-\/]+$/.test(key) || key.includes('..')) return new Response('Not found', { status: 404 });
  const range = request.headers.get('range');
  const obj = request.method === 'HEAD' ? await env.MEDIA.head(key)
    : await env.MEDIA.get(key, range ? { range: request.headers } : undefined);
  if (!obj) return new Response('Not found', { status: 404 });
  const h = new Headers();
  obj.writeHttpMetadata(h);
  h.set('etag', obj.httpEtag);
  h.set('accept-ranges', 'bytes');
  h.set('cache-control', 'public, max-age=31536000, immutable');
  h.set('access-control-allow-origin', '*');
  if (key.endsWith('.pdf')) h.set('content-disposition', 'inline; filename="' + key.split('/').pop() + '"');   // read in the browser, not downloaded
  if (!h.get('content-type')) h.set('content-type', key.endsWith('.mp3') ? 'audio/mpeg' : key.endsWith('.webp') ? 'image/webp' : 'application/pdf');
  if (request.method === 'HEAD') { h.set('content-length', String(obj.size)); return new Response(null, { headers: h }); }
  if (range && obj.range) {
    const off = obj.range.offset ?? (obj.range.suffix != null ? obj.size - obj.range.suffix : 0);
    const len = obj.range.length ?? (obj.range.suffix != null ? obj.range.suffix : obj.size - off);
    h.set('content-range', `bytes ${off}-${off + len - 1}/${obj.size}`);
    h.set('content-length', String(len));
    return new Response(obj.body, { status: 206, headers: h });
  }
  h.set('content-length', String(obj.size));
  return new Response(obj.body, { headers: h });
}
