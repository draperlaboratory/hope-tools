# How to Build

This is a step by step guide on how to build the HOPE software toolchain.

To work with the HOPE toolchain, begin by creating a directory called
"dover-repos" and placing this repository inside it.  This README assumes your
working directory is this repository, so executing `pwd` should reveal a path
that ends in `dover-repos/hope-tools`.

The instructions in this README will create two other directories in the same
directory as `dover-repos`.  In the remainder of the README, we will assume that
this is your home directory.  If that is not the case, replace $HOME with the
appropriate directory in the instructions below.


## Installing Necessary Software

On Ubuntu 16.04 run the following to install the necessary software.  Note that
if `ghc` and `cabal` are already installed and on your path, you can remove
`haskell-platform` from the list below to avoid conflicting versions.

```
sudo apt-get install autoconf automake autotools-dev curl \
   libmpc-dev libmpfr-dev libgmp-dev gawk build-essential \
   bison flex texinfo gperf iverilog libelf-dev socat \
   expat libexpat1-dev git python3 python3-setuptools \
   cmake haskell-platform
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
export DOVER_SOURCES=$HOME/dover-repos
export FREE_RTOS_BASE=$HOME/dover-repos/FreeRTOS-RISCV
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

This build takes a while (at least 10 minutes, and possibly much longer,
depending on your machine).


## Getting started

You now have installed a variety of HOPE-related tools, including a custom
version of the RISC-V Spike software simulator that has been enhanced with the
PIPE and a tool for compiling micropolicies.  One good way to get started is to
run our policy tests.

```
cd dover-repos/hope-internal-tests/policy/unit_tests
make install-kernels
make
```

The `make install-kernels` command builds PEX kernels with several default
micropolicies.  The final `make` runs our policy tests - a collection of simple
C programs that do or do not violate various policies.  You should see that
these tests pass, withoutput like:

```
run_unit_tests.py::test_simple[dover.dos.main.cfi-printf_works_1.c-O2] PASSED                     [  0%]
run_unit_tests.py::test_simple[dover.dos.main.cfi-hello_works_1.c-O2] PASSED                      [  1%]
run_unit_tests.py::test_simple[dover.dos.main.cfi-stanford_int_treesort_fixed.c-O2] PASSED        [  2%]
run_unit_tests.py::test_simple[dover.dos.main.cfi-link_list_works_1.c-O2] PASSED                  [  3%]
run_unit_tests.py::test_simple[dover.dos.main.cfi-ptr_arith_works_1.c-O2] PASSED                  [  4%]
...
```

It's often useful to explore an individual test in the simulator.  To do this, run:

```
make debug-TESTNAME
```

Where TESTNAME is the name of one of the tests.  For example, you can run:

```
make debug-dover.dos.main.cfi-hello_works_1.c-O2
```

This should results in the creation of some files:

```
cd debug/dover.dos.main.cfi-hello_works_1.c-O2
```

Here you can see the C program that is run as part of the test (`main.c`) as
well as assembly listings of the application code and how they are tagged at
boot (`*.text.tagged`).  To run the simulator, do:

```
make && make spike
```

You are now in the PIPE-enhanced Spike simulator.  You can now step through the
program and examine tags and memory.  Type "help" for more information.
