// The game and the HD pack never come from this site. They are read from the
// game repository on GitHub with the owner's own read-only key, or from folders
// on this machine, and kept in IndexedDB. Only the ScummVM engine is downloaded
// from the site.
export const GAME_ROOT = '/data/games/zak/';
export const MOD_ROOT = '/data/mods/gpt/';

// The game repository and where in it the files are. Tom vil ha alt i main (14. oktober
// 2026): spillfilene i game/ og HD-moden i mods/gpt/. Til grenene er flettet inn, ligger
// spillet i grenen spilldata og moden i grenen hd-mod. Siden ser i main først og bruker
// grenene når main ikke har filene, så den virker både før og etter flettingen.
// Moden er valgfri: uten mod.json (hd-mod har bare README og SHA256SUMS til den første
// moden er laget) starter spillet med originalgrafikken.
export const REPO = 'Tombonator3000/ZakMcKracken-HD';
export const SOURCES = {
  game: [{branch: 'main', prefix: 'game/', marker: '00.LFL'}, {branch: 'spilldata', prefix: 'game/', marker: '00.LFL'}],
  mod: [{branch: 'main', prefix: 'mods/gpt/', marker: 'mod.json'}, {branch: 'hd-mod', prefix: '', marker: 'mod.json'}]
};
const API = 'https://api.github.com/repos/' + REPO + '/';

export function selectFiles(files, kind) {
  const root = kind === 'game' ? GAME_ROOT : MOD_ROOT;
  const selected = new Map();
  for (const file of files) {
    const parts = (file.webkitRelativePath || file.name).split('/');
    if (file.webkitRelativePath) parts.shift();
    if (parts.some(part => !part || part === '.' || part === '..')) continue;
    let relative = parts.join('/');
    if (kind === 'game') {
      relative = relative.toUpperCase();
      // Zak FM-Towns: indeksen 00.LFL, rommene 01.LFL til 59.LFL, tegnsettene 98.LFL og
      // 99.LFL, og CD-musikken Track1.fla til Track21.fla
      if (!/^(\d\d\.LFL|TRACK\d+\.FLA)$/.test(relative)) continue;
    } else {
      if (!/^(mod\.json|rooms\/room\d+(_idx)?\.png|objects\/obj\d+_[0-9a-fA-F]{2}(_idx)?\.png|costumes\/costume\d+_\d+(_idx|_hd)?\.png|fonts\/[a-z0-9-]+\.(txt|png)|ui\/verbhjul\/[a-z-]+\.png|inventory\/obj\d+\.png)$/.test(relative)) continue;
    }
    const path = root + relative;
    if (selected.has(path)) throw new Error('To filer har samme navn: ' + relative);
    selected.set(path, {path, size: file.size, blob: file});
  }
  if (kind === 'game' && ['00.LFL', '98.LFL', '99.LFL'].some(name => !selected.has(root + name))) {
    throw new Error('Velg mappen som inneholder 00.LFL, 98.LFL og 99.LFL.');
  }
  if (kind !== 'game' && (!selected.has(root + 'mod.json') || ![...selected.keys()].some(p => /\/rooms\/room\d+\.png$/.test(p)))) {
    throw new Error('Velg HD-mappen som inneholder mod.json og rooms.');
  }
  return [...selected.values()];
}

// What the page shows about a chosen folder. Counts the HD images, not the _idx files.
// A figure cel can have both a cut-out image and a soft one (_hd.png); it counts once.
export function summarize(rows, created = null) {
  const count = re => rows.filter(row => re.test(row.path)).length;
  return {
    files: rows.map(({path, size}) => ({path, size})),
    bytes: rows.reduce((sum, row) => sum + row.size, 0),
    rooms: count(/\/rooms\/room\d+\.png$/),
    objects: count(/\/objects\/obj\d+_[0-9a-fA-F]{2}\.png$/),
    cels: new Set(rows.map(row => row.path.match(/\/costumes\/(costume\d+_\d+)(_hd)?\.png$/)?.[1]).filter(Boolean)).size,
    created
  };
}

export function makeIndexes(rows, staticRoot = {}) {
  const indexes = new Map([['/data/index.json', {...staticRoot}]]);
  for (const {path, size} of rows) {
    const parts = path.split('/').filter(Boolean);
    if (parts.shift() !== 'data' || parts.some(p => p === '..' || p === '.')) throw new Error('Ugyldig filsti');
    let directory = '/data';
    for (let i = 0; i < parts.length; i++) {
      const key = directory + '/index.json';
      if (!indexes.has(key)) indexes.set(key, {});
      const index = indexes.get(key);
      index[parts[i]] = i === parts.length - 1 ? size : {};
      directory += '/' + parts[i];
    }
  }
  return indexes;
}

// A git tree listing as rows for makeIndexes(), with the same rules as a chosen folder.
// Hver fil er én git-blob: alle Zak-filene er under 90 MB, så ingen ligger i deler.
export function treeRows(tree, prefix, kind) {
  const files = [];
  for (const item of tree) {
    if (item.type !== 'blob' || !item.path.startsWith(prefix)) continue;
    const relative = item.path.slice(prefix.length);
    files.push({name: relative.split('/').at(-1), webkitRelativePath: 'repo/' + relative, size: item.size, sha: item.sha});
  }
  return selectFiles(files, kind).map(row => ({path: row.path, size: row.size, sha: row.blob.sha}));
}

// All blob ids a listing uses
export function blobIds(rows) {
  return new Set(rows.map(row => row.sha));
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function apiError(status) {
  if (status === 401) return new ApiError(status, 'GitHub godtar ikke nøkkelen. Lag en ny og lim den inn.');
  if (status === 403 || status === 404) return new ApiError(status, 'Nøkkelen har ikke lesetilgang til ' + REPO + '.');
  return new ApiError(status, 'GitHub svarte ' + status + '. Prøv igjen litt senere.');
}

// Reads a response while telling how far it has come; big files show progress.
async function readBody(response, size, progress) {
  if (!response.body || !progress) return response.blob();
  const reader = response.body.getReader();
  const chunks = [];
  let done = 0;
  for (;;) {
    const part = await reader.read();
    if (part.done) break;
    chunks.push(part.value);
    done += part.value.length;
    progress(done, size);
  }
  progress(size, size);
  return new Blob(chunks);
}

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

// The files from the game repository (main, or the old branches), fetched when the engine asks for them
// and kept by git blob id, so a new HD pack only fetches what has changed.
// A lost connection is tried again and again while the game waits: a file the
// engine cannot open stops the game.
//   progress(name, done, size): big files on their way
//   waiting(seconds): the connection is gone, next try in so many seconds
export class RemoteSource {
  constructor(library, token, networkFetch, {progress = null, waiting = null, sleep = wait} = {}) {
    this.library = library;
    this.token = token;
    this.fetch = networkFetch;
    this.progress = progress;
    this.waiting = waiting;
    this.sleep = sleep;
    this.rows = new Map();
  }

  api(path, accept, cache = 'default') {
    return this.fetch(API + path, {headers: {Authorization: 'Bearer ' + this.token, Accept: accept}, cache});
  }

  // Runs attempt() until it works. Network errors, 5xx, 429 and rate limits are
  // tried again (at most `tries` times), a key GitHub rejects is not.
  async retry(attempt, tries = Infinity) {
    for (let n = 1; ; n++) {
      let delay = Math.min(1000 * 2 ** (n - 1), 15000);
      try {
        return await attempt();
      } catch (error) {
        const limited = error instanceof ApiError && (error.status === 429 || error.status >= 500 || error.rateLimited);
        if (!(error instanceof TypeError || limited) || n >= tries) throw error;
        if (error.retryAfter) delay = Math.min(error.retryAfter * 1000, 60000);
      }
      this.waiting?.(Math.round(delay / 1000));
      await this.sleep(delay);
    }
  }

  async get(path, accept, cache) {
    const response = await this.api(path, accept, cache);
    if (response.ok) return response;
    const error = apiError(response.status);
    error.rateLimited = response.status === 403 && (response.headers.get('x-ratelimit-remaining') === '0' || response.headers.has('retry-after'));
    error.retryAfter = Number(response.headers.get('retry-after')) || 0;
    throw error;
  }

  // The file list of one branch, read once per list(). main must be readable: 404 there
  // means the key has no access. The other branches may be gone after the merge (null).
  async tree(branch, trees) {
    if (trees.has(branch)) return trees.get(branch);
    let tree = null;
    try {
      const data = await this.retry(async () =>
        (await this.get('git/trees/' + branch + '?recursive=1', 'application/vnd.github+json', 'no-store')).json(), 3);
      if (data.truncated) throw new Error('Fillisten fra GitHub ble avkortet.');
      tree = data.tree;
    } catch (error) {
      if (branch === 'main' || !(error instanceof ApiError && error.status === 404)) throw error;
    }
    trees.set(branch, tree);
    return tree;
  }

  // The game and, if there is one, the HD pack: from main when it has them, else from
  // the old branches (SOURCES). Offline, the last list is used.
  async list() {
    let rows = [];
    try {
      const trees = new Map();
      for (const kind of ['game', 'mod']) {
        let found = false;
        for (const {branch, prefix, marker} of SOURCES[kind]) {
          const tree = await this.tree(branch, trees);
          if (!tree?.some(item => item.type === 'blob' && item.path === prefix + marker)) continue;
          rows.push(...treeRows(tree, prefix, kind));
          found = true;
          break;
        }
        if (kind === 'game' && !found) throw new Error('Fant ikke spillfilene (game/00.LFL) i ' + REPO + '.');
      }
      await this.library.setMeta('listing', rows);
    } catch (error) {
      const saved = error instanceof TypeError ? await this.library.getMeta('listing') : null;
      if (!saved) throw error;
      rows = saved;
    }
    this.rows = new Map(rows.map(row => [row.path, row]));
    return rows;
  }

  async read(path) {
    const row = this.rows.get(path);
    if (!row) return undefined;
    return this.blob(row, path.split('/').at(-1));
  }

  // One git blob, from the browser if it is there, else from GitHub
  async blob({sha, size}, name) {
    const cached = await this.library.getBlob(sha);
    if (cached) return cached;
    const progress = this.progress && ((done) => this.progress(name, done, size));
    const blob = await this.retry(async () => {
      const response = await this.get('git/blobs/' + sha, 'application/vnd.github.raw+json');
      const body = await readBody(response, size, progress && size >= 4 * 1048576 ? progress : null);
      // A connection that breaks off can give a short body without an error
      if (body.size !== size) throw new TypeError('Filen kom ikke helt fram.');
      return body;
    });
    await this.library.putBlob(sha, blob);
    return blob;
  }
}

function requestResult(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export class LocalLibrary {
  constructor(basePath) {
    // GitHub Pages projects share an origin; keep this game's cache separate.
    this.name = 'zakmckracken-hd-files:' + basePath;
    this.db = null;
    this.metadata = {};
  }

  async open() {
    const request = indexedDB.open(this.name, 2);
    request.onupgradeneeded = () => {
      const db = request.result;
      // files: chosen folders; blobs: files from GitHub by blob id
      if (!db.objectStoreNames.contains('files')) db.createObjectStore('files', {keyPath: 'path'});
      if (!db.objectStoreNames.contains('metadata')) db.createObjectStore('metadata');
      if (!db.objectStoreNames.contains('blobs')) db.createObjectStore('blobs');
    };
    this.db = await requestResult(request);
    this.db.onversionchange = () => this.db.close();
    const store = this.db.transaction('metadata').objectStore('metadata');
    const [game, mod] = await Promise.all(['game', 'mod'].map(key => requestResult(store.get(key))));
    this.metadata = {game, mod};
    return this.metadata;
  }

  async import(files, kind) {
    const rows = selectFiles(files, kind);
    let mod;
    if (kind === 'mod') {
      mod = JSON.parse(await rows.find(row => row.path === MOD_ROOT + 'mod.json').blob.text());
      if (mod.format !== 1 || mod.scale !== 4) throw new Error('HD-pakken må være i DigHD-format 1 med skala 4.');
    }
    const prefix = kind === 'game' ? GAME_ROOT : MOD_ROOT;
    const metadata = summarize(rows, mod?.created || null);
    await new Promise((resolve, reject) => {
      const tx = this.db.transaction(['files', 'metadata'], 'readwrite');
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error('Lagringen ble avbrutt.'));
      const store = tx.objectStore('files');
      // Replacement is atomic: a storage error preserves the previous usable set.
      store.delete(IDBKeyRange.bound(prefix, prefix + '\uffff'));
      for (const row of rows) store.put({path: row.path, blob: row.blob});
      tx.objectStore('metadata').put(metadata, kind);
    });
    this.metadata[kind] = metadata;
    return metadata;
  }

  async read(path) {
    const row = await requestResult(this.db.transaction('files').objectStore('files').get(path));
    return row?.blob;
  }

  getMeta(key) {
    return requestResult(this.db.transaction('metadata').objectStore('metadata').get(key));
  }

  setMeta(key, value) {
    const store = this.db.transaction('metadata', 'readwrite').objectStore('metadata');
    return requestResult(value === undefined ? store.delete(key) : store.put(value, key));
  }

  getBlob(sha) {
    return requestResult(this.db.transaction('blobs').objectStore('blobs').get(sha));
  }

  putBlob(sha, blob) {
    return requestResult(this.db.transaction('blobs', 'readwrite').objectStore('blobs').put(blob, sha));
  }

  // Removes files an older HD pack had, but the current one does not
  async pruneBlobs(keep) {
    const store = this.db.transaction('blobs', 'readwrite').objectStore('blobs');
    const keys = await requestResult(store.getAllKeys());
    await Promise.all(keys.filter(key => !keep.has(key)).map(key => requestResult(store.delete(key))));
  }

  async clear() {
    await new Promise((resolve, reject) => {
      const tx = this.db.transaction(['files', 'metadata', 'blobs'], 'readwrite');
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error('Slettingen ble avbrutt.'));
      tx.objectStore('files').clear();
      tx.objectStore('metadata').clear();
      tx.objectStore('blobs').clear();
    });
    this.metadata = {};
  }
}

// source: LocalLibrary (chosen folders) or RemoteSource (the game repository on GitHub)
export function privateFetch(source, indexes, baseURL, networkFetch) {
  return async (input, options) => {
    const url = new URL(typeof input === 'string' || input instanceof URL ? input : input.url, baseURL);
    if (url.origin !== baseURL.origin || !url.pathname.startsWith('/data/')) return networkFetch(input, options);
    const path = decodeURIComponent(url.pathname);
    const headers = {'Cache-Control': 'no-store'};
    if (indexes.has(path)) {
      headers['Content-Type'] = 'application/json';
      return new Response(JSON.stringify(indexes.get(path)), {headers});
    }
    if (path.startsWith(GAME_ROOT) || path.startsWith('/data/mods/')) {
      const blob = await source.read(path);
      // Never send a game/HD filename to GitHub or another server, even if missing.
      return new Response(blob || null, {status: blob ? 200 : 404, headers});
    }
    // Built-in ScummVM themes/translations use /data, but Pages has a project prefix.
    return networkFetch(new URL('data/' + path.slice('/data/'.length), baseURL), options);
  };
}
