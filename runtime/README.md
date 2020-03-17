# ISP Runtime

This directory contains resources for building and running standalone ISP applications.
Included are scripts for building and installing policies, compiling applications, and running the supported simulators.

### Setup

Run the following commands to install the runtime tools:

```
make install
```

### Usage

The ISP runtime consists of the following commands:

- `isp_install_runtime`
- `isp_install_policy`
- `isp_run_app`
- `isp_debug`

##### Building an application

The `isp_install_runtime` script bootstraps an existing project directory with resources that allow applications to build with one of
ISP's currently supported runtimes: FreeRTOS, seL4, Bare (bare metal). Use the script as follows:

```
isp_install_runtime <frtos/sel4/bare> -b <project directory (default .)>
```

The `stock` variants build the runtime using a non-ISP toolchain. It looks for `clang`, `riscv32-unknown-elf-*`, `riscv64-unknown-elf-*`  binaries to be located in `ISP_PREFIX/stock-tools/bin`. When `hope-tools` is installed, the stock toolchain in `hope-src` is linked into this location by default, and if there is an installed copy of `clang`, it is linked as well.

This will generate the `isp-runtime` directory in the project directory, as well as a Makefile `isp-runtime.mk`.
This Makefile sets `CC` to the ISP or stock version of Clang and exposes the following variables:

- `ISP_CFLAGS` - required compiler flags to pass to Clang
- `ISP_INCLUDES` - header files for the chosen runtime
- `ISP_LDFLAGS` - command to use a custom linker script for the target application

To build an application for ISP, include `isp-runtime-<frtos/sel4/bare>.mk` in an existing Makefile and add the above variables to your targets as needed.

NOTE: You must rename the `main()` function of your executable to `isp_main()` so that the runtime can locate it.

##### Generating a policy

The `isp_install_policy` script is responsible for compiling policies as well as PEX software binaries. A standard invocation of `isp_install_policy` is as follows:

```
isp_install_policy -p rwx stack heap -s qemu
```

This command will generate the following:
- A composite `heap-rwx-stack` policy directory
- `rv32-heap-rwx-stack-validator.so` QEMU validator library

Without the `-s` argument, `isp_install_policy` will only generate a policy directory.
The `-p` option accepts either a path to a pre-compiled policy directory or a list of policy names.
The `-P` option accepts a list of global policies (and does nothing when `-p` is a directory).

For more options, run `isp_install_policy --help`.

##### Running an application

The `isp_run_app` script generates tags for an application and runs it on the specified simulator (or hardware). A standard invocation of `isp_run_app` is as follows:

```
isp_run_app /path/to/application -s qemu -r bare -p rwx stack heap
```

This command runs the bare-metal `application` on the QEMU simulator with the RWX, Stack, and Heap policies.

The `-p` option accepts either a path to a pre-compiled policy directory or a list of policy names.
The `-P` option accepts a list of global policies (and does nothing when `-p` is a directory).
If the specified policy is not pre-compiled and does not exist in `$ISP_PREFIX/policies`, `isp_run_app` will automatically generate it by calling `isp_install_policy`.
If the specified policy does not have a corresponding PEX binary in `$ISP_PREFIX`, `isp_run_app` will automatically generate one by calling `isp_install_policy`.

For more information about command line options, run `isp_run_app --help`.

###### Output directory

`isp_run_app` generates a directory containing tagging and runtime information. By default, this directory is named as follows:

```
./isp-run-<application_basename>-<policies>-<rule_cache_name>-<rule_cache_size>
```

If the generated directory already exists, `isp_run_app` deletes it before running.

The `-o` argument can be used to specify the parent directory for this directory. The default is the current working directory.

The `-S` argument can be used to add a suffix to the end of the directory name.

##### Debugging an application

While `isp_run_app` is started with the `-g` option, use the `isp_debug` script to attach to the debugging session with GDB. Use the script as follows:

```
isp_debug <executable> <port> -s <simulator>
```

### Tool structure

This section describes the design of the runtime tools and serves as a set of guidelines for extending them.

##### Simulator modules

The runtime tools are modular with respect to the simulator/hardware in use (chosen with the `-s` option in all tools).
Each simulator module is named `isp_<simulator>.py` (e.g. `isp_qemu.py`).
Each simulator module must contain the following functions:

-`installPex(policy_dir, output_dir)`: Using the policy in `policy_dir`, builds a PEX binary (kernel, validator, etc) and stores it in `output_dir`
-`defaultPexPath(policy_name)`: given `policy_name`, returns the default path in `ISP_PREFIX` where the corresponding PEX binary would exist (e.g. for a `heap-rwx-stack` policy, `isp_qemu.py` returns `$ISP_PREFIX/validator/rv32-heap-rwx-stack-validator.so`)
- `runSim(exe_path, run_dir, policy_dir, pex_path, runtime, rule_cache, gdb_port, tagfile, soc_cfg, extra, use_validator=True)`: runs the simulator/hardware, generating any required tagging info
  - *TODO*: this should be split up into separate tagging and running functions

##### Extending `isp_install_runtime`

`isp_install_runtime` pulls its runtime assets from the `templates` directory. For each simulator, these assets are as follows:

-`isp_utils.c`: a library containing utilities that may have board-specific functionality. See `isp_utils.h` for functions to implement.
-`<runtime>.mk`: For each runtime supported by the simulator, include a Makefile that defines `ISP_CFLAGS`, `ISP_INCLUDES`, and `ISP_LDFLAGS`.

For each runtime, there is a `<runtime>_main.c` file that defines `main()`.

##### Python Virtual Environment

When the runtime tools are installed, a Python Virtual Environment is created in `$ISP_PREFIX/venv`.
The tools are called via wrapper scripts which source this Virtual Environment.

*This means that you will never need to pip install any python dependency to run the tools.*

If you need to add a python dependency to the tools, do so by adding it to `python-requirements.txt` in this directory.

##### ISP_PREFIX directories

The runtime tools install a number of resources to the user's `$ISP_PREFIX` directory. They are as follows:

-`$ISP_PREFIX/bin`: contains wrapper scripts which call the runtime Python scripts.
-`$ISP_PREFIX/runtime`: contains the runtime Python scripts.
-`$ISP_PREFIX/runtime/modules`: contains simulator modules for the runtime
-`$ISP_PREFIX/stock_tools`: contains stock (non-PIPE) versions of some dependencies
-`$ISP_PREFIX/gdb-scripts`: contains GDB scripts used by `isp_debug` to inspect tag state in GDB
-`$ISP_PREFIX/policies`: default path for compiled policies
-`$ISP_PREFIX/validator`: default path used by `isp_qemu.py` for PEX validator libraries
-`$ISP_PREFIX/venv`: Python Virtual Environment
