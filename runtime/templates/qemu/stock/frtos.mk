ISP_PREFIX ?= $(HOME)/.local/isp/

ISP_RUNTIME := $(basename $(filter /%/isp-runtime-frtos.mk, $(abspath $(MAKEFILE_LIST))))
FREERTOS_DIR := $(ISP_PREFIX)/FreeRTOS
FREERTOS_RVDEMO_DIR := $(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio
SDK_DIR := $(FREERTOS_RVDEMO_DIR)/freedom-e-sdk
FREERTOS_BUILD_DIR := $(FREERTOS_RVDEMO_DIR)/build

STOCK_TOOLS      ?= $(abspath $(ISP_PREFIX)/stock-tools)
TOOLCHAIN_TRIPLE ?= riscv32-unknown-elf

include $(FREERTOS_RVDEMO_DIR)/BuildEnvironment.mk

ISP_INCLUDES := -I$(FREERTOS_DIR)/Source/include
ISP_INCLUDES += -I$(FREERTOS_DIR)/Source/portable/GCC/RISC-V
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio_Galois
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio_Galois/freedom-e-sdk/include
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio_Galois/freedom-e-sdk/env
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio_Galois/freedom-e-sdk/env/freedom-e300-hifive1
ISP_INCLUDES += -I$(STOCK_TOOLS)/$(TOOLCHAIN_TRIPLE)/include
ISP_INCLUDES += -I$(ISP_RUNTIME)

ISP_LIBS := $(FREERTOS_BUILD_DIR)/libfreertos-stock.a
RISCV_PATH    ?= $(STOCK_TOOLS)
RISCV_CLANG   ?= $(abspath $(STOCK_TOOLS)/bin/clang)
RISCV_GXX     ?= $(RISCV_CLANG)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/$(TOOLCHAIN_TRIPLE)-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/$(TOOLCHAIN_TRIPLE)-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/$(TOOLCHAIN_TRIPLE)-ar)

CC=$(RISCV_CLANG)

all:

$(ISP_LIBS):
	$(MAKE) -C $(FREERTOS_RVDEMO_DIR) clean-libfreertos-objs
	$(MAKE) -C $(FREERTOS_RVDEMO_DIR) build/libfreertos-stock.a MALLOC_VERSION=stock_heap_2

.PHONY: isp-runtime-common
isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)

include $(FREERTOS_RVDEMO_DIR)/BuildEnvironment.mk
