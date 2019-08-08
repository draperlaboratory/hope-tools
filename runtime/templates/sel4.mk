ISP_PREFIX ?= $(HOME)/.local/isp/

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-sel4\.mk"))
SEL4_DIR := $(ISP_PREFIX)/sel4test

RISCV_PATH 		?= $(ISP_PREFIX)
RISCV_GCC     ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX     ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_GCC)

all:
	bash $(SEL4_DIR)/init-build.sh -DPLATFORM=spike -DRISCV32=TRUE
	ninja
