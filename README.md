# A Smile from Kenya — Events Dashboard

A lightweight, single-file dashboard for tracking the field activities of
**A Smile from Kenya**: sessions delivered, people reached, facilitator and
driver payments, and monthly impact.

Everything — markup, styling, logic, login screen and favicon — lives in one
self-contained `dashboard.html`. No build step, no dependencies to install.

> ### ▶ [Open the dashboard](https://boazbuilds.github.io/ASFK/dashboard.html)
> `https://boazbuilds.github.io/ASFK/dashboard.html`
>
> _Bookmark this link. It goes live once GitHub Pages is enabled — see
> [Hosting](#hosting-optional)._

## Features

- **Summary cards** — sessions, people reached, facilitators, hours delivered,
  drive time and follow-ups at a glance.
- **Monthly overview** — sessions & participants per month (Chart.js), with a
  per-month breakdown of facilitators, drivers and individual sessions.
- **Payment summary** — session counts per facilitator and driver for a chosen
  period, with configurable driver rates (remembered by the browser), ready to
  verify and approve payouts. Sessions with several drivers ("John, Peter")
  count for each driver individually.
- **Sessions table** — every session, sorted by date, with follow-up flags.
- **Follow-up alerts** — highlights sessions that still need attention.
- **Print-ready** — print the payment summary as a clean report.

## Data source

The dashboard reads from a published Google Sheet (CSV via the gviz endpoint),
or from a CSV/TSV file you upload manually. The sheet must be shared as
**"Anyone with the link can view."** Use the **Upload CSV** button to load an
exported sheet without going online (when offline only the trend chart is
skipped — it needs the Chart.js CDN; everything else works).

## Usage

1. Open `dashboard.html` in any modern browser (or host it — see below).
2. Enter the password on the login screen.
3. Data loads automatically; press **↻ Refresh** to reload.

## Hosting (optional)

Because it's a single static file, you can host it for free:

- **GitHub Pages** — Settings → Pages → deploy from `main`. The dashboard will
  live at `https://boazbuilds.github.io/ASFK/dashboard.html`.
- Or any static host (Netlify, Cloudflare Pages), or just open the file locally.

## Configuration

All settings live in `dashboard.html`:

| What | Where |
|------|-------|
| Google Sheet ID / tab | `SHEET_ID` and `SHEET_GID` |
| Column mapping | the `COL` object at the top of the script |
| Login password | `PWD_HASH` — the SHA-256 hash of the password |
| Driver rates | editable live in the Drivers panel; saved in the browser (`localStorage`) |

To change the password, replace `PWD_HASH` with the SHA-256 hash of your new
password.

## Tech

Vanilla HTML, CSS and JavaScript. The only external dependency is
[Chart.js](https://www.chartjs.org/), loaded from a CDN.

## Notes

- The login password is hashed in client-side code and the sheet is public —
  this gates casual viewing, not a determined visitor. Fine for an internal
  tool; don't treat it as real access control.
- Column 22 (`COL.driveMinutes`) is treated as **trip duration in minutes**
  everywhere: the "Drive time" summary card, the sessions table and the driver
  payout categories (0–10 min / 10–20 min). If your sheet ever logs kilometres
  there instead, update the card label and the payout thresholds together.
