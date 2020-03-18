ISP_PREFIX       ?= $(HOME)/.local/isp/
ARCH ?= rv32
ARCH_XLEN = $(subst rv,,$(ARCH))

ISP_RUNTIME      := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-bare\.mk"))

ISP_HEADERS      += $(wildcard $(ISP_RUNTIME)/*.h)
ISP_C_SRCS       += $(wildcard $(ISP_RUNTIME)/*.c)
ISP_ASM_SRCS     += $(wildcard $(ISP_RUNTIME)/*.S)

ISP_OBJECTS      := $(patsubst %.c,%.o,$(ISP_C_SRCS))
ISP_OBJECTS      += $(patsubst %.S,%.o,$(ISP_ASM_SRCS))

ifneq ($(ARCH), rv64)
ISP_CFLAGS			 := -march=rv32im -mabi=ilp32 --target=riscv32-unknown-elf -mcmodel=medium
else
ISP_CFLAGS			 := -march=rv64imafd -mabi=ilp32 --target=riscv64-unknown-elf -mcmodel=medium
endif

ISP_CFLAGS			 += -Wall -Wextra -O0 -g3 -std=gnu11 -mno-relax
ISP_CFLAGS			 += -ffunction-sections -fdata-sections -fno-builtin-printf
ISP_INCLUDES     += -I$(ISP_PREFIX)/clang_sysroot/riscv$(ARCH_XLEN)-unknown-elf/include
ISP_INCLUDES     += -I$(ISP_RUNTIME)

RISCV_PATH			 ?= $(ISP_PREFIX)
RISCV_CLANG			 ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX			   ?= $(RISCV_CLANG)
RISCV_OBJDUMP		 ?= $(abspath  $(RISCV_PATH)/bin/llvm-objdump)
RISCV_GDB				 ?= $(abspath $(RISCV_PATH)/bin/riscv64-unknown-elf-gdb)
RISCV_AR				 ?= $(abspath  $(RISCV_PATH)/bin/llvm-ar)

CC 							 := $(RISCV_CLANG)

BSP_BASE				 := $(ISP_RUNTIME)/bsp

LIBVCU118				 := $(BSP_BASE)/libvcu118.a
LIBISP           := $(ISP_RUNTIME)/libisp.a

ISP_LIBS         := $(LIBISP) $(LIBVCU118)

ISP_LDFLAGS			 := -T $(BSP_BASE)/link.ld -nostartfiles -defsym=_STACK_SIZE=4K -fuse-ld=lld
ISP_LDFLAGS			 += -Wl,--wrap=isatty
ISP_LDFLAGS      += -Wl,--wrap=printf
ISP_LDFLAGS      += -Wl,--wrap=puts
ISP_LDFLAGS      += -Wl,--wrap=read
ISP_LDFLAGS      += -Wl,--wrap=write
ISP_LDFLAGS      += -Wl,--wrap=malloc
ISP_LDFLAGS      += -Wl,--wrap=free
ISP_LDFLAGS 		 += -Wl,--undefined=pvPortMalloc
ISP_LDFLAGS      += -Wl,--undefined=pvPortFree

ISP_LDFLAGS      += -lvcu118 -L$(BSP_BASE)
ISP_LDFLAGS      += -lisp -L$(ISP_RUNTIME)

all:

$(LIBVCU118):
	make -C $(BSP_BASE)

$(LIBISP): $(ISP_OBJECTS)
	$(RISCV_AR) rcs $@ $(ISP_OBJECTS)

$(ISP_RUNTIME)/%.o: $(ISP_RUNTIME)/%.c
	$(CC) $(ISP_CFLAGS) $(ISP_INCLUDES) -c $< -o $@

clean: isp-clean

.PHONY: isp-clean isp-runtime-common
isp-clean:
	make -C $(BSP_BASE) clean

isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)
