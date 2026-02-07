# Unit Test Generator with Ollama for C Functions

This project automatically generates and evaluates unit tests for C code using Ollama.
It is run once to generate test cases for all files inside a given folder ("code" in this case).

## Project Methodology

To be defined. For now, assume a similar methodology to the one described in the C unit tests project, but adapted to the specifics of glibc and its testing requirements.

## Project Structure

```
├── Dockerfile                  # Container definition
├── orchestrator.py             # Python orchestration script. Main entry point to the programrun by the container after setup.
├── requirements.txt            # Python dependencies
├── create_glibc_build.sh       # Script to create the glibc build environment and build glibc. 
├── prompt_generator.py         # Script to generate the prompt.
├── gen_ai_querier.py           # Script to query Ollama for test generation.
├── test_generator.py           # Script to generate the test files. Calls the prompt generator and the AI querier.
├── test_evaluator.py           # Script to compile, run and evaluate the generated tests.
├── run.sh                      # Main execution script inside the local machine. Builds the container and runs it.
├── inputs/                     # Input folder for the glibc functions and other necessary information.
├── prompts/                    # Folder for prompt templates.
├── tests/                      # Generated test files (output)
└── results/                    # Evaluation results (output)
```

## Prerequisites

1. **Docker** - Install from [docker.com](https://www.docker.com/)
2. **Ollama** - Install from [ollama.ai](https://ollama.ai/)
3. **Bash** - Pre-installed on Linux/Mac, use Git Bash on Windows
4. **Folder** - Have the *glibc-unit-tests* folder downloaded (it is from where this will be executed)

## Setup

1. **Clone the main repository and navigate to the glibc-unit-tests folder:**
   ```bash
   git clone <repository_url>
   cd glibc-unit-tests
   ```

2. **Create the inputs directory (if not already present) and fill it with the necessary files, according to the following structure:**
   ```bash
    mkdir -p inputs  
   ```

Inside the inputs/ folder, create the following files and folders:
- **code/** — a folder containing code files for each glibc function to be tested. Each file should contain the implementation of a single function, and the filename should match the function name (e.g., `printf.c` for the `printf` function).   
- **metadata.json** — a JSON file containing necessary information about the glibc functions to be tested. This includes function signatures, descriptions, and any other relevant information that can help the model generate accurate tests.

```
metadata.json structure example:
{
    "glibc_version": "2.32",
    "type": "function",
    "name": "printf",
    "signature": "int printf(const char *format, ...);",
    "description": "Prints formatted output to stdout. The first argument is a format string that specifies how subsequent arguments are converted for output."
}
```

3. **Make the orchestration script executable:**
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
4. ✓ Execute the Docker container, which will:
   - Process the data in the `inputs/` folder
   - Create the glibc build environment and build glibc (**create_glibc_build.py**)
   - Generate unit tests using Ollama (**test_generator.py**, which calls **prompt_generator.py** and **gen_ai_querier.py**)
   - Compile, execute and evaluate the tests (**test_evaluator.py**)
   - Save results to `tests/` and `results/`

   
## Configuration

You can customize the behavior with environment variables:

```bash
# Choose a local or remote Ollama host (this one tends to be necessary for Docker)
OLLAMA_HOST=localhost ./run.sh
or
OLLAMA_HOST=remote ./run.sh

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

