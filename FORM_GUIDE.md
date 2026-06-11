# Improving the data-entry form

The dashboard is only as good as what facilitators type into the Google Form.
Today the form lets people type freely, so the dashboard has to *guess*: it
re-parses dates, splits `"John, Peter"`, treats `no`/`nee`/`0` as the same
answer, and merges `John` with `john`. Every one of those guesses is a place
where a payout or an impact number can go wrong.

**Fix the input and the guessing disappears.** This guide gives the design
principles, a question-by-question plan, and two ways to apply it.

---

## Design principles for better field data

1. **Turn free text into choices.** Names (facilitator, driver, place) and the
   event type should be **dropdowns or checkboxes**, never open text. This is
   the single biggest win: it stops `John` / `john` / `Jon` from splitting one
   person's pay across three cards, and stops event-type typos from breaking
   the charts. Add a single *"Other…"* option that opens a text box for the
   genuinely new case.

2. **Use the right question type per field.** A Date question kills the
   DD-MM vs MM-DD ambiguity; Time questions give clean start/end times; a
   Number question with validation stops "twenty" or blanks landing in the
   participant count.

3. **Make the money/impact fields required.** Date, facilitator, place,
   participants, driver and drive time drive payouts and reporting — mark them
   required so you never get a blank the dashboard has to invent a value for.

4. **One language, one vocabulary.** The data mixes Dutch and English
   (`no`/`nee`). Pick one for every option list so the answers are consistent.

5. **Model "several people" explicitly.** If a session can have more than one
   driver, use **checkboxes of known drivers** rather than a typed
   `"John, Peter"`. Each person is then attributed exactly.

6. **Ask only what's relevant, with conditional logic.** Use *"Go to section
   based on answer"*: only ask *why* a follow-up is needed when the answer is
   *Yes*. Shorter form, fewer junk fields.

7. **Label units in the question itself.** The famous one: **drive time is in
   minutes.** Put "(in minutes)" in the question title and the help text, so it
   never gets logged as kilometres again.

8. **Validate and bound numbers.** Participants `0–500`, drive time `0–120`.
   Response validation catches fat-finger entries at the source.

9. **Collect identity automatically.** Turn on *Collect email addresses* and/or
   a facilitator dropdown so every row is reliably attributable.

10. **Keep the form mobile-first.** Field workers use phones: prefer taps
    (multiple choice) over typing, keep it short, and consider a pre-filled
    link per facilitator.

11. **Don't reorder questions after launch.** Question order *is* the sheet's
    column order, and the dashboard reads fixed column positions (`COL` in
    `dashboard.html`). Add new questions at the **end**; never drag old ones
    around or the columns shift under the dashboard.

12. **One source of truth for the option lists.** When a new facilitator,
    driver or place appears, add them to the dropdown — don't let people fall
    back to free text. Keep the canonical list somewhere (a sheet tab) so it's
    easy to maintain.

---

## Question-by-question plan

Each row shows the field, the recommended Google Forms question type, and the
dashboard workaround it removes.

| Field | Recommended type | Required | Removes this dashboard guess |
|------|------------------|:---:|------------------------------|
| Facilitator | **Dropdown** (+ Other) | ✓ | case/spelling merge of names |
| Date | **Date** | ✓ | `DD-MM-YYYY` text re-parsing |
| Place | **Dropdown** (+ Other) | ✓ | distinct-location miscount |
| Driver(s) | **Checkboxes** (+ Other) | ✓ | splitting `"John, Peter"` |
| Event type | **Dropdown** | ✓ | keyword-matching the project text |
| Topics covered | Checkboxes or Paragraph | – | — |
| Participants | **Short answer → Number**, `0–500` | ✓ | blank/`NaN` participant counts |
| Age group | Dropdown / Checkboxes | – | — |
| What they learned | Paragraph | – | — |
| Questions raised | Paragraph | – | — |
| Follow-up needed? | **Multiple choice: Yes / No** | ✓ | `no`/`nee`/`0` normalization |
| Follow-up reason | Paragraph (**only if Yes**) | – | — |
| Comments | Paragraph | – | — |
| Drive time **(in minutes)** | **Short answer → Number**, `0–120` | ✓ | the km-vs-minutes ambiguity & "unknown" trips |
| Start time | **Time** | ✓ | unparsable session times |
| End time | **Time** | ✓ | unparsable session times |

> **Tip for drive time:** if exact minutes are hard to capture in the field,
> use a **Multiple choice** with the payout bands instead — *0–10 min* /
> *10–20 min* / *20+ min*. That matches the driver-rate tiers in the dashboard
> exactly and removes the "? min / unknown" bucket entirely.

---

## How to apply it

### Option A — improve your existing form *(recommended, keeps everything working)*

Editing a question **in place** keeps its column, so your sheet, your history
and the live dashboard keep working unchanged.

1. Open the form → for each free-text field above, click the question, open the
   type menu (top-right of the question) and switch it to **Dropdown**,
   **Checkboxes**, **Date**, **Time** or **Short answer**.
   - For dropdowns/checkboxes, paste the current distinct values from the sheet
     as options, then add **Other**.
   - For Participants and Drive time, choose **Short answer →** ⋮ **Response
     validation → Number → between**.
2. Toggle **Required** on every field marked ✓ in the table.
3. For *Follow-up reason*, put it in its own section and set the *Follow-up
   needed?* question to **Go to section based on answer** (Yes → reason, No →
   submit).
4. Add **"(in minutes)"** to the drive-time question title and help text.
5. In **Settings**, turn on **Collect email addresses**.
6. **Don't** reorder questions. Add anything new at the end.

Because the columns don't move, **no dashboard change is needed.**

### Option B — generate a fresh, clean form automatically

`tools/build-improved-form.gs` is a Google Apps Script that builds the whole
improved form (correct types, validation, required flags, conditional
follow-up section) in one run.

1. Go to <https://script.google.com> → **New project**.
2. Paste in the contents of `tools/build-improved-form.gs`.
3. Edit the option lists at the top (facilitators, drivers, places, event
   types) to match your team.
4. Run `buildImprovedForm()` and authorize it. The script logs the new form's
   edit and response URLs.
5. Link the form to a new spreadsheet (**Responses → Link to Sheets**).

Because this is a **new** sheet with a clean column order (no historical gap),
point the dashboard at it: update `SHEET_ID` and `SHEET_GID` in `dashboard.html`
and replace the `COL` object with the one the script prints (it matches the
generated column order). Also set the sheet's **Date** column format to *Plain
text* or `DD-MM-YYYY`, since the dashboard reads dates as day-first text.

> Option B starts you with an empty response sheet. Keep using your current
> form until you've migrated historical rows, or just go with Option A.

---

## Keeping it clean over time

- Add new facilitators/drivers/places to the **dropdown options**, not as free
  text.
- Review the dashboard's **Data quality** panel after each round of sessions —
  it lists exactly which rows are missing fields and flags duplicate spellings,
  which tells you what to tighten in the form.
- Keep the form in one language and never reorder its questions.
