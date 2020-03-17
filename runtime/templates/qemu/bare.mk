ISP_PREFIX ?= $(HOME)/.local/isp/
ARCH ?= rv32
ARCH_XLEN = $(subst rv,,$(ARCH))

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-bare\.mk"))

ISP_HEADERS += $(wildcard $(ISP_RUNTIME)/*.h)
C_SRCS += $(wildcard $(ISP_RUNTIME)/*.c)

TOOLCHAIN = riscv$(ARCH_XLEN)-unknown-elf

ISP_CFLAGS   += -O2 -fno-builtin-printf
ISP_INCLUDES += -I$(ISP_RUNTIME)
ISP_INCLUDES += -I$(ISP_PREFIX)/$(TOOLCHAIN)/include

RISCV_PATH    ?= $(ISP_PREFIX)
RISCV_CLANG   ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX     ?= $(abspath $(RISCV_PATH)/bin/$(TOOLCHAIN)-gcc)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/$(TOOLCHAIN)-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/$(TOOLCHAIN)-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/$(TOOLCHAIN)-ar)

CC = $(RISCV_CLANG)

ifneq ($(ARCH), rv64)
   RISCV_ARCH ?= rv32ima
   RISCV_ABI ?= ilp32
else
   CC = $(RISCV_GXX)

   RISCV_ARCH ?= rv64imafd
   RISCV_ABI ?= lp64d

   ISP_CFLAGS += -mcmodel=medany
   ISP_LDFLAGS += -mcmodel=medany
endif

BOARD ?= freedom-e300-hifive1
LINK_TARGET ?= flash

BSP_BASE = $(ISP_RUNTIME)/bsp

ISP_LIBS := $(BSP_BASE)/libwrap/libwrap.a

all:

.PHONY: isp-runtime-common
isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)

include $(BSP_BASE)/env/common.mk
