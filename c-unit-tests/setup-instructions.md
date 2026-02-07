# Unit Test Generator with Ollama for C Functions

This project automatically generates and evaluates unit tests for C code using Ollama.
It is run once to generate test cases for all files inside a given folder ("code" in this case).

## Project Methodology

<img width="5742" height="5430" alt="methodology-unit-test-case-generation_background" src="https://github.com/user-attachments/assets/f4a3f786-a1b9-420d-bdfe-5e7f7e7e60c8" />

## Project Structure

```
.
├── Dockerfile             # Container definition
├── generator.py           # Python orchestration script
├── requirements.txt       # Python dependencies
├── run.sh                 # Main execution script
├── code/                  # Place your .c files here (input)
├── tests/                 # Generated test files (output)
└── results/               # Evaluation results (output)
```

## Prerequisites

1. **Docker** - Install from [docker.com](https://www.docker.com/)
2. **Ollama** - Install from [ollama.ai](https://ollama.ai/)
3. **Bash** - Pre-installed on Linux/Mac, use Git Bash on Windows
4. **Folder** - Have the *unit-tests* folder downloaded (it is from where this will be executed)

## Setup

1. **Create the code directory and add your C files:**
   ```bash
   mkdir -p code
   # Copy your glibc .c files to the code/ directory
   ```

2. **Make the orchestration script executable:**
   ```bash
   chmod +x run.sh
   ```

## Usage

Simply run:

```bash
./run.sh
```

This single command will:
1. ✓ Check if Ollama is running (start it if needed)
2. ✓ Check if the required model is available (download if needed)
3. ✓ Build the Docker container
4. ✓ Process all .c files in the `code/` directory
5. ✓ Generate unit tests using Ollama
6. ✓ Compile and execute the tests
7. ✓ Calculate evaluation metrics
8. ✓ Save results to `tests/` and `results/`

## Configuration

You can customize the behavior with environment variables:

```bash
# Use a different Ollama host (this one tends to be necessary)
OLLAMA_URL=http://host.docker.internal:11434 ./run.sh

# Use a different model
OLLAMA_MODEL=llama2 ./run.sh

# Use a different port
OLLAMA_PORT=11435 ./run.sh
```

## Output

### Generated Tests (`./tests/`)
- `test_<original_filename>.c` - Generated unit test code

### Results (`./results/`)
- `result_<filename>.json` - Detailed metrics results for each file
- `summary.json` - Overall summary

### Result Format

Each result file contains:

```json
{
  "source_file": "example.c",
  "test_file": "test_example.c",
  "execution_results": {
    "build_success": true,
    "execution_success": true,
    "test_passed": true,
    "stdout": "...",
    "stderr": "..."
  },
  "metrics": {
    "valid_unit_tests": {
      "build_success": true,
      "execution_success": true,
      "test_passed": true
    },
    "effective_unit_tests": {
      "line_coverage": null,
      "mutation_score": null
    },
    "readability": {
      "halstead_vocabulary": null,
      "halstead_length": null,
      "halstead_volume": null,
      "halstead_difficulty": null,
      "halstead_effort": null
    }
  }
}
```

## Example Code File

Place this in `./code/example.c` to test the system:

```c
#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}
```

Then run:
```bash
./run.sh
```
