#!/usr/bin/env python3
import os
import json
import requests
import subprocess
import sys
import re
from pathlib import Path

# =============== Global Variables ===============
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
CODE_DIR = Path('/app/code')
TESTS_DIR = Path('/app/tests')
RESULTS_DIR = Path('/app/results')
PROMPT_FILE = Path('/app/prompt.txt')


# ============== Auxiliar Functions ==============
def query_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """
    Query Ollama API and return the response.
    """
    try:
        response = requests.post(
            f'{OLLAMA_URL}/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            },
            timeout=300
        )
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.RequestException as e:
        print(f"Error querying Ollama: {e}")
        sys.exit(1)

def read_c_file(filepath: Path) -> str:
    """
    Read a C source file.
    """
    with open(filepath, 'r') as f:
        return f.read()

def extract_function_signatures(code: str) -> list[str]:    
    """
    Extract function signatures from C code to create declarations.
    Returns a list of function declaration strings.
    """
    signatures = []
    
    # Pattern to match function definitions (simplified)
    # Matches: return_type function_name(parameters) 
    pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_\s\*]*?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{'
    
    for line in code.split('\n'):
        match = re.match(pattern, line)
        if match and not line.strip().startswith('//'):
            return_type = match.group(1).strip()
            func_name = match.group(2).strip()
            params = match.group(3).strip()
            
            # Skip main function
            if func_name == 'main':
                continue
            
            # Create declaration
            signature = f"{return_type} {func_name}({params});"
            signatures.append(signature)
    
    return signatures

def create_header_file(code: str, code_path: Path) -> Path | None:
    """
    Create a header file for the source code with function declarations.
    Add include to the main .c file.
    """
    header_filename = code_path.stem + '.h'
    header_path = os.path.join(CODE_DIR, header_filename)
    
    # Extract function signatures
    signatures = extract_function_signatures(code)
    
    if not signatures:
        print(f"Warning: No function signatures found in {code_path.name}")
        return None
    
    # Create header content with include guards
    guard_name = f"_{header_filename.upper().replace('.', '_')}_"
    
    header_content = f"""#ifndef {guard_name}
#define {guard_name}

#include <stddef.h>
#include <stdint.h>

// Function declarations
{chr(10).join(signatures)}

#endif /* {guard_name} */
"""
        
    # Write header file
    with open(header_path, 'w') as f:
        f.write(header_content)
    
    print(f"Created header file: {header_path}")

    # Add include to the main .c file if not already present
    include_statement = f'#include "{header_filename}"'
    if include_statement not in code:
        with open(code_path, 'r') as f:
            original_code = f.read()
        
        # Insert include after existing includes or at the top
        lines = original_code.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#include'):
                insert_index = i + 1
        
        lines.insert(insert_index, include_statement)
        
        with open(code_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Added include statement to {code_path.name}: {include_statement}")
    return header_path

def create_test_generation_prompt(code: str, filename: str, header_filename: str | None = None) -> str:
    """
    Create a prompt for generating unit tests.
    """
    header_include = f'#include "{header_filename}"' if header_filename else f'// Functions from {filename}'
    
    if PROMPT_FILE.exists():
        # Load base prompt template
        with open(PROMPT_FILE, 'r') as f:
            base_prompt = f.read()
        
        # Replace placeholders if they exist
        prompt = base_prompt + f"\nAdd this header to the includes: ../code/{header_include}.\nCode: {code}\n"
    else:
        # Use a generic prompt
        print("Warning: Prompt file not found, using generic prompt.")
        prompt = f"""Write unit tests in C for the following source code file named.
        Use the following header inclusion: {header_include}

        FILE NAME: {filename}
        SOURCE CODE:
        ```c
        {code}
        ```"""

    return prompt

def validate_test_code(test_code: str) -> str:
    """
    Validate and clean the generated test code.
    """
    # Remove markdown code blocks if present
    if '```c' in test_code:
        start = test_code.index('```c') + 4
        end = test_code.rindex('```')
        test_code = test_code[start:end].strip()
    elif '```' in test_code:
        start = test_code.index('```') + 3
        end = test_code.rindex('```')
        test_code = test_code[start:end].strip()
    
    return test_code.strip()

def save_test_file(test_code: str, original_filename: str) -> Path:
    """
    Save generated test code to a file.
    """
    test_filename = f"test_{original_filename}"
    test_path = TESTS_DIR / test_filename
    
    with open(test_path, 'w') as f:
        f.write(test_code)
    
    print(f"Saved test file: {test_path}")
    return test_path

def compile_and_run_test(test_path: Path, code_path: Path, header_path: Path | None = None) -> dict:
    """
    Compile and execute the test.
    """
    # Define executable path
    test_executable = test_path.with_suffix('')

    # Include directory for header if exists
    include_dir = ["-I", str(CODE_DIR)] if header_path else []
    
    # Compile command
    # Format: gcc test_path.c code_path.c -lm -Wall -Wextra -Wno-unused-variable -Wno-unused-function -o test_executable
    compile_cmd = [
        'gcc',
        str(test_path),
        str(code_path),
        '-lm',
        '-Wall',
        '-Wextra',
        '-Wno-unused-variable',
        '-Wno-unused-function',
        '-o',
        str(test_executable)
    ] + include_dir 


    print(f"Compiling: {' '.join(compile_cmd)}")
    compile_result = subprocess.run(
        compile_cmd,
        capture_output=True,
        text=True
    )
    
    build_success = compile_result.returncode == 0
    
    if not build_success:
        print(f"Compilation failed:\n{compile_result.stderr}")
        return {
            'build_success': False,
            'execution_success': False,
            'all_tests_passed': False,
            'tests_passed': 0,
            'tests_run': 0,
            'stdout': '',
            'stderr': compile_result.stderr
        }
    
    # Execute
    print(f"Executing: {test_executable}")
    try:
        exec_result = subprocess.run(
            [str(test_executable)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        execution_success = True
        all_tests = exec_result.returncode == 0
        
        # Count tests run (count ✓ symbols)
        tests_failed = exec_result.stdout.count('✗')
        tests_passed = exec_result.stdout.count('✓')
        total_tests = tests_passed + tests_failed
        
        # Clean up executable
        if test_executable.exists():
            test_executable.unlink()
        
        return {
            'build_success': True,
            'execution_success': execution_success,
            'all_tests_passed': all_tests,
            'tests_passed': tests_passed,
            'tests_run': total_tests,
            'stdout': exec_result.stdout,
            'stderr': exec_result.stderr
        }
    except subprocess.TimeoutExpired:
        print("Test execution timed out")
        if test_executable.exists():
            test_executable.unlink()
        return {
            'build_success': True,
            'execution_success': False,
            'all_tests_passed': False,
            'tests_passed': 0,
            'tests_run': 0,
            'stdout': '',
            'stderr': 'Test execution timed out after 30 seconds'
        }

def calculate_metrics(test_path, code_path, execution_results):
    """
    Calculate evaluation metrics for the generated tests.
    """
    metrics = {
        'validity': {},
        'effectiveness': {},
        'readability': {}
    }
    
    # =========== Validity Metrics ============
    metrics['validity']['build_success'] = execution_results['build_success']
    metrics['validity']['execution_success'] = execution_results['execution_success']
    metrics['validity']['tests_passed'] = execution_results['tests_passed']
    metrics['validity']['tests_run'] = execution_results['tests_run']
    
    # ========= Effectiveness Metrics =========
    # TODO: Implement line coverage calculation
    # Example: subprocess.run(['lcov', '--capture', '--directory', '.', '--output-file', 'coverage.info'])
    metrics['effectiveness']['line_coverage'] = None  # Placeholder
    
    # TODO: Implement mutation score calculation
    metrics['effectiveness']['mutation_score'] = None  # Placeholder
    
    # =========== Readability Metrics ==========
    # TODO: Implement Halstead complexity metrics
    metrics['readability']['halstead_vocabulary'] = None    # Placeholder
    metrics['readability']['halstead_length'] = None        # Placeholder
    metrics['readability']['halstead_volume'] = None        # Placeholder
    metrics['readability']['halstead_difficulty'] = None    # Placeholder
    metrics['readability']['halstead_effort'] = None        # Placeholder
    
    return metrics

def process_code_file(code_path):
    """
    Process a single C code file.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {code_path.name}")
    print(f"{'='*60}")
    
    # Read the code
    code = read_c_file(code_path)
    
    # Create header file for the code
    header_path = create_header_file(code, code_path)
    print(f"Header path: {header_path}")
    if header_path:
        header_filename = header_path.split('/')[-1]
    
    # Generate test
    print("Generating unit tests via Ollama...")
    prompt = create_test_generation_prompt(code, code_path.name, header_filename)
    test_code = query_ollama(prompt)
    test_code = validate_test_code(test_code)
    
    # Save test file
    test_path = save_test_file(test_code, code_path.name)
    
    # Compile and run test
    print("Compiling and executing test...")
    execution_results = compile_and_run_test(test_path, code_path, header_path)
    
    # Calculate metrics
    print("Calculating metrics...")
    metrics = calculate_metrics(test_path, code_path, execution_results)
    
    # Save results
    result = {
        'source_file': code_path.name,
        'test_file': test_path.name,
        'header_file': header_filename,
        'execution_results': execution_results,
        'metrics': metrics
    }
    
    result_path = RESULTS_DIR / f"result_{code_path.stem}.json"
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to: {result_path}")
    print(f"\nSummary:")
    print(f"  Build: {'✓' if execution_results['build_success'] else '✗'}")
    print(f"  Execution: {'✓' if execution_results['execution_success'] else '✗'}")
    print(f"  All Tests Passed: {'✓' if execution_results['all_tests_passed'] else '✗'}")
    print(f"  Tests Passed: {execution_results['tests_passed']}")
    print(f"  Tests Run: {execution_results['tests_run']}")
    
    return result


# ============= Main Processing Loop =============
def main():
    print("Starting unit test generation and evaluation...")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"LLM Model: {OLLAMA_MODEL}")
    
    # Find all C files in the code directory
    print(f"Scanning for C files in {CODE_DIR}...")
    c_files = list(CODE_DIR.glob('*.c'))
    
    if not c_files:
        print(f"No .c files found in {CODE_DIR}")
        sys.exit(1)
    
    print(f"Found {len(c_files)} C file(s) to process")
    
    results = []
    for code_file in c_files:
        try:
            result = process_code_file(code_file)
            results.append(result)
        except Exception as e:
            print(f"Error processing {code_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Save summary
    summary = {
        'total_files': len(c_files),
        'processed_files': len(results),
        'successful_builds': sum(1 for r in results if r['execution_results']['build_success']),
        'successful_executions': sum(1 for r in results if r['execution_results']['execution_success']),
        'all_tests_passed': sum(1 for r in results if r['execution_results']['all_tests_passed']),
        'total_tests_passed': sum(r['execution_results']['tests_passed'] for r in results),
        'total_tests_run': sum(r['execution_results']['tests_run'] for r in results),
        'results': results
    }

    summary_path = RESULTS_DIR / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"{'='*60}")
    print(f"Total files: {summary['total_files']}")
    print(f"Processed: {summary['processed_files']}")
    print(f"Successful builds: {summary['successful_builds']}")
    print(f"Successful executions: {summary['successful_executions']}")
    print(f"All tests passed: {summary['all_tests_passed']}")
    print(f"Total Tests passed: {summary['total_tests_passed']}")
    print(f"Total tests run: {summary['total_tests_run']}")
    print(f"Summary saved to: {summary_path}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()