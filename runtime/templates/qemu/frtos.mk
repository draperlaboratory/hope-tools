ISP_PREFIX ?= $(HOME)/.local/isp/

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-frtos\.mk"))
FREERTOS_DIR := $(ISP_PREFIX)/FreeRTOS
FREERTOS_INCLUDE_DIR := $(FREERTOS_DIR)/include
FREERTOS_LIB_DIR := $(FREERTOS_DIR)/lib

LINKER_SCRIPT := $(FREERTOS_DIR)/build/flash.lds

include $(FREERTOS_DIR)/build/BuildEnvironment.mk

ISP_INCLUDES := -I$(FREERTOS_INCLUDE_DIR)/Source/include
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/Source/portable/GCC/RISC-V
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/RISC-V-Qemu-sifive_e-FreedomStudio
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/include
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env
ISP_INCLUDES += -I$(FREERTOS_INCLUDE_DIR)/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env/freedom-e300-hifive1
ISP_INCLUDES += -I$(ISP_PREFIX)/riscv32-unknown-elf/include
ISP_INCLUDES += -I$(ISP_RUNTIME)

ISP_HEADERS      += $(wildcard $(ISP_RUNTIME)/*.h)
ISP_C_SRCS       += $(wildcard $(ISP_RUNTIME)/*.c)
ISP_ASM_SRCS     += $(wildcard $(ISP_RUNTIME)/*.S)

ISP_OBJECTS      := $(patsubst %.c,%.o,$(ISP_C_SRCS))
ISP_OBJECTS      += $(patsubst %.S,%.o,$(ISP_ASM_SRCS))

ISP_LDFLAGS      += -lisp -L$(ISP_RUNTIME)
ISP_LDFLAGS      += -lfreertos-hifive -L$(FREERTOS_LIB_DIR)

LIBISP           := $(ISP_RUNTIME)/libisp.a
LIBFREERTOS 		 := $(FREERTOS_LIB_DIR)/libfreertos.a

ISP_LIBS := $(LIBFREERTOS)
ISP_LIBS += $(LIBISP)

RISCV_PATH    ?= $(ISP_PREFIX)
RISCV_CLANG   ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX     ?= $(RISCV_CLANG)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_CLANG)

all:

$(LIBISP): $(ISP_OBJECTS)
	$(RISCV_AR) rcs $@ $(ISP_OBJECTS)

$(ISP_RUNTIME)/%.o: $(ISP_RUNTIME)/%.c
	$(CC) $(ISP_CFLAGS) $(ISP_INCLUDES) -c $< -o $@

.PHONY: isp-runtime-common
isp-runtime-common: $(LIBISP) $(ISP_OBJECTS)
