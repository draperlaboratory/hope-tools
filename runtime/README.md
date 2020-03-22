# ISP Runtime

This directory contains resources for building and running standalone ISP applications.
Included are scripts for building and installing kernels, compiling applications, and running the supported simulators.

### Setup

Run the following commands to install the PEX kernels and runtime tools, respectively:
```
make kernels
make install
```

The PEX kernels installed support the `none`, `heap`, `rwx`, `stack`, and `threeClass` policies and all of their composites.

### Usage

The ISP runtime consists of three commands: `isp_install_runtime`, `isp_run_app`, and `isp_debug`.

##### Building an application

The `isp_install_runtime` script bootstraps an existing project directory with resources that allow applications to build with one of
ISP's currently supported runtimes: FreeRTOS, seL4, Bare (bare metal). Use the script as follows:

```
isp_install_runtime <frtos/sel4/bare/stock_frtos/stock_sel4/stock_bare> -b <project directory (default .)>
```

The `stock` variants build the runtime using a non-ISP toolchain. It looks for `clang` and `riscv32-unknown-elf-*` binaries to be located in `ISP_PREFIX/stock-tools/bin`. When `hope-tools` is installed, the stock toolchain in `hope-src` is linked into this location by default, and if there is an installed copy of `clang`, it is linked as well. 

This will generate the `isp-runtime` directory in the project directory, as well as a Makefile `isp-runtime.mk`.
This Makefile sets `CC` to the ISP or stock version of Clang and exposes the following variables:
- `ISP_CFLAGS` - required compiler flags to pass to Clang
- `ISP_INCLUDES` - header files for the chosen runtime
- `ISP_LDFLAGS` - command to use a custom linker script for the target application
- `ISP_DEPS` - additional dependencies for the runtime
- `ISP_CLEAN` - files to be removed by `make clean`

To build an application for ISP, include `isp-runtime.mk` in an existing Makefile and add the above variables to your targets as needed.

NOTE: You must rename the `main()` function of your executable to `isp_main()` so that the runtime can locate it.

##### Running an application

The `isp_run_app` script runs an application on one of the supported simulators: QEMU or Renode. Use the script as follows:

```
isp_run_app <executable> -p <policy (default none)> -s <qemu/renode (default qemu)> -r <frtos/sel4/bare/stock_frtos/stock_sel4/stock_bare (default bare)> -o <output directory (default .)>
```

Additional options are:
- `-u/--uart`: echo the output of the application to stdout
- `-d/--debug`: print extra debug logs
- `-g/--gdb <port>`: start the simulator in gdbserver mode on the specified port
- `-N/--no_validator`: Do not use the validator and run the stock version of the simulator (which must be manually linked at `ISP_PREFIX/stock-tools/bin/qemu-system-riscv32`)

`isp_run_app` creates a directory containing application logs and support files in the location specified by `-o`. The name of this directory is `isp-run-<executable name>`.
Important files in this directory are:
- `uart.log`: The application output
- `sim.log`: The output from QEMU/Renode
- `pex.log`: The output from the PEX core, containing any policy violation messages
- `bininfo/<executable name>.text`: the disassembled source of the application

##### Debugging an application

While `isp_run_app` is started with the `-g` option, use the `isp_debug` script to attach to the debugging session. Use the script as follows:

```
isp_debug <executable> <port> -s <qemu/renode (default qemu)>
```
