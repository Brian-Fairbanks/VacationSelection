# WebApp Refactoring Guide

## Overview
This folder contains a Google Apps Script web application for the Vacation Selection system. The code has been refactored into modular components for better maintainability.

## File Structure

### Main Files
- **`Code.gs`** - Server-side Google Apps Script code
  - Handles data retrieval from Google Sheets
  - User authentication and matching
  - API endpoints for the web app

- **`Index.html`** - Entry point (currently empty, to be implemented)

- **`Form_Refactored.html`** - Main form page (NEW - modular version)
  - Uses `<?!= include('FileName'); ?>` to import other HTML files
  - Clean, maintainable structure

- **`Form.html`** - Original monolithic form (642 lines)
  - Can be deprecated once Form_Refactored.html is tested

### Modular Components

#### **`Styles.html`**
Contains all CSS styling for:
- jQuery UI Datepicker customization
- 2-day shift block visual styling
- Shift color coding (A/B/C shifts)
- Weekend handling
- Responsive design with Tailwind CSS

#### **`ShiftLogic.html`**
Core shift calculation logic:
- `getShiftAndBlock(date)` - Calculates which shift (A/B/C) works on a given date
- `formatDate(date)` - Date formatting helper
- `toggleBlockHover(blockStartDate, action)` - Hover effects for 2-day blocks
- `updateShiftFeedback(dateText)` - Updates the shift badge next to date input

**Key Features:**
- DST-safe date calculations using UTC
- 6-day cycle (3 shifts × 2 days each)
- Reference date: Feb 4, 2026

#### **`DatepickerInit.html`**
jQuery UI Datepicker initialization:
- `initializeDatepicker()` - Sets up the calendar widget
- 2-day block selection logic
- Visual styling for shift blocks
- Weekend detection (only breaks blocks if BOTH days are weekends)

#### **`FormLogic.html`**
Form interaction and submission:
- `initializeFormLogic()` - Sets up form event handlers
- Submit button enable/disable logic
- Form validation
- Modal display for submission data

## How to Use in Google Apps Script

### 1. Upload Files to Google Apps Script
1. Open your Google Apps Script project
2. Create new HTML files for each component:
   - `Styles.html`
   - `ShiftLogic.html`
   - `DatepickerInit.html`
   - `FormLogic.html`
   - `Form_Refactored.html`

### 2. Update Code.gs
Make sure your `Code.gs` has the `include()` function:

```javascript
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}
```

### 3. Update doGet() Function
```javascript
function doGet() {
  return HtmlService.createTemplateFromFile("Form_Refactored")
    .evaluate()
    .setTitle("Vacation Selection Form");
}
```

### 4. Include Syntax
In any HTML file, use this syntax to include another file:
```html
<?!= include('Styles'); ?>
<?!= include('ShiftLogic'); ?>
<?!= include('DatepickerInit'); ?>
<?!= include('FormLogic'); ?>
```

**Note:** Do NOT include the `.html` extension in the include statement.

## Benefits of Refactoring

### Before (Monolithic)
- ❌ 642 lines in one file
- ❌ Hard to find specific code
- ❌ Difficult to maintain
- ❌ CSS, JavaScript, and HTML all mixed together

### After (Modular)
- ✅ Separated concerns (Styles, Logic, UI)
- ✅ Each file has a single responsibility
- ✅ Easy to locate and update specific features
- ✅ Reusable components
- ✅ Better collaboration (different people can work on different files)
- ✅ Easier testing and debugging

## Component Dependencies

```
Form_Refactored.html
├── Styles.html (no dependencies)
├── ShiftLogic.html (requires jQuery)
├── DatepickerInit.html (requires ShiftLogic.html, jQuery UI)
└── FormLogic.html (requires ShiftLogic.html, jQuery)
```

**Load Order:**
1. External libraries (jQuery, jQuery UI, Tailwind CSS)
2. Styles.html
3. ShiftLogic.html
4. DatepickerInit.html
5. FormLogic.html
6. Main initialization script

## Key Features

### Shift Calculation
- **48-hour shifts** starting Feb 4, 2026
- **6-day cycle:** A shift (days 0-1), B shift (days 2-3), C shift (days 4-5)
- **DST-safe** using UTC calculations

### Visual Design
- **2-day blocks** with connected borders
- **Rounded corners** only on outer edges of blocks
- **Weekend handling:** Blocks only break if BOTH days are weekends
- **Color coding:** Red (A), Blue (B), Orange (C)

### User Experience
- **Hover effects** highlight entire 2-day block
- **Auto-selection** of block start date
- **Shift feedback badge** shows which shift the selected date belongs to
- **Responsive design** works on mobile and desktop

## Testing

### Local Testing
Use `Form.html` (the original monolithic version) for local testing in a browser, as it doesn't require Google Apps Script's `include()` function.

### Google Apps Script Testing
1. Deploy as web app
2. Test the `Form_Refactored.html` version
3. Check browser console for any errors
4. Verify all includes are loading correctly

## Migration Path

1. ✅ Create modular components (Styles, ShiftLogic, DatepickerInit, FormLogic)
2. ✅ Create Form_Refactored.html using includes
3. ⏳ Test Form_Refactored.html in Google Apps Script
4. ⏳ Update Index.html to use modular approach
5. ⏳ Deprecate Form.html once testing is complete

## Future Enhancements

- [ ] Add more form fields (multiple date selections)
- [ ] Integrate with Code.gs for real data loading
- [ ] Add form validation
- [ ] Add loading states
- [ ] Add error handling
- [ ] Create ShiftCalendar.html component
- [ ] Add unit tests for shift calculation logic

## Troubleshooting

### Include Not Working
- Make sure the file name matches exactly (case-sensitive)
- Don't include the `.html` extension
- Verify the `include()` function exists in Code.gs

### Styles Not Applying
- Check that Styles.html is included in the `<head>` section
- Verify CSS syntax is correct
- Check browser console for CSS errors

### JavaScript Errors
- Ensure jQuery and jQuery UI are loaded before custom scripts
- Check that ShiftLogic.html is loaded before DatepickerInit.html and FormLogic.html
- Verify function names match between files

## Contact
For questions or issues, contact the development team.

