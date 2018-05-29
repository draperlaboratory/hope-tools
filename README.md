# How to Build

This is a step by step guide on how to build the HOPE software toolchain.

By default everything is built in `/opt/isp/`.  This is also where the package
installs everything.  You will need to add `/opt/isp/bin/` to your `PATH` before
you build.  After you can change the install location by creating an
environmental variable `ISP_PREFIX` and setting that to whatever you prefer.
Note that `ISP_PREFIX` must end with a `/`.

## Installing Necessary Software

On Ubuntu 16.04 run the following to install the necessary software.  Note that
if `ghc` and `cabal` are already installed and on your path, you can remove
`haskell-platform` from the list below to avoid conflicting versions.


The policy tool uses `stack` to build.  If you don't have stack
installed, you can find [installation instructions at the Stack
website](https://docs.haskellstack.org/en/stable/README/).

Everything else can be installed via the following:

```
sudo apt-get install -y python3-pip
sudo -H pip3 install pyelftools
sudo apt-get install -y autoconf automake autotools-dev curl \
    libmpc-dev libmpfr-dev libgmp-dev gawk build-essential \
    bison flex texinfo gperf iverilog libelf-dev socat \
    expat libexpat1-dev git python3 python3-setuptools \
    cmake haskell-platform
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
    --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
echo "deb http://download.mono-project.com/repo/ubuntu xenial main" | \
    sudo tee /etc/apt/sources.list.d/mono-xamarin.list
sudo apt-get update
sudo apt-get -y install git mono-complete automake autoconf libtool g++ realpath \
    gksu libgtk2.0-dev screen uml-utilities gtk-sharp2 python2.7
sudo apt-get -y install cmake libboost-dev libboost-program-options-dev \
    libyaml-cpp-dev libgflags-dev


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

Read the README.md in the policy-engine repository for instructions on how to
build and run a program under renode.

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
