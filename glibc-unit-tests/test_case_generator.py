from ollama_querier import OllamaQuerier
import argparse
import os

# Return codes
# 0: Success
# 1: Output directory already exists
# 2: Code file does not exist

# ======================================================
# Variables
# ======================================================
DEFAULT_PROMPT_FILE = "ut_prompt_v1.txt"

# ======================================================
# Functions
# ======================================================
def generate_prompt(base_prompt, args):
    mode = args['mode']
    function_name = args['function_name']
    glibc_version = args['glibc_version']
    code_file = args['code_file']

    if mode == 1:
        # Mode 1 — Base prompt + function code + glibc version
        with open(code_file, 'r') as f:
            code_content = f.read()

        prompt = base_prompt + f"\nInput Variables\nFunction Name: {function_name}\nGlibc Version: {glibc_version}\nCode:\n```{code_content}```"
        return prompt
    else:
        print(f"Mode {mode} not implemented yet. Using base prompt only.")
        return base_prompt


# ======================================================
# Main execution
# ======================================================
def main():
    # ---------------------- PROCESS ARGUMENTS ----------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--function-name", type=str, required=True, default=None,
                        help="Name of the function being tested.")
    parser.add_argument("-v", "--glibc-version", type=str, required=True, default=None,
                        help="Version of glibc being tested.")
    parser.add_argument("-c", "--code-file", type=str, required=True, default=None,
                        help="Path to the code file for the function being tested.")
    parser.add_argument("-p", "--prompt-file", type=str, required=False, default=None,
                        help="Path to a custom prompt file. If not provided, a default prompt will be used based on the mode.")
    parser.add_argument("-m", "--mode", type=int, choices=[1, 2, 3, 4], required=False, default=1,
                        help="Mode of operation for the type of prompt to be used.")
    parser.add_argument("-o", "--output", type=str, required=False, default="tests",
                        help="Define output directory for the tests.")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable debug prints.")
    args = parser.parse_args()

    FUNCTION_NAME = args.function_name
    glibc_version = args.glibc_version
    code_file = args.code_file
    prompt_file = args.prompt_file
    mode = args.mode
    output_dir = args.output
    debug = args.debug
    args_dict = vars(args)

    # Check if code file exists
    if not os.path.isfile(code_file):
        print(f"Code file '{code_file}' does not exist. Please provide a valid path.")
        return 2
    
    # Chck if function name matches the one in the code file
    with open(code_file, 'r') as f:
        content = f.read()
        if FUNCTION_NAME not in content:
            print(f"Function name '{FUNCTION_NAME}' not found in code file '{code_file}'. Please provide a valid function name.")
            return 2
    
    # ----------------------- GENERATE PROMPT -----------------------
    
    # Retreive the base prompt
    if prompt_file is not None: 
        with open(prompt_file, 'r') as f:
            base_prompt = f.read()
    else:
        prompt_file = DEFAULT_PROMPT_FILE
        with open(prompt_file, 'r') as f:
            base_prompt = f.read()

    # Generate the final prompt based on the mode
    prompt = generate_prompt(base_prompt, args_dict)

    # ------------------------ QUERY OLLAMA -------------------------

    querier = OllamaQuerier("http://localhost:11434", "qwen2.5-coder:3b")
    response = querier.query(prompt)
    print(response)

    # Clean up the response if necessary
    return 0

    # ------------------------- SAVE OUTPUT -------------------------

    # Check if the parent output directory exists, if not create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a subdirectory for the function and glibc version, if it already exists, return an error
    output_dir = os.path.join(output_dir, f"{FUNCTION_NAME}_glibc_{glibc_version}")
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        print(f"Output directory '{output_dir}' already exists. Please choose a different name.")
        return 1


if __name__=="__main__":
    exit(main())