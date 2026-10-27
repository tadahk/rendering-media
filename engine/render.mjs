// Render a city timeline to JPEG frames (and optionally an MP4) with headless Chromium and software WebGL.
//   node engine/render.mjs --scene chicago/data/scene.json --timeline chicago/timeline.json --out out/x [--w 1920 --h 1080 --fps 30]
//   --from 10 --to 16        render only that span (a slice); frames are numbered from the global frame index
//   --encode slice.mp4       encode the rendered span to this file
//   --stills 2,15,27.5       render single frames instead; --opts '{"clean":true,"year":1803.8}' passes options to renderAt
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/npm-tools/node_modules/playwright')); }

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, all) => (v.startsWith('--') ? [...a, [v.slice(2), all[i + 1]]] : a), []));
const ROOT = resolve(new URL('..', import.meta.url).pathname);
const W = +(args.w || 1920), H = +(args.h || 1080), FPS = +(args.fps || 30);
const outDir = resolve(ROOT, args.out || 'out/render');
const timeline = JSON.parse(await readFile(resolve(ROOT, args.timeline), 'utf8'));
const opts = args.opts ? JSON.parse(args.opts) : {};

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.woff2': 'font/woff2' };
const server = createServer(async (req, res) => {
  try {
    const p = join(ROOT, decodeURIComponent(req.url.split('?')[0]));
    if (!p.startsWith(ROOT)) throw new Error('outside root');
    res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' });
    res.end(await readFile(p));
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-sandbox'] });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.error('page:', m.text().slice(0, 400)); });
page.on('pageerror', (e) => console.error('page error:', e.message));
await page.goto(`http://localhost:${port}/engine/city.html?w=${W}&h=${H}&aa=${args.aa ?? 1}&shadow=${args.shadow ?? 2048}&soft=${args.soft ?? 0}&shadows=${args.shadows ?? 1}&scene=/${args.scene}&timeline=/${args.timeline}`);
await page.waitForFunction('window.ready === true', null, { timeout: 600000 });
await mkdir(outDir, { recursive: true });

const save = async (file, dataUrl) => writeFile(file, Buffer.from(dataUrl.split(',')[1], 'base64'));
const t0 = Date.now();
if (args.stills) {
  for (const s of args.stills.split(',').map(Number)) {
    await save(join(outDir, `still_${s.toFixed(2).padStart(7, '0')}.jpg`), await page.evaluate(([t, o]) => window.renderAt(t, o), [s, { q: 0.97, ...opts }]));
    console.log(`still ${s}s`);
  }
} else {
  const start = +(args.from || 0), end = +(args.to || timeline.duration);
  const first = Math.round(start * FPS), last = Math.round(end * FPS);
  for (let f = first; f < last; f++) {
    await save(join(outDir, `f_${String(f).padStart(5, '0')}.jpg`), await page.evaluate(([t, o]) => window.renderAt(t, o), [f / FPS, opts]));
    if ((f - first) % 60 === 0) console.log(`frame ${f - first}/${last - first}  ${((Date.now() - t0) / 1000 / (f - first + 1)).toFixed(2)} s/frame`);
  }
  if (args.encode) {
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-start_number', String(first), '-i', join(outDir, 'f_%05d.jpg'),
      '-frames:v', String(last - first), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', resolve(ROOT, args.encode)]);
    console.log('encoded', args.encode);
  }
}
console.log(`done in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
await browser.close();
server.close();
