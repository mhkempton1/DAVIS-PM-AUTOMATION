# utils.py
# This file will contain utility functions for the Project Management System.

import datetime

# Placeholder for holidays - this will be populated or made configurable later
HOLIDAYS = [
    datetime.date(2024, 1, 1),   # New Year's Day
    datetime.date(2024, 7, 4),   # Independence Day
    datetime.date(2024, 12, 25), # Christmas Day
    # Add more holidays as needed
]

# Placeholder for working days (e.g., Monday=0, Tuesday=1, ..., Sunday=6)
# Default: Monday to Friday
WORKING_DAYS = [0, 1, 2, 3, 4] # Monday to Friday

def calculate_end_date(start_date_str: str, duration_days: int,
                       holidays: list[datetime.date] = None,
                       working_days: list[int] = None) -> str:
    """
    Calculates the end date based on a start date, duration in days,
    a list of holidays, and a list of working days (0=Monday, 6=Sunday).

    Args:
        start_date_str: The start date in 'YYYY-MM-DD' format.
        duration_days: The duration of the project in days.
        holidays: A list of datetime.date objects representing holidays.
                  Defaults to the global HOLIDAYS list if None.
        working_days: A list of integers representing working days (0-6).
                      Defaults to the global WORKING_DAYS list if None.

    Returns:
        The calculated end date in 'YYYY-MM-DD' format, or an error message string.
    """
    if holidays is None:
        holidays = HOLIDAYS
    if working_days is None:
        working_days = WORKING_DAYS

    if not all(0 <= day <= 6 for day in working_days):
        return "Error: Invalid working_days configuration (must be 0-6)."
    if duration_days < 0: # Duration of 0 means end date is the start date if it's a working day.
        return "Error: Duration must be non-negative."

    try:
        current_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        return "Error: Invalid start_date format. Please use YYYY-MM-DD."

    days_added = 0

    # If duration is 0, the end date is the start date,
    # but we still need to ensure it's a "valid" day if we were to advance.
    # For simplicity, if duration is 0, we consider the start date itself as the end date,
    # assuming the process implies "inclusive" of the start day for work.
    # If the very first day is not a working day or a holiday, and duration is >0,
    # we'll skip it.

    temp_date = current_date

    while days_added < duration_days:
        temp_date += datetime.timedelta(days=1)
        if temp_date.weekday() in working_days and temp_date not in holidays:
            days_added += 1

    # The loop advances temp_date one day past the actual end_date when days_added == duration_days.
    # So, if duration_days is 1, and start_date is a valid working day,
    # temp_date becomes start_date + 1 day, and that's the end date.
    # If duration_days = 0, loop isn't entered, end_date = start_date.
    # This interpretation seems more aligned with "duration of X working days *after* start".
    # Let's adjust: the duration should include the start day if it's a working day.

    # Re-thinking the loop for duration:
    # If duration is 1 day, and start_date is a working day, end_date is start_date.

    calculated_end_date = current_date
    days_counted = 0

    # First, check if the start_date itself is a working day.
    # If duration is 1, and start_date is a valid working day, then end_date is start_date.

    if duration_days == 0:
         # Ensure start date itself is valid if we consider 0 duration means it ends on start day
        while not (calculated_end_date.weekday() in working_days and calculated_end_date not in holidays):
            calculated_end_date += datetime.timedelta(days=1) # Find next valid working day if start is not
        return calculated_end_date.strftime("%Y-%m-%d")

    # Loop to find the end date
    while days_counted < duration_days:
        if calculated_end_date.weekday() in working_days and calculated_end_date not in holidays:
            days_counted += 1

        # If we haven't found enough working days yet, move to the next day
        if days_counted < duration_days:
            calculated_end_date += datetime.timedelta(days=1)
            # Skip non-working days and holidays quickly for the next iteration's check
            while not (calculated_end_date.weekday() in working_days and calculated_end_date not in holidays):
                if days_counted == duration_days: # Edge case if last day lands on non-working
                    break
                calculated_end_date += datetime.timedelta(days=1)

    return calculated_end_date.strftime("%Y-%m-%d")


if __name__ == '__main__':
    # Test cases
    print("--- Testing calculate_end_date ---")

    # Test 1: Simple duration, no holidays/weekends in between
    start1 = "2024-07-01" # Monday
    duration1 = 3 # Should be 2024-07-03 (Mon, Tue, Wed)
    print(f"Start: {start1}, Duration: {duration1} days -> End: {calculate_end_date(start1, duration1)}")

    # Test 2: Duration crossing a weekend
    start2 = "2024-07-05" # Friday
    duration2 = 2 # Should be 2024-07-08 (Fri, Mon)
    print(f"Start: {start2}, Duration: {duration2} days -> End: {calculate_end_date(start2, duration2)}")

    # Test 3: Duration including a holiday
    start3 = "2024-07-01" # Monday
    duration3 = 4 # Holiday on 2024-07-04 (Thu). So, Mon, Tue, Wed, Fri -> 2024-07-05
    h_test = [datetime.date(2024, 7, 4)]
    print(f"Start: {start3}, Duration: {duration3} days (Holiday on 7/4) -> End: {calculate_end_date(start3, duration3, holidays=h_test)}")

    # Test 4: Start date is a weekend
    start4 = "2024-07-06" # Saturday
    duration4 = 1 # Should be 2024-07-08 (Monday)
    print(f"Start: {start4}, Duration: {duration4} day -> End: {calculate_end_date(start4, duration4)}")

    # Test 5: Start date is a holiday
    start5 = "2024-07-04" # Thursday (Holiday)
    duration5 = 1 # Should be 2024-07-05 (Friday)
    print(f"Start: {start5}, Duration: {duration5} day (Start is holiday) -> End: {calculate_end_date(start5, duration5, holidays=h_test)}")

    # Test 6: Zero duration
    start6 = "2024-07-01" # Monday
    duration6 = 0
    # Expected: 2024-07-01 (If start date is a working day, 0 duration means it ends on start day)
    # Or, if start day is not working, the next working day. Let's refine this.
    # My current logic for 0 duration: it finds the *next* available working day if start_date isn't one.
    # If start_date is a working day, it returns start_date. This seems reasonable.
    print(f"Start: {start6}, Duration: {duration6} days -> End: {calculate_end_date(start6, duration6)}")

    start7 = "2024-07-04" # Holiday
    duration7 = 0
    # Expected: 2024-07-05 (Friday, as 7/4 is holiday)
    print(f"Start: {start7}, Duration: {duration7} days (Start is holiday) -> End: {calculate_end_date(start7, duration7, holidays=h_test)}")

    # Test 8: Longer duration spanning multiple weeks and a holiday
    start8 = "2024-06-24" # Monday
    duration8 = 10 # Holiday on 7/4.
    # Jun 24,25,26,27,28 (5 days)
    # Jul 1,2,3 (3 days) -> 8 days total, ends July 3
    # Jul 4 is holiday
    # Jul 5 (1 day) -> 9 days total, ends July 5
    # Jul 8 (1 day) -> 10 days total, ends July 8
    print(f"Start: {start8}, Duration: {duration8} days (Holiday on 7/4) -> End: {calculate_end_date(start8, duration8, holidays=h_test)}")

    # Test 9: Duration is 1 day, start date is a working day
    start9 = "2024-07-01" # Monday
    duration9 = 1
    print(f"Start: {start9}, Duration: {duration9} days -> End: {calculate_end_date(start9, duration9)}")

    # Test 10: Duration is 1 day, start date is Friday
    start10 = "2024-07-05" # Friday
    duration10 = 1
    print(f"Start: {start10}, Duration: {duration10} days -> End: {calculate_end_date(start10, duration10)}")

    # Test 11: Duration makes it end on a Friday before a holiday weekend
    start11 = "2024-12-20" # Friday
    duration11 = 1 # End 2024-12-20
    holidays_dec = [datetime.date(2024, 12, 25)]
    print(f"Start: {start11}, Duration: {duration11}, Holidays: {holidays_dec} -> End: {calculate_end_date(start11, duration11, holidays=holidays_dec)}")

    # Test 12: Duration makes it skip Christmas
    start12 = "2024-12-23" # Monday
    duration12 = 3 # Mon (23rd), Tue (24th), Thu (26th) -> End 2024-12-26
    print(f"Start: {start12}, Duration: {duration12}, Holidays: {holidays_dec} -> End: {calculate_end_date(start12, duration12, holidays=holidays_dec)}")

    # Test with different working days (e.g. Mon-Sat)
    working_days_mon_sat = [0,1,2,3,4,5]
    start13 = "2024-07-05" # Friday
    duration13 = 3 # Fri, Sat, Mon (if Sunday is off)
    print(f"Start: {start13}, Duration: {duration13} (Mon-Sat working) -> End: {calculate_end_date(start13, duration13, working_days=working_days_mon_sat)}")
    # Expected: 2024-07-05 (Fri), 2024-07-06 (Sat), 2024-07-08 (Mon) -> End: 2024-07-08

    # Test with invalid date format
    print(f"Start: 'invalid-date', Duration: 5 -> End: {calculate_end_date('invalid-date', 5)}")
    # Test with negative duration
    print(f"Start: {start1}, Duration: -1 -> End: {calculate_end_date(start1, -1)}")

    # Test case where start date is a non-working day (Sunday) and duration is 0
    start14 = "2024-07-07" # Sunday
    duration14 = 0
    # Expected: 2024-07-08 (Monday)
    print(f"Start: {start14}, Duration: {duration14} (Start on Sunday) -> End: {calculate_end_date(start14, duration14)}")

    # Test case: Start date is a working day, duration is 1
    start15 = "2024-07-01" # Monday
    duration15 = 1
    # Expected: 2024-07-01
    print(f"Start: {start15}, Duration: {duration15} -> End: {calculate_end_date(start15, duration15)}")

    # Test case: Start date is a working day, duration is 2
    start16 = "2024-07-01" # Monday
    duration16 = 2
    # Expected: 2024-07-02
    print(f"Start: {start16}, Duration: {duration16} -> End: {calculate_end_date(start16, duration16)}")

    # Test case: Start date is Friday, duration is 3 (Fri, Mon, Tue)
    start17 = "2024-07-05" # Friday
    duration17 = 3
    # Expected: 2024-07-09 (Tuesday)
    print(f"Start: {start17}, Duration: {duration17} -> End: {calculate_end_date(start17, duration17)}")

    # Test with a holiday that falls on a weekend (should not affect if weekend is already off)
    holidays_weekend_holiday = [datetime.date(2024, 7, 6)] # July 6th is a Saturday
    start18 = "2024-07-05" # Friday
    duration18 = 2 # Should be Mon, July 8th
    print(f"Start: {start18}, Duration: {duration18}, Holidays: {holidays_weekend_holiday} -> End: {calculate_end_date(start18, duration18, holidays=holidays_weekend_holiday)}")

    # Test with a start date that is a holiday, and duration pushes past more holidays and weekends
    holidays_multiple = [datetime.date(2024,1,1), datetime.date(2024,1,2), datetime.date(2024,1,3)] # Jan 1,2,3 are holidays
    start19 = "2024-01-01" # Monday (Holiday)
    duration19 = 3 # Should count Jan 4 (Thu), Jan 5 (Fri), Jan 8 (Mon) -> End: 2024-01-08
    print(f"Start: {start19}, Duration: {duration19}, Holidays: {holidays_multiple} -> End: {calculate_end_date(start19, duration19, holidays=holidays_multiple)}")

    # Test with duration that ends on the day before a holiday
    start20 = "2024-06-28" # Friday
    duration20 = 3 # Fri (28th), Mon (Jul 1st), Tue (Jul 2nd) -> End: 2024-07-02
    print(f"Start: {start20}, Duration: {duration20}, Holidays: {h_test} (Jul 4th) -> End: {calculate_end_date(start20, duration20, holidays=h_test)}")

    # Test with start date as Friday, duration 1 day, Saturday and Sunday as non-working days.
    start21 = "2024-08-02"  # Friday
    duration21 = 1
    # Expected: 2024-08-02
    print(f"Start: {start21}, Duration: {duration21} -> End: {calculate_end_date(start21, duration21)}")

    # Test with start date as Friday, duration 2 days
    start22 = "2024-08-02"  # Friday
    duration22 = 2
    # Expected: 2024-08-05 (Monday)
    print(f"Start: {start22}, Duration: {duration22} -> End: {calculate_end_date(start22, duration22)}")

    # Test case where the end date lands on a holiday, so it should push to the next working day.
    start23 = "2024-07-01" # Monday
    duration23 = 3 # Mon, Tue, Wed. If Wed (Jul 3) was a holiday, it should push.
                   # For this test, let Jul 3 be a holiday.
    holidays_jul3 = [datetime.date(2024, 7, 3)]
    # Days counted: Mon (Jul 1), Tue (Jul 2), Thu (Jul 4 is also holiday from global) -> No, global HOLIDAYS is used by default.
    # Need to pass specific holiday list for this test to be isolated.
    # If Jul 3 is holiday: Day1=Jul1, Day2=Jul2, Day3 must be Jul 5 (as Jul4 is also holiday)
    # Let's use a clean holiday list for this test.
    print(f"Start: {start23}, Duration: {duration23}, Holidays: {holidays_jul3} -> End: {calculate_end_date(start23, duration23, holidays=holidays_jul3)}")
    # Expected for duration 3 with Jul 3 as holiday: Jul 1, Jul 2, Jul 4 -> End 2024-07-04 (assuming Jul 4 is NOT a holiday for this specific test call)
    # Let's make it more explicit:
    h_jul3_only = [datetime.date(2024, 7, 3)]
    print(f"Start: {start23}, Duration: 3, Holidays: [Jul 3] -> End: {calculate_end_date(start23, 3, holidays=h_jul3_only)}")
    # Expected: Jul 1 (Mon), Jul 2 (Tue), Jul 4 (Thu) -> End 2024-07-04

    h_jul3_jul4 = [datetime.date(2024, 7, 3), datetime.date(2024, 7, 4)]
    print(f"Start: {start23}, Duration: 3, Holidays: [Jul 3, Jul 4] -> End: {calculate_end_date(start23, 3, holidays=h_jul3_jul4)}")
    # Expected: Jul 1 (Mon), Jul 2 (Tue), Jul 5 (Fri) -> End 2024-07-05

    # Test: start date is a non-working day (Saturday), duration 0. Should give next working day (Monday)
    start24 = "2024-08-03" # Saturday
    duration24 = 0
    print(f"Start: {start24}, Duration: {duration24} -> End: {calculate_end_date(start24, duration24)}")
    # Expected: 2024-08-05

    # Test: start date is a working day, duration 0. Should give start date.
    start25 = "2024-08-05" # Monday
    duration25 = 0
    print(f"Start: {start25}, Duration: {duration25} -> End: {calculate_end_date(start25, duration25)}")
    # Expected: 2024-08-05

    # Test: start date is a holiday, duration 0. Should give next working day.
    start26 = "2024-07-04" # Thursday (Holiday)
    duration26 = 0
    print(f"Start: {start26}, Duration: {duration26}, Holidays: [Jul 4] -> End: {calculate_end_date(start26, duration26, holidays=[datetime.date(2024,7,4)])}")
    # Expected: 2024-07-05 (Friday)
