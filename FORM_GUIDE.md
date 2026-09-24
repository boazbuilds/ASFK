# Improving the data-entry form

The dashboard is only as good as what people type into the Google Form. It
now works around the problems below, but every workaround is a guess, and a
guess on a payment is a risk. Fixing the form removes the guessing.

This guide has three parts: what the current data shows, the form changes
that fix it, and the principles behind them.

---

## What the current data shows

Checked on 24 September 2026 across 559 reports. Only totals are listed here,
no names.

| Problem | How often | Effect before the fix |
|---|---|---|
| End time typed as a morning time, such as 1:00 instead of 13:00 | 112 of 509 sessions (22%) | "Hours delivered" was far too low |
| Several people typed into one *Facilitator(s)* or *Driver(s)* box | 19 facilitator and 35 driver answers | Pay split over made-up "people" |
| One person spelled several ways | 4 facilitators, 2 drivers | One person's sessions spread over several cards |
| Follow-up answered in free text | 61 sentences next to 105 "yes" and 37 "no" answers ("No", "Nop", "No follow-up.") | Follow-ups over-counted. Some sentences belong to other questions ("Amazing!", "Adult") |
| Headcount typed with words | 8 participant answers ("948 participants", "more than 200") and 3 × "No" as a teacher count | About 1,400 people missing from "People reached" |
| Age group typed freely | 96 different answers | Cannot be summarised |
| Distance left empty | 44 sessions | Driver paid at the "unknown distance" rate |
| Start or end time left empty | 50 sessions | No hours counted |
| Same report submitted twice | 4 identical reports | Counted and paid twice |
| Impossible date | 1 report | Session missing from months and payment periods |

The dashboard now handles all of these. It reads the end times as afternoon,
splits and merges names, counts headcounts written with words, and leaves out
exact duplicates. It also lists everything it corrected in its **Data quality**
panel. The form changes below stop the problems from being created at all.

**Already good:** *Distance from Malindi (one way)* is a multiple-choice
question with fixed bands (0–10 … 50–60 minutes drive). The driver payments
are built on it. Only two of its six bands had a driver rate, so set the
others in the dashboard's **Payment Summary**.

---

## Changes to make in the current form

Changing a question's **type** keeps its column, so existing answers stay put.
New questions are added as new columns at the end. The dashboard finds
columns by their question title, so both changes are safe.

1. **Name(s) of facilitator(s)** → **Checkboxes** with the team's names, plus
   *Other*. This ends made-up combinations and spelling variants.
2. **Driver(s)** → **Checkboxes** with the drivers' names, plus *Other*.
3. **Number of participants** and **Number of participating teachers** →
   Short answer, then ⋮ → **Response validation → Number → Greater than or
   equal to 0**. Help text: *"Just the number, e.g. 45."*
4. **Is there any follow-up needed (counseling)?** → **Multiple choice:
   Yes / No**. Add two new questions at the end: **"For how many children?"**
   (number) and **"Follow-up details"** (paragraph). The dashboard shows the
   details answer in its follow-up list automatically when the question title
   contains "Follow-up details".
5. **Age group** → **Dropdown** with fixed bands, for example *Under 6 · 6–12
   · 13–17 · 18 and over · Mixed*.
6. **Distance from Malindi (one way)** → mark as **Required**.
7. **Start time** and **End time** → mark as **Required**. Add this help text
   to *End time*: *"24-hour clock: 1 pm is 13:00."*
8. **Date** → make sure it is a **Date** question, not short answer.
9. **Settings → Presentation → Confirmation message**: *"Thank you, your report
   is saved. Please don't submit it again. Use 'Edit your response' to change
   it."* Also turn on **Allow response editing**, so people fix a report
   instead of sending a second one.

Don't delete questions that already have answers. Rename a question only
lightly: the dashboard recognises columns by keywords in their title (see
`COL_HEADERS` in `dashboard.html`). When it can't find a title, it falls back
to the column's usual position.

---

## Design principles behind these changes

- **Choose, don't type.** Names, places, activity types and age groups work
  best as choices. Free text creates spelling variants, and variants split
  people and categories.
- **The right question type for each answer.** Use a Date question for dates,
  Time questions for times, and Number validation for counts. The form then
  rejects impossible input before it reaches the sheet.
- **Required means reliable.** Everything that drives pay or impact numbers
  should be required: date, facilitator, driver, distance, times and
  headcount.
- **One question, one answer.** "Is follow-up needed? If yes, for how many?"
  is two questions. Asking them separately gives a clean yes/no plus a number.
- **Put the unit and format in the question.** "24-hour clock", "just the
  number", "minutes drive". People fill in what they read.
- **Design for a phone in the field.** Taps beat typing. Keep it short, and
  use sections to show extra questions only when relevant.
- **Make resubmitting unnecessary.** On a slow connection people press Submit
  again. A clear confirmation and editable responses prevent duplicates.
- **Keep the option lists current.** When someone joins the team or a new
  place is visited, add them to the choices, so nobody falls back to "Other".

---

## Starting fresh: `tools/build-improved-form.gs`

This Google Apps Script builds a new form with all of the above in one run:
checkboxes for people, validated numbers, the six distance bands, required
fields, and a conditional follow-up section. Its question titles match what
the dashboard recognises, so no code changes are needed apart from the sheet
link.

1. Go to <https://script.google.com>, choose **New project**, and paste the
   script in.
2. Edit the name lists at the top: facilitators, drivers and places.
3. Run `buildImprovedForm()` and authorise it. The log prints the new form's
   links.
4. In the form, open **Responses → Link to Sheets**. In the new spreadsheet,
   set **File → Settings → Locale** to a day-first country such as Kenya or
   the United Kingdom. The dashboard reads dates day-first.
5. Put the new sheet's ID and tab ID (`gid`) into `SHEET_ID` and `SHEET_GID`
   in `dashboard.html`.

A new form starts with an empty sheet. Keep the current form running until
you've decided how to handle the history, or simply apply the changes above to
the current form instead.
