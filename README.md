# A Smile from Kenya — Events Dashboard

A lightweight, single-file dashboard for the field activities of
**A Smile from Kenya**: sessions delivered, people reached, driver and
facilitator payments, and monthly impact.

Everything — markup, styling, logic, login screen and favicon — lives in one
self-contained `dashboard.html`. No build step, no dependencies to install.

> ### ▶ [Open the dashboard](https://boazbuilds.github.io/ASFK/dashboard.html)
> `https://boazbuilds.github.io/ASFK/dashboard.html`
>
> _Bookmark this link._

## Features

- **Impact at a glance** — sessions, people reached (participants plus
  teachers), counseling sessions, hours delivered, facilitators and
  follow-ups, with a breakdown by activity type.
- **Monthly overview** — sessions and people reached per month, and for each
  month the facilitators, the drivers with what they are owed, and every
  session. The chosen month stays selected when you refresh.
- **Payment summary** — per period (all time, this month, last month or a
  custom range): each driver's trips by distance band and the amount to pay,
  and each facilitator's sessions, people reached and hours. **Print** it or
  **Export CSV** for the records.
- **Data quality panel** — lists what the dashboard had to skip, correct or
  leave out: duplicate submissions, unreadable dates, missing headcounts,
  distances or times, afternoon times typed as morning, and names spelled in
  several ways.
- **Follow-ups** — the most recent sessions that asked for a follow-up, with
  the answer given; "Show all" for the rest.
- **All sessions** — every session, newest first, with a search box.
- **Works in the field** — the last loaded data is kept in the browser, so the
  dashboard still opens without internet (clearly marked as a saved copy).
  **Upload CSV** loads an exported sheet by hand.

## Driver pay

The form's *Distance from Malindi (one way)* answer (0–10, 10–20 … 50–60
minutes drive) decides the rate for each trip. Rates are entered per band in
the **Payment Summary**, and each browser remembers them. Defaults for the
first bands are in `RATE_DEFAULTS` in `dashboard.html`.

- A band without a rate is **never guessed**. Its trips are left out of the
  totals and a warning names the band until a rate is entered.
- **Count driver trips** can be set to *one per session report* or to *one per
  driver, day and place*. The second option matters when one visit produces
  several reports, as with counseling.
- Sessions with several drivers count for each driver. Spelling variants of one
  name are merged.

## Better data at the source

**[FORM_GUIDE.md](FORM_GUIDE.md)** shows what the current sheet data looks
like and which Google Form changes fix it: checkboxes for names, validated
numbers, and a clear follow-up question. It also explains
`tools/build-improved-form.gs`, an Apps Script that builds an improved form
in one run.

## Data source

The dashboard reads the Google Sheet's plain CSV export. If that fails, it
falls back to the gviz endpoint. The sheet must be shared as **"Anyone with
the link can view."**

Columns are found by their question title (`COL_HEADERS`), so moving or adding
questions in the form doesn't break anything. When a title isn't recognised,
the usual position in `COL_DEFAULTS` is used.

**Upload CSV** accepts comma-, semicolon- (Dutch Excel) and tab-separated
files.

## Usage

1. Open the dashboard link, or `dashboard.html` in any modern browser.
2. Enter the password.
3. Data loads automatically; press **↻ Refresh** to reload.

## Hosting

The dashboard is hosted on GitHub Pages from `main` (Settings → Pages). Any
static host works too, or open the file locally.

## Configuration

All settings live at the top of the script in `dashboard.html`:

| What | Where |
|------|-------|
| Google Sheet and tab | `SHEET_ID` and `SHEET_GID` |
| Column titles and fallback positions | `COL_HEADERS` and `COL_DEFAULTS` |
| Login password | `PWD_HASH`, the SHA-256 hash of the password |
| Default driver rates | `RATE_DEFAULTS`, in shillings per trip, by distance band |

To change the password, replace `PWD_HASH` with the SHA-256 hash of the new
password.

## Development

```sh
node tests/run-tests.mjs
```

The unit tests need nothing but Node.js. When Playwright is installed
(`npm i -g playwright`), the same command also runs the dashboard in headless
Chromium and checks what users see. That covers the numbers, rates, exports,
printing, offline use and phone layout. All test data is made up.

## Notes

- The password check runs in the browser and the sheet is public by link. This
  keeps casual visitors out; it is not real access control.
- The offline copy lives in the browser's local storage on each device that
  opened the dashboard.
- The CSV export opens directly in Google Sheets, Numbers and English Excel.
  In Dutch Excel, use *Data → From Text/CSV* and choose comma as separator.
