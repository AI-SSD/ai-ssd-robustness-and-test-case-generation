# Base image: full Ubuntu 22.04 
# Chosen because it already includes many necessary glibc build tools
FROM ubuntu:22.04

# Environment variables for non-interactive installs
# Can be overridden at runtime if needed 
ENV DEBIAN_FRONTEND=noninteractive
ENV CODE_DIR=/app/code
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
RUN apt-get update \
    && apt-get install -y \
       build-essential \      # gcc, g++, make needed for glibc build
       wget curl ca-certificates \
       python3 python3-pip python3-dev \ # Python for test generator
       lcov \
       clang \
       valgrind \
       automake autoconf libtool bison gawk pkg-config \
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