ISP_PREFIX  ?= $(HOME)/.local/isp/
STOCK_TOOLS ?= $(abspath $(ISP_PREFIX)/stock-tools)

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-sel4\.mk"))

RISCV_PATH    ?= $(STOCK_TOOLS)
RISCV_CLANG   ?= $(abspath $(STOCK_TOOLS)/bin/clang)
RISCV_GXX     ?= $(RISCV_CLANG)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_CLANG)

RISCV_ARCH ?= rv32ima
RISCV_ABI  ?= ilp32

sel4-build: sel4-lib
	rm $(OBJECTS)
	mv target.a hope-seL4-app-template/projects/bootstrap_main/src/target.a
	cd hope-seL4-app-template; bash ./make-riscv-build.sh -b 32 -p spike
