// Tests for dashboard.html — run with:  node tests/run-tests.mjs
//
// Unit tests load the dashboard's own <script> into a sandbox and need no
// dependencies. The browser tests run the real page in headless Chromium when
// Playwright is installed (`npm i -g playwright`), and are skipped otherwise.
// All data below is made up; it mirrors the structure of the real sheet.

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { execSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = path.join(HERE, '..', 'dashboard.html');
const html = fs.readFileSync(PAGE, 'utf8');

let failures = 0, passes = 0;
function check(label, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) passes++; else failures++;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${label}${ok ? '' : `\n     got      ${JSON.stringify(actual)}\n     expected ${JSON.stringify(expected)}`}`);
}

// ── Synthetic sheet ─────────────────────────────────────────────────────
const HEADERS = ['Tijdstempel', 'E-mailadres', 'Name(s) of facilitator(s)', 'Date', 'Place', 'Driver(s)',
  'Project/event', 'Which lesson(s)/topic(s)', 'Number of participants', 'Age group', 'What did they learn?',
  'Questions?', 'Is there any follow-up needed (counseling)? If yes, for how many children?', 'Comments',
  'Reason for counseling', 'One on one or group counseling', 'One time or recurring counseling',
  'Which TtT lesson(s)/topic(s)', 'Number of participating teachers', 'What did the teachers learn?',
  'Teacher questions', 'Comments (TtT)', 'Distance from Malindi (one way)', 'Start time', 'End time',
  'Doctor advice', 'Follow up?', 'Contact details', 'Agreement', 'Contact person'];
const IDX = { ts: 0, email: 1, fac: 2, date: 3, place: 4, driver: 5, project: 6, topics: 7, pax: 8,
  followup: 12, comments: 13, reason: 14, teachers: 18, dist: 22, start: 23, end: 24 };

function mk(fields) {
  const r = Array(HEADERS.length).fill('');
  Object.entries(fields).forEach(([k, v]) => { r[IDX[k]] = v; });
  return r;
}
const toCsv = rows => rows.map(r => r.map(v => /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v).join(',')).join('\r\n');

const ROWS = [
  // 1 children — end time typed as 1:00 (means 13:00)
  mk({ ts: '3-7-2026 18:00:00', fac: 'Alice', date: '3-7-2026', place: 'Kakuyuni School', driver: 'Omar',
       project: 'Amazing You! session children', pax: '40', followup: 'Yes for 2 children',
       dist: '0-10 minutes drive', start: '10:00:00', end: '1:00:00', comments: 'Went well,\nkids "loved" it' }),
  // 2 parents — facilitator spelled differently, two drivers
  mk({ ts: '5-7-2026 18:00:00', fac: 'alice ', date: '5-7-2026', place: 'Kakuyuni School', driver: 'Omar, Peter',
       project: 'Amazing You! session parents', pax: '25', followup: 'No', dist: '10-20 minutes drive',
       start: '9:00:00', end: '11:30:00' }),
  // 3 teach the teacher — two facilitators, headcount in the teachers column
  mk({ ts: '10-7-2026 18:00:00', fac: 'Bob, Alice', date: '10-7-2026', place: 'Malindi Primary', driver: 'Peter',
       project: 'Teach the Teacher', teachers: '30+', dist: '20-30 minutes drive', start: '9:00:00', end: '12:00:00' }),
  // 4 + 5 counseling — one visit, two children, two reports
  mk({ ts: '12-7-2026 18:00:00', fac: 'Carol', date: '12-7-2026', place: 'Watamu', driver: 'Omar',
       project: 'Next to You! counseling', reason: 'Reason A', dist: '30-40 minutes drive', start: '10:00:00', end: '11:00:00' }),
  mk({ ts: '12-7-2026 18:05:00', fac: 'Carol', date: '12-7-2026', place: 'Watamu', driver: 'Omar',
       project: 'Next to You! counseling', reason: 'Reason B', dist: '30-40 minutes drive', start: '10:00:00', end: '11:00:00' }),
  // 6 office meeting, 7 the same report submitted twice
  mk({ ts: '2-8-2026 17:00:00', fac: 'Carol', date: '2-8-2026', place: 'Office Malindi', driver: 'Omar',
       project: 'Office meeting', dist: '0-10 minutes drive', start: '14:00:00', end: '16:00:00' }),
  mk({ ts: '2-8-2026 17:01:00', email: 'x@example.org', fac: 'Carol', date: '2-8-2026', place: 'Office Malindi', driver: 'Omar',
       project: 'Office meeting', dist: '0-10 minutes drive', start: '14:00:00', end: '16:00:00' }),
  // 8 no distance, no times, "~50", '/' between drivers, free-text follow-up
  mk({ ts: '15-8-2026 18:00:00', fac: 'Bob', date: '15-8-2026', place: 'Gede', driver: 'Peter/Omar',
       project: 'Next to You! session', pax: '~50', followup: 'They need more sessions' }),
  // 9 impossible date (31 April)
  mk({ ts: '1-5-2026 18:00:00', fac: 'Bob', date: '31-4-2026', place: 'Gede', driver: 'Peter',
       project: 'Amazing You! session children', pax: '20', followup: 'Nop', dist: '0-10 minutes drive',
       start: '10:00:00', end: '12:00:00' }),
  // 10 typed into the sheet by hand: no timestamp; no headcount; equal times
  mk({ fac: 'Alice', date: '20-8-2026', place: 'Kakuyuni School', driver: 'Omar',
       project: 'Amazing You! session children', dist: '0-10 minutes drive', start: '9:00', end: '9:00' }),
];
const SHEET = toCsv([HEADERS, ...ROWS]);
const UPLOAD = toCsv([HEADERS, ROWS[0], ROWS[5]]);
// Same data after someone moved the Place and Driver(s) questions to the end of
// the form and added a "Follow-up details" question
const MOVED = toCsv([HEADERS, ...ROWS.slice(0, 2)].map((r, i) => {
  const c = [...r];
  [c[4], c[29]] = [c[29], c[4]]; // Place ↔ Contact person
  [c[5], c[28]] = [c[28], c[5]]; // Driver(s) ↔ Agreement
  return [...c, i === 0 ? 'Follow-up details' : 'Visit the family next week'];
}));

// ════════════════════════════════════════════════════════════════════════
//  Unit tests
// ════════════════════════════════════════════════════════════════════════
function sandbox() {
  const store = () => { const m = new Map(); return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k) }; };
  const script = html.match(/<script>\n([\s\S]*?)<\/script>/)[1];
  const definitions = script.slice(0, script.lastIndexOf('initControls();')); // skip DOM start-up
  const ctx = vm.createContext({ window: {}, document: {}, navigator: { onLine: true }, console,
    localStorage: store(), sessionStorage: store() });
  vm.runInContext(definitions, ctx);
  return { ctx, run: code => vm.runInContext(code, ctx) };
}

const { ctx, run } = sandbox();
const F = run(`({ COL, COL_DEFAULTS, parseCsv, parseDataset, selectDataRows, parseDate, parseDateInput, parseTime,
  sessionDuration, formatHours, parseCount, peopleCount, parseBand, bandsFor, splitPeople, groupPeople,
  followupStatus, eventTypeLabel, computeDriverPay, payTotals, rateFor, loadRates, collectDataQuality,
  csvField, buildPaymentsCsv, getFilteredRows })`);
const setState = code => run(code);

console.log('── parsing');
check('csv: quoted newline + escaped quotes stay one field',
  F.parseCsv('a,"x,\n""y""",c\nd,e,f'), [['a', 'x,\n"y"', 'c'], ['d', 'e', 'f']]);
check('csv: CRLF and BOM', F.parseCsv('﻿a,b\r\nc,d'), [['a', 'b'], ['c', 'd']]);
check('csv: semicolons (Dutch Excel)', F.parseCsv('Tijdstempel;Datum;Plaats\n1;2;3'), [['Tijdstempel', 'Datum', 'Plaats'], ['1', '2', '3']]);
check('csv: tabs', F.parseCsv('a\tb\nc\td'), [['a', 'b'], ['c', 'd']]);

const ds = F.parseDataset(SHEET);
check('dataset: header dropped, hand-typed row kept, exact re-submission removed',
  [ds.rows.length, ds.duplicates.length], [9, 1]);
check('dataset: two counseling reports of one visit are NOT duplicates',
  ds.rows.filter(r => r[F.COL.project].includes('counseling')).length, 2);
check('columns: real headers resolve to the default positions',
  JSON.stringify(ds.cols) === JSON.stringify({ ...F.COL_DEFAULTS }), true);

const movedDs = F.parseDataset(MOVED);
check('columns: moved and added questions are found by their title',
  [movedDs.cols.place, movedDs.cols.driver, movedDs.cols.followupDetails, movedDs.rows[0][movedDs.cols.place]],
  [29, 28, 30, 'Kakuyuni School']);
check('columns: no header row keeps the default positions',
  F.parseDataset(toCsv(ROWS.slice(0, 2))).cols.place, 4);

console.log('── dates & times');
const ymd = d => d && [d.getFullYear(), d.getMonth() + 1, d.getDate()];
check('date D-M-YYYY', ymd(F.parseDate('3-7-2026')), [2026, 7, 3]);
check('date DD/MM/YYYY', ymd(F.parseDate('15/03/2025')), [2025, 3, 15]);
check('date ISO', ymd(F.parseDate('2026-08-20')), [2026, 8, 20]);
check('date 31-4 is rejected, not rolled into May', F.parseDate('31-4-2026'), null);
check('date 13-13 is rejected', F.parseDate('13-13-2026'), null);
check('date input is local midnight', [ymd(F.parseDateInput('2026-06-01')), F.parseDateInput('2026-06-01').getHours()], [[2026, 6, 1], 0]);
check('time 24h', F.parseTime('13:30:00').minutes, 810);
check('time 1:30 PM', F.parseTime('1:30 PM').minutes, 810);
check('time 12:15 AM', F.parseTime('12:15 AM').minutes, 15);
check('duration 10:00 → 1:00 read as 13:00', F.sessionDuration('10:00:00', '1:00:00'), { minutes: 180, correctedPm: true, present: true });
check('duration 9:00 → 11:30', F.sessionDuration('9:00:00', '11:30:00').minutes, 150);
check('duration equal times is unclear', F.sessionDuration('9:00', '9:00').minutes, null);
check('duration explicit AM end is not flipped', F.sessionDuration('10:00', '9:00 AM').minutes, null);
check('duration over 10h is rejected', F.sessionDuration('6:00', '17:00').minutes, null);
check('duration missing end', F.sessionDuration('9:00', '').present, false);
check('hours format', [F.formatHours(870), F.formatHours(150)], ['15h', '2h 30m']);

console.log('── counts, bands, people');
check('counts', ['25', '1,200', '1.200', '~50', '30+', '', 'n/a'].map(v => F.parseCount(v)),
  [25, 1200, 1200, 50, 30, NaN, NaN]);
check('people = participants + teachers', [F.peopleCount(ROWS[0]), F.peopleCount(ROWS[2])], [40, 30]);
check('bands', ['0-10 minutes drive', '10-20 minutes drive', '50-60 minutes drive', '15', '10', '60+ min', '']
  .map(v => F.parseBand(v)?.key ?? null), ['0-10', '10-20', '50-60', '10-20', '0-10', '60+', null]);
check('split people: comma, slash, dedupe', [F.splitPeople('Mary, John'), F.splitPeople('Peter/Omar'), F.splitPeople('John, john ,')],
  [['Mary', 'John'], ['Peter', 'Omar'], ['John']]);
const facGroups = F.groupPeople(ds.rows, r => F.splitPeople(r[F.COL.facilitator]))
  .map(g => [g.name, g.rows.length, g.variants.length]).sort();
check('facilitators: variants merged, co-facilitators split', facGroups, [['Alice', 4, 2], ['Bob', 3, 1], ['Carol', 3, 1]]);

console.log('── follow-ups & types');
check('follow-up answers', ['Yes', 'yes for 2 children', 'No', 'Nop', 'No follow-up.', 'none', 'N/A', 'They need more sessions', 'Amazing!', '']
  .map(F.followupStatus), ['yes', 'yes', 'no', 'no', 'no', 'no', 'no', 'check', 'check', 'none']);
check('activity types', ['Next to You! counseling', 'Amazing You! session children', 'Amazing You! session parents',
  'Teach the Teacher', 'Office meeting', 'Next to You! session', 'x'.repeat(40)].map(F.eventTypeLabel),
  ['Counseling', 'Children', 'Parents', 'Teachers', 'Office', 'Next to You! session', 'Other']);

console.log('── driver pay');
const pay = (basis, rates = {}) => F.computeDriverPay(ds.rows, rates, basis)
  .map(p => ({ name: p.name, trips: p.trips, amount: p.amount, missing: p.missing }))
  .sort((a, b) => a.name.localeCompare(b.name));
check('per report, default rates (20–30 and 30–40 have none)', pay('report'), [
  { name: 'Omar', trips: 7, amount: 650, missing: 2 },
  { name: 'Peter', trips: 4, amount: 450, missing: 1 }]);
check('per trip: two counseling reports of one visit count once', pay('trip'), [
  { name: 'Omar', trips: 6, amount: 650, missing: 1 },
  { name: 'Peter', trips: 4, amount: 450, missing: 1 }]);
check('rates filled in for the missing bands', pay('report', { '20-30': 300, '30-40': 400 }), [
  { name: 'Omar', trips: 7, amount: 1450, missing: 0 },
  { name: 'Peter', trips: 4, amount: 750, missing: 0 }]);
const tot = F.payTotals(F.computeDriverPay(ds.rows, {}, 'report'), {});
check('totals list the bands without a rate', [tot.amount, tot.trips, tot.missing, tot.missingBands], [1100, 11, 3, ['20-30', '30-40']]);
check('a cleared rate stays cleared; an unset one uses the default', [F.rateFor({ '0-10': null }, '0-10'), F.rateFor({}, '0-10')], [null, 100]);
check('bands offered for rates', F.bandsFor(ds.rows), ['0-10', '10-20', '20-30', '30-40', 'unknown']);
ctx.localStorage.setItem('asfk_rates', JSON.stringify({ short: 120, long: 220, unknown: 160 }));
check('old two-band rates carry over', F.loadRates(), { '0-10': 120, '10-20': 220, unknown: 160 });

console.log('── data quality');
const dq = F.collectDataQuality(ds.rows, new Date(2026, 8, 24));
const tagsOf = place => dq.issues.filter(i => i.row[F.COL.place] === place).flatMap(i => i.tags.map(t => t.label)).sort();
check('office and counseling rows are not asked for a headcount', tagsOf('Watamu').concat(tagsOf('Office Malindi')), []);
check('gede rows: unreadable date, no distance, no times',
  tagsOf('Gede'), ['date unreadable', 'no distance (paid at the unknown rate)', 'no start/end time']);
check('hand-typed row: no headcount, unclear time', tagsOf('Kakuyuni School'), ['no participant count', 'session time unclear']);
check('afternoon corrections are counted', dq.pmCorrected, 1);
check('spelling variants surfaced', dq.variants.map(v => [v.role, v.variants.sort()]), [['facilitator', ['Alice', 'alice']]]);
const future = F.collectDataQuality([mk({ fac: 'A', date: '1-1-2030', place: 'P', driver: 'D', project: 'Office meeting', dist: '0-10', start: '9:00', end: '10:00' })], new Date(2026, 8, 24));
check('future date flagged', future.issues[0].tags.map(t => t.label), ['date in the future']);

console.log('── export & filters');
check('csv field: formula injection neutralised, quotes escaped', [F.csvField('=SUM(A1)'), F.csvField('a "b", c'), F.csvField(12)],
  ["'=SUM(A1)", '"a ""b"", c"', '12']);
setState(`allRows = ${JSON.stringify(ds.rows)}; activeFilter = { preset: 'custom', from: '2026-07-12', to: '2026-08-02' };`);
check('custom range is inclusive on both ends', F.getFilteredRows().map(r => r[F.COL.date]), ['12-7-2026', '12-7-2026', '2-8-2026']);
setState(`activeFilter = { preset: 'all', from: null, to: null };`);
const csv = F.buildPaymentsCsv(ds.rows, {}, 'report');
check('payments csv has driver rows, totals and unset rates',
  [csv.includes('Omar,7,7,3,1,0,2,1,650,2'), csv.includes('Total,11,11,4,2,1,2,2,1100,3'), csv.includes('not set')], [true, true, true]);

// ════════════════════════════════════════════════════════════════════════
//  Browser tests (headless Chromium via Playwright)
// ════════════════════════════════════════════════════════════════════════
async function loadPlaywright() {
  try { return await import('playwright'); } catch { /* not installed locally */ }
  try {
    const root = execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
    return createRequire(path.join(root, 'noop.js'))('playwright');
  } catch { return null; }
}

async function browserTests(pw) {
  const browser = await pw.chromium.launch();
  const url = pathToFileURL(PAGE).href;
  const pageErrors = [];

  // Every test page gets the fake sheet; Chart.js loads from the CDN when reachable.
  async function open({ sheet = SHEET, delayMs = 0, fail = false, auth = true, viewport, storage } = {}) {
    const context = await browser.newContext({ viewport: viewport || { width: 1200, height: 900 }, acceptDownloads: true });
    if (auth) await context.addInitScript(() => sessionStorage.setItem('asfk_auth', '1'));
    if (storage) await context.addInitScript(s => { for (const [k, v] of Object.entries(s)) localStorage.setItem(k, v); }, storage);
    await context.route(/docs\.google\.com\/spreadsheets/, async route => {
      if (fail) return route.abort('internetdisconnected');
      if (delayMs) await new Promise(r => setTimeout(r, delayMs));
      // The page may have aborted this request meanwhile (that is the point of one test)
      await route.fulfill({ status: 200, contentType: 'text/csv; charset=utf-8', body: sheet }).catch(() => {});
    });
    const page = await context.newPage();
    page.on('pageerror', e => pageErrors.push(e.message));
    await page.goto(url);
    return { context, page };
  }
  const text = (page, sel) => page.locator(sel).first().innerText();

  console.log('── browser: load & numbers');
  {
    const { context, page } = await open();
    await page.waitForFunction(() => /sessions/.test(document.getElementById('last-updated').textContent));
    check('cards', await Promise.all(['#stat-sessions', '#stat-participants', '#stat-teachers-sub', '#stat-counseling',
      '#stat-hours', '#stat-facilitators', '#stat-followup'].map(s => text(page, s))), ['9', '165', 'incl. 30 teachers', '2', '15h', '3', '2']);
    check('status mentions the ignored duplicate', /1 duplicate submission ignored/.test(await text(page, '#last-updated')), true);
    check('type chips', await page.$$eval('.type-summary-chip', els => els.map(e => e.textContent)),
      ['3Children', '1Parents', '1Teachers', '2Counseling', '1Next to You! session', '1Office']);
    check('driver total with default rates', await text(page, '#driver-grand-total .dgt-amount'), '1,100 sh');
    check('missing-rate warning names the bands', /20–30 min, 30–40 min/.test(await text(page, '#rate-warning')), true);

    await page.fill('input[data-band="20-30"]', '300');
    await page.fill('input[data-band="30-40"]', '400');
    check('entering rates updates the total', await text(page, '#driver-grand-total .dgt-amount'), '2,200 sh');
    check('…and clears the warning', await page.locator('#rate-warning').isVisible(), false);
    await page.check('input[name="pay-basis"][value="trip"]');
    check('per-trip counting', await text(page, '#driver-grand-total .dgt-sub'), '10 trips');

    await page.click('.month-btn[data-month="2026-07"]');
    await page.click('#refresh-btn');
    await page.waitForFunction(() => !document.getElementById('refresh-btn').disabled);
    check('picked month survives a refresh', await page.getAttribute('.month-btn.active', 'data-month'), '2026-07');

    await page.fill('#table-search', 'gede');
    await page.waitForFunction(() => /of 9/.test(document.getElementById('table-count').textContent));
    check('table search', await text(page, '#table-count'), '2 of 9 sessions');

    await page.click('.filter-btn[data-preset="custom"]');
    await page.fill('#filter-from', '2026-07-01');
    await page.fill('#filter-to', '2026-07-31');
    await page.click('#filter-apply');
    const [download] = await Promise.all([page.waitForEvent('download'), page.click('#export-btn')]);
    const exported = fs.readFileSync(await download.path(), 'utf8');
    check('export: file name and July totals', [download.suggestedFilename(), exported.includes('Total,6,5,1,2,1,1,0,1200,0')],
      ['asfk-payments-2026-07-01_to_2026-07-31.csv', true]);

    await page.emulateMedia({ media: 'print' });
    check('print shows payments, hides controls', [await page.locator('#payment-section').isVisible(),
      await page.locator('#rate-config').isVisible(), await page.locator('#print-rates').isVisible()], [true, false, true]);
    await context.close();
  }

  console.log('── browser: robustness');
  {
    // An upload made while a slow Sheets request is still running must win.
    const { context, page } = await open({ delayMs: 1500 });
    await page.setInputFiles('#file-input', { name: 'upload.csv', mimeType: 'text/csv', buffer: Buffer.from(UPLOAD) });
    await page.waitForTimeout(2500);
    check('late Sheets response does not overwrite an upload', [await text(page, '#stat-sessions'),
      /from upload\.csv/.test(await text(page, '#last-updated')), await page.isEnabled('#refresh-btn')], ['2', true, true]);
    await context.close();
  }
  {
    // A sheet whose questions were moved: search, drivers and follow-up details still line up
    const { context, page } = await open();
    await page.waitForFunction(() => /updated/.test(document.getElementById('last-updated').textContent));
    await page.setInputFiles('#file-input', { name: 'moved.csv', mimeType: 'text/csv', buffer: Buffer.from(MOVED) });
    await page.waitForFunction(() => /moved\.csv/.test(document.getElementById('last-updated').textContent));
    await page.fill('#table-search', 'kakuyuni');
    await page.waitForFunction(() => /of 2/.test(document.getElementById('table-count').textContent));
    check('moved columns: search, driver cards and follow-up details', [await text(page, '#table-count'),
      await page.$$eval('#payment-drivers .person-name', els => els.map(e => e.textContent.trim())),
      /Visit the family next week/.test(await text(page, '#followup-detail'))],
      ['2 of 2 sessions', ['🏍️ Omar', '🏍️ Peter'], true]);
    await context.close();
  }
  {
    // Offline with a saved copy: show it and say so.
    const cache = JSON.stringify({ savedAt: '2026-09-01T08:00:00.000Z', text: SHEET });
    const { context, page } = await open({ fail: true, storage: { asfk_cache_v1: cache } });
    await page.waitForFunction(() => document.getElementById('data-error').style.display === 'block');
    check('offline: saved copy shown with a notice', [await text(page, '#stat-sessions'),
      /Could not refresh/.test(await text(page, '#data-error')), /saved copy/.test(await text(page, '#last-updated'))], ['9', true, true]);
    await context.close();
  }
  {
    const { context, page } = await open({ auth: false });
    check('login: dashboard behind it is inert', [await page.locator('#login-screen').isVisible(),
      await page.evaluate(() => document.querySelector('header').hasAttribute('inert') && document.querySelector('main').hasAttribute('inert'))], [true, true]);
    await context.close();
  }
  {
    const { context, page } = await open({ viewport: { width: 360, height: 780 } });
    await page.waitForFunction(() => /sessions/.test(document.getElementById('last-updated').textContent));
    check('phone width: no sideways scrolling', await page.evaluate(() => document.documentElement.scrollWidth <= 360), true);
    await context.close();
  }

  check('no uncaught page errors', pageErrors, []);
  await browser.close();
}

const pw = await loadPlaywright();
if (pw) {
  try { await browserTests(pw); }
  catch (err) { failures++; console.log(`FAIL browser tests crashed: ${err.stack || err}`); }
} else {
  console.log('── browser tests skipped (Playwright not installed)');
}

console.log(`\n${passes} passed, ${failures} failed`);
process.exit(failures ? 1 : 0);
