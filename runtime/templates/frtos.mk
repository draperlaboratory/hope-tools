ISP_PREFIX ?= /opt/isp

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-frtos\.mk"))

FREE_RTOS_BUILD_DIR := $(ISP_RUNTIME)/frtos

FREE_RTOS_DIR := $(ISP_PREFIX)/FreeRTOS

ISP_INCLUDES := -I$(FREE_RTOS_DIR)/Source/include
ISP_INCLUDES += -I$(FREE_RTOS_DIR)/Source/portable/GCC/RISCV
ISP_INCLUDES += -I$(FREE_RTOS_DIR)/Demo/RISCV_DOVER_GCC/arch
ISP_INCLUDES += -I$(FREE_RTOS_DIR)/Demo/RISCV_DOVER_GCC/conf
ISP_INCLUDES += -I$(FREE_RTOS_DIR)/Demo/RISCV_DOVER_GCC/soc/include
ISP_INCLUDES += -I$(ISP_PREFIX)/riscv32-unknown-elf/include

ISP_INCLUDES += -I$(ISP_RUNTIME)

ISP_LIBS := $(FREE_RTOS_BUILD_DIR)/libfree-rtos.a
ISP_LIBS += $(FREE_RTOS_BUILD_DIR)/libfree-rtos-dover.a

ISP_LDFLAGS := -T$(FREE_RTOS_DIR)/Demo/RISCV_DOVER_GCC/soc/link.ld -nostartfiles

ISP_CFLAGS := -O2

ISP_SOURCES := $(wildcard $(ISP_RUNTIME)/*.c)
ISP_OBJECTS := $(patsubst %.c,%.o,$(ISP_SOURCES))

RISCV_PATH 		?= $(ISP_PREFIX)
RISCV_GCC     ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_GXX     ?= $(abspath $(RISCV_PATH)/bin/clang)
RISCV_OBJDUMP ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-objdump)
RISCV_GDB     ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-gdb)
RISCV_AR      ?= $(abspath $(RISCV_PATH)/bin/riscv32-unknown-elf-ar)

CC=$(RISCV_GCC)

all:


$(ISP_OBJECTS): %.o: %.c
	$(CC) $(ISP_CFLAGS) $(ISP_INCLUDES) $< -c -o $@

$(ISP_LIBS):
	cd $(FREE_RTOS_BUILD_DIR) && cmake . && make
