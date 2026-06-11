/**
 * Builds an improved "A Smile from Kenya" session form with structured inputs:
 * dropdowns/checkboxes instead of free text, real Date/Time/Number questions,
 * required fields, validation, and a conditional follow-up section.
 *
 * HOW TO USE
 *   1. https://script.google.com → New project → paste this file.
 *   2. Edit the lists in CONFIG below to match your team.
 *   3. Run buildImprovedForm() and authorize it.
 *   4. Read the Execution log: it prints the form URLs and the exact `COL`
 *      object to paste into dashboard.html (the generated column order).
 *   5. In the new form: Responses → Link to Sheets, then point the dashboard's
 *      SHEET_ID / SHEET_GID at that sheet.
 *
 * Note: this creates a NEW form + sheet. Keep using your current form until
 * you've migrated history, or prefer "Option A" (edit the existing form in
 * place) from FORM_GUIDE.md, which needs no dashboard change at all.
 */

var CONFIG = {
  title: 'A Smile from Kenya — Session Report',
  description: 'Log one report per session. Fields marked * are required.',

  facilitators: ['Add your', 'facilitators', 'here', 'Other'],
  drivers:      ['Add your', 'drivers', 'here'],
  places:       ['Add your', 'common places', 'here', 'Other'],
  eventTypes:   ['Children', 'Parents', 'Teachers (TTT)', 'Office', 'Other'],
  ageGroups:    ['Under 6', '6–12', '13–18', 'Adults', 'Mixed'],

  // Drive time: capture exact minutes (number) or duration bands (multiple
  // choice). Bands match the dashboard's payout tiers and remove "unknown".
  driveTimeAsBands: false,
  driveTimeBands: ['0–10 min', '10–20 min', '20+ min'],

  maxParticipants: 500,
  maxDriveMinutes: 120,
};

function buildImprovedForm() {
  var form = FormApp.create(CONFIG.title)
    .setDescription(CONFIG.description)
    .setCollectEmail(true)            // reliable attribution (column B)
    .setLimitOneResponsePerUser(false)
    .setAllowResponseEdits(true)
    .setProgressBar(true);

  // ── Main questions, in column order ────────────────────────────────
  form.addListItem().setTitle('Facilitator *').setRequired(true)
    .setChoiceValues(CONFIG.facilitators);

  form.addDateItem().setTitle('Session date *').setRequired(true);

  form.addListItem().setTitle('Place *').setRequired(true)
    .setChoiceValues(CONFIG.places);

  // Checkboxes → several drivers come through as one comma-separated cell,
  // which the dashboard already splits per driver.
  form.addCheckboxItem().setTitle('Driver(s) *').setRequired(true)
    .setChoiceValues(CONFIG.drivers);

  form.addListItem().setTitle('Event type *').setRequired(true)
    .setChoiceValues(CONFIG.eventTypes);

  form.addParagraphTextItem().setTitle('Topics covered');

  // Participants: number, bounded.
  form.addTextItem().setTitle('Number of participants *').setRequired(true)
    .setValidation(FormApp.createTextValidation()
      .setHelpText('Enter a whole number (0–' + CONFIG.maxParticipants + ').')
      .requireNumberBetween(0, CONFIG.maxParticipants).build());

  form.addListItem().setTitle('Age group').setChoiceValues(CONFIG.ageGroups);

  form.addParagraphTextItem().setTitle('What did participants learn?');
  form.addParagraphTextItem().setTitle('Questions raised by participants');
  form.addParagraphTextItem().setTitle('Other comments');

  // Drive time — minutes (number) or bands.
  if (CONFIG.driveTimeAsBands) {
    form.addMultipleChoiceItem().setTitle('Drive time *').setRequired(true)
      .setChoiceValues(CONFIG.driveTimeBands);
  } else {
    form.addTextItem().setTitle('Drive time in minutes *').setRequired(true)
      .setValidation(FormApp.createTextValidation()
        .setHelpText('Minutes, not kilometres (0–' + CONFIG.maxDriveMinutes + ').')
        .requireNumberBetween(0, CONFIG.maxDriveMinutes).build());
  }

  form.addTimeItem().setTitle('Start time *').setRequired(true);
  form.addTimeItem().setTitle('End time *').setRequired(true);

  // ── Conditional follow-up section ──────────────────────────────────
  var followupSection = form.addPageBreakItem()
    .setTitle('Follow-up')
    .setHelpText('A few more details about the follow-up.');
  var reason = form.addParagraphTextItem()
    .setTitle('Why is a follow-up needed?');
  followupSection.setGoToPage(FormApp.PageNavigationType.SUBMIT); // after reason → submit

  // Yes/No must be created after the page break so it can target it, then
  // moved back to just before the section (after End time).
  var followup = form.addMultipleChoiceItem().setTitle('Follow-up needed? *').setRequired(true);
  followup.setChoices([
    followup.createChoice('Yes', followupSection),
    followup.createChoice('No', FormApp.PageNavigationType.SUBMIT),
  ]);
  form.moveItem(followup.getIndex(), followupSection.getIndex());

  // ── Report the resulting column mapping for dashboard.html ──────────
  // Timestamp(0) + Email(1) are added automatically by Forms/CollectEmail.
  var col = {
    timestamp: 0, email: 1,
    facilitator: 2, date: 3, place: 4, driver: 5, project: 6, topics: 7,
    participants: 8, ageGroup: 9, learned: 10, questions: 11, comments: 12,
    driveMinutes: 13, startTime: 14, endTime: 15, followup: 16, followupReason: 17,
  };

  Logger.log('Form created.');
  Logger.log('Edit URL:    ' + form.getEditUrl());
  Logger.log('Live URL:    ' + form.getPublishedUrl());
  Logger.log('Paste this COL object into dashboard.html:');
  Logger.log('const COL = ' + JSON.stringify(col, null, 2) + ';');
  Logger.log('Then: Responses → Link to Sheets, and set SHEET_ID / SHEET_GID.');
}
