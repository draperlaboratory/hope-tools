ISP_PREFIX ?= $(HOME)/.local/isp/

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-sel4\.mk"))

RISCV_PATH    ?= $(ISP_PREFIX)
RISCV_CLANG   ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX     ?= $(RISCV_CLANG)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_CLANG)

sel4-build: sel4-lib
	rm $(OBJECTS)
	mv target.a hope-seL4-app-template/projects/bootstrap_main/src/target.a
	cd hope-seL4-app-template; bash ./make-riscv-build.sh -b 32 -p spike
	cd build_sel4; bash ../hope-seL4/init-build.sh -DPLATFORM=spike -DRISCV32=TRUE; ninja
