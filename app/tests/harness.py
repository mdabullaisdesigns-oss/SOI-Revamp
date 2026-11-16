"""Shared by the app test and the screenshot script: serves app/www, answers the website (app-config.json:
remote) from dist/, and answers every audio request with a short generated WAV so playback can be tested."""
import asyncio, io, json, os, struct, subprocess, sys, time, wave
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REMOTE = json.load(open(ROOT + '/app/app-config.json'))['remote'].rstrip('/')
PORT = 8765
B = f'http://localhost:{PORT}'

def wav(seconds=40):
    b = io.BytesIO()
    with wave.open(b, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(1); w.setframerate(8000); w.writeframes(bytes([128]) * 8000 * seconds)
    return b.getvalue()
WAV = wav()

def serve():
    p = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '-d', ROOT + '/app/www'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1); return p

async def route_all(ctx, state, log):
    """state['online'] False = no internet. log collects every request that left the app."""
    async def handle(route):
        u = route.request.url
        if u.startswith(B) or u.startswith('blob:') or u.startswith('data:'): return await route.continue_()
        log.append(u)
        if not state['online']: return await route.abort()
        if '/media/audio/' in u or u.endswith('.mp3'):
            await asyncio.sleep(state.get('audio_delay', 0))
            return await route.fulfill(body=WAV, content_type='audio/wav', headers={'Access-Control-Allow-Origin': '*', 'Accept-Ranges': 'bytes'})
        if not u.startswith(REMOTE): return await route.abort()
        path = u[len(REMOTE):].split('?')[0]
        f = ROOT + '/dist' + path + ('index.html' if path.endswith('/') else '')
        if os.path.exists(f):
            await route.fulfill(body=open(f, 'rb').read(), content_type='text/html' if f.endswith('html') else 'application/json', headers={'Access-Control-Allow-Origin': '*'})
        else: await route.fulfill(status=404, body='no')
    await ctx.route('**/*', handle)
