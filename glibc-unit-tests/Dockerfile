# Base image: Ubuntu 20.04 for glibc 2.31 compatibility
# Use 20.04 for testing glibc 2.31-2.32, 18.04 for 2.27, etc.
FROM ubuntu:20.04

# Environment variables for non-interactive installs
# Can be overridden at runtime if needed 
ENV INPUTS_DIR=/app/inputs
ENV TESTS_DIR=/app/tests
ENV RESULTS_DIR=/app/results
ENV GLIBC_DIR=/app/glibc_build
ENV GLIBC_VERSION=2.32
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=codellama

# Create working folder and subfolders
WORKDIR /app
RUN mkdir -p $CODE_DIR $TESTS_DIR $RESULTS_DIR $GLIBC_DIR

# Install necessary packages for building and testing glibc
RUN apt-get update && apt-get install -y \
    # gcc, g++, make needed for glibc build
    build-essential \
    # Network utilities
    wget curl ca-certificates \
    # Python for test generator
    python3 python3-pip python3-dev \
    # Coverage tools
    lcov \
    # Tools for testing and debugging
    clang valgrind \
    # Build system tools
    automake autoconf libtool bison gawk pkg-config \
    # Locale support
    locales \
 && rm -rf /var/lib/apt/lists/*

# Set UTF-8 locale (required for some glibc functions)
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy test generator and evaluator scripts
# ...

# Optional: Download and compile custom GLIBC version
# Uncomment to test older/newer glibc versions
# RUN cd $GLIBC_DIR \
#     && wget https://ftp.gnu.org/gnu/libc/glibc-$GLIBC_VERSION.tar.gz \
#     && tar -xvzf glibc-$GLIBC_VERSION.tar.gz \
#     && mkdir glibc-$GLIBC_VERSION/build && cd glibc-$GLIBC_VERSION/build \
#     && ../configure --prefix=$GLIBC_DIR/install \
#     && make -j$(nproc) \
#     && make install
# ENV LD_LIBRARY_PATH=$GLIBC_DIR/install/lib:$LD_LIBRARY_PATH