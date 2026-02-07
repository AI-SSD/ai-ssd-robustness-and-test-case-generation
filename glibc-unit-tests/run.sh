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

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}     Unit Test Generator for Glibc Functions${NC}"
echo -e "${GREEN}==================================================${NC}"

# ======================================================
# Configure environment variables if not set previously
# ======================================================
OLLAMA_PORT=${OLLAMA_PORT:-11434}
OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5-coder:3b}
LOCAL_OLLAMA_URL="http://localhost:${OLLAMA_PORT}"  # used only to test to Ollama connectivity while outside the container
CONTAINER_NAME=${CONTAINER_NAME:-"glibc-unit-test-generator"}
IMAGE_NAME=${IMAGE_NAME:-"${CONTAINER_NAME}-image"}

# If OLLAMA_HOST not provided, ask for input
if [ -z "$OLLAMA_HOST" ]; then
    read -p ">>> Is Ollama running locally or remotely? (local/remote): " OLLAMA_HOST
fi

# Ask for Ollama URL if host is remote and URL not provided
if [ "$OLLAMA_HOST" == "local" ]; then
    OLLAMA_URL="http://host.docker.internal:${OLLAMA_PORT}"
else if [ "$OLLAMA_HOST" == "remote" ]; then
    if [ -z "$OLLAMA_URL" ]; then
        read -p ">>> Enter the Ollama URL (e.g. http://1.1.1.1:11434): " OLLAMA_URL
    fi
else
    echo -e "${RED}✗ Invalid input for Ollama host.${NC}"
    return 1
fi


# ======================================================
# Functions
# ======================================================

# Check if ollama is running
check_ollama() {
    echo -e "\n${YELLOW}Checking if Ollama is running...${NC}"
    if [ "$OLLAMA_HOST" == "local" ]; then
        echo -e "${YELLOW}Checking local Ollama at ${LOCAL_OLLAMA_URL}...${NC}"
        temp_url="${LOCAL_OLLAMA_URL}"
    else
        echo -e "${YELLOW}Checking remote Ollama at ${OLLAMA_URL}...${NC}"
        temp_url="${OLLAMA_URL}"
    fi

    if curl -s "${temp_url}/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is running on ${temp_url}${NC}"
        return 0
    else
        echo -e "${RED}✗ Ollama is not running${NC}"
        return 1
    fi
}

# Start ollama if not running already
start_ollama() {
    if [ "$OLLAMA_HOST" == "remote" ]; then
        echo -e "${RED}✗ Cannot start Ollama because it's configured as remote.${NC}"
        echo -e "Please start Ollama on the remote host and ensure it's reachable at ${OLLAMA_URL}"
        exit 1
    fi

    echo -e "\n${YELLOW}Starting Ollama...${NC}"
    if command -v ollama &> /dev/null; then
        ollama serve > /dev/null 2>&1 & OLLAMA_PID=$!
        echo -e "${GREEN}✓ Ollama started (PID: ${OLLAMA_PID})${NC}"
        
        # Wait for Ollama to be ready
        echo -n "Waiting for Ollama to be ready"
        for i in {1..30}; do
            if curl -s "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
                echo -e "\n${GREEN}✓ Ollama is ready${NC}"
                return 0
            fi
            echo -n "."
            sleep 1
        done
        echo -e "\n${RED}✗ Ollama failed to start${NC}"
        exit 1
    else
        echo -e "${RED}✗ Ollama is not installed. Please install it first.${NC}"
        exit 1
    fi
}

# Check if model is available
check_model() {
    echo -e "\n${YELLOW}Checking if model '${OLLAMA_MODEL}' is available...${NC}"
    if curl -s "${OLLAMA_URL}/api/tags" | grep -q "\"name\":\"${OLLAMA_MODEL}:latest\""; then
        echo -e "${GREEN}✓ Model '${OLLAMA_MODEL}' is available${NC}"
    else
        echo -e "${YELLOW}Model '${OLLAMA_MODEL}' not found. Pulling...${NC}"
        ollama pull "${OLLAMA_MODEL}"
        echo -e "${GREEN}✓ Model '${OLLAMA_MODEL}' downloaded${NC}"
    fi
}

# Check if code directory exists and has files
check_inputs_directory() {
    if [ ! -d "./inputs" ]; then
        echo -e "${RED}✗ ./inputs directory not found${NC}"
        echo -e "  Please create a ./inputs directory and add the required files (function info JSON, C implementation, etc.)"
        exit 1
    fi
    
    # Check for json file named metadata.json
    if [ ! -f "./inputs/metadata.json" ]; then
        echo -e "${RED}✗ metadata.json file not found in ./inputs directory${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Found metadata.json file in ./inputs directory${NC}"

    # Check for at least one .c file in the inputs directory
    if ! ls ./inputs/*.c 1> /dev/null 2>&1; then
        echo -e "${RED}✗ No .c files found in ./inputs directory${NC}"
        exit 1
    fi
    
    local file_count=$(ls -1 ./inputs/*.c | wc -l)
    echo -e "${GREEN}✓ Found ${file_count} C file(s) in ./inputs directory${NC}"
    echo -e "${GREEN}✓ Input directory is properly set up, but did not check structure inside files.${NC}"
}

# Build Docker image
build_image() {
    echo -e "\n${YELLOW}Building Docker image...${NC}"
    docker build -t "${IMAGE_NAME}" .
    echo -e "${GREEN}✓ Docker image built${NC}"
}

# Run the container
run_container() {
    echo -e "\n${YELLOW}Running container...${NC}"
    
    # Create results directories if they don't exist
    mkdir -p ./tests
    mkdir -p ./results
    
    # Remove old container if exists
    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
    
    # Run container and mount volumes to share code and results
    docker run --name "${CONTAINER_NAME}" \
        -v "$(pwd)/inputs:/app/inputs" \
        -v "$(pwd)/tests:/app/tests" \
        -v "$(pwd)/results:/app/results" \
        -e OLLAMA_URL="${OLLAMA_URL}" \
        -e OLLAMA_MODEL="${OLLAMA_MODEL}" \
        "${IMAGE_NAME}"
    
    echo -e "${GREEN}✓ Container execution completed${NC}"
}

# Display results
display_results() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  Summary of the Results${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    if [ -f "./results/summary.json" ]; then
        echo -e "\n${YELLOW}Summary:${NC}"
        cat ./results/summary.json | python3 -m json.tool | head -20
        
        echo -e "\n${GREEN}✓ Full results available in ./results/${NC}"
        echo -e "${GREEN}✓ Generated tests available in ./tests/${NC}"
    else
        echo -e "${RED}✗ No results found${NC}"
    fi
}

# ======================================================
# Main execution
# ======================================================
# Main execution
main() {
    # Check prerequisites
    check_inputs_directory
    
    # Handle Ollama
    if ! check_ollama; then
        if [ "$OLLAMA_HOST" == "local" ]; then
            start_ollama
        else
            echo -e "${RED}✗ Cannot connect to Ollama remotely at ${OLLAMA_URL}${NC}"
            return 1
        fi
    fi
    
    check_model
    
    # Build and run
    build_image
    run_container
    
    # Show results
    display_results
    
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  All done!${NC}"
    echo -e "${GREEN}========================================${NC}"
}

main