# ISP SDK Getting Started

## Installation

The ISP SDK is delivered as a distribution package for Ubuntu 16.04 or CentOS 7.
The package can be installed via the follow command for Ubuntu:

```
$ sudo apt-get install -y ./isp-sdk_X.X.X_amd64.deb
```

or for CentOS 7

```
$ sudo yum install -y isp-sdk-X.X.X-0.x86_64.rpm
```

where `X.X.X` is the version of the ISP SDK you are installing.

The ISP SDK is also delivered as a various Docker images which can be used to
build projects.  There is one docker image for each distribution supported by
ISP.  While you can use any docker image on any Linux distribution you can use
the image you are most familiar with.  The docker images come with the SDK
package preinstalled.  When using a Docker image you will most likely want to
mount part of your host file system to the docker image.  The following is a
suitable command to run the Ubuntu 16 docker image:

```
$ docker run --rm --user=`id -u`:`id -g` -i \
$     -v $PWD:/workdir -t isp-sdk-ubuntu16:latest
```

This will run the docker image so the current user will be the owner of any
newly created files.  The current directory will be mounted to `/workdir` within
the docker image.

## Creating A Project

The SDK provides a tool to create an ISP project: `isp-init-project`.  Use this
tool from within your project directory to copy some necessary files for an ISP
project.  NOTE: If you are using the docker SDK make sure your current working
directory is `/workdir`.

```
$ mkdir isp-project
$ cd isp-project
$ isp-init-project
```

Within the `pex` directory is a file that must be sourced to include various
environmental variables specific to this project.  Assuming you are using bash
run the following:

```
$ source pex/activate
```

## Copy Sample Applications

To copy the sample applications used in this getting started guide run the
following:

```
$ isp-copy-samples
```

## Building PEX Kernel

The first step in building a project is building the PEX kernel.  The script
`isp-build-pex` is used to build the PEX kernel.  When building the PEX kernel
the policies that are being used must be specified.  Within the `policies`
directory, created by `isp-init-project`, are various policies that have already
been developed.  In this example we will use the RWX policy.  `isp-build-pex`
takes two arguments, the first being the application kernel (either `dos` for
Dover OS or `frtos` for FreeRTOS) and the policy.  Policy names have a directory
hierarchy.  Since we will be using both Dover OS and FreeRTOS `isp-build-pex`
must be invoked twice.

Note that `isp-build-pex` is not available if you have not performed the
previous `source activate` step.

```
$ isp-build-pex dos dover.dos.main.rwx
$ isp-build-pex frtos dover.frtos.main.rwx
```

## Dover OS Hello World

Within the `samples` directory of your ISP project directory are various samples
that can be run, one of course being the obligatory `hello_world`.  This is a
simple `hello_world` program that if inspected appears just like `hello_world`
on Linux/Windows/OSX.  To build this program the policy must be specified.  Here
the policy is specified via the environment variable `POLICIES`.

```
$ cd samples/hello_world
$ POLICIES=dover.dos.main.rwx make
```

To run the hello world program in the simulator use the `rundk` program

```
$ rundk --policies=dover.dos.main.rwx hello_world
```

A majority of the output will be related to initializing the process and the
kernel.  Near the end of the output you will see `hello world!`.


## FreeRTOS Hello World

The ISP SDK also includes the ability to create FreeRTOS applications.  There
are sample applications provided in `FreeRTOS-RISCV/samples`.  One of these
samples is `hello_world`.  The FreeRTOS hello world can be built using the
following commands:

```
$ cd <project-root>/FreeRTOS-RISCV/samples/hello_world
$ POLICIES=dover.frtos.main.rwx make
```

The FreeRTOS application does not use the Dover OS so the `runap` script is used
instead of `rundk`.  The hello world application can be run using the following
command:

```
$ runap --policies=dover.frtos.main.rwx main.rom
```

The FreeRTOS application does not terminate but instead runs in an infinite
loop.  The simulator can be terminated by pressing Ctrl^C twice.