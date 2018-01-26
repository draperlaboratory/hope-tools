# How to Build

This is a step by step guide on how to build the ISP software toolchain.  Unless
otherwise stated the README assumes your working directory is this repository.
It is recommend that the git directories be stored in a directory called
`dover-repo` in your home directory for now.

## Installing Necessary Software

On Ubuntu 16.04 run the following to install the necessary software:

```
sudo apt-get install autoconf automake autotools-dev curl \
   libmpc-dev libmpfr-dev libgmp-dev gawk build-essential \
   bison flex texinfo gperf iverilog libelf-dev socat \
   expat libexpat1-dev git python3 python3-setuptools \
   haskell-platform cmake

```

## Setting Up Environmental Variables

The first step is to ensure you have all the necessary environmental variables
set up.  This can be accomplished by cutting and pasting the following into your
`.bash_aliases` or `.bashrc` if you use `bash`.  If you are not using `bash` you
will need to do the equivalent for your shell.

```
export DISTDIR=$HOME/download_cache
export DOWNLOAD_CACHE=$HOME/download_cache

export DOVER=$HOME/dover-install
export RISCV=$DOVER
export PATH=$DOVER/pex/bin:$DOVER/bin:${PATH}
```

After setting these environmental variables in your shell init file your current
shell(s) will not have the new environmental variables.  You can either launch a
new shell from your current shell or exit from your current shell and launch a
new shell.

## Setting Up The Download Cache

Assuming you have the appropriate environmental variables set the download cache
can be set up by just running the following:

```
./download-cache
```

## Download The Other Repositories

The other repositories can be downloaded running the following:

```
./git-clone-repos
```

## Building

The software can be built using the Makefile provided in this repository.  It is
recommend you run `make` with the `-j#` flag as this will instruct `make` to
perform a parallel build with a maximum of `#` processes.  A decent enough
choice for `#` is the number of CPUs you have which is returned by `nproc`.
Therefore you can run the following:

```
make -j `nproc`
```
