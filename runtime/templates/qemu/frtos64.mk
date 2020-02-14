ISP_PREFIX ?= $(HOME)/.local/isp/

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-frtos64\.mk"))
FREERTOS_DIR := $(ISP_PREFIX)/FreeRTOS
FREERTOS_INCLUDE_DIR := $(FREERTOS_DIR)/include
FREERTOS_LIB_DIR := $(FREERTOS_DIR)/lib

LINKER_SCRIPT := $(FREERTOS_DIR)/build/hifive/flash.lds

RVXX := RV64
include $(FREERTOS_DIR)/build/hifive/BuildEnvironment.mk

ISP_INCLUDES := -I$(FREERTOS_INCLUDE_DIR)/Source/include
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/Source/portable/GCC/RISC-V
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/include
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env/freedom-e300-hifive1
ISP_INCLUDES += -I$(ISP_PREFIX)/riscv64-unknown-elf/include
ISP_INCLUDES += -I$(ISP_RUNTIME)

ISP_HEADERS      += $(wildcard $(ISP_RUNTIME)/*.h)
ISP_C_SRCS       += $(wildcard $(ISP_RUNTIME)/*.c)
ISP_ASM_SRCS     += $(wildcard $(ISP_RUNTIME)/*.S)

ISP_OBJECTS      := $(patsubst %.c,%.o,$(ISP_C_SRCS))
ISP_OBJECTS      += $(patsubst %.S,%.o,$(ISP_ASM_SRCS))

ISP_LDFLAGS      += -L$(ISP_RUNTIME) -L$(FREERTOS_LIB_DIR)
ISP_LDFLAGS      += -Wl,--start-group -lfreertos-hifive64 -lisp -lc -Wl,--end-group

LIBISP           := $(ISP_RUNTIME)/libisp.a
LIBFREERTOS 		 := $(FREERTOS_LIB_DIR)/libfreertos-hifive64.a

ISP_LIBS := $(LIBFREERTOS)
ISP_LIBS += $(LIBISP)

RISCV_PATH    ?= $(ISP_PREFIX)
RISCV_CLANG   ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX     ?= $(abspath $(RISCV_PATH)/bin/riscv64-unknown-elf-gcc)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv64-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv64-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv64-unknown-elf-ar)

CC=$(RISCV_GXX)

all:

$(LIBISP): $(ISP_OBJECTS)
	$(RISCV_AR) rcs $@ $(ISP_OBJECTS)

$(ISP_RUNTIME)/%.o: $(ISP_RUNTIME)/%.c
	$(CC) $(ISP_CFLAGS) $(ISP_INCLUDES) -c $< -o $@

.PHONY: isp-runtime-common
isp-runtime-common: $(LIBISP) $(ISP_OBJECTS)
