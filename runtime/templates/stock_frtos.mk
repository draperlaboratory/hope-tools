ISP_PREFIX ?= $(HOME)/.local/isp/

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-stock-frtos\.mk"))
FREERTOS_DIR := $(ISP_PREFIX)/FreeRTOS
FREERTOS_RVDEMO_DIR := $(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio
SDK_DIR := $(FREERTOS_RVDEMO_DIR)/freedom-e-sdk
FREERTOS_BUILD_DIR := $(FREERTOS_RVDEMO_DIR)/build

include $(FREERTOS_RVDEMO_DIR)/BuildEnvironment.mk

ISP_INCLUDES := -I$(FREERTOS_DIR)/Source/include
ISP_INCLUDES += -I$(FREERTOS_DIR)/Source/portable/GCC/RISC-V
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/include
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env/freedom-e300-hifive1
ISP_INCLUDES += -I$(ISP_PREFIX)/riscv-none-embed/include
ISP_INCLUDES += -I$(ISP_RUNTIME)

ISP_LIBS := $(FREERTOS_BUILD_DIR)/libfreertos.a

RISCV_PATH    ?= $(ISP_PREFIX)
STOCK_TOOLS   ?= $(abspath $(ISP_PREFIX)/stock-tools)
RISCV_CLANG   ?= $(abspath $(STOCK_TOOLS)/bin/clang)
RISCV_GXX     ?= $(RISCV_CLANG)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_CLANG)

all:

$(ISP_LIBS):
	$(MAKE) -C $(FREERTOS_RVDEMO_DIR) lib

.PHONY: isp-runtime-common
isp-runtime-common: $(ISP_LIBS) $(ISP_OBJECTS)

include $(FREERTOS_RVDEMO_DIR)/BuildEnvironment.mk
