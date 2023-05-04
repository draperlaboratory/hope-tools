ISP_PREFIX ?= $(HOME)/.local/isp/
ARCH ?= rv32
ARCH_XLEN = $(subst rv,,$(ARCH))

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-bare\.mk"))

ISP_HEADERS += $(wildcard $(ISP_RUNTIME)/*.h)
C_SRCS += $(wildcard $(ISP_RUNTIME)/*.c)

ISP_CFLAGS   += -O2 -fno-builtin-printf -mno-relax
ISP_CFLAGS   += --sysroot=${ISP_PREFIX}/clang_sysroot/riscv64-unknown-elf
ISP_INCLUDES += -I$(ISP_RUNTIME)
ISP_INCLUDES += -I$(ISP_PREFIX)/clang_sysroot/riscv64-unknown-elf/include

RISCV_PATH    ?= $(ISP_PREFIX)
RISCV_CLANG   ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/llvm-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv64-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/llvm-ar)

CC = $(RISCV_CLANG)

ifneq ($(ARCH), rv64)
   RISCV_ARCH ?= rv32ima
   RISCV_ABI ?= ilp32
   ISP_CFLAGS += --target=riscv32-unknown-elf
else
   RISCV_ARCH ?= rv64imafd
   RISCV_ABI ?= lp64d
   ISP_CFLAGS += --target=riscv64-unknown-elf -mcmodel=medany
endif
ISP_LDFLAGS += -fuse-ld=lld

BOARD ?= freedom-e300-hifive1
LINK_TARGET ?= flash

BSP_BASE = $(ISP_RUNTIME)/bsp
BSP_SRC = $(BSP_BASE)/src

ISP_LIBS := $(BSP_SRC)/libwrap/libwrap.a

all:

.PHONY: isp-runtime-common
isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)

include $(BSP_SRC)/env/common.mk
