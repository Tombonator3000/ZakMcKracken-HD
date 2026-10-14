#!/usr/bin/env python3
"""Spiller nettsiden i Chromium (Playwright) med spillfilene fra repoet, og tar skjermbilder.

Forespørslene til api.github.com og tombonator3000.github.io går gjennom Python (requests),
så en proxy med egen CA (som i Claude-økten) virker uten oppsett i nettleseren. I økten
holder en dummy-nøkkel (proxyen legger på tilgangen); ellers settes NOKKEL til en ekte
lesenøkkel. Skriver skjermbilder og rapport.json (kall til GitHub, konsollen, feil).

Bruk:
  python3 tools/nettsidetest.py https://tombonator3000.github.io/ZakMcKracken-HD/ work/nettsidetest
  ... --sekunder 150 --klikktid 100 --etter 10 --klikk 62.5,55 --klikk h68,31
      (venter til spillet er i gang, klikker på gulvet og holder høyre knapp over telefonen)
  ... --mobil            (Pixel 7 med berøring; SwiftShader er da svært treg)

Krever: pip install playwright requests pillow, og playwright install chromium.
Første gang 14. oktober 2026 (Claude), se docs/PAGES.md under Verifisering.
"""
import argparse
import json
import os
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('url')
ap.add_argument('ut')
ap.add_argument('--sekunder', type=int, default=90)
ap.add_argument('--mobil', action='store_true')
ap.add_argument('--esc', action='store_true', help='Esc etter 40 s (hopper over introen)')
ap.add_argument('--klikk', action='append', default=[], help='x,y i prosent av lerretet (h foran for høyreklikk holdt), etter --klikktid s')
ap.add_argument('--klikktid', type=int, default=60)
ap.add_argument('--etter', type=int, default=0, help='sekunder å vente etter at spillet er i gang')
args = ap.parse_args()
ut = Path(args.ut)
ut.mkdir(parents=True, exist_ok=True)

ca = '/root/.ccr/ca-bundle.crt'
session = requests.Session()
session.verify = ca if os.path.exists(ca) else True
api = []
site = []
console = []
errors = []
CORS = {'access-control-allow-origin': '*',
        'access-control-expose-headers': 'Retry-After, X-RateLimit-Remaining'}


def pages(route, request):
    # Nettsiden på github.io, også gjennom Python og proxyen
    if request.method != 'GET':
        route.continue_()
        return
    r = session.get(request.url, timeout=300)
    site.append(request.url)
    keep = {k: v for k, v in r.headers.items() if k.lower() in ('content-type', 'cache-control', 'etag', 'last-modified')}
    route.fulfill(status=r.status_code, body=r.content, headers=keep)


def github(route, request):
    if request.method == 'OPTIONS':
        route.fulfill(status=204, headers={**CORS, 'access-control-allow-headers': 'authorization, accept',
                                           'access-control-allow-methods': 'GET'})
        return
    headers = {k: v for k, v in request.headers.items() if k.lower() in ('authorization', 'accept')}
    t = time.time()
    r = session.get(request.url, headers=headers, timeout=300)
    api.append({'url': request.url.split('/repos/')[1], 'status': r.status_code, 'bytes': len(r.content),
                'sek': round(time.time() - t, 1), 'auth': headers.get('authorization', '')[:12]})
    route.fulfill(status=r.status_code, body=r.content,
                  headers={**CORS, 'content-type': r.headers.get('content-type', 'application/octet-stream')})


with sync_playwright() as p:
    browser = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader',
                                      '--autoplay-policy=no-user-gesture-required'])
    if args.mobil:
        context = browser.new_context(**p.devices['Pixel 7'])
    else:
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    page.route('https://api.github.com/**', github)
    page.route('https://tombonator3000.github.io/**', pages)
    page.on('request', lambda r: site.append(r.url) if r.url.startswith('http://127.0.0.1') else None)
    page.on('console', lambda m: console.append(f'{m.type}: {m.text}'))
    page.on('pageerror', lambda e: errors.append(str(e)))
    start = time.time()
    page.goto(args.url)
    page.wait_for_selector('#token', state='visible', timeout=30000)
    page.screenshot(path=str(ut / '00-nokkel.png'))
    page.fill('#token', os.environ.get('NOKKEL', 'dummy-nokkel'))
    page.press('#token', 'Enter')
    shots = [5, 15, 30, 45, 60, 75, 90, 120, 150, 180]
    done_esc = done_click = False
    for s in shots:
        if s > args.sekunder:
            break
        while time.time() - start < s:
            page.wait_for_timeout(500)
            if args.esc and not done_esc and time.time() - start > 40:
                page.locator('#canvas').focus()
                page.keyboard.press('Escape')
                done_esc = True
            if args.klikk and not done_click and time.time() - start > args.klikktid:
                box = page.locator('#canvas').bounding_box()
                # Vent til spillet er i gang: setningslinjen og inventaret nederst har tekst
                # (under mellomsekvensene er den delen svart)
                import io
                from PIL import Image
                for _ in range(240):
                    shot = Image.open(io.BytesIO(page.screenshot(clip={'x': box['x'], 'y': box['y'] + box['height'] * 0.6,
                                                                      'width': box['width'], 'height': box['height'] * 0.18}))).convert('L')
                    if sum(1 for v in shot.getdata() if v > 40) > 200:
                        break
                    page.wait_for_timeout(1000)
                print('spillet i gang etter', round(time.time() - start), 's', flush=True)
                page.wait_for_timeout(args.etter * 1000)
                for n, k in enumerate(args.klikk):
                    hold = k.startswith('h')
                    x, y = (float(v) for v in k.lstrip('h').split(','))
                    px, py = box['x'] + box['width'] * x / 100, box['y'] + box['height'] * y / 100
                    page.mouse.move(px, py)
                    page.wait_for_timeout(300)
                    if hold:
                        page.mouse.down(button='right')
                        page.wait_for_timeout(1200)
                        page.screenshot(path=str(ut / f'klikk{n}-holdt.png'))
                        page.mouse.up(button='right')
                    elif args.mobil:
                        page.touchscreen.tap(px, py)
                    else:
                        page.mouse.click(px, py)
                    page.wait_for_timeout(2500)
                    page.screenshot(path=str(ut / f'klikk{n}.png'))
                done_click = True
        page.screenshot(path=str(ut / f'{s:03d}s.png'))
    state = page.evaluate('''() => ({
        status: document.getElementById('status').textContent,
        statusHidden: document.getElementById('status').hidden,
        keyHidden: document.getElementById('key').hidden,
        canvas: [document.getElementById('canvas').width, document.getElementById('canvas').height,
                 document.getElementById('canvas').clientWidth, document.getElementById('canvas').clientHeight],
        hash: location.hash
    })''')
    browser.close()

report = {'state': state, 'api': api, 'site': sorted(set(u.split('?')[0] for u in site)),
          'console': console[-80:], 'errors': errors}
(ut / 'rapport.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
print(json.dumps({'state': state, 'api_kall': len(api), 'api_bytes': sum(a['bytes'] for a in api),
                  'site': report['site'], 'errors': errors}, indent=1, ensure_ascii=False))
