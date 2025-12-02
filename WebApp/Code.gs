// --- CONFIGURATION ---
const HR_VALIDATION_ID = "1QDF8CUhbC4cZKK0dnf5gOPL3SA7hXFihK1BqmJsufic"; // 2026 HR Validations
const HR_VALIDATION_SHEET_NAME = "Sheet1";
const EMAILS_SHEET_NAME = "Emails";
const ManualEntriesSheetName = "ManualEntries";
const SHEET_CACHE = "Cache"; // The new sheet name created for maintaining fuzzy lookups of user names
const SubmissionSheetName = "2026-Vacation Picks";

// --- CORE WEB APP FUNCTIONS ---
function doGet() {
  var html = HtmlService.createTemplateFromFile("Index");
  // 1. Get roster data (this is your existing code)
  var rosterList = getHrRosterList();
  html.rosterData = JSON.stringify(rosterList);

  return html.evaluate().setTitle("Vacation Selection Form");
}

/**
 * A helper function to include other HTML files in our main template.
 */
function include(filename) {
  return HtmlService.createTemplateFromFile(filename).evaluate().getContent();
}


// --- HELPER: GET EMAIL MAP ---
// Returns an object: { "538": "bfairbanks@...", "123": "..." }
function getEmployeeEmailMap() {
  var ss = SpreadsheetApp.openById(HR_VALIDATION_ID);
  var sheet = ss.getSheetByName(EMAILS_SHEET_NAME);
  if (!sheet) return {};

  var data = sheet.getDataRange().getValues();
  var map = {};
  
  // Headers: [ID, First, Last, Email, ...]
  // Assumes ID is Col A (0) and Email is Col D (3) based on your description
  for (var i = 1; i < data.length; i++) {
    var id = String(data[i][0]);
    var email = String(data[i][3]).toLowerCase().trim();
    if (id && email) {
      map[id] = email;
    }
  }
  return map;
}

// --- INITIAL PAGE LOAD ---
function getInitialUserInfo(passedEmail) {
  var data = { userInfo: null, previousPicks: null, logs: [] };

  var email = (passedEmail || Session.getActiveUser().getEmail()).toLowerCase();

  data.logs.push("Email found: " + email);
  if (!email) return data;

  // --- 1. EXACT EMAIL MATCH (New Priority) ---
  var roster = getHrRosterList();
  var directMatch = roster.find(u => u.email === email);

  if (directMatch) {
    data.logs.push("Exact email match found: " + directMatch.id);
    var successData = getEmployeeDataAndPicks(directMatch.id);
    data.userInfo = successData.userInfo;
    data.previousPicks = successData.previousPicks;
    return data;
  }

  // --- 2. FALLBACK: FUZZY SEARCH ---
  data.logs.push("No email match. Falling back to name search.");
  
  var searchName = convertEmailToSearchableName(email);
  var matches = findMatchingUsers(searchName); // This uses the roster we already fetched essentially

  // ... (Existing Confidence Check Logic) ...
  if (matches.length > 0) {
      var bestMatch = matches[0];
      var isConfident = (matches.length === 1 && bestMatch.score === 1.0) ||
                        (matches.length > 1 && bestMatch.score === 1.0 && matches[1].score < 1.0);
      
      if (isConfident) {
        var successData = getEmployeeDataAndPicks(bestMatch.id);
        data.userInfo = successData.userInfo;
        data.previousPicks = successData.previousPicks;
        return data;
      }
  }
  
  return data; // No match found
}

function convertEmailToSearchableName(email) {
  var username = email.split("@")[0];
  return username.replace(".", " ");
}

// --- DATA-GETTING FUNCTIONS (CALLED FROM HTML) ---
function getEmployeeDataAndPicks(employeeId) {
  // Finds user details in the Roster sheet
  var userInfo = findUserById(employeeId);
  if (!userInfo) return null;

  // Finds user's last submission in the Picks sheet
  var previousPicks = findPreviousPicks(employeeId);
  return { userInfo: userInfo, previousPicks: previousPicks };
}

// --- NEW, SIMPLIFIED, AND RELIABLE FUZZY MATCHING ---
function findMatchingUsers(searchText) {
  var q = normalizeText(String(searchText || "").trim());
  if (!q) return [];

  var roster = getHrRosterList(); // [{id, name, searchString, tokensCsv}, ...]
  var scored = [];

  // 1. We must create a "spaced" version for prefix matching
  // e.g., search for "bf" should match " bfairbanks " or " bf "
  var qSpaced = " " + q;

  for (var i = 0; i < roster.length; i++) {
    var emp = roster[i];
    var score = 0;

    // We add spaces to the start and end to ensure we match whole words/tokens
    var corpus = " " + emp.tokensCsv + " ";

    // 2. Check for a match
    if (corpus.includes(qSpaced)) {
      // This is a "prefix" or "whole token" match.
      // e.g., " bfairbanks " includes " bfairbanks"
      // e.g., " bf " includes " bf"
      score = 1.0; // Perfect match
    } else if (corpus.includes(q)) {
      // This is a partial match inside a token (e.g., "airbanks")
      score = 0.5; // Good match
    }

    // 3. Check for ID match (always a perfect score)
    if (String(emp.id).includes(q)) {
      score = 1.0;
    }

    if (score > 0) {
      scored.push({ id: emp.id, name: emp.name, score: score });
    }
  }

  // 4. Sort by best score
  scored.sort(function (a, b) {
    return b.score - a.score;
  });
  return scored.slice(0, 5);
}

// --- CACHE MANAGEMENT ---

/**
 * REBUILDS the entire Cache sheet.
 * It combines data from the Main HR Sheet AND the Manual Entries sheet.
 * Run this manually if the cache gets out of sync, or if the sheet is empty.
 */
function buildNormalizedCacheSheet() {
  var ss = SpreadsheetApp.openById(HR_VALIDATION_ID);
  var cacheSheet = ss.getSheetByName(SHEET_CACHE);
  
  if (!cacheSheet) { cacheSheet = ss.insertSheet(SHEET_CACHE); } 
  else { cacheSheet.clear(); }

  // UPDATED HEADER: Added "Email" at index 2
  cacheSheet.appendRow(["EmployeeID", "DisplayName", "Email", "NormalizedSearchString", "TokensCSV"]);
  cacheSheet.setFrozenRows(1);

  var outputRows = [];
  
  // 1. Get the Map of IDs to Emails
  var emailMap = getEmployeeEmailMap();

  // 2. Process HR Validation Sheet (Sheet1)
  var hrSheet = ss.getSheetByName(HR_VALIDATION_SHEET_NAME);
  if (hrSheet) {
    processSheetForCache(hrSheet, outputRows, emailMap);
  }

  // 3. Process Manual Entries
  var manualSheet = ss.getSheetByName(ManualEntriesSheetName);
  if (manualSheet) {
    // Manual entries won't be in the Email sheet, so they will get blank/default emails logic inside the helper
    processSheetForCache(manualSheet, outputRows, emailMap);
  }

  if (outputRows.length > 0) {
    // Write 5 columns now
    cacheSheet.getRange(2, 1, outputRows.length, 5).setValues(outputRows);
  }
  
  Logger.log("Cache built with " + outputRows.length + " rows.");
}

/**
 * Helper to process a sheet and add rows to the output array.
 */
function processSheetForCache(sheet, outputArray, emailMap) {
  var data = sheet.getDataRange().getValues();
  // Skip header (i=1)
  for (var i = 1; i < data.length; i++) {
    var id = String(data[i][0]);
    var name = String(data[i][1] || "").trim();
    
    if (!id || !name) continue; 

    // Deduplicate
    var exists = outputArray.some(function(row){ return String(row[0]) === id; });
    if(exists) continue;

    // LOOKUP EMAIL
    // If found in map, use it. If not, check if it was manually entered in the row (unlikely for now).
    var email = emailMap[id] || ""; 

    var searchParts = normalizeRosterName(name); 
    var searchString = searchParts.join(' ');
    var toks = Array.from(new Set(tokenize(name).concat(tokenize(searchString))));
    
    // Push 5 columns: ID, Name, Email, SearchStr, Tokens
    outputArray.push([id, name, email, searchString, toks.join(' ')]);
  }
}

/**
 * APPENDS a single user to the Cache.
 * Call this immediately after a manual entry is saved.
 * Updates the Cache if the ID exists, or appends if it doesn't.
 */
function appendUserToCache(userInfo) {
  var ss = SpreadsheetApp.openById(HR_VALIDATION_ID);
  var cacheSheet = ss.getSheetByName(SHEET_CACHE);

  // Safety: If cache is missing, build it fresh
  if (!cacheSheet || cacheSheet.getLastRow() < 1) {
    buildNormalizedCacheSheet();
    return;
  }

  var id = String(userInfo.employeeId);
  var displayName = userInfo.lastName + ", " + userInfo.firstName; 
  
  // --- HANDLE EMAIL ---
  // Use provided email, or default to the dummy email
  var email = (Session.getActiveUser().getEmail()).toLowerCase();

  var searchParts = normalizeRosterName(displayName);
  var searchString = searchParts.join(' ');
  var toks = Array.from(new Set(tokenize(displayName).concat(tokenize(searchString))));
  
  // 5 Columns: ID, Name, Email, SearchString, Tokens
  var newRowData = [id, displayName, email, searchString, toks.join(' ')];

  // ... (Existing ID lookup and update/append logic) ...
  // [Copy the loop logic from previous answer, just ensure setValues uses newRowData]
  
  var data = cacheSheet.getDataRange().getValues();
  var rowIndexToUpdate = -1;

  for (var i = 1; i < data.length; i++) {
    if (String(data[i][0]) === id) {
      rowIndexToUpdate = i + 1; 
      break;
    }
  }

  // 3. Execute Write
  if (rowIndexToUpdate > -1) {
    cacheSheet.getRange(rowIndexToUpdate, 1, 1, 5).setValues([newRowData]); // Update 5 cols
  } else {
    cacheSheet.appendRow(newRowData);
  }
}

// --- TEXT NORMALIZATION (Keep This) ---
function normalizeText(s) {
  return String(s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
function tokenize(s) {
  var n = normalizeText(s);
  if (!n) return [];
  return n.split(" ").filter(function (t) {
    return t.length > 0;
  });
}

// --- ROSTER ACCESS (Keep This) ---
function getHrRosterList() {
  try {
    var ss = SpreadsheetApp.openById(HR_VALIDATION_ID);
    var sh = ss.getSheetByName(SHEET_CACHE);
    
    if (!sh || sh.getLastRow() < 2) {
      buildNormalizedCacheSheet();
      sh = ss.getSheetByName(SHEET_CACHE);
    }

    var rows = sh.getLastRow();
    // Get 5 columns now
    var data = sh.getRange(2, 1, rows - 1, 5).getValues(); 
    var roster = [];
    for (var i = 0; i < data.length; i++) {
      roster.push({
        id: data[i][0],
        name: String(data[i][1] || ""),
        email: String(data[i][2] || "").toLowerCase(), // <--- NEW
        searchString: String(data[i][3] || ""), 
        tokensCsv: String(data[i][4] || ""), 
      });
    }
    return roster;
  } catch (e) { Logger.log(e); return []; }
}

// --- MAIN DATA LOOKUPS (Keep This) ---
function findUserById(employeeId) {
  var sheetNames = [HR_VALIDATION_SHEET_NAME, ManualEntriesSheetName];
  // 1. Try to find in HR Validation Sheet
  for (var j = 0; j < sheetNames.length; j++) {
    try {
      console.log("Checking sheet: ", sheetNames[j]);
      var ss = SpreadsheetApp.openById(HR_VALIDATION_ID);
      var sheet = ss.getSheetByName(sheetNames[j]);
      var data = sheet.getDataRange().getValues();
      var ID_COLUMN_INDEX = 0;
      for (var i = 1; i < data.length; i++) {
        if (String(data[i][ID_COLUMN_INDEX]) == String(employeeId)) {
          // Convert Date objects to simple strings so they can be sent.
          /*
          0 Employee Number
          1 Employee Name
          2 Default Tracking Level 3
          3 Rank
          4 Hire Date
          5 As of date
          6 Years of Service
          7 # of Holiday Leave Hours awarded
          8 # of Vacation Leave Hours awarded
          */
          return {
            employeeId: data[i][0],
            employeeName: data[i][1],
            trackingLevel: data[i][2],
            rank: data[i][3],
            hireDate: data[i][4].toString(),
            yearsOfService: data[i][6].toString(), // <-- CONVERTED
            holidayHours: data[i][7],
            vacationHours: data[i][8],
            shift: data[i][9],
          };
        }
      }
    } catch (e) {
      Logger.log(e);
    }
  }
  return null;
}

function findPreviousPicks(employeeId) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SubmissionSheetName);

    // --- USE YOUR NEW INDEXES ---
    // Column F = index 5
    const ID_COLUMN_INDEX = 5;
    // Column B = index 1
    const STATUS_COLUMN_INDEX = 1;
    // ----------------------------

    if (!sheet) {
      Logger.log("ERROR: Submission sheet not found: " + SubmissionSheetName);
      return null;
    }

    var data = sheet.getDataRange().getValues();

    // Search backwards from the latest submission
    for (var i = data.length - 1; i > 0; i--) {
      // i > 0 to skip header
      const rowId = data[i][ID_COLUMN_INDEX];
      const rowStatus = data[i][STATUS_COLUMN_INDEX];

      if (String(rowId) == String(employeeId) && rowStatus === "Active") {
        // Found the most recent, active submission for this user
        // We return the raw row, as the map-to-string logic
        // is now handled in the getEmployeeDataAndPicks function.
        return data[i].slice(2).map(function (value) {
          return value ? String(value) : "";
        });
      }
    }

    return null; // No *active* picks found
  } catch (e) {
    Logger.log("Error in findPreviousPicks: " + e.message);
    return null;
  }
}

function normalizeRosterName(rosterName) {
  var parts = String(rosterName || "").split(",");
  if (parts.length < 2) return [normalizeText(rosterName)];
  var lastName = normalizeText(parts[0].trim());
  var firstMiParts = parts[1].trim().split(/\s+/);
  var firstName = normalizeText(firstMiParts[0] || "");
  if (!firstName) return [lastName];
  var firstInitial = firstName.charAt(0);
  var lastInitial = lastName.charAt(0);
  var mi = normalizeText(firstMiParts.length > 1 ? firstMiParts[1] : "");
  var combos = [
    lastName,
    firstName,
    firstName + " " + lastName,
    lastName + " " + firstName,
    firstInitial + lastName,
    firstInitial + " " + lastName,
    lastName + " " + firstInitial,
    firstInitial + " " + lastInitial,
    firstInitial + lastInitial,
  ];
  if (mi) {
    var miInitial = mi.charAt(0);
    combos.push(firstInitial + miInitial + lastName);
    combos.push(firstName + " " + mi + " " + lastName);
    combos.push(firstInitial + " " + miInitial + " " + lastInitial);
    combos.push(firstInitial + miInitial + lastInitial);
  }
  combos.push(firstInitial + lastName);
  combos.push(firstName + lastName);
  combos.push(lastName + firstName);
  return Array.from(new Set(combos.map(normalizeText).filter(Boolean)));
}

/**
 *
 * Form Submission Handling
 */

/**
 * Saves manually entered user info to the ManualEntries sheet.
 * Mirrors the structure of the HR Validation sheet.
 */
function logManualUserToSheets(userInfo) {
  // const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ss = SpreadsheetApp.openById(HR_VALIDATION_ID);
  let sheet = ss.getSheetByName(ManualEntriesSheetName);

  // Create the sheet if it doesn't exist
  if (!sheet) {
    sheet = ss.insertSheet(ManualEntriesSheetName);
    const headers = [
      "Employee Number",
      "Employee Name",
      "Default Tracking Level 3",
      "Rank",
      "Hire Date",
      "As of date",
      "Years of Service",
      "# of Holiday Leave Hours awarded",
      "# of Vacation Leave Hours awarded",
      "Shift",
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }

  // --- CALCULATE "LAST OCTOBER 1st" ---
  const now = new Date();
  let refYear = now.getFullYear();
  // If we are currently before October (Month 9), the "last Oct 1st" was last year.
  if (now.getMonth() < 9) {
    refYear -= 1;
  }
  const asOfDate = `10/1/${refYear}`;
  // ------------------------------------

  // Prepare the row data (Mirrored Structure)
  const newRow = [
    userInfo.employeeId,
    `${userInfo.lastName}, ${userInfo.firstName}`, // Fixed: Use backticks for interpolation
    "Manual Entry", // Placeholder for Tracking Level
    userInfo.rank,
    userInfo.hireDate,
    asOfDate, // Dynamic date
    userInfo.yearsOfService,
    userInfo.holidayHours,
    userInfo.vacationHours,
    userInfo.shift,
  ];

  // Check for existing ID to update
  const data = sheet.getDataRange().getValues();
  const idColumnIndex = 0;
  let userUpdated = false;

  for (let i = 1; i < data.length; i++) {
    if (String(data[i][idColumnIndex]) === String(userInfo.employeeId)) {
      sheet.getRange(i + 1, 1, 1, newRow.length).setValues([newRow]);
      userUpdated = true;
      break;
    }
  }

  if (!userUpdated) {
    sheet.appendRow(newRow);
  }
  // Update the fuzzy search cache immediately
  appendUserToCache(userInfo);
}

/**
 * Flattens the nested client-side data into a single array row
 * starting from "Submission Date" (Column C).
 * @param {Object} formData - The complete submission payload.
 * @returns {Array} - A single array row with 89 columns of data.
 */
function flattenSubmissionData(formData) {
  const user = formData.userInfo;
  const submissions = formData.daySelections || [];

  // 9 header columns + 40*2 day columns = 89 total columns
  const fullRow = new Array(89).fill("");

  // --- Fill Static Header Data (First 9 Columns) ---
  const headerData = [
    new Date(), // Submission Date
    user.firstName,
    user.lastName,
    user.employeeId,
    user.rank,
    user.shift,
    user.hireDate,
    formData.acknowledgment,
    user.yearsOfService,
  ];

  // Place header data into the beginning of the array
  for (let i = 0; i < headerData.length; i++) {
    fullRow[i] = headerData[i];
  }

  // --- Fill Dynamic Day Selections ---
  // Start column index for Day 1 is 9 (the 10th column in this array)
  const START_DAY_INDEX = 9;

  submissions.forEach((daySelection) => {
    // Ensure the day index is valid (1-40)
    if (daySelection.day >= 1 && daySelection.day <= 40) {
      // Calculate the start position for this day's pair of columns
      const startIndex = START_DAY_INDEX + (daySelection.day - 1) * 2;

      // Safety check
      if (startIndex + 1 < fullRow.length) {
        // Column 1: Date (e.g., 'Day 1')
        fullRow[startIndex] = daySelection.date;

        // Column 2: Shifts (e.g., 'Shift Selection 1')
        fullRow[startIndex + 1] = daySelection.shifts.join(", ");
      }
    }
  });

  return fullRow;
}

/**
 * Processes the shift request data and appends it to the Google Sheet.
 * This function now handles versioning by superseding old picks.
 * @param {Object} formData - Data submitted from the client-side form.
 */
function processShiftRequest(formData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // Assuming SubmissionSheetName is defined and accessible
  const sheet = ss.getSheetByName(SubmissionSheetName);
  if (!sheet) {
    throw new Error("Could not find the target sheet.");
  }

  const employeeId = formData.userInfo.employeeId;

  // --- 1. DYNAMIC COLUMN INDEXING (Crucial for the lookup loop) ---
  // Get headers to find the correct 1-based column indices.
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  // Convert 0-based index from indexOf() to 1-based column number (+1)
  const statusColNum = headers.indexOf("Status") + 1;
  const idColNum = headers.indexOf("Employee ID #") + 1;

  // Convert 0-based index from indexOf() to 0-based array index (no change)
  const statusArrIndex = headers.indexOf("Status");
  const idArrIndex = headers.indexOf("Employee ID #");

  // Ensure the required columns exist
  if (statusColNum === 0 || idColNum === 0) {
    throw new Error(
      'Could not find "Status" or "Employee ID #" column in the sheet.'
    );
  }

  // --- 2. Supersede Old Submissions ---
  const data = sheet.getDataRange().getValues();
  // data[i] is the whole row array. We must use the 0-based array index (statusArrIndex, idArrIndex)
  for (let i = 1; i < data.length; i++) {
    // Start at 1 to skip header
    const rowId = data[i][idArrIndex];
    const rowStatus = data[i][statusArrIndex];

    if (String(rowId) === String(employeeId) && rowStatus === "Active") {
      // Found an old, active row for this user.
      // i + 1 is the 1-based row number. statusColNum is the 1-based column number.
      sheet.getRange(i + 1, statusColNum).setValue("Superseded");
    }
  }

  // --- 3. Flatten the New Data ---
  const flatData = flattenSubmissionData(formData);

  // --- 4. Prepare the New Row with Status and Manual Entry Flag, and log if needed ---

  // Determine the value for the "Manual Entry" column (Assumed to be the 1st column)
  const manualEntryValue = formData.isManualEntry ? "Yes" : "";
  if (formData.isManualEntry) {
    // Log or update the manually entered user info for future use
    logManualUserToSheets(formData.userInfo);
  }

  // Determine the value for the "Status" column (Assumed to be the 2nd column)
  // NOTE: This assumes your spreadsheet structure is: [Manual Entry], [Status], [Submission Date]...

  const newRow = [
    manualEntryValue, // Column 1: Manual Entry (Yes or blank)
    "Active", // Column 2: Status
    ...flatData, // Column 3 onwards: Submission Date, Employee Info, Day Selections
  ];

  // --- 5. Append the New Row ---
  sheet.appendRow(newRow);
}

// --- TEST FUNCTION ---
function testLookup() {
  Logger.log("--- Test 0: Rebuilding Cache Sheet ---");
  // buildNormalizedCacheSheet();

  Logger.log("--- Test 1: Find User by ID 538 ---");
  var data = findUserById("538");
  Logger.log(data);

  Logger.log("--- Test 2: Email Guesser (bfairbanks) ---");
  var email = "bfairbanks@pflugervillefire.org";
  var searchName = convertEmailToSearchableName(email);
  Logger.log("Email becomes search term: " + searchName);
  var nameData = findMatchingUsers(searchName);
  Logger.log(nameData);

  Logger.log("--- Test 3: Initials (b f) ---");
  var nameData2 = findMatchingUsers("b f");
  Logger.log(nameData2);

  Logger.log("--- Test 4: Compact Initials (bf) ---");
  var nameData3 = findMatchingUsers("bf");
  Logger.log(nameData3);

  Logger.log("--- Test 5: Full email (bfairbanks) ---");
  var nameData4 = findMatchingUsers("bfairbanks");
  Logger.log(nameData4);

  Logger.log("--- Test 6: Full Data Retreival", email, " ---");
  var emailCheck = getInitialUserInfo(email);
  Logger.log(emailCheck);
}

// --- NEW DEBUG TEST FUNCTION ---
/**
 * Test function to simulate client submission and verify data flattening.
 * Run this by selecting 'testFormSubmissionData' in the Apps Script menu and clicking 'Run'.
 */
function testFormSubmissionData() {
  Logger.log("--- STARTING TEST FORM SUBMISSION ---");

  // 1. SIMULATE CLIENT PAYLOAD
  // Use the structure of the data the client would send.
  // const testPayload = {
  //   acknowledgment: "continue",
  //   submittedAt: new Date().toISOString(),
  //   userInfo: {
  //     firstName: "Brian",
  //     lastName: "Fairbanks",
  //     employeeId: "538",
  //     rank: "Probationary Firefighter",
  //     shift: "B",
  //     hireDate: "Mon Jan 13 2025 00:00:00 GMT-0600 (Central Standard Time)",
  //     yearsOfService: "0",
  //     vacationHours: 192,
  //     holidayHours: 144
  //   },
  //   daySelections: [
  //     { day: 1, date: "02/06/2026", shifts: ["Day1", "Day2"] },
  //     { day: 2, date: "03/20/2026", shifts: ["Day1", "Day2"] },
  //     { day: 4, date: "06/18/2026", shifts: ["Day1", "Day2"] }
  //   ]
  // };

  // // 2. TEST DATA FLATTENING
  // Logger.log("Testing data flattening...");
  // const flatData = flattenSubmissionData(testPayload);

  // Logger.log("--- FLATTENED DATA STRUCTURE ---");
  // Logger.log("Total Columns: " + flatData.length);
  // // Log the first 15 columns to check header data and Day 1/2 structure
  // Logger.log("Header/Picks Preview (Cols 1-15): " + flatData.slice(0, 15).join(' | '));

  // // Example of what Day 4 (Cols 15-16) looks like (index 15)
  // Logger.log("Day 4 Data (Cols 16-17): " + flatData[15] + " | " + flatData[16]);

  // 3. TEST FIND PREVIOUS PICKS
  Logger.log("\nTesting previous picks lookup for ID 538...");
  const previousPicks = findPreviousPicks("538");

  if (previousPicks) {
    Logger.log("--- PREVIOUS PICKS FOUND ---");
    // Log the date of the first pick to confirm it's reading the row
    Logger.log("First Pick Date (Col 10): " + previousPicks[9]);
    Logger.log(previousPicks);
  } else {
    Logger.log(
      "--- PREVIOUS PICKS NOT FOUND (This may be correct if sheet is empty) ---"
    );
  }

  Logger.log("--- TEST COMPLETE ---");
}
