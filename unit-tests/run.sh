#!/bin/bash
set -e

# Configuration
OLLAMA_PORT=${OLLAMA_PORT:-11434}
OLLAMA_MODEL=${OLLAMA_MODEL:-llama3}
OLLAMA_URL=${OLLAMA_URL:-"http://localhost:${OLLAMA_PORT}"}
CONTAINER_NAME="glibc-unit-test-generator"
IMAGE_NAME="glibc-unit-test-generator-image"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Glibc Unit Test Generator${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if ollama is running
check_ollama() {
    echo -e "\n${YELLOW}Checking if Ollama is running...${NC}"
    if curl -s "http://localhost:${OLLAMA_PORT}/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is running on port ${OLLAMA_PORT}${NC}"
        return 0
    else
        echo -e "${RED}✗ Ollama is not running${NC}"
        return 1
    fi
}

# Start ollama if not running
start_ollama() {
    echo -e "\n${YELLOW}Starting Ollama...${NC}"
    if command -v ollama &> /dev/null; then
        ollama serve > /dev/null 2>&1 & OLLAMA_PID=$!
        echo -e "${GREEN}✓ Ollama started (PID: ${OLLAMA_PID})${NC}"
        
        # Wait for Ollama to be ready
        echo -n "Waiting for Ollama to be ready"
        for i in {1..30}; do
            if curl -s "http://localhost:${OLLAMA_PORT}/api/tags" > /dev/null 2>&1; then
                echo -e "\n${GREEN}✓ Ollama is ready${NC}"
                return 0
            fi
            echo -n "."
            sleep 1
        done
        echo -e "\n${RED}✗ Ollama failed to start${NC}"
        exit 1
    else
        echo -e "${RED}✗ Ollama is not installed. Please install it from https://ollama.ai${NC}"
        exit 1
    fi
}

# Check if model is available
check_model() {
    echo -e "\n${YELLOW}Checking if model '${OLLAMA_MODEL}' is available...${NC}"
    if curl -s "http://localhost:${OLLAMA_PORT}/api/tags" | grep -q "\"name\":\"${OLLAMA_MODEL}\""; then
        echo -e "${GREEN}✓ Model '${OLLAMA_MODEL}' is available${NC}"
    else
        echo -e "${YELLOW}Model '${OLLAMA_MODEL}' not found. Pulling...${NC}"
        ollama pull "${OLLAMA_MODEL}"
        echo -e "${GREEN}✓ Model '${OLLAMA_MODEL}' downloaded${NC}"
    fi
}

# Check if code directory exists and has files
check_code_directory() {
    if [ ! -d "./code" ]; then
        echo -e "${RED}✗ ./code directory not found${NC}"
        echo -e "  Please create a ./code directory and add your .c files"
        exit 1
    fi
    
    if ! ls ./code/*.c 1> /dev/null 2>&1; then
        echo -e "${RED}✗ No .c files found in ./code directory${NC}"
        exit 1
    fi
    
    local file_count=$(ls -1 ./code/*.c | wc -l)
    echo -e "${GREEN}✓ Found ${file_count} C file(s) in ./code directory${NC}"
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
        -v "$(pwd)/code:/app/code" \
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
    echo -e "${GREEN}  Results${NC}"
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

# Main execution
main() {
    # Check prerequisites
    check_code_directory
    
    # Handle Ollama
    if ! check_ollama; then
        start_ollama
    fi
    
    check_model
    
    # Build and run
    build_image
    run_container
    
    # Show results
    display_results
    
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  Done!${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function
main