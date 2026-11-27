import functions as fn


def print_banner():
    print("\n" + "=" * 70)
    print("   MALAYSIAN PERSONAL INCOME TAX INPUT PROGRAM (YA 2026) - LHDN")
    print("=" * 70)


def handle_registration():
    print("\n--- NEW USER REGISTRATION ---")
    while True:
        user_id = input("Enter a new User ID (min 3 chars, no spaces/commas) or '0' to cancel: ").strip()
        if user_id == "0":
            print("Registration cancelled.")
            return

        ic_number = input("Enter your 12-digit Malaysian IC Number (without dashes): ").strip()
        success, message = fn.register_user(user_id, ic_number)
        print(message)
        if success:
            break


def handle_login():

    print("\n--- USER LOGIN ---")
    user_id = input("Enter User ID: ").strip()
    password = input("Enter Password (last 4 digits of your registered IC): ").strip()

    is_valid, message = fn.authenticate_user(user_id, password)
    print(message)
    if is_valid:
        return user_id
    return None


def prompt_valid_amount(prompt_text, field_name):
    while True:
        raw_input = input(prompt_text)
        is_valid, value, message = fn.validate_monetary_input(raw_input, field_name)
        if is_valid:
            return value
        print(message)


def handle_tax_calculation(current_user):

    print("\n--- YA 2026 INCOME TAX CALCULATION ---")
    print("Note: Include your RM9,000 individual relief in the Total Tax Relief amount where applicable.")

    annual_income = prompt_valid_amount("Enter Annual Income (RM): ", "Annual Income")
    total_relief = prompt_valid_amount("Enter Total Eligible Tax Relief (RM): ", "Total Tax Relief")

    if total_relief > annual_income:
        print("Notice: Total Tax Relief exceeds Annual Income. Chargeable Income will be set to RM 0.00.")

    # Step 1: Perform tax calculation (returns a Python list)
    results_list = fn.calculate_malaysian_tax(annual_income, total_relief)

    # Step 2: Convert list into a structured dictionary
    record_dict = fn.create_tax_record_dict(
        user_id=current_user,
        calc_results_list=results_list,
        test_case_id="N/A",
        year_of_assessment=2026,
    )

    print("\n" + "-" * 55)
    print(f"TAX CALCULATION SUMMARY (User: {current_user} | YA 2026)")
    print("-" * 55)
    print(f"Annual Income        : RM {record_dict['Annual Income']:,.2f}")
    print(f"Total Tax Relief     : RM {record_dict['Total Tax Relief']:,.2f}")
    print(f"Chargeable Income    : RM {record_dict['Chargeable Income']:,.2f}")
    print(f"Tax Before Rebate    : RM {record_dict['Tax Before Rebate']:,.2f}")
    print(f"Tax Rebate (<=35k)   : RM {record_dict['Tax Rebate']:,.2f}")
    print("-" * 55)
    print(f"FINAL TAX PAYABLE    : RM {record_dict['Final Tax Payable']:,.2f}")
    print("-" * 55)

    save_choice = input("Would you like to save this tax record to tax_records.csv? (Y/N): ").strip().upper()
    if save_choice == "Y":
        success, msg = fn.save_tax_records([record_dict])
        print(msg)
    else:
        print("Record not saved.")


def authenticated_menu(current_user):
    while True:
        print(f"\n--- MAIN TAX MENU (Logged in as: {current_user}) ---")
        print("1. Calculate Personal Income Tax (YA 2026)")
        print("2. View My Saved Tax Records")
        print("3. View All Tax Records (Users + Test Cases)")
        print("4. Run & Save 5 Required Tax Test Cases (T01 - T05)")
        print("5. Logout")

        choice = input("Select an option (1-5): ").strip()

        if choice == "1":
            handle_tax_calculation(current_user)
        elif choice == "2":
            user_df = fn.retrieve_tax_records(user_id=current_user, record_type="USER")
            fn.display_tax_records(user_df, title=f"INDIVIDUAL TAX RECORDS FOR {current_user.upper()}")
        elif choice == "3":
            all_df = fn.retrieve_tax_records(record_type="ALL")
            fn.display_tax_records(all_df, title="ALL SAVED TAX RECORDS (INDIVIDUAL & TEST CASES)")
        elif choice == "4":
            fn.run_predefined_test_cases(user_id=current_user)
        elif choice == "5":
            print(f"Logging out {current_user}. Goodbye!")
            break
        else:
            print("Error: Invalid selection. Please enter a number between 1 and 5.")


def main():
    print_banner()
    while True:
        print("\n--- WELCOME / AUTHENTICATION MENU ---")
        print("1. Register New User")
        print("2. Login")
        print("3. Exit Program")

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            handle_registration()
        elif choice == "2":
            authenticated_user = handle_login()
            if authenticated_user:
                authenticated_menu(authenticated_user)
        elif choice == "3":
            print("Exiting Malaysian Tax Input Program. Thank you!")
            break
        else:
            print("Error: Invalid option. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
