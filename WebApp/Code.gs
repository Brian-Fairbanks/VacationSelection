// --- CONFIGURATION ---
const configs = {
  hr_validation_sheet_id: "1QDF8CUhbC4cZKK0dnf5gOPL3SA7hXFihK1BqmJsufic", // 2026 HR Validations
};
const SHEET_MAIN = "Sheet1";
const SHEET_CACHE = "Cache";

// --- CORE WEB APP FUNCTIONS ---
function doGet() {
  var html = HtmlService.createTemplateFromFile("Index");
  // 1. Get roster data (this is your existing code)
  var rosterList = getHrRosterList();
  html.rosterData = JSON.stringify(rosterList);

  // --- NEW DEBUG CODE ---
  // Let's find out what email the app is *really* seeing
  var userEmail = "";
  try {
    userEmail = Session.getActiveUser().getEmail();
    if (!userEmail) {
      userEmail = "EMAIL_IS_BLANK (empty string)";
    }
  } catch (e) {
    userEmail = "ERROR_GETTING_EMAIL: " + e.message;
  }
  // Pass this 'userEmail' string to the HTML file
  html.debugEmail = userEmail;
  // --- END DEBUG CODE ---

  return html.evaluate().setTitle("Vacation Selection Form");
}

/**
 * A helper function to include other HTML files in our main template.
 */
function include(filename) {
  return HtmlService.createTemplateFromFile(filename).evaluate().getContent();
}

// --- INITIAL PAGE LOAD ---
function getInitialUserInfo(passedEmail) {
  var data = { userInfo: null, previousPicks: null, logs: [] };

  var email = passedEmail || Session.getActiveUser().getEmail(); // This is the cleanest syntax
  data.logs.push("Email found: " + (email || "NULL/BLANK"));
  if (!email) return data;

  var searchName = convertEmailToSearchableName(email);
  data.logs.push("Search term: " + searchName);
  var matches = findMatchingUsers(searchName);

  data.logs.push("Matches found: " + JSON.stringify(matches));
  if (matches.length === 0) {
    data.logs.push("No matches found.");
    return data;
  }

  // Confidence check
  var bestMatch = matches[0];
  var isConfident =
    (matches.length === 1 && bestMatch.score === 1.0) ||
    (matches.length > 1 && bestMatch.score === 1.0 && matches[1].score < 1.0);
  data.logs.push("is confident: " + isConfident);

  if (isConfident) {
    // --- This is the correct logic ---
    data.logs.push("Confident match found: " + JSON.stringify(bestMatch));
    data.logs.push("Now calling getEmployeeDataAndPicks...");

    // 1. Call the function to get the data
    var successData = getEmployeeDataAndPicks(bestMatch.id);
    // data.logs.push("Data (as JSON): " + JSON.stringify(successData));

    // 2. Merge the results into your main 'data' object
    data.userInfo = successData.userInfo;
    data.previousPicks = successData.previousPicks;

    // 3. Log success and return the *full* object
    // data.logs.push("Successfully retrieved data for user.");
    return data;
    // --- End correct logic ---
  } else {
    data.logs.push("No confident match found.");
    return data; // Not confident, return the object with logs
  }
}

function convertEmailToSearchableName(email) {
  var username = email.split("@")[0];
  return username.replace(".", " ");
}

// --- DATA-GETTING FUNCTIONS (CALLED FROM HTML) ---
function getEmployeeDataAndPicks(employeeId) {
  var userInfo = findUserById(employeeId);
  if (!userInfo) return null;
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
    var ss = SpreadsheetApp.openById(configs.hr_validation_sheet_id);
    var sh = ss.getSheetByName(SHEET_CACHE);
    var rows = sh.getLastRow(),
      cols = sh.getLastColumn();
    if (rows < 2) return [];
    var data = sh.getRange(2, 1, rows - 1, 4).getValues(); // Get all 4 columns
    var roster = [];
    for (var i = 0; i < data.length; i++) {
      roster.push({
        id: data[i][0],
        name: String(data[i][1] || ""),
        searchString: String(data[i][2] || ""), // This is the 'NormalizedSearchString' column
        tokensCsv: String(data[i][3] || ""), // This is the 'TokensCSV' column
      });
    }
    return roster;
  } catch (e) {
    Logger.log(e);
    return [];
  }
}

// --- MAIN DATA LOOKUPS (Keep This) ---
function findUserById(employeeId) {
  try {
    var ss = SpreadsheetApp.openById(configs.hr_validation_sheet_id);
    var sheet = ss.getSheetByName(SHEET_MAIN);
    var data = sheet.getDataRange().getValues();
    var ID_COLUMN_INDEX = 0;
    for (var i = 1; i < data.length; i++) {
      if (String(data[i][ID_COLUMN_INDEX]) == String(employeeId)) {
        // --- THIS IS THE FIX ---
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
        // --- END FIX ---
      }
    }
    return null;
  } catch (e) {
    Logger.log(e);
    return null;
  }
}

function findPreviousPicks(employeeId) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet(); // Correctly get submission sheet
    var sheet = ss.getSheetByName(SHEET_MAIN);
    var data = sheet.getDataRange().getValues();
    var ID_COLUMN_INDEX = 3; // From your CSV
    for (var i = data.length - 1; i > 0; i--) {
      if (String(data[i][ID_COLUMN_INDEX]) == String(employeeId)) {
        return data[i];
      }
    }
    return null;
  } catch (e) {
    Logger.log(e);
    return null;
  }
}

// --- CACHE BUILDER (Keep This) ---
function buildNormalizedCacheSheet() {
  var ss = SpreadsheetApp.openById(configs.hr_validation_sheet_id);
  var cacheSheet = ss.getSheetByName(SHEET_CACHE);
  if (cacheSheet) {
    cacheSheet.clear();
  } else {
    cacheSheet = ss.insertSheet(SHEET_CACHE);
  }

  cacheSheet.appendRow([
    "EmployeeID",
    "DisplayName",
    "NormalizedSearchString",
    "TokensCSV",
  ]);
  cacheSheet.setFrozenRows(1);

  var rosterSheet = ss.getSheetByName(SHEET_MAIN);
  var data = rosterSheet.getDataRange().getValues();
  var ID_COL = 0,
    NAME_COL = 1;
  var outputRows = [];

  for (var i = 1; i < data.length; i++) {
    var id = data[i][ID_COL];
    var name = String(data[i][NAME_COL] || "").trim();
    if (!name) continue;
    var searchParts = normalizeRosterName(name);
    var searchString = searchParts.join(" ");
    var toks = Array.from(
      new Set(tokenize(name).concat(tokenize(searchString)))
    );
    outputRows.push([id, name, searchString, toks.join(" ")]);
  }

  if (outputRows.length > 0) {
    cacheSheet.getRange(2, 1, outputRows.length, 4).setValues(outputRows);
  }
  SpreadsheetApp.flush();
  Logger.log(
    "SUCCESS: 'Cache' built with " + outputRows.length + " employees."
  );
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

// --- TEST FUNCTION ---
function testLookup() {
  Logger.log("--- Test 0: Rebuilding Cache Sheet ---");
  buildNormalizedCacheSheet();

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

  var emailCheck = getInitialUserInfo(email);
  Logger.log(emailCheck);
}
