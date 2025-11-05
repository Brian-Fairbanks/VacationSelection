"""
Test script to demonstrate runner-up tracking functionality.
Runner-ups are denied picks tracked in order of denial (seniority order).
"""
from datetime import datetime, date
from vacation_selection.firefighter import FFighter, Pick
from vacation_selection.cal import Day, make_calendar
from vacation_selection.file_io import write_runner_ups_to_csv
import os

# Configure for 48-hour shifts
Day.increment_names = ["day_1", "day_2"]
Day.shift_duration_hours = 48
Day.transition_date = datetime(2025, 2, 4).date()
Day.max_total_ffighters_allowed = 6

print("=" * 80)
print("Runner-Up Tracking Test - 48-Hour Shifts")
print("=" * 80)

# Create test firefighters with different seniority
test_ffighters = []

# Create 8 firefighters (6 will be approved, 2 will be runner-ups)
for i in range(8):
    ff = FFighter(
        idnum=i+1,
        fname=f"Firefighter{i+1}",
        lname="Test",
        hireDate=date(2015 - i, 1, 1),  # Earlier hire date = higher seniority
        rank="Captain",
        shift="A",
        picks=[]
    )
    ff.max_shifts_off = 18
    ff.awarded_vacation_shifts = 12
    ff.awarded_holiday_shifts = 6
    
    # All request the same date (Oct 2-3, 2025) - day_1 increment only
    pick = Pick(date(2025, 10, 2), type="Vacation", increments="day_1")
    ff.picks = [pick]
    
    test_ffighters.append(ff)

print(f"\nCreated {len(test_ffighters)} firefighters all requesting Oct 2 (day_1)")
print("Expected: First 6 approved, last 2 become runner-ups")
print("-" * 80)

# Process the calendar
calendar = {}
rejected = {}
results = make_calendar(test_ffighters, existing_calendar_data=None, rejected=rejected, silent_mode=True, count=1)

# Check results
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

approved_count = 0
denied_count = 0

for ff in test_ffighters:
    if ff.processed:
        result = ff.processed[0]
        status = "✅ APPROVED" if result.determination == "Approved" else "❌ DENIED"
        print(f"{ff.name:20} (Hire: {ff.hireDate}) - {status} - {result.reason if result.reason else 'N/A'}")
        
        if result.determination == "Approved":
            approved_count += 1
        else:
            denied_count += 1

print(f"\nApproved: {approved_count}, Denied: {denied_count}")

# Check the increment's runner-up list
print("\n" + "=" * 80)
print("RUNNER-UPS IN INCREMENT")
print("=" * 80)

target_date = date(2025, 10, 2)
if target_date in results['calendar']:
    day = results['calendar'][target_date]
    increment = day.increments.get(0)  # day_1 increment
    
    if increment and increment.runner_ups:
        print(f"\nIncrement: {increment.name}")
        print(f"Date: {increment.date}")
        print(f"Runner-ups: {len(increment.runner_ups)}")
        print("-" * 80)
        
        for runner_up in increment.runner_ups:
            ff = runner_up['ffighter']
            pick = runner_up['pick']
            reason = runner_up['reason']
            position = runner_up['position']
            
            print(f"Position {position}: {ff.name} (ID: {ff.idnum}, Hire: {ff.hireDate})")
            print(f"  Requested: {pick.increments_plain_text()}")
            print(f"  Reason: {reason}")
            print()
    else:
        print("No runner-ups found in increment")
else:
    print("Date not found in calendar")

# Test CSV export
print("=" * 80)
print("TESTING CSV EXPORT")
print("=" * 80)

output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)
runtime = datetime.now().strftime("%Y.%m.%d %H.%M")

try:
    csv_file = write_runner_ups_to_csv(results['calendar'], "A", output_dir, runtime)
    print(f"\n✅ Runner-ups CSV created: {csv_file}")
    
    # Read and display the CSV content
    with open(csv_file, 'r') as f:
        content = f.read()
        print("\nCSV Content:")
        print("-" * 80)
        print(content)
except Exception as e:
    print(f"\n❌ Error creating CSV: {e}")

# Test Scenario 2: Multiple dates with runner-ups
print("\n" + "=" * 80)
print("SCENARIO 2: Multiple Dates with Runner-ups")
print("=" * 80)

# Reset firefighters
test_ffighters2 = []
for i in range(8):
    ff = FFighter(
        idnum=i+1,
        fname=f"FF{i+1}",
        lname="Test",
        hireDate=date(2015 - i, 1, 1),
        rank="Lieutenant",
        shift="B",
        picks=[]
    )
    ff.max_shifts_off = 18
    ff.awarded_vacation_shifts = 12
    ff.awarded_holiday_shifts = 6
    
    # First 4 request Oct 2-3 (full shift)
    # Last 4 request Oct 4-5 (full shift)
    if i < 4:
        pick = Pick(date(2025, 10, 2), type="Vacation", increments="day_1day_2")
    else:
        pick = Pick(date(2025, 10, 4), type="Vacation", increments="day_1day_2")
    
    ff.picks = [pick]
    test_ffighters2.append(ff)

print("\n4 firefighters request Oct 2-3 (full shift)")
print("4 firefighters request Oct 4-5 (full shift)")
print("Expected: Some approved, some runner-ups on each date")

# Process
calendar2 = {}
rejected2 = {}
results2 = make_calendar(test_ffighters2, existing_calendar_data=None, rejected=rejected2, silent_mode=True, count=1)

# Export
try:
    csv_file2 = write_runner_ups_to_csv(results2['calendar'], "B", output_dir, runtime)
    print(f"\n✅ Runner-ups CSV created: {csv_file2}")
    
    # Count runner-ups
    total_runner_ups = 0
    for date_key, day in results2['calendar'].items():
        for inc_index, increment in day.increments.items():
            if increment.runner_ups:
                total_runner_ups += len(increment.runner_ups)
    
    print(f"Total runner-ups across all dates/increments: {total_runner_ups}")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
print("\nRunner-up files created in ./output/ directory")
print("These files can be distributed to Captains to know who to contact")
print("if approved firefighters need to cancel their time off.")

