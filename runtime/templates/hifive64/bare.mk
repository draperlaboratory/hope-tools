ISP_PREFIX ?= $(HOME)/.local/isp/

BOARD ?= freedom-e300-hifive1
LINK_TARGET ?= flash

BSP_BASE    := $(ISP_PREFIX)/bsp

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-bare\.mk"))

ISP_HEADERS += $(wildcard $(ISP_RUNTIME)/*.h)
ISP_C_SRCS  += $(wildcard $(ISP_RUNTIME)/*.c)

ISP_OBJECTS      := $(patsubst %.c,%.o,$(ISP_C_SRCS))

ISP_CFLAGS   += -O2 -fno-builtin-printf -mno-relax
ISP_CFLAGS   += --sysroot=${ISP_PREFIX}/clang_sysroot/riscv64-unknown-elf
ISP_INCLUDES += -I$(ISP_RUNTIME)
ISP_INCLUDES += -I$(ISP_PREFIX)/bsp/hifive64/ap/include
ISP_INCLUDES += -I$(ISP_PREFIX)/clang_sysroot/riscv64-unknown-elf/include

RISCV_PATH    ?= $(ISP_PREFIX)
RISCV_CLANG   ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/llvm-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv64-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/llvm-ar)

CC = $(RISCV_CLANG)

LIBISP   := $(ISP_RUNTIME)/libisp.a
ISP_LIBS := $(LIBISP)

RISCV_ARCH ?= rv64imafd
RISCV_ABI ?= lp64d
ISP_CFLAGS += --target=riscv64-unknown-elf -mcmodel=medany
ISP_CFLAGS += -march=$(RISCV_ARCH) -mabi=$(RISCV_ABI)

ISP_LDFLAGS := -T$(ISP_PREFIX)/bsp/hifive64/ap/$(LINK_TARGET).lds -nostartfiles
ISP_LDFLAGS += -Wl,--wrap=isatty
ISP_LDFLAGS += -Wl,--wrap=printf
ISP_LDFLAGS += -Wl,--wrap=puts
ISP_LDFLAGS += -Wl,--wrap=read
ISP_LDFLAGS += -Wl,--wrap=write
ISP_LDFLAGS += -Wl,--wrap=malloc
ISP_LDFLAGS += -Wl,--wrap=free
ISP_LDFLAGS += -Wl,--undefined=pvPortMalloc
ISP_LDFLAGS += -Wl,--undefined=pvPortFree
ISP_LDFLAGS += -fuse-ld=lld
ISP_LDFLAGS += -lbsp -L$(BSP_BASE)/hifive64/ap/lib
ISP_LDFLAGS += -lisp -L$(ISP_RUNTIME)

$(LIBISP): $(ISP_OBJECTS)
	$(RISCV_AR) rcs $@ $(ISP_OBJECTS)

$(ISP_RUNTIME)/%.o: $(ISP_RUNTIME)/%.c
	$(CC) $(ISP_CFLAGS) $(ISP_INCLUDES) -c $< -o $@

.PHONY: isp-runtime-common
isp-runtime-common: $(LIBISP)
