ISP_PREFIX ?= $(HOME)/.local/isp/

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-stock_bare\.mk"))

ISP_HEADERS += $(wildcard $(ISP_RUNTIME)/*.h)
C_SRCS += $(wildcard $(ISP_RUNTIME)/*.c)

ISP_CFLAGS += -O2 -fno-builtin-printf
ISP_INCLUDES += -I$(ISP_PREFIX)/riscv32-unknown-elf/include
ISP_INCLUDES += -I$(ISP_RUNTIME)

RISCV_PATH    ?= $(ISP_PREFIX)
STOCK_TOOLS   ?= $(abspath $(ISP_PREFIX)/stock-tools)
RISCV_CLANG   ?= $(abspath $(STOCK_TOOLS)/bin/clang)
RISCV_GXX     ?= $(RISCV_CLANG)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_CLANG)

RISCV_ARCH ?= rv32ima
RISCV_ABI ?= ilp32

BOARD ?= freedom-e300-hifive1
LINK_TARGET ?= flash

BSP_BASE = $(ISP_RUNTIME)/bsp

ISP_LIBS := $(BSP_BASE)/libwrap/libwrap.a

all:

.PHONY: isp-runtime-common
isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)

include $(BSP_BASE)/env/common.mk
