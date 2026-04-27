"""
======================================================
PRE-STAGE INPUT SANITIZER FOR GLIBC UNIT-TEST PIPELINE
======================================================

This script belongs to a pre-normalization stage that runs before the
actual/real pipeline stages. Its only goal is to sanitize and reshape raw
dataset input (CSV) into the canonical JSON structure expected by stage 1
(`phase1_input.json`).

The later stages assume a stable input schema. Source files used during
experimentation can have inconsistent column names, missing fields, or extra
columns. This pre-stage provides a one-time interactive mapping from CSV
columns to the standard fields used by the pipeline (which can be extended as 
needed, but for now include:):

- Type:         function, macro, etc.
- Scope:        public or internal to glibc
- Name:         function/macro name
- Path:         path to the glibc build file where the function/macro is defined
- Code:         the actual code of the function/macro 
- Description:  a brief description of the function/macro

This is intentionally a utility/sanitization script, not part of the core generation 
logic. It should be run only to prepare clean input for the real stages.

-> How to use:
1. Place the raw CSV file(s) in the same directory as this script.
2. Run the script: `python3 phase0_input_prep.py`
3. Follow the interactive prompts to select the CSV file and map columns to categories.
4. The sanitized output will be saved as `phase1_input.json` in the same directory.
"""

import os
import pandas as pd
import json

# ===============================================
# Global constants and utility functions
# ===============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_INPUT_CATEGORIES = ["type", "scope", "name", "path", "code","description"]
OUTPUT_FILE = os.path.join(BASE_DIR, "phase1_input.json")

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

def get_user_input(valid_options: list, prompt: str, max_retries: int = 1, allow_none: bool = False) -> str:
    """Prompt the user to select one option from a list.

    Args:
        valid_options: Available selectable options.
        prompt: Message shown before listing options.
        max_retries: Maximum number of invalid attempts allowed.
        allow_none: If True, a "None" option is offered at the end.

    Returns:
        The selected option string, or None if selection fails/exceeds retries
        (or if the user chooses "None" when allowed).
    """
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
    """Run the pre-stage CSV-to-JSON sanitization flow.

    Workflow:
    1. Discover CSV files in the current stage directory.
    2. Let the user choose the CSV file (if more than one exists).
    3. Ask the user to map CSV columns to the canonical JSON categories.
    4. Generate `phase1_input.json` with normalized records.
    """

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
    empty_cell = False
    for row in data:
        output_row = {}
        for category, column in category_to_column_mapping.items():
            value = row.get(column)
            if pd.isna(value) or value is None:
                empty_cell = True
                break
            output_row[category] = None if pd.isna(value) else value

        if not empty_cell:
            output_data.append(output_row)
            empty_cell = False

    # Save output in json format
    print(f"\nSaving output to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

if __name__=="__main__":
    exit(main())