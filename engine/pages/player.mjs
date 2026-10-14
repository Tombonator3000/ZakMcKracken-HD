import {LocalLibrary, RemoteSource, ApiError, makeIndexes, privateFetch, blobIds, GAME_ROOT, MOD_ROOT} from './local-files.mjs';
import {attachTouch} from './touch.mjs';

// The page goes straight into the game. Only the first time (no key and no
// chosen folders) it asks for the read-only key to the game repository.
// HD or original graphics is chosen in the game's own menu (F5) in The Dig.
// I Zak er HD-patchen (DigHD) ikke slått på ennå: DigHD::create godtar bare The Dig
// og Sam & Max, så Zak kjører med originalgrafikken og trenger ingen HD-pakke.

const baseURL = new URL('./', location.href);
const library = new LocalLibrary(baseURL.pathname);
const networkFetch = window.fetch.bind(window);
const query = new URLSearchParams(location.search);
const $ = id => document.getElementById(id);
const canvas = $('canvas');
const statusElement = $('status');
let started = false;

function status(text = '', error = false) {
  statusElement.textContent = text;
  statusElement.hidden = !text;
  statusElement.classList.toggle('error', error);
}

function showScreen(id) {
  for (const screen of ['key', 'ended']) $(screen).hidden = screen !== id;
}

function showKey(message = '') {
  showScreen('key');
  status();
  $('key-error').textContent = message;
  $('key-error').hidden = !message;
  $('token').focus();
}

function megabytes(bytes) {
  return Math.round(bytes / 1048576);
}

// Big files are fetched once and kept. The game waits for them, so the screen
// says what is coming and how far it has come. De store filene er CD-musikken,
// TRACK1.FLA til TRACK21.FLA (2 til 25 MB hver), som hentes første gang et spor spilles.
function fileName(name) {
  const track = /^TRACK(\d+)\.FLA$/.exec(name);
  return track ? 'musikkspor ' + track[1] : name;
}
function progress(name, done, size) {
  if (done >= size) {
    $('loading').hidden = true;
    return;
  }
  const what = fileName(name);
  $('loading-text').textContent = 'Laster ned ' + what + ': ' + megabytes(done) + ' av ' + megabytes(size) + ' MB';
  $('loading-bar').style.width = (100 * done / size).toFixed(1) + '%';
  $('loading').hidden = false;
}

// WebGL draws the game. Without it, ScummVM's software drawing is used.
function hasWebGL() {
  try {
    const test = document.createElement('canvas');
    return Boolean(test.getContext('webgl2') || test.getContext('webgl'));
  } catch {
    return false;
  }
}

// The whole screen: browsers allow it only after a click or a key, so it comes
// with the first one. In Chrome and Edge Esc then still reaches the game (skip a
// scene); holding Esc leaves full screen. Firefox leaves full screen on Esc, and
// the next click or key brings it back.
function fullscreen() {
  if (!started || document.fullscreenElement || !document.documentElement.requestFullscreen) return;
  document.documentElement.requestFullscreen({navigationUI: 'hide'})
    .then(() => navigator.keyboard?.lock?.(['Escape']))
    .catch(() => {});
}
window.addEventListener('mousedown', fullscreen, true);
window.addEventListener('keydown', fullscreen, true);

// The connection is gone; the game waits and the file is tried again
function waiting(seconds) {
  status('Mistet kontakten med GitHub. Prøver igjen om ' + seconds + ' s …');
}

$('key').addEventListener('submit', async event => {
  event.preventDefault();
  const token = $('token').value.trim();
  if (!token) return;
  $('token').value = '';
  await library.setMeta('token', token);
  // Keeps the game in the browser when space runs low
  if (navigator.storage?.persist) navigator.storage.persist().catch(() => false);
  startRemote(token);
});

$('folders-link').addEventListener('click', () => { $('folders').hidden = false; });
for (const kind of ['game', 'mod']) {
  $(kind + '-files').addEventListener('change', async event => {
    if (!event.target.files.length) return;
    status(kind === 'game' ? 'Lagrer spillfilene i nettleseren …' : 'Lagrer HD-grafikken i nettleseren …');
    try {
      await library.import(event.target.files, kind);
      if (navigator.storage?.persist) await navigator.storage.persist().catch(() => false);
      if (library.metadata.game) {
        // Folders on this machine instead of the repository. HD-mappen er valgfri
        // (Zak har ingen HD-pakke ennå) og velges før spillmappen.
        await library.setMeta('token', undefined);
        startLocal();
      } else {
        status('Velg spillmappen også.');
      }
    } catch (error) {
      status(error.name === 'QuotaExceededError' ? 'Nettleseren har ikke nok lagringsplass.' : error.message, true);
    } finally {
      event.target.value = '';
    }
  });
}

$('again').addEventListener('click', () => location.reload());

async function startRemote(token) {
  showScreen(null);
  status('Henter fillisten fra GitHub …');
  const source = new RemoteSource(library, token, networkFetch, {progress, waiting});
  let rows;
  try {
    rows = await source.list();
  } catch (error) {
    if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
      await library.setMeta('token', undefined);
      showKey(error.message);
    } else {
      status(error instanceof TypeError ? 'Fikk ikke kontakt med GitHub. Sjekk nettet og last siden på nytt.' : error.message, true);
    }
    return;
  }
  // CD-musikken (TRACK1.FLA til TRACK21.FLA, 311 MiB i alt) hentes spor for spor
  // første gang sporet spilles, og hvert spor som har spilt, blir liggende i minnet
  // mens spillet kjører. Utelatt med ?uten-lyd, og på enheter som melder mindre enn
  // 4 GB minne. ScummVM sier da ved start at CD-sporene mangler (OK lukker meldingen),
  // og spillet går uten musikk. Ikke testet i nettleser.
  const withoutSound = query.has('uten-lyd') || (navigator.deviceMemory && navigator.deviceMemory < 4);
  await launch(source, withoutSound ? rows.filter(row => !/\/TRACK\d+\.FLA$/.test(row.path)) : rows);
  // Files an older HD pack had, are removed when the game has started
  setTimeout(() => library.pruneBlobs(blobIds(rows)).catch(() => {}), 30000);
}

function startLocal() {
  return launch(library, [...library.metadata.game.files, ...(library.metadata.mod?.files || [])]);
}

function sendKey(key, code, keyCode) {
  canvas.focus();
  const dispatch = type => canvas.dispatchEvent(new KeyboardEvent(type, {key, code, keyCode, which: keyCode, bubbles: true, cancelable: true}));
  dispatch('keydown');
  // ScummVM reads the key while polling; let it stay down for a moment
  setTimeout(() => dispatch('keyup'), 120);
}

// Touch on phones and tablets (touch.mjs): tap, drag, hold, two and three fingers
const keys = {F5: ['F5', 'F5', 116], Escape: ['Escape', 'Escape', 27]};
attachTouch(canvas, name => sendKey(...keys[name]));

canvas.addEventListener('contextmenu', event => event.preventDefault());
canvas.addEventListener('webglcontextlost', event => {
  event.preventDefault();
  status('Grafikken i nettleseren ble borte. Last siden på nytt.', true);
});

// Lerretet får riktig størrelse først etter en resize (Known Issues i
// dists/emscripten/README.md i ScummVM), så en sendes når spillet har satt opp
// skjermen. HD-patchen skriver "DigHD: screen" da, men DigHD er av for Zak. Det
// andre tegnet er den første spillfilen etter 00.LFL: ScummVM leser bare indeksen
// 00.LFL før spillet setter opp skjermen, og rommene og tegnsettene etterpå (sjekket
// med motoren på maskinen, ikke i nettleser). Statuslinjen fjernes samtidig.
let screenSeen = false;
function screenReady() {
  if (screenSeen) return;
  screenSeen = true;
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
    if (!statusElement.classList.contains('error')) status();
  }, 300);
}

async function launch(source, rows) {
  if (started) return;
  started = true;
  showScreen(null);
  status('Laster spillmotoren …');
  try {
    const [response, buildResponse] = await Promise.all([
      networkFetch(new URL('data/index.json', baseURL)),
      networkFetch(new URL('build.json', baseURL), {cache: 'no-store'})
    ]);
    if (!response.ok) throw new Error('Fant ikke spillmotorens data. Last siden på nytt.');
    if (!buildResponse.ok) throw new Error('Fant ikke spillmotorens versjon. Last siden på nytt.');
    // GitHub Pages lar nettleseren beholde filene i ti minutter. Etter en ny motor kan
    // scummvm.js og scummvm.wasm da komme fra hver sin versjon, og motoren stopper.
    // Motorfilene hentes derfor med sjekksummen fra build.json i adressen (fra Dig-HD-Web).
    const build = await buildResponse.json();
    const engineURL = path => {
      const url = new URL(path, baseURL);
      const hash = build.sha256?.[path];
      if (/^[a-f0-9]{64}$/.test(hash)) url.searchParams.set('v', hash);
      return url.href;
    };
    const indexes = makeIndexes(rows, await response.json());
    // A file the game could not get is shown, not swallowed
    const reader = {read: path => {
      if (path.startsWith(GAME_ROOT) && path !== GAME_ROOT + '00.LFL') screenReady();
      return source.read(path).then(blob => {
        if (/^Mistet kontakten/.test(statusElement.textContent)) status();
        return blob;
      }, error => { status(error.message, true); throw error; });
    }};
    window.fetch = privateFetch(reader, indexes, baseURL, networkFetch);

    // The DIGHD_ variables keep their names from The Dig. De gjør ingenting for
    // Zak før DigHD er slått på for spillet. DIGHD_MOD bare når det finnes en HD-pakke.
    const env = {HOME: '/home/zakmckracken-hd' + baseURL.pathname.replace(/[^a-zA-Z0-9_-]/g, '_')};
    if (rows.some(row => row.path.startsWith(MOD_ROOT))) env.DIGHD_MOD = MOD_ROOT.slice(0, -1);
    if (query.has('rom')) {
      // Zak har romfilene 01.LFL til 59.LFL
      const room = Number(query.get('rom'));
      if (!Number.isInteger(room) || room < 1 || room > 59) throw new Error('Romnummeret må være mellom 1 og 59.');
      Object.assign(env, {DIGHD_TEST_ROOM: String(room), DIGHD_TEST_AT: '240', DIGHD_SKIP_VIDEO: '1'});
    }
    if (query.has('klassisk')) env.DIGHD_CLASSIC = '1';
    if (query.has('gult')) env.DIGHD_SHOW_MISSING = '1';
    // The engine's test hooks work here too (docs/HD-MOTOR.md)
    for (const [key, value] of query) if (/^DIGHD_(TEST_[A-Z0-9_]+|SKIP_VIDEO|TEXT|VERIFY|BENCH)$/.test(key)) env[key] = value;
    // Uten høydekorrigering: FM-Towns-skjermen er 320 x 240, og med korrigeringen på
    // (standard i ScummVM) viser Zak en melding om det ved hver start.
    const args = ['--path=/data/games/zak', '--savepath=' + env.HOME, '--no-aspect-ratio', '--subtitles'];
    if (query.has('programvare') || !hasWebGL()) args.push('--gfx-mode=surfacesdl');
    args.push('zak');
    history.replaceState(null, '', location.pathname + location.search + '#' + args.join(' '));

    canvas.focus();
    // F5 is the game's menu, not reload; Ctrl+H is HD or classic (with the HD patch), not history
    window.addEventListener('keydown', event => {
      if (/^F([1-9]|10)$/.test(event.key) || event.key === 'Tab' || event.key === 'Backspace' ||
          ((event.ctrlKey || event.altKey) && !event.metaKey && event.key.length === 1)) event.preventDefault();
    }, true);
    // ScummVM asks for Web MIDI when it loads (dists/emscripten/custom_shell-pre.js),
    // and the browser then asks the player for permission. This blocks that question.
    // Zak (FM-Towns) bruker ikke MIDI: musikken kommer fra CD-sporene (TRACKn.FLA,
    // krever at motoren er bygget med FLAC) og lydeffektene fra FM-Towns-lydemuleringen
    // i ScummVM.
    Object.defineProperty(navigator, 'requestMIDIAccess', {configurable: true, value: () => new Promise(() => {})});
    window.Module = {
      canvas,
      locateFile: engineURL,
      preRun: [() => {
        for (const [key, value] of Object.entries(env)) ENV[key] = value;
        FS.mkdirTree(env.HOME);
      }],
      onRuntimeInitialized: () => status('Starter Zak McKracken …'),
      onAbort: text => status('Spillmotoren stoppet: ' + text, true),
      onExit: () => { status(); showScreen('ended'); },
      print: text => {
        console.log(text);
        if (/Could not load any graphics mode/.test(text)) {
          status('Nettleseren fikk ikke tegnet spillet. Slå på maskinvareakselerasjon i nettleseren, eller legg ?programvare bak adressen.', true);
        }
        // Fra HD-patchen, når den kjører (se screenReady)
        if (/^DigHD: screen /.test(text)) screenReady();
      },
      printErr: text => console.error(text),
      setStatus: text => { if (text) console.log(text); }
    };
    // An engine that stops must not leave the page looking like it is still starting
    window.addEventListener('error', event => status('Spillmotoren stoppet: ' + (event.message || 'ukjent feil'), true));
    window.addEventListener('unhandledrejection', event => {
      if (!statusElement.classList.contains('error')) status('Spillmotoren stoppet: ' + (event.reason?.message || event.reason || 'ukjent feil'), true);
    });
    const script = document.createElement('script');
    script.src = engineURL('scummvm.js');
    script.onerror = () => status('Spillmotoren kunne ikke lastes. Last siden på nytt.', true);
    document.body.appendChild(script);
  } catch (error) {
    started = false;
    window.fetch = networkFetch;
    status(error.message, true);
  }
}

try {
  if (!globalThis.WebAssembly) throw new Error('Denne nettleseren støtter ikke spillmotoren. Bruk en oppdatert Chrome, Edge eller Firefox.');
  await library.open();
  // ?ny-nokkel asks for a new key
  const token = query.has('ny-nokkel') ? null : await library.getMeta('token');
  if (token) await startRemote(token);
  else if (!query.has('ny-nokkel') && library.metadata.game) await startLocal();
  else showKey();
} catch (error) {
  status('Kunne ikke starte: ' + error.message, true);
}
