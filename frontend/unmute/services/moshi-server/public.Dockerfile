# This is the public-facing version.
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS base

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
        python3.12 \
        python3.12-dev \
        python3.12-venv \
        curl \
        build-essential \
        ca-certificates \
        libssl-dev \
        git \
        pkg-config \
        cmake \
        wget \
        openssh-client \
        --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.12 /usr/local/bin/python3

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/

WORKDIR /app

# When starting the container for the first time, we need to compile and download
# everything, so disregarding healthcheck failure for 10 minutes is fine.
# We have a volume storing the build cache, so subsequent starts will be faster.
HEALTHCHECK --start-period=10m \
    CMD curl --fail http://localhost:8080/api/build_info || exit 1

EXPOSE 11003
EXPOSE 11004
ENV RUST_BACKTRACE=1

RUN wget https://raw.githubusercontent.com/kyutai-labs/moshi/a40c5612ade3496f4e4aa47273964404ba287168/rust/moshi-server/pyproject.toml
RUN wget https://raw.githubusercontent.com/kyutai-labs/moshi/a40c5612ade3496f4e4aa47273964404ba287168/rust/moshi-server/uv.lock

COPY . .
#COPY start_moshi_server_public.sh .
#RUN dos2unix start_moshi_server_public.sh 
ENTRYPOINT ["uv", "run", "--locked", "--project", ".", "/bin/bash", "./start_moshi_server_public.sh"]