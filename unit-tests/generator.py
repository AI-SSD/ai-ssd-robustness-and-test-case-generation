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
def query_ollama(prompt, model=OLLAMA_MODEL):
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

def read_c_file(filepath):
    """
    Read a C source file.
    """
    with open(filepath, 'r') as f:
        return f.read()

def extract_function_signatures(code):
    """
    Extract function signatures from C code to create declarations.
    Returns a list of function declaration strings.
    """
    signatures = []
    
    # Pattern to match function definitions (simplified)
    # Matches: return_type function_name(parameters) {
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

def create_header_file(code, code_path):
    """
    Create a header file for the source code with function declarations.
    """
    header_filename = code_path.stem + '.h'
    header_path = CODE_DIR / header_filename
    
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
    return header_path

def create_test_generation_prompt(code, filename, header_filename=None):
    """
    Create a prompt for generating unit tests.
    """
    header_include = f'#include "{header_filename}"' if header_filename else f'// Functions from {filename}'
    
    if PROMPT_FILE.exists():
        # Load base prompt template
        with open(PROMPT_FILE, 'r') as f:
            base_prompt = f.read()
        
        # Replace placeholders if they exist
        prompt = base_prompt.replace('{filename}', filename)
        prompt = prompt.replace('{header_include}', header_include)
        prompt = prompt + f"\n\nSOURCE CODE:\n```c\n{code}\n```"
    else:
        prompt = f"""You are the TESTER agent. Your job is to generate comprehensive unit tests for glibc C code.

SOURCE FILE: {filename}

SOURCE CODE:
```c
{code}
```

RESPONSIBILITIES:

1. ANALYZE the source code and identify:
   - All functions that need testing
   - All execution paths (branches, loops, conditions)
   - All boundary conditions (0, -1, NULL, MAX_INT, MIN_INT, empty inputs)
   - All error conditions (invalid inputs, edge cases, overflow/underflow)
   - All possible return values and states

2. GENERATE unit tests covering:
   - TC-01: Normal/Happy Path - Standard use cases with valid inputs
   - TC-02: Boundary Values - Test at, below, and above limits
   - TC-03: Edge Cases - Empty inputs, null pointers, zero-length, extreme values
   - TC-04: Error Handling - Invalid inputs, error returns, exceptional conditions
   - TC-05: Logic Coverage - Each branch, each condition (true/false), each loop iteration (0, 1, many)
   - TC-06: Type Edge Cases - INT_MAX, INT_MIN, SIZE_MAX, signed/unsigned boundaries
   - TC-07: Memory Cases - NULL pointers, uninitialized values (if applicable)

3. STRUCTURE Requirements:
   - Create ONE complete C file with MULTIPLE test functions (minimum 8-12 tests)
   - Include: {header_include}
   - Each test function follows naming: test_<function_name>_<scenario>()
   - Use descriptive scenario names: _normal, _boundary_zero, _null_pointer, _overflow, etc.
   - Each test uses assert() from <assert.h> for validation
   - Each test prints status using printf(): "✓ test_name passed\\n"
   - Include main() function that calls ALL test functions sequentially
   - main() returns 0 on complete success, 1 if any assertion fails

4. CODE TEMPLATE:
```c
#include <assert.h>
#include <stdio.h>
#include <limits.h>
#include <string.h>
#include <stdlib.h>
{header_include}

// ============================================
// TEST FUNCTIONS
// ============================================

void test_function_normal_case() {{
    // Test standard, expected behavior
    int result = function(valid_input);
    assert(result == expected_output);
    printf("✓ test_function_normal_case passed\\n");
}}

void test_function_boundary_zero() {{
    // Test boundary at zero
    int result = function(0);
    assert(result == expected_for_zero);
    printf("✓ test_function_boundary_zero passed\\n");
}}

void test_function_boundary_negative() {{
    // Test negative boundary
    int result = function(-1);
    assert(result == expected_for_negative);
    printf("✓ test_function_boundary_negative passed\\n");
}}

void test_function_edge_null() {{
    // Test NULL pointer handling (if applicable)
    int result = function(NULL);
    assert(result == expected_error_value);
    printf("✓ test_function_edge_null passed\\n");
}}

void test_function_edge_max() {{
    // Test maximum value
    int result = function(INT_MAX);
    assert(result == expected_for_max);
    printf("✓ test_function_edge_max passed\\n");
}}

void test_function_error_invalid() {{
    // Test error handling
    int result = function(invalid_input);
    assert(result == error_code);
    printf("✓ test_function_error_invalid passed\\n");
}}

void test_function_logic_branch_true() {{
    // Test specific branch taken
    int result = function(value_for_true_branch);
    assert(result == expected_from_true_branch);
    printf("✓ test_function_logic_branch_true passed\\n");
}}

void test_function_logic_branch_false() {{
    // Test alternative branch
    int result = function(value_for_false_branch);
    assert(result == expected_from_false_branch);
    printf("✓ test_function_logic_branch_false passed\\n");
}}

// ... Generate 8-15 total test functions covering all scenarios ...

// ============================================
// MAIN TEST RUNNER
// ============================================

int main() {{
    printf("\\n========================================\\n");
    printf("Running tests for {filename}\\n");
    printf("========================================\\n\\n");
    
    test_function_normal_case();
    test_function_boundary_zero();
    test_function_boundary_negative();
    test_function_edge_null();
    test_function_edge_max();
    test_function_error_invalid();
    test_function_logic_branch_true();
    test_function_logic_branch_false();
    // ... call all test functions ...
    
    printf("\\n========================================\\n");
    printf("All tests passed successfully!\\n");
    printf("========================================\\n");
    return 0;
}}
```

CRITICAL RULES:

1. Output ONLY valid C code - no markdown, no explanations, no comments outside the code
2. Every test function must be self-contained and test ONE specific scenario
3. Use descriptive names that clearly indicate what is being tested
4. Include necessary headers at the top
5. Use {header_include} to access the functions being tested
6. Ensure all tests are called in main()
7. Use assert() for all validations
8. Print clear success messages for each test
9. Generate minimum 8-12 test functions, more for complex code
10. Cover ALL functions present in the source code
11. Test both success paths AND failure paths

FLOATING-POINT RULES (if applicable):
- For floating-point comparisons, use epsilon-based comparison:
  assert(fabs(result - expected) < 1e-6);
- Never use direct == for float or double comparisons

POINTER RULES:
- Always test NULL pointer cases where applicable
- Test valid pointer with valid data
- Test pointer to empty data (if applicable)

OUTPUT FORMAT:
Provide ONLY the complete C test file as plain text. No markdown code blocks, no explanations before or after.
Begin directly with #include statements and end with the closing brace of main()."""

    return prompt

def validate_test_code(test_code):
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

def save_test_file(test_code, original_filename):
    """
    Save generated test code to a file.
    """
    test_filename = f"test_{original_filename}"
    test_path = TESTS_DIR / test_filename
    
    with open(test_path, 'w') as f:
        f.write(test_code)
    
    print(f"Saved test file: {test_path}")
    return test_path

def compile_and_run_test(test_path, code_path, header_path=None):
    """
    Compile and execute the test.
    """
    # Define executable path
    test_executable = test_path.with_suffix('')
    
    # Prepare include directories
    include_dirs = ['-I', str(CODE_DIR)]
    
    # Compile command
    compile_cmd = [
        'gcc',
        '-o', str(test_executable),
        str(test_path),
        str(code_path),
        *include_dirs,
        '-lm',  # Math library
        '-Wall',  # Enable warnings
        '-Wno-unused-variable',  # Suppress unused variable warnings
        '-Wno-unused-function'  # Suppress unused function warnings
    ]
    
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
            'tests_passed': False,
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
        tests_passed = exec_result.returncode == 0
        
        # Count tests run (count ✓ symbols)
        tests_run = exec_result.stdout.count('✓')
        
        # Clean up executable
        if test_executable.exists():
            test_executable.unlink()
        
        return {
            'build_success': True,
            'execution_success': execution_success,
            'tests_passed': tests_passed,
            'tests_run': tests_run,
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
            'tests_passed': False,
            'tests_run': 0,
            'stdout': '',
            'stderr': 'Test execution timed out after 30 seconds'
        }

def calculate_metrics(test_path, code_path, execution_results):
    """
    Calculate evaluation metrics for the generated tests.
    """
    metrics = {
        'valid_unit_tests': {},
        'effective_unit_tests': {},
        'readability': {}
    }
    
    # =========== Validity Metrics ============
    metrics['valid_unit_tests']['build_success'] = execution_results['build_success']
    metrics['valid_unit_tests']['execution_success'] = execution_results['execution_success']
    metrics['valid_unit_tests']['tests_passed'] = execution_results['tests_passed']
    metrics['valid_unit_tests']['tests_run'] = execution_results['tests_run']
    
    # ========= Effectiveness Metrics =========
    # TODO: Implement line coverage calculation
    # Example: subprocess.run(['lcov', '--capture', '--directory', '.', '--output-file', 'coverage.info'])
    metrics['effective_unit_tests']['line_coverage'] = None  # Placeholder
    
    # TODO: Implement mutation score calculation
    metrics['effective_unit_tests']['mutation_score'] = None  # Placeholder
    
    # =========== Readability Metrics ==========
    # TODO: Implement Halstead complexity metrics
    metrics['readability']['halstead_vocabulary'] = None  # Placeholder
    metrics['readability']['halstead_length'] = None  # Placeholder
    metrics['readability']['halstead_volume'] = None  # Placeholder
    metrics['readability']['halstead_difficulty'] = None  # Placeholder
    metrics['readability']['halstead_effort'] = None  # Placeholder
    
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
    header_filename = header_path.name if header_path else None
    
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
    print(f"  Tests Passed: {'✓' if execution_results['tests_passed'] else '✗'}")
    print(f"  Tests Run: {execution_results['tests_run']}")
    
    return result


# ============= Main Processing Loop =============
def main():
    """ Main processing loop. """
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
        'all_tests_passed': sum(1 for r in results if r['execution_results']['tests_passed']),
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
    print(f"Total tests run: {summary['total_tests_run']}")
    print(f"Summary saved to: {summary_path}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()