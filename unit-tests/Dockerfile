# Individual test case generation Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app
RUN mkdir -p /app/code /app/tests /app/results

# Toolchain needed for compiling/running C tests
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test case generator script and prompt file to the container
COPY generator.py .
COPY prompts/ut_prompt_v1.txt ./prompt.txt

# Define environment variables for directories and settings
ENV FUNCTIONS_DIR=/app/code
ENV TESTS_DIR=/app/tests
ENV RESULTS_DIR=/app/results
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=codellama

# Default command to run the test case generator
CMD ["python", "generator.py"]
