"""
Test script to demonstrate date formatting for full shifts vs partial shifts.
"""
from datetime import datetime, date
from vacation_selection.firefighter import Pick
from vacation_selection.cal import Day

# Configure for 48-hour shifts
Day.increment_names = ["day_1", "day_2"]
Day.shift_duration_hours = 48
Day.transition_date = datetime(2025, 2, 4).date()

print("=" * 80)
print("Date Formatting Test - 48-Hour Shifts")
print("=" * 80)

# Test date after transition
test_date = date(2025, 10, 2)

print(f"\nTest Date: {test_date}")
print(f"Shift Duration: {Day.shift_duration_hours} hours")
print(f"Increments: {Day.increment_names}")
print("-" * 80)

# Test 1: Full shift request (both increments)
print("\n1. FULL SHIFT REQUEST (day_1 + day_2):")
pick1 = Pick(test_date, type="Vacation", determination="Approved", increments="day_1day_2")
pick1.approved_increments = [1, 1]  # Both approved
print(f"   Requested: {pick1.increments_plain_text(pick1.increments)}")
print(f"   Approved:  {pick1.increments_plain_text(pick1.approved_increments)}")
print(f"   Date Display: {pick1.format_date_display()}")
print(f"   Expected: 10/2 - 10/3")

# Test 2: Partial grant - only day_1 approved
print("\n2. PARTIAL GRANT - Only day_1 available:")
pick2 = Pick(test_date, type="Vacation", determination="Approved", increments="day_1day_2")
pick2.approved_increments = [1, 0]  # Only day_1 approved
pick2.reason = "Partial grant - only day_1 available"
print(f"   Requested: {pick2.increments_plain_text(pick2.increments)}")
print(f"   Approved:  {pick2.increments_plain_text(pick2.approved_increments)}")
print(f"   Date Display: {pick2.format_date_display()}")
print(f"   Reason: {pick2.reason}")
print(f"   Expected: 10/2")

# Test 3: Partial grant - only day_2 approved
print("\n3. PARTIAL GRANT - Only day_2 available:")
pick3 = Pick(test_date, type="Vacation", determination="Approved", increments="day_1day_2")
pick3.approved_increments = [0, 1]  # Only day_2 approved
pick3.reason = "Partial grant - only day_2 available"
print(f"   Requested: {pick3.increments_plain_text(pick3.increments)}")
print(f"   Approved:  {pick3.increments_plain_text(pick3.approved_increments)}")
print(f"   Date Display: {pick3.format_date_display()}")
print(f"   Reason: {pick3.reason}")
print(f"   Expected: 10/3")

# Test 4: Single increment request - day_1 only
print("\n4. SINGLE INCREMENT REQUEST - day_1 only:")
pick4 = Pick(test_date, type="Vacation", determination="Approved", increments="day_1")
pick4.approved_increments = [1, 0]
print(f"   Requested: {pick4.increments_plain_text(pick4.increments)}")
print(f"   Approved:  {pick4.increments_plain_text(pick4.approved_increments)}")
print(f"   Date Display: {pick4.format_date_display()}")
print(f"   Expected: 10/2")

# Test 5: Single increment request - day_2 only
print("\n5. SINGLE INCREMENT REQUEST - day_2 only:")
pick5 = Pick(test_date, type="Vacation", determination="Approved", increments="day_2")
pick5.approved_increments = [0, 1]
print(f"   Requested: {pick5.increments_plain_text(pick5.increments)}")
print(f"   Approved:  {pick5.increments_plain_text(pick5.approved_increments)}")
print(f"   Date Display: {pick5.format_date_display()}")
print(f"   Expected: 10/3")

# Test 6: Denied request
print("\n6. DENIED REQUEST:")
pick6 = Pick(test_date, type="Vacation", determination="Rejected", increments="day_1day_2")
pick6.reason = "All requested increments are full"
print(f"   Requested: {pick6.increments_plain_text(pick6.increments)}")
print(f"   Date Display: {pick6.format_date_display()}")
print(f"   Reason: {pick6.reason}")
print(f"   Expected: 10/2 - 10/3 (shows what was requested)")

# Test 7: Month boundary crossing
print("\n7. MONTH BOUNDARY - Full shift Oct 31 - Nov 1:")
test_date_boundary = date(2025, 10, 31)
pick7 = Pick(test_date_boundary, type="Vacation", determination="Approved", increments="day_1day_2")
pick7.approved_increments = [1, 1]
print(f"   Date Display: {pick7.format_date_display()}")
print(f"   Expected: 10/31 - 11/1")

# Test 8: Before transition date (24-hour shifts)
print("\n8. BEFORE TRANSITION DATE (24-hour shifts):")
test_date_before = date(2025, 1, 15)
pick8 = Pick(test_date_before, type="Vacation", determination="Approved", increments="AMPM")
pick8.approved_increments = [1, 1]
print(f"   Date: {test_date_before}")
print(f"   Date Display: {pick8.format_date_display()}")
print(f"   Expected: 01/15 (single date for 24-hour shifts)")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)

