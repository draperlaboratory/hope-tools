# How to Build

This is a step by step guide on how to build the HOPE software toolchain.

By default everything is built in `/opt/isp/`.  This is also where the package
installs everything.  You will need to add `/opt/isp/bin/` to your `PATH` before
you build.  After you can change the install location by creating an
environmental variable `ISP_PREFIX` and setting that to whatever you prefer.
Note that `ISP_PREFIX` must end with a `/`.

## Installing Necessary Software

Ubuntu 18.04 is the preferred platform for HOPE development.

### Ubuntu 18.04

On Ubuntu 18.04 run the following to install the necessary software.

```
sudo ./isp-support/install-dependencies-ubuntu-1804
```

### Ubuntu 16.04

On Ubuntu 16.04 run the following to install the necessary software.

```
sudo ./isp-support/install-dependencies
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

## Running Tests

### Renode

```
make kernel test
```

Note: Renode does not support parallel test runs.

### QEMU

```
make kernel test SIM=qemu CONFIG=hifive XDIST='-n auto'
```

Note: XDIST allows for parallel test runs. You may specify the number of parallel jobs with '-n X'.
