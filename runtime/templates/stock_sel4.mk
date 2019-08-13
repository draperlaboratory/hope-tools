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

all:
	cp $(SOURCE) hope-seL4/projects/bootstrap_main/src/main.c 
	cd build_sel4 && bash ../hope-seL4/init-build.sh -DPLATFORM=spike -DRISCV32=TRUE && ninja
