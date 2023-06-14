FROM ubuntu:22.04

RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" TZ="America/New_York" apt-get install -yq \
            tzdata
RUN apt-get update && \
    apt-get install -yq \
        apt-utils \
        autoconf \
        autogen \
        automake \
        autotools-dev \
        binutils-dev \
        bison \
        build-essential \
        clang \
        cmake \
        curl \
        device-tree-compiler \
        expat \
        flex \
        g++ \
        gawk \
        gcc-multilib \
        git \
        gperf \
        haskell-platform \
        haskell-stack \
        iverilog \
        libboost-all-dev \
        libboost-dev \
        libboost-program-options-dev \
        libboost-regex-dev \
        libelf-dev \
        libexpat1-dev \
        libftdi1-2 \
        libgflags-dev \
        libglib2.0-dev \
        libgmp-dev \
        libmpc-dev \
        libmpfr-dev \
        libpixman-1-dev \
        libstdc++-12-dev \
        libtinfo5 \
        libtool \
        libusb-1.0-0-dev \
        libyaml-cpp-dev \
        ninja-build \
        pandoc \
        pkg-config \
        python3 \
        python3-distutils \
        python3-pip \
        python3-psutil \
        python3-pyelftools \
        python3-pytest \
        python3-pytest-timeout \
        python3-pytest-xdist \
        python3-setuptools \
        python-is-python3 \
        rsync \
        socat \
        texinfo \
        texlive-fonts-recommended \
        verilator \
        virtualenv \
        xterm && \
    rm -rf /var/lib/apt/lists/*

RUN stack upgrade --binary-only --allow-different-user --local-bin-path /usr/bin
