import test from 'node:test';
import assert from 'node:assert/strict';
import {selectFiles, makeIndexes, privateFetch, summarize, treeRows, blobIds, RemoteSource, ApiError, REPO, GAME_ROOT, MOD_ROOT} from '../local-files.mjs';

const file = (name, content = 'sample') => ({name: name.split('/').at(-1), webkitRelativePath: name, size: content.length});

// Det minste spillet ScummVM starter: indeksen og de to tegnsettene
const core = ['game/00.LFL', 'game/98.LFL', 'game/99.LFL'];

test('imports game files from a directory without importing unrelated files', () => {
  const rows = selectFiles([...core, 'game/01.lfl', 'game/59.LFL', 'game/Track1.fla', 'game/token.txt', 'game/SHA256SUMS'].map(name => file(name)), 'game');
  assert.deepEqual(rows.map(row => row.path),
    ['00.LFL', '98.LFL', '99.LFL', '01.LFL', '59.LFL', 'TRACK1.FLA'].map(name => GAME_ROOT + name));
  assert.throws(() => selectFiles([file('game/00.LFL'), file('game/98.LFL')], 'game'), /99.LFL/);
  assert.throws(() => selectFiles([file('game/01.LFL'), file('game/98.LFL'), file('game/99.LFL')], 'game'), /00.LFL/);
});

test('all 21 CD tracks are game files; other files in the game folder are left out', () => {
  const tracks = Array.from({length: 21}, (_, i) => 'game/Track' + (i + 1) + '.fla');
  const rows = selectFiles([...core, ...tracks,
    'game/Track1.flac', 'game/Track1.ogg', 'game/track22.wav', 'game/100.LFL', 'game/1.LFL', 'game/00.LFL.001',
    'game/SAMNMAX.000', 'game/MONSTER.SOU', 'game/MT32_PCM.ROM', 'game/sub/01.LFL'].map(name => file(name)), 'game');
  assert.deepEqual(rows.map(row => row.path),
    [...['00.LFL', '98.LFL', '99.LFL'], ...Array.from({length: 21}, (_, i) => 'TRACK' + (i + 1) + '.FLA')].map(name => GAME_ROOT + name));
});

test('HD references, prompts and film frames are excluded; an incomplete mod is rejected', () => {
  // Zak har ingen SMUSH-filmer, så san/ (filmrutene i The Dig) er ikke med i modden
  const rows = selectFiles([file('gpt/mod.json'), file('gpt/rooms/room022.png'), file('gpt/rooms/room022_idx.png'), file('gpt/prompt.txt'), file('gpt/referanse.png'), file('gpt/san/INTRO/00001.png')], 'mod');
  assert.equal(rows.length, 3);
  assert.throws(() => selectFiles([file('gpt/mod.json')], 'mod'), /HD-mappen/);
  assert.throws(() => selectFiles([file('gpt/mod.json'), file('gpt/rooms/room022.png'), file('gpt/rooms/room022.png')], 'mod'), /samme navn/);
});

test('HD objects and figure cels are imported and counted without their _idx files', () => {
  const rows = selectFiles([
    file('gpt/mod.json'), file('gpt/rooms/room022.png'), file('gpt/rooms/room022_idx.png'),
    file('gpt/objects/obj097_0a.png'), file('gpt/objects/obj097_0a_idx.png'),
    file('gpt/costumes/costume014_003.png'), file('gpt/costumes/costume014_003_idx.png'),
    file('gpt/costumes/costume014_016.png'), file('gpt/costumes/costume014_016_idx.png'),
    file('gpt/costumes/costume014_016_hd.png'),
    file('gpt/fonts/map.txt'), file('gpt/fonts/exo2.png'), file('gpt/fonts/exo2.txt'), file('gpt/fonts/OFL.txt'),
    file('gpt/SHA256SUMS'), file('gpt/README.md')], 'mod');
  assert.equal(rows.length, 13);
  assert.ok(rows.some(row => row.path === MOD_ROOT + 'fonts/map.txt'));
  assert.ok(rows.some(row => row.path === MOD_ROOT + 'fonts/exo2.png'));
  assert.ok(rows.some(row => row.path === MOD_ROOT + 'costumes/costume014_016_hd.png'));
  assert.ok(rows.some(row => row.path === MOD_ROOT + 'costumes/costume014_016_idx.png'));
  const sum = summarize(rows, '2026-10-09 09:49');
  assert.deepEqual([sum.rooms, sum.objects, sum.cels, sum.created], [1, 1, 2, '2026-10-09 09:49']);
  assert.equal(sum.bytes, 13 * 'sample'.length);
});

test('ScummVM directory indexes combine local game/HD files with built-in themes', () => {
  const indexes = makeIndexes([{path: GAME_ROOT + 'TRACK1.FLA', size: 45}, {path: MOD_ROOT + 'rooms/room022.png', size: 23}], {'scummmodern.zip': 99});
  assert.deepEqual(indexes.get('/data/index.json'), {'scummmodern.zip': 99, games: {}, mods: {}});
  assert.deepEqual(indexes.get('/data/games/index.json'), {zak: {}});
  assert.deepEqual(indexes.get('/data/games/zak/index.json'), {'TRACK1.FLA': 45});
  assert.deepEqual(indexes.get('/data/mods/gpt/rooms/index.json'), {'room022.png': 23});
});

test('private data and missing private files never reach the network; themes use the Pages prefix', async () => {
  const requests = [];
  const base = new URL('https://example.github.io/ZakMcKracken-HD-Web/');
  const fetch = privateFetch({read: async path => path.endsWith('00.LFL') ? new Blob(['local']) : undefined}, makeIndexes([{path: GAME_ROOT + '00.LFL', size: 5}]), base, async url => {
    requests.push(String(url)); return new Response('network');
  });
  assert.equal(await (await fetch(GAME_ROOT + '00.LFL')).text(), 'local');
  assert.equal((await fetch(GAME_ROOT + 'TRACK1.FLA')).status, 404);
  assert.equal((await fetch(MOD_ROOT + 'missing.png')).status, 404);
  assert.deepEqual(requests, []);
  assert.equal(await (await fetch('/data/scummmodern.zip')).text(), 'network');
  assert.deepEqual(requests, ['https://example.github.io/ZakMcKracken-HD-Web/data/scummmodern.zip']);
});

const tree = [
  {path: 'README.md', type: 'blob', sha: 'r', size: 10},
  {path: 'game', type: 'tree', sha: 't'},
  {path: 'game/00.LFL', type: 'blob', sha: 'i0', size: 7},
  {path: 'game/01.LFL', type: 'blob', sha: 'l1', size: 7},
  {path: 'game/98.LFL', type: 'blob', sha: 'c98', size: 7},
  {path: 'game/99.LFL', type: 'blob', sha: 'c99', size: 7},
  {path: 'game/Track1.fla', type: 'blob', sha: 't1', size: 7},
  {path: 'game/SHA256SUMS', type: 'blob', sha: 'x', size: 3}
];
const modTree = [
  {path: 'mod.json', type: 'blob', sha: 'm', size: 6},
  {path: 'rooms/room022.png', type: 'blob', sha: 'r22', size: 8},
  {path: 'costumes/costume014_003.png', type: 'blob', sha: 'c3', size: 7},
  {path: 'SHA256SUMS', type: 'blob', sha: 'y', size: 3}
];

test('git tree listings become the same paths as chosen folders, with blob ids', () => {
  assert.deepEqual(treeRows(tree, 'game/', 'game'), [
    {path: GAME_ROOT + '00.LFL', size: 7, sha: 'i0'},
    {path: GAME_ROOT + '01.LFL', size: 7, sha: 'l1'},
    {path: GAME_ROOT + '98.LFL', size: 7, sha: 'c98'},
    {path: GAME_ROOT + '99.LFL', size: 7, sha: 'c99'},
    {path: GAME_ROOT + 'TRACK1.FLA', size: 7, sha: 't1'}]);
  assert.deepEqual(treeRows(modTree, '', 'mod').map(row => row.path),
    [MOD_ROOT + 'mod.json', MOD_ROOT + 'rooms/room022.png', MOD_ROOT + 'costumes/costume014_003.png']);
});

function memoryLibrary() {
  const blobs = new Map(), meta = new Map();
  return {
    blobs,
    getBlob: async sha => blobs.get(sha),
    putBlob: async (sha, blob) => { blobs.set(sha, blob); },
    getMeta: async key => meta.get(key),
    setMeta: async (key, value) => { meta.set(key, value); }
  };
}

function github(requests, status = 200, {withMod = true} = {}) {
  return async (url, options) => {
    requests.push({url: String(url), auth: options?.headers?.Authorization, accept: options?.headers?.Accept});
    if (status !== 200) return new Response('{}', {status});
    const u = new URL(url);
    if (u.pathname.endsWith('/git/trees/spilldata')) return Response.json({tree, truncated: false});
    if (u.pathname.endsWith('/git/trees/hd-mod') && withMod) return Response.json({tree: modTree, truncated: false});
    if (u.pathname.includes('/git/blobs/')) return new Response('blob ' + u.pathname.split('/').at(-1));
    return new Response('', {status: 404});
  };
}

test('files come from the private branches with the key, once per blob id', async () => {
  const requests = [];
  const library = memoryLibrary();
  const source = new RemoteSource(library, 'KEY', github(requests));
  const rows = await source.list();
  assert.equal(rows.length, 8);
  assert.equal(REPO, 'Tombonator3000/ZakMcKracken-HD');
  assert.ok(requests.every(r => r.url.startsWith('https://api.github.com/repos/' + REPO + '/') && r.auth === 'Bearer KEY'));
  assert.equal(await (await source.read(GAME_ROOT + '01.LFL')).text(), 'blob l1');
  assert.equal(await (await source.read(GAME_ROOT + '01.LFL')).text(), 'blob l1');
  assert.equal(requests.filter(r => r.url.includes('/git/blobs/l1')).length, 1);
  assert.equal(requests.find(r => r.url.includes('/git/blobs/')).accept, 'application/vnd.github.raw+json');
  assert.equal(await source.read(GAME_ROOT + 'TRACK2.FLA'), undefined);
  assert.equal(requests.length, 3);
  assert.deepEqual([...blobIds(rows)].sort(), ['c3', 'c98', 'c99', 'i0', 'l1', 'm', 'r22', 't1']);

  // Offline: the last list is used, and kept files still work
  const offline = new RemoteSource(library, 'KEY', async () => { throw new TypeError('Failed to fetch'); });
  assert.equal((await offline.list()).length, 8);
  assert.equal(await (await offline.read(GAME_ROOT + '01.LFL')).text(), 'blob l1');
});

test('without the hd-mod branch the game starts from spilldata alone', async () => {
  const requests = [];
  const source = new RemoteSource(memoryLibrary(), 'KEY', github(requests, 200, {withMod: false}), {sleep: async () => {}});
  const rows = await source.list();
  assert.deepEqual(rows.map(row => row.path), ['00.LFL', '01.LFL', '98.LFL', '99.LFL', 'TRACK1.FLA'].map(name => GAME_ROOT + name));
  // 404 for hd-mod is not tried again
  assert.equal(requests.filter(r => r.url.includes('/git/trees/hd-mod')).length, 1);

  // A key without access gets 404 already for spilldata, and that still stops
  const denied = new RemoteSource(memoryLibrary(), 'BAD', github([], 404), {sleep: async () => {}});
  await assert.rejects(denied.list(), error => error instanceof ApiError && error.status === 404);
});

test('a key GitHub does not accept gives an error the page can show', async () => {
  for (const status of [401, 404]) {
    const source = new RemoteSource(memoryLibrary(), 'BAD', github([], status));
    await assert.rejects(source.list(), error => error instanceof ApiError && error.status === status);
  }
});

test('with the private branches, game paths never go to the site', async () => {
  const requests = [];
  const source = new RemoteSource(memoryLibrary(), 'KEY', github(requests));
  const rows = await source.list();
  const base = new URL('https://example.github.io/ZakMcKracken-HD-Web/');
  const site = [];
  const fetch = privateFetch(source, makeIndexes(rows), base, async url => { site.push(String(url)); return new Response('x'); });
  assert.equal(await (await fetch(GAME_ROOT + '00.LFL')).text(), 'blob i0');
  assert.equal((await fetch(GAME_ROOT + 'TRACK2.FLA')).status, 404);
  assert.equal((await fetch(MOD_ROOT + 'rooms/room023.png')).status, 404);
  assert.deepEqual(site, []);
});

test('no file is put together from parts: names with a part number are left out', () => {
  // Zak-filene er alle under 90 MB, så spilldata har ingen deler
  const parts = [
    {path: 'game/00.LFL', type: 'blob', sha: 'i0', size: 5},
    {path: 'game/98.LFL', type: 'blob', sha: 'c98', size: 5},
    {path: 'game/99.LFL', type: 'blob', sha: 'c99', size: 5},
    {path: 'game/Track10.fla', type: 'blob', sha: 't10', size: 7},
    {path: 'game/Track10.fla.001', type: 'blob', sha: 'p1', size: 4},
    {path: 'game/01.LFL.002', type: 'blob', sha: 'p2', size: 3}
  ];
  const rows = treeRows(parts, 'game/', 'game');
  assert.deepEqual(rows, [
    {path: GAME_ROOT + '00.LFL', size: 5, sha: 'i0'},
    {path: GAME_ROOT + '98.LFL', size: 5, sha: 'c98'},
    {path: GAME_ROOT + '99.LFL', size: 5, sha: 'c99'},
    {path: GAME_ROOT + 'TRACK10.FLA', size: 7, sha: 't10'}]);
  assert.ok(rows.every(row => !('parts' in row)));
});

test('a big track shows how far the download has come', async () => {
  const seen = [];
  const body = 'x'.repeat(5 * 1048576);
  const source = new RemoteSource(memoryLibrary(), 'KEY', async () => new Response(body),
    {progress: (name, done, size) => seen.push([name, done, size])});
  source.rows = new Map([[GAME_ROOT + 'TRACK10.FLA', {path: GAME_ROOT + 'TRACK10.FLA', size: body.length, sha: 't10'}]]);
  assert.equal((await source.read(GAME_ROOT + 'TRACK10.FLA')).size, body.length);
  assert.ok(seen.length >= 2);
  assert.ok(seen.every(([name, , size]) => name === 'TRACK10.FLA' && size === body.length));
  assert.deepEqual(seen.at(-1), ['TRACK10.FLA', body.length, body.length]);
});

test('a lost connection is tried again until the file comes', async () => {
  let calls = 0;
  const waits = [];
  const source = new RemoteSource(memoryLibrary(), 'KEY', async () => {
    calls++;
    if (calls === 1) throw new TypeError('Failed to fetch');
    if (calls === 2) return new Response('x', {status: 502});
    if (calls === 3) return new Response('kort');  // body cut off
    return new Response('hele filen');
  }, {waiting: s => waits.push(s), sleep: async () => {}});
  source.rows = new Map([[GAME_ROOT + 'TRACK7.FLA', {path: GAME_ROOT + 'TRACK7.FLA', size: 10, sha: 't7'}]]);
  assert.equal(await (await source.read(GAME_ROOT + 'TRACK7.FLA')).text(), 'hele filen');
  assert.equal(calls, 4);
  assert.deepEqual(waits, [1, 2, 4]);

  // A key GitHub rejects is not tried again
  let rejected = 0;
  const bad = new RemoteSource(memoryLibrary(), 'BAD', async () => { rejected++; return new Response('', {status: 401}); }, {sleep: async () => {}});
  bad.rows = source.rows;
  await assert.rejects(bad.read(GAME_ROOT + 'TRACK7.FLA'), error => error.status === 401);
  assert.equal(rejected, 1);
});
