import datetime

# Placeholder for holidays - this will be populated or made configurable later
HOLIDAYS = [
    datetime.date(2024, 1, 1),   # New Year's Day
    datetime.date(2024, 7, 4),   # Independence Day
    datetime.date(2024, 12, 25), # Christmas Day
]

# Default: Monday to Friday (0=Monday, 6=Sunday)
WORKING_DAYS = [0, 1, 2, 3, 4]


def calculate_end_date(
    start_date_str: str,
    duration_days: int,
    holidays: list[datetime.date] = None,
    working_days: list[int] = None
) -> str:
    """
    Calculates the end date based on a start date, duration in days,
    a list of holidays, and a list of working days.

    Args:
        start_date_str: Start date in 'YYYY-MM-DD'.
        duration_days: Duration in working days.
        holidays: List of holiday dates. Defaults to global HOLIDAYS.
        working_days: List of working day numbers (0-6). Defaults to global WORKING_DAYS.

    Returns:
        Calculated end date in 'YYYY-MM-DD', or an error message.
    """
    holidays = holidays if holidays is not None else HOLIDAYS
    working_days = working_days if working_days is not None else WORKING_DAYS

    if not all(0 <= day <= 6 for day in working_days):
        return "Error: Invalid working_days configuration (must be 0-6)."
    if duration_days < 0:
        return "Error: Duration must be non-negative."

    try:
        current_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        return "Error: Invalid start_date format. Please use YYYY-MM-DD."

    # Handle zero duration: if start_date is not a working day/holiday, find the next valid one.
    # Otherwise, the end date is the start date itself.
    if duration_days == 0:
        # Adjust current_date to be the first valid working day if it's not already
        while not (current_date.weekday() in working_days and current_date not in holidays):
            current_date += datetime.timedelta(days=1)
        return current_date.strftime("%Y-%m-%d")

    # For positive duration, count working days including the start date if it's valid
    calculated_end_date = current_date
    days_counted = 0

    while days_counted < duration_days:
        if calculated_end_date.weekday() in working_days and \
           calculated_end_date not in holidays:
            days_counted += 1

        if days_counted < duration_days:
            calculated_end_date += datetime.timedelta(days=1)
            # Skip non-working days and holidays efficiently for the next iteration
            while not (calculated_end_date.weekday() in working_days and \
                       calculated_end_date not in holidays):
                # This inner loop check is to prevent infinite loop if duration is too large
                # and all subsequent days are non-working (highly unlikely in practice with typical setup)
                # However, the primary loop condition (days_counted < duration_days) will handle termination.
                calculated_end_date += datetime.timedelta(days=1)

    return calculated_end_date.strftime("%Y-%m-%d")


if __name__ == '__main__':
    print("--- Testing calculate_end_date ---")

    test_cases = [
        ("2024-07-01", 3, None, "2024-07-03"),  # Mon, Tue, Wed
        ("2024-07-05", 2, None, "2024-07-08"),  # Fri, Mon
        ("2024-07-01", 4, [datetime.date(2024, 7, 4)], "2024-07-05"), # Mon, Tue, Wed, (Thu Hol), Fri
        ("2024-07-06", 1, None, "2024-07-08"),  # Sat start, 1 day -> Mon
        ("2024-07-04", 1, [datetime.date(2024, 7, 4)], "2024-07-05"), # Thu Hol start, 1 day -> Fri
        ("2024-07-01", 0, None, "2024-07-01"),  # 0 duration, Mon start
        ("2024-07-04", 0, [datetime.date(2024, 7, 4)], "2024-07-05"), # 0 duration, Thu Hol start -> Fri
        ("2024-06-24", 10, [datetime.date(2024, 7, 4)], "2024-07-08"), # Long span with holiday
        ("2024-07-01", 1, None, "2024-07-01"), # 1 day duration, Mon start
        ("2024-07-05", 1, None, "2024-07-05"), # 1 day duration, Fri start
        ("2024-12-23", 3, [datetime.date(2024, 12, 25)], "2024-12-26"), # Skip Christmas
        ("2024-07-05", 3, None, "2024-07-09"), # Fri, Mon, Tue
        ("2024-08-03", 0, None, "2024-08-05"), # Sat start, 0 duration -> Mon
        ("2024-08-05", 0, None, "2024-08-05"), # Mon start, 0 duration -> Mon
        ("2024-07-01", 3, [datetime.date(2024,7,3)], "2024-07-04"), # Mon,Tue,(Wed Hol),Thu
    ]

    for start, duration, holidays_list, expected in test_cases:
        actual = calculate_end_date(start, duration, holidays=holidays_list)
        status = "PASS" if actual == expected else f"FAIL (Expected: {expected})"
        print(f"Start: {start}, Duration: {duration}, Holidays: {holidays_list} -> Actual: {actual} ({status})")

    print("\n--- Testing with custom working days (Mon-Sat) ---")
    custom_working_days = [0, 1, 2, 3, 4, 5] # Mon-Sat
    start_custom = "2024-07-05" # Friday
    duration_custom = 3 # Fri, Sat, Mon (Sun off)
    expected_custom = "2024-07-08"
    actual_custom = calculate_end_date(start_custom, duration_custom, working_days=custom_working_days)
    status_custom = "PASS" if actual_custom == expected_custom else f"FAIL (Expected: {expected_custom})"
    print(f"Start: {start_custom}, Duration: {duration_custom} (Mon-Sat) -> Actual: {actual_custom} ({status_custom})")

    print("\n--- Error Handling Tests ---")
    print(f"Invalid date: {calculate_end_date('invalid-date', 5)}")
    print(f"Negative duration: {calculate_end_date('2024-07-01', -1)}")
    print(f"Invalid working days: {calculate_end_date('2024-07-01', 5, working_days=[0,7])}")
