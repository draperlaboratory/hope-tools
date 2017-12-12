# ISP SDK Getting Started

## Installation

The ISP SDK is delivered as a Debian package for Ubuntu 16.04.  The package can
be installed via the follow command:

```
$ sudo apt-get install apt-get install -y ./isp-sdk_X.X.X_amd64.deb
```

Where `X.X.X` is the version of the ISP SDK you are installing.

The ISP SDK is also delivered as a Docker image which can be used to build
projects.  The docker image comes with the SDK package preinstalled.  When using
the Docker image you will most likely want to mount part of your host filesystem
to the docker image.  The following is a suitable command to run the docker
image:

```
$ docker run --rm --user=`id -u`:`id -g` -i -v $PWD:/workdir -t isp-sdk:latest
```

This will run the docker image so the current user will be the owner of any
newly created files.  The current directory will be mounted to `/workdir` within
the docker image.

## Creating A Project

The SDK provides a tool to create an ISP project: `isp-create-project`.  Use
this tool to create a directory containing all the necessary files for an ISP
project.  NOTE: If you are using the docker SDK make sure your current working
directory is /workdir

```
$ isp-create-project first-isp-project
$ cd first-isp-project
```

Within the new project directory is a file that must be sourced to include
various environmental variables specific to this project.  Assuming you are
using bash run the following:

```
$ source activate
```


Finally, you need to configure your project.  This can be done via the project
root `Makefile`.

```
$ make configure
```

## Building Policy-Specific Components

The first step in building a project is building the policy specific components.
These are derivered from the policy file and therefore must be specified when
building.  In this example we will use the `rwx` policy located in `RWXPolicy`.

```
$ POLICY_FILES=RWXPolicy make policy
```

## Hello World

Within the `samples` directory of your ISP project directory are various samples
that can be run, one of course being the obligatory `hello_world`.  This is a
simple `hello_world` program that if inspected appears just like `hello_world`
on Linux/Windows/OSX.  To build this program the policy must be specified.  When
specifying the policy here it is in all lower case and the "Policy" part is
omitted.

```
$ cd samples/hello_world
$ POLICIES=rwx make
```

To run the hello world program in the simulator use the `rundk` program

```
$ rundk --policies=rwx hello_world
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
$ POLICIES=rwx make
```

The FreeRTOS application does not use the Dover OS so the `runap` script is used
instead of `rundk`.  The hello world application can be run using the following
command:

```
$ runap --policies=rwx main.rom
```

The FreeRTOS application does not terminate but instead runs in an infinite
loop.  The simulator can be terminated by pressing Ctrl^C twice.