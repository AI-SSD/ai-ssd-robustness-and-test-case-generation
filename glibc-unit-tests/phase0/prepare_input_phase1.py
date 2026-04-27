import os
import pandas as pd
import json

# This file is specifically to get the cves or functions from an excel or .csv file into a format that can be used as input for stage 1.
# It is not meant to be a general-purpose file parser, but rather a one-off script to convert the data we have into the format we need for stage 1.

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_INPUT_CATEGORIES = ["type", "scope", "name", "path", "code","description"]
OUTPUT_FILE = os.path.join(BASE_DIR, "phase1_input.json")

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

def get_user_input(valid_options: list, prompt: str, max_retries: int = 1, allow_none: bool = False) -> str:
    retries = 0
    while retries < max_retries:
        if retries == 0:
            print(prompt)
            for i, option in enumerate(valid_options):
                print(f"{i + 1}. {option}")
            if allow_none:
                print(f"{len(valid_options) + 1}. None")
        try:
            choice = int(input("Enter your choice: ")) - 1
            if allow_none and choice == len(valid_options):
                return None
            if 0 <= choice < len(valid_options):
                return valid_options[choice]
            else:
                retries += 1
                print(f"{RED}Invalid choice. Please try again.{RESET}")
        except ValueError:
            retries += 1
            print(f"{RED}Invalid input type. Please try again{RESET}")
    print("Max retries exceeded.")
    return None


def main():
    print("""
    ===============================================
    |                                            |
    |   GLIBC UNIT TESTS - PHASE 0 INPUT PREP    |
    |                                            |
    ===============================================\n
    """)

    # ===============================================
    # Find all the .csv files in the input directory 
    # ===============================================
    # Get list of all .csv files in the input directory
    csv_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.csv')]

    # End execution if no .csv files found
    if not csv_files:
        print("No .csv files found in the input directory.")
        return 1
    
    # Let user choose which .csv file to use
    if len(csv_files) > 1:
        selected_csv = get_user_input(csv_files, "The current directory has multiple .csv files. Please select a file to use:", 3)
    else:
        selected_csv = csv_files[0]

    if selected_csv is None:
        print("No valid .csv file selected. Ending execution.")
        return 1
    

    # ===============================================
    # Parse the selected .csv file and save the data in a list of dictionaries
    # ===============================================
    # Read csv file
    selected_csv_path = os.path.join(BASE_DIR, selected_csv)
    data = pd.read_csv(selected_csv_path).to_dict(orient='records')

    # Iterate through all columns and allows the user to choose which column 
    # corresponds to each category in the final json output
    column_names = data[0].keys()
    column_names = list(column_names)
    print("\n===============================================")
    print("Choose which column corresponds to each category in the final output file. If a category does not apply, you can select 'None' for that category.")
    print(f"Available final categories: {GREEN}{JSON_INPUT_CATEGORIES}{RESET}")
    print("\n===============================================\n")

    category_to_column_mapping = {}
    for category in JSON_INPUT_CATEGORIES:
        selected_column = get_user_input(column_names, f"Select the column that corresponds to the {GREEN}'{category}'{RESET} category:", 3, allow_none=True)
        
        if selected_column is None:
            print(f"No column selected for category '{category}'. This category will be empty in the final output.")
        else:
            category_to_column_mapping[category] = selected_column

        print("\n=====================")

    # Create a new dataset with the selected columns and save it in json format
    output_data = []
    for row in data:
        output_row = {}
        for category, column in category_to_column_mapping.items():
            value = row.get(column)
            output_row[category] = None if pd.isna(value) else value
        output_data.append(output_row)

    # Save output in json format
    print(f"\nSaving output to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

if __name__=="__main__":
    exit(main())