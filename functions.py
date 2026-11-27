import os
import pandas as pd

USERS_FILE = "users.csv"
TAX_RECORDS_FILE = "tax_records.csv"

USER_COLUMNS = ["User ID", "IC Number"]
TAX_COLUMNS = [
    "User ID",
    "Test Case ID",
    "Year of Assessment",
    "Annual Income",
    "Total Tax Relief",
    "Chargeable Income",
    "Tax Before Rebate",
    "Tax Rebate",
    "Final Tax Payable",
]

# YA 2026 Malaysian Resident Individual Income Tax Brackets:
# Each tuple represents (lower_bound, upper_bound, tax_rate)
YA2026_TAX_BRACKETS = [
    (0.0, 5000.0, 0.00),
    (5000.0, 20000.0, 0.01),
    (20000.0, 35000.0, 0.03),
    (35000.0, 50000.0, 0.06),
    (50000.0, 70000.0, 0.11),
    (70000.0, 100000.0, 0.19),
    (100000.0, 400000.0, 0.25),
    (400000.0, 600000.0, 0.26),
    (600000.0, 2000000.0, 0.28),
    (2000000.0, float("inf"), 0.30),
]


def validate_user_id(user_id):
    """
    Validate that the User ID is non-empty and contains no spaces or commas.
    Returns (bool, str): (is_valid, message)
    """
    cleaned = user_id.strip()
    if not cleaned:
        return False, "Error: User ID cannot be empty."
    if "," in cleaned or " " in cleaned:
        return False, "Error: User ID cannot contain spaces or commas."
    if len(cleaned) < 3:
        return False, "Error: User ID must be at least 3 characters long."
    return True, "Valid User ID."


def validate_ic_number(ic_number):
    """
    Validate that the Malaysian IC number consists of strictly 12 numeric digits.
    Returns (bool, str): (is_valid, message)
    """
    cleaned = ic_number.strip()
    if len(cleaned) != 12 or not cleaned.isdigit():
        return False, "Error: IC number must be exactly 12 numeric digits (e.g., 051128071234)."
    return True, "Valid IC number."


def validate_monetary_input(raw_value, field_name="Amount"):
    """
    Validate and convert a string input into a non-negative float.
    Returns (bool, float_or_none, str): (is_valid, parsed_value, message)
    """
    try:
        cleaned = raw_value.strip().replace(",", "")
        value = float(cleaned)
        if value < 0:
            return False, None, f"Error: {field_name} cannot be negative."
        return True, round(value, 2), "Valid input."
    except ValueError:
        return False, None, f"Error: Invalid numeric input for {field_name}. Please enter a valid number."


def load_users(filename=USERS_FILE):
    """
    Load registered users from users.csv into a list of dictionaries.
    Reads all columns as strings so leading zeros in IC numbers are preserved.
    """
    if not os.path.exists(filename):
        return []
    try:
        df = pd.read_csv(filename, dtype=str)
        if df.empty:
            return []
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as exc:
        print(f"Warning: Could not read {filename} ({exc}). Initializing empty user list.")
        return []


def register_user(user_id, ic_number, filename=USERS_FILE):
    """
    Register a new user after validating User ID and 12-digit IC number.
    Stores user data in a Python list -> dictionary -> pandas DataFrame -> CSV file.
    Returns (bool, str): (success, message)
    """
    user_id = user_id.strip()
    ic_number = ic_number.strip()

    valid_id, msg_id = validate_user_id(user_id)
    if not valid_id:
        return False, msg_id

    valid_ic, msg_ic = validate_ic_number(ic_number)
    if not valid_ic:
        return False, msg_ic

    users_list = load_users(filename)

    # Prevent duplicate User IDs (case-insensitive check)
    for existing in users_list:
        if existing["User ID"].lower() == user_id.lower():
            return False, f"Error: User ID '{user_id}' is already registered. Please log in or choose another ID."

    # Store collected user info in a Python list first, then convert to dictionary
    user_info_list = [user_id, ic_number]
    new_user_dict = dict(zip(USER_COLUMNS, user_info_list))
    users_list.append(new_user_dict)

    # Convert list of dictionaries to pandas DataFrame and save to CSV
    df_users = pd.DataFrame(users_list, columns=USER_COLUMNS)
    df_users.to_csv(filename, index=False)

    password_hint = ic_number[-4:]
    return True, f"Registration successful! Your login password is the last 4 digits of your IC: {password_hint}"


def authenticate_user(user_id, password, filename=USERS_FILE):
    """
    Authenticate a registered user using User ID and the last 4 digits of their IC number.
    Returns (bool, str): (is_authenticated, message)
    """
    user_id = user_id.strip()
    password = password.strip()

    if not os.path.exists(filename):
        return False, "Error: No registered users found (users.csv does not exist). Please register first."

    users_list = load_users(filename)
    if not users_list:
        return False, "Error: User database is empty. Please register first."

    for user in users_list:
        if user["User ID"].lower() == user_id.lower():
            expected_password = str(user["IC Number"])[-4:]
            if password == expected_password:
                return True, f"Login successful! Welcome, {user['User ID']}."
            return False, "Error: Incorrect password (must match the last 4 digits of your registered IC)."

    return False, f"Error: User ID '{user_id}' not found. Please register first."


def calculate_chargeable_income(annual_income, total_relief):
    """
    Calculate chargeable income by deducting total eligible tax relief from annual income.
    Chargeable income cannot be negative.
    """
    chargeable = annual_income - total_relief
    return round(max(0.0, chargeable), 2)


def calculate_progressive_tax(chargeable_income):
    """
    Calculate Malaysian resident individual income tax before rebate (YA 2026)
    by applying progressive tax rates to each income band.
    """
    if chargeable_income <= 0:
        return 0.0

    total_tax = 0.0
    for lower, upper, rate in YA2026_TAX_BRACKETS:
        if chargeable_income > lower:
            taxable_in_band = min(chargeable_income, upper) - lower
            total_tax += taxable_in_band * rate
        else:
            break

    return round(total_tax, 2)


def calculate_tax_rebate(chargeable_income):
    """
    Determine individual tax rebate for YA 2026:
    RM400.00 rebate applies if chargeable income does not exceed RM35,000.00.
    """
    if chargeable_income <= 35000.0:
        return 400.00
    return 0.00


def calculate_malaysian_tax(annual_income, total_relief):
    """
    Perform complete YA 2026 Malaysian personal income tax calculation.
    Returns a Python list containing:
    [annual_income, total_relief, chargeable_income, tax_before_rebate, tax_rebate, final_tax_payable]
    """
    chargeable_income = calculate_chargeable_income(annual_income, total_relief)
    tax_before_rebate = calculate_progressive_tax(chargeable_income)
    tax_rebate = calculate_tax_rebate(chargeable_income)
    final_tax_payable = round(max(0.0, tax_before_rebate - tax_rebate), 2)

    return [
        round(float(annual_income), 2),
        round(float(total_relief), 2),
        chargeable_income,
        tax_before_rebate,
        tax_rebate,
        final_tax_payable,
    ]


def create_tax_record_dict(user_id, calc_results_list, test_case_id="N/A", year_of_assessment=2026):
    """
    Convert a Python list of collected inputs and calculated tax results into a dictionary
    with meaningful keys matching TAX_COLUMNS.
    """
    full_record_list = [
        user_id,
        test_case_id,
        year_of_assessment,
        calc_results_list[0],  # Annual Income
        calc_results_list[1],  # Total Tax Relief
        calc_results_list[2],  # Chargeable Income
        calc_results_list[3],  # Tax Before Rebate
        calc_results_list[4],  # Tax Rebate
        calc_results_list[5],  # Final Tax Payable
    ]
    return dict(zip(TAX_COLUMNS, full_record_list))


def save_tax_records(new_records_list, filename=TAX_RECORDS_FILE):
    """
    Convert a list of tax record dictionaries into a pandas DataFrame and append/save
    to tax_records.csv while preserving previously saved records.
    """
    if not new_records_list:
        return False, "No tax records to save."

    new_df = pd.DataFrame(new_records_list, columns=TAX_COLUMNS)

    try:
        if os.path.exists(filename):
            existing_df = pd.read_csv(filename)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        combined_df.to_csv(filename, index=False)
        return True, f"Successfully saved {len(new_records_list)} record(s) to {filename}."
    except Exception as exc:
        return False, f"Error saving records to {filename}: {exc}"


def retrieve_tax_records(user_id=None, record_type="ALL", filename=TAX_RECORDS_FILE):
    """
    Retrieve saved tax records from tax_records.csv using pandas.
    record_type options:
      - "ALL": All records in the CSV file
      - "USER": Individual user records (Test Case ID == 'N/A') filtered by user_id if provided
      - "TEST": Test case records (Test Case ID != 'N/A')
    Returns a pandas DataFrame (empty DataFrame if file does not exist or no matches).
    """
    if not os.path.exists(filename):
        return pd.DataFrame(columns=TAX_COLUMNS)

    try:
        df = pd.read_csv(filename)
        if df.empty:
            return pd.DataFrame(columns=TAX_COLUMNS)

        df["Test Case ID"] = df["Test Case ID"].fillna("N/A").astype(str)
        df["User ID"] = df["User ID"].astype(str)

        if record_type == "USER":
            df = df[df["Test Case ID"] == "N/A"]
            if user_id:
                df = df[df["User ID"].str.lower() == user_id.strip().lower()]
        elif record_type == "TEST":
            df = df[df["Test Case ID"] != "N/A"]

        return df
    except Exception as exc:
        print(f"Error reading {filename}: {exc}")
        return pd.DataFrame(columns=TAX_COLUMNS)


def display_tax_records(df, title="SAVED TAX RECORDS"):
    """
    Format and display a pandas DataFrame of tax records cleanly with RM two-decimal formatting.
    """
    print("\n" + "=" * 105)
    print(f"{title:^105}")
    print("=" * 105)

    if df.empty:
        print("No matching tax records found.")
        print("=" * 105)
        return

    display_df = df.copy()
    monetary_cols = [
        "Annual Income",
        "Total Tax Relief",
        "Chargeable Income",
        "Tax Before Rebate",
        "Tax Rebate",
        "Final Tax Payable",
    ]
    for col in monetary_cols:
        display_df[col] = display_df[col].apply(lambda x: f"RM {float(x):,.2f}")

    print(display_df.to_string(index=False))
    print("=" * 105)


def run_predefined_test_cases(user_id="TEST_ADMIN", filename=TAX_RECORDS_FILE):
    """
    Execute all five required tax calculation test cases (T01 - T05),
    demonstrate list -> dictionary -> pandas DataFrame processing,
    and save/retrieve from tax_records.csv.
    """
    test_cases = [
        ("T01", 9000.00, 9000.00),
        ("T02", 40000.00, 9000.00),
        ("T03", 65000.00, 14000.00),
        ("T04", 120000.00, 18000.00),
        ("T05", 83000.00, 12000.00),
    ]

    # Remove previous T01-T05 entries if re-running so tax_records.csv stays clean
    if os.path.exists(filename):
        try:
            existing_df = pd.read_csv(filename)
            existing_df["Test Case ID"] = existing_df["Test Case ID"].fillna("N/A").astype(str)
            existing_df = existing_df[~existing_df["Test Case ID"].isin(["T01", "T02", "T03", "T04", "T05"])]
            existing_df.to_csv(filename, index=False)
        except Exception:
            pass

    test_records_dict_list = []
    for tc_id, income, relief in test_cases:
        # Step 1: Calculate and obtain Python list
        results_list = calculate_malaysian_tax(income, relief)
        # Step 2: Convert list to dictionary
        record_dict = create_tax_record_dict(
            user_id=user_id,
            calc_results_list=results_list,
            test_case_id=tc_id,
            year_of_assessment=2026,
        )
        # Step 3: Append to list of dictionaries
        test_records_dict_list.append(record_dict)

    # Step 4: Convert list of dictionaries into pandas DataFrame & save to CSV
    success, msg = save_tax_records(test_records_dict_list, filename=filename)
    print(f"\n{msg}")

    # Step 5: Retrieve from CSV using pandas and display
    saved_test_df = retrieve_tax_records(record_type="TEST", filename=filename)
    display_tax_records(saved_test_df, title="YA 2026 TAX CALCULATION TEST CASES (T01 - T05)")
    return saved_test_df