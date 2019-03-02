FREERTOS_DIR := ../../../FreeRTOS/FreeRTOS
FREERTOS_RVDEMO_DIR := $(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio
SDK_DIR := $(FREERTOS_RVDEMO_DIR)/freedom-e-sdk

include $(FREERTOS_RVDEMO_DIR)/BuildEnvironment.mk

ISP_PREFIX ?= /opt/isp

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-frtos\.mk"))
ISP_RUNTIME=./isp-runtime-frtos

FREERTOS_BUILD_DIR := $(FREERTOS_RVDEMO_DIR)/build

ISP_INCLUDES := -I$(FREERTOS_DIR)/Source/include
ISP_INCLUDES += -I$(FREERTOS_DIR)/Source/portable/GCC/RISC-V
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/include
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env
ISP_INCLUDES += -I$(FREERTOS_DIR)/Demo/RISC-V-Qemu-sifive_e-FreedomStudio/freedom-e-sdk/env/freedom-e300-hifive1
ISP_INCLUDES += -I$(ISP_PREFIX)/riscv32-unknown-elf/include
ISP_INCLUDES += -I$(ISP_RUNTIME)

ISP_LIBS := $(FREERTOS_BUILD_DIR)/libfreertos.a

#ISP_CFLAGS := -O2

RISCV_PATH 		?= $(ISP_PREFIX)
RISCV_GCC     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gcc)
RISCV_GXX     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-g++)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_GCC)

all:

$(ISP_LIBS):
	cd $(FREERTOS_RVDEMO_DIR) && make
