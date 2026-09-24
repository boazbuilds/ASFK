/**
 * Builds an improved "A Smile from Kenya" session form: checkboxes instead of
 * typed names, validated numbers, the six distance bands, required fields and
 * a follow-up section that only appears when it's needed. Background and the
 * reasons behind each question: FORM_GUIDE.md.
 *
 * HOW TO USE
 *   1. https://script.google.com → New project → paste this file.
 *   2. Fill in the name lists in CONFIG below.
 *   3. Run buildImprovedForm() and authorise it.
 *   4. The execution log prints the form links plus SHEET_ID and SHEET_GID.
 *      Put those two in dashboard.html. Question titles are recognised by the
 *      dashboard, so nothing else needs to change.
 *   5. Share the new responses spreadsheet as "Anyone with the link can view"
 *      (the dashboard reads it from the browser).
 *
 * This creates a NEW form and spreadsheet; the current one keeps working.
 */

var CONFIG = {
  title: 'A Smile from Kenya — Session report',
  description: 'One report per session, please. Questions marked * are required.',
  sheetLocale: 'en_GB',   // day-first dates, as the dashboard expects

  facilitators: ['Name 1', 'Name 2', 'Name 3'],
  drivers:      ['Driver 1', 'Driver 2'],
  places:       ['Place 1', 'Place 2'],
  projects: [
    'Amazing You! session children',
    'Amazing You! session parents',
    'Next to You! session',
    'Next to You! counseling',
    'Teach the Teacher',
    'Office meeting',
  ],
  ageGroups: ['Under 6', '6–12', '13–17', '18 and over', 'Mixed'],
  // Must match the driver-rate bands on the dashboard
  distanceBands: [
    '0-10 minutes drive', '10-20 minutes drive', '20-30 minutes drive',
    '30-40 minutes drive', '40-50 minutes drive', '50-60 minutes drive',
  ],
};

function wholeNumber(help) {
  return FormApp.createTextValidation().setHelpText(help).requireWholeNumber().build();
}

function buildImprovedForm() {
  var form = FormApp.create(CONFIG.title)
    .setDescription(CONFIG.description)
    .setCollectEmail(true)
    .setAllowResponseEdits(true)   // people fix a report instead of sending it twice
    .setProgressBar(true)
    .setConfirmationMessage('Thank you, your report is saved. Please don\'t submit it again — '
      + 'use "Edit your response" if something needs changing.');

  // Titles contain the words the dashboard looks for (COL_HEADERS).
  form.addCheckboxItem().setTitle('Name(s) of facilitator(s)').setRequired(true)
    .setChoiceValues(CONFIG.facilitators).showOtherOption(true);
  form.addDateItem().setTitle('Date').setRequired(true);
  form.addMultipleChoiceItem().setTitle('Place').setRequired(true)
    .setChoiceValues(CONFIG.places).showOtherOption(true);
  form.addCheckboxItem().setTitle('Driver(s)').setRequired(true)
    .setChoiceValues(CONFIG.drivers).showOtherOption(true);
  form.addMultipleChoiceItem().setTitle('Project/event').setRequired(true)
    .setChoiceValues(CONFIG.projects).showOtherOption(true);
  form.addParagraphTextItem().setTitle('Which lesson(s)/topic(s)');
  form.addTextItem().setTitle('Number of participants')
    .setHelpText('Children or parents present — just the number, e.g. 45. Leave empty for teacher trainings, counseling and office meetings.')
    .setValidation(wholeNumber('Just the number, e.g. 45'));
  form.addTextItem().setTitle('Number of participating teachers')
    .setHelpText('Teach the Teacher only — just the number.')
    .setValidation(wholeNumber('Just the number, e.g. 20'));
  form.addListItem().setTitle('Age group').setChoiceValues(CONFIG.ageGroups);
  form.addParagraphTextItem().setTitle('What did the participants learn?');
  form.addParagraphTextItem().setTitle('Did participants ask questions? If yes, which?');
  form.addParagraphTextItem().setTitle('Comments: share positive and negative aspects');
  form.addMultipleChoiceItem().setTitle('Distance from Malindi (one way)').setRequired(true)
    .setChoiceValues(CONFIG.distanceBands);
  form.addTimeItem().setTitle('Start time').setRequired(true);
  form.addTimeItem().setTitle('End time').setRequired(true)
    .setHelpText('24-hour clock: 1 pm is 13:00.');

  // Follow-up: Yes opens one more short section, No submits.
  var followup = form.addMultipleChoiceItem().setTitle('Follow-up needed?').setRequired(true);
  var section = form.addPageBreakItem().setTitle('Follow-up');
  form.addTextItem().setTitle('For how many children?').setValidation(wholeNumber('Just the number'));
  form.addParagraphTextItem().setTitle('Follow-up details');
  followup.setChoices([
    followup.createChoice('Yes', section),
    followup.createChoice('No', FormApp.PageNavigationType.SUBMIT),
  ]);

  // Responses spreadsheet with day-first dates
  var ss = SpreadsheetApp.create(CONFIG.title + ' (responses)');
  ss.setSpreadsheetLocale(CONFIG.sheetLocale);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
  var responses = ss.getSheets().filter(function (s) { return s.getFormUrl(); })[0] || ss.getSheets()[0];

  Logger.log('Form (edit):   ' + form.getEditUrl());
  Logger.log('Form (fill in): ' + form.getPublishedUrl());
  Logger.log('Responses:     ' + ss.getUrl());
  Logger.log('Put these in dashboard.html:');
  Logger.log("  const SHEET_ID  = '" + ss.getId() + "';");
  Logger.log("  const SHEET_GID = '" + responses.getSheetId() + "';");
  Logger.log('Then share the responses spreadsheet as "Anyone with the link can view".');
}
