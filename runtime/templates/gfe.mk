ISP_PREFIX       ?= $(HOME)/.local/isp/

ISP_RUNTIME      := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-gfe\.mk"))

ISP_HEADERS      += $(wildcard $(ISP_RUNTIME)/*.h)
ISP_C_SRCS       += $(wildcard $(ISP_RUNTIME)/*.c)
ISP_ASM_SRCS     += $(wildcard $(ISP_RUNTIME)/*.S)

ISP_CFLAGS			 := -march=rv32i -mabi=ilp32 -mcmodel=medium
ISP_CFLAGS			 += -Wall -Wextra -O0 -g3 -std=gnu11
ISP_CFLAGS			 += -ffunction-sections -fdata-sections -fno-builtin-printf

RISCV_PATH			 ?= $(ISP_PREFIX)
RISCV_CLANG			 ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX			   ?= $(RISCV_CLANG)
RISCV_OBJDUMP		 ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB				 ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR				 ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC 							 := $(RISCV_CLANG)

BSP_BASE				 := $(ISP_RUNTIME)/bsp
BSP_LIB					 := $(BSP_BASE)/libvcu118.a

ISP_LIBS         := $(BSP_LIB)

ISP_LDFLAGS			 := -T $(BSP_BASE)/link.ld -nostartfiles -defsym=_STACK_SIZE=4K
ISP_LDFLAGS			 += -Wl,--wrap=isatty -Wl,--wrap=printf -Wl,--wrap=puts -Wl,--wrap=write

all:

$(BSP_LIB):
	make -C $(BSP_BASE)

clean:
	make -C $(BSP_BASE) clean

.PHONY: isp-runtime-common
isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)
