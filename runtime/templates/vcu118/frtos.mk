ISP_PREFIX       ?= $(HOME)/.local/isp/

ISP_RUNTIME      := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-frtos\.mk"))

FREERTOS_DIR := $(ISP_PREFIX)/FreeRTOS
FREERTOS_INCLUDE_DIR := $(FREERTOS_DIR)/include
FREERTOS_LIB_DIR := $(FREERTOS_DIR)/lib

LINKER_SCRIPT := $(FREERTOS_DIR)/build/vcu118/link.ld

ISP_HEADERS      += $(wildcard $(ISP_RUNTIME)/*.h)
ISP_C_SRCS       += $(wildcard $(ISP_RUNTIME)/*.c)
ISP_ASM_SRCS     += $(wildcard $(ISP_RUNTIME)/*.S)

ISP_OBJECTS      := $(patsubst %.c,%.o,$(ISP_C_SRCS))
ISP_OBJECTS      += $(patsubst %.S,%.o,$(ISP_ASM_SRCS))

ISP_CFLAGS			 := -march=rv32im -mabi=ilp32 -mcmodel=medium
ISP_CFLAGS			 += -Wall -Wextra -O0 -g3 -std=gnu11
ISP_CFLAGS			 += -ffunction-sections -fdata-sections -fno-builtin-printf
ISP_CFLAGS 			 += -Dmalloc\(x\)=pvPortMalloc\(x\) -Dfree\(x\)=vPortFree\(x\)

ISP_INCLUDES 		 := -I$(FREERTOS_INCLUDE_DIR)/Source/include
ISP_INCLUDES 		 += -I$(FREERTOS_INCLUDE_DIR)/Source/portable/GCC/RISC-V
ISP_INCLUDES 		 += -I$(FREERTOS_INCLUDE_DIR)/Demo/Common/include
ISP_INCLUDES 		 += -I$(FREERTOS_INCLUDE_DIR)/Demo/RISC-V_Galois_P1
ISP_INCLUDES 		 += -I$(FREERTOS_INCLUDE_DIR)/Demo/RISC-V_Galois_P1/bsp
ISP_INCLUDES     += -I$(ISP_PREFIX)/riscv32-unknown-elf/include
ISP_INCLUDES     += -I$(ISP_RUNTIME)

RISCV_PATH			 ?= $(ISP_PREFIX)
RISCV_CLANG			 ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX			   ?= $(RISCV_CLANG)
RISCV_OBJDUMP		 ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB				 ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR				 ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC 							 := $(RISCV_CLANG)

LIBISP           := $(ISP_RUNTIME)/libisp.a

ISP_LIBS         := $(LIBISP)

ISP_LDFLAGS			 := -T $(LINKER_SCRIPT) -nostartfiles -defsym=_STACK_SIZE=4K
ISP_LDFLAGS  		 += -Wl,--gc-sections

ISP_LDFLAGS      += -lfreertos-vcu118 -L$(FREERTOS_LIB_DIR)
ISP_LDFLAGS      += -lisp -L$(ISP_RUNTIME)
ISP_LDFLAGS      += -Wl,--wrap=puts
ISP_LDFLAGS      += -Wl,--wrap=printf

all:

$(LIBISP): $(ISP_OBJECTS)
	$(RISCV_AR) rcs $@ $(ISP_OBJECTS)

$(ISP_RUNTIME)/%.o: $(ISP_RUNTIME)/%.c
	$(CC) $(ISP_CFLAGS) $(ISP_INCLUDES) -c $< -o $@

clean: isp-clean

.PHONY: isp-clean isp-runtime-common
isp-clean:

isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)
