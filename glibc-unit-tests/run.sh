# File Workflow
# 1. Read argument inputs (whether Ollama runs locally or remotely, the model to use and the Ollama URL)
# 2.1. If Ollama is local, check if it's installed and running. If not, start it and wait for it to be ready. 
# 2.2. If Ollama is remote, check if it's reachable at the provided URL.
# 3. Check if the specified model is available. If not, pull it.
# 4. Check if the ./code directory exists and has the necessary files:
#    - Json with information on the function to test (name, signature, description, etc.)
#    - C file with the implementation of the function to test
#    - The correct glibc version for that function
# 5. Check if docker is installed and running. If not, print instructions to install/start it.
# 6. Build the Docker image.
# 7. Run the Docker container, mounting the code directory and passing necessary environment variables.

# Inside the Docker container:
# 1. Install all necessary dependencies (glibc build tools, testing tools, etc.)
# 2. Create the correct directory structure and mount the code directory
# 3. Build the specified version of glibc from source
# 4. Construct the prompt for the test generator model, including the function information and any additional context (e.g. glibc version, edge cases to consider, etc.)
# 5. Call the Ollama API to generate the test cases
# 6. Save the generated test cases in the correct build structure for glibc tests
# 7. Build and run the tests, collecting results and coverage information
# 8. Save results and coverage information to the mounted results directory
# 9. Terminate the container

#!/bin/bash

# Before running this script, make sure to:
# - define the type of Ollama host (local or remote) by setting the OLLAMA_HOST environment variable or by providing input when prompted
# - if using a remote Ollama, set the OLLAMA_URL environment variable or provide it when prompted
# - to use a different Ollama port do "export OLLAMA_PORT=your_port"
# - to use a different Ollama model do "export OLLAMA_MODEL=your_model"
# - to use a different container name do "export CONTAINER_NAME=your_container_name"
# - to use a different image name do "export IMAGE_NAME=your_image_name"

# Robustness flags
set -Eeuo pipefail
IFS=$'\n\t'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'        # no color

# ======================================================
# Configure environment variables if not set previously
# ======================================================
OLLAMA_PORT=${OLLAMA_PORT:-11434}
OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5-coder:3b}
CONTAINER_NAME=${CONTAINER_NAME:-"glibc-unit-test-generator"}
IMAGE_NAME=${IMAGE_NAME:-"${CONTAINER_NAME}-image"}

# If OLLAMA_HOST not provided, ask for input
if [ -z "$OLLAMA_HOST" ]; then
    read -p "Is Ollama running locally or remotely? (local/remote): " OLLAMA_HOST
fi

# Ask for Ollama URL if host is remote and URL not provided
if [ "$OLLAMA_HOST" == "local" ]; then
    OLLAMA_URL="http://host.docker.internal:${OLLAMA_PORT}"
else
    if [ -z "$OLLAMA_URL" ]; then
        read -p "Enter the Ollama URL (e.g. http://1.1.1.1:11434): " OLLAMA_URL
    fi
fi




echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}     Unit Test Generator for Glibc Functions${NC}"
echo -e "${GREEN}==================================================${NC}"