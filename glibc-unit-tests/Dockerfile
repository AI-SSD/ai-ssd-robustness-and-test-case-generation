# Base image: a minimal Debian image to build and run glibc tests.
# Debian is chosen for its stability and compatibility with all glibc versions.
FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive

# Environment variables for non-interactive installs
# Can be overridden at runtime if needed 
ENV INPUTS_DIR=/app/inputs
ENV TESTS_DIR=/app/tests
ENV RESULTS_DIR=/app/results
ENV GLIBC_DIR=/app/glibc_build

# Default variables overridable at runtime
ENV GLIBC_VERSION=2.32
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV OLLAMA_MODEL=qwen2.5-coder:3b

# Create working folder and subfolders
WORKDIR /app
RUN mkdir -p $INPUTS_DIR $TESTS_DIR $RESULTS_DIR $GLIBC_DIR

# Install necessary packages for building and testing glibc
RUN apt-get update && apt-get install -y --no-install-recommends \
    # gcc, g++, make needed for glibc build
    build-essential \
    # Network utilities
    wget curl ca-certificates \
    # Python for test generator
    python3 python3-pip python3-dev python3-venv \
    # Coverage tools
    lcov \
    # Tools for testing and debugging
    clang valgrind llvm \
    # Build system tools
    automake autoconf libtool bison gawk pkg-config texinfo \
    # Locale support
    locales \
    # Clean up apt cache to reduce image size (note to use apt-get update before installing anything new)
    && rm -rf /var/lib/apt/lists/*


# Set UTF-8 locale (required for some glibc functions)
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Setup Python virtual environment and install dependencies
# Debian Bookworm does not allow installing packages in the system Python, 
# so it must be done in a virtual environment or with --break-system-packages
COPY requirements.txt .
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Make the venv Python default
# Use Python normally afterwards
ENV PATH="/opt/venv/bin:$PATH"

# Copy scrpts
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