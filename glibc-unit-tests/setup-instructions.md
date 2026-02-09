# Unit Test Generator with Ollama for GLibc Functions

This project automatically generates and evaluates unit tests for glibc functions using Ollama.
It is run once to generate test cases for the functions defined in the `inputs/` folder, and it outputs the generated test files in the `tests/` folder and the evaluation results in the `results/` folder.

## Project Methodology

To be defined. For now, assume a similar methodology to the one described in the C unit tests project, but adapted to the specifics of glibc and its testing requirements.

## Project Structure

```
├── Dockerfile                  # Container definition
├── orchestrator.sh             # Shell orchestration script. Main entry point to the program run by the container after setup.
├── requirements.txt            # Python dependencies
├── build_glibc.sh              # Script to create the glibc build environment and build glibc. 
├── prompt_generator.py         # Script to generate the prompt.
├── ollama_querier.py           # Script to query Ollama for test generation.
├── test_case_generator.py      # Script to generate the test files. Calls the prompt generator and the AI querier.
├── test_case_evaluator.py      # Script to compile, run and evaluate the generated tests.
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

> [!WARNING]
> - Start Docker on your machine. Optionally, start Ollama if you want to check its status before running the script (the script will also check and start it if needed).
> - Define the specific configurations for the script through environment variables if you want to override the defaults (see Configuration section below).

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
   - Create the glibc build environment and build glibc (**build_glibc.sh**)
   - Generate unit tests using Ollama (**test_generator.py**, which calls **prompt_generator.py** and **gen_ai_querier.py**)
   - Compile, execute and evaluate the tests (**test_evaluator.py**)
   - Save results to `tests/` and `results/`

   
## Configuration

You must define **whether the Ollama host runs locally or remotely**. If using a remote host, you must also specify the URL.
This can be done through environment variables or by providing input when prompted at runtime. 

```bash
OLLAMA_HOST=local ./run.sh
or
OLLAMA_HOST=remote OLLAMA_URL=http://<remote_host_ip> ./run.sh
```

Other configurations that can be set through environment variables include:
- **Changing Ollama port** (default: 11434) ```OLLAMA_PORT=<port_nbr> ./run.sh```
- **Changing Ollama model** (default: `qwen2.5-coder:3b`) ```OLLAMA_MODEL=<model_name> ./run.sh```
- **Changing container name** (default: `glibc-unit-tests-container`) ```CONTAINER_NAME=<container_name> ./run.sh```
- **Reusing existing Docker image** (default: `false`) ```REUSE_IMAGE=true ./run.sh```

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

