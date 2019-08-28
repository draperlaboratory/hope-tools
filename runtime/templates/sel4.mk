ISP_PREFIX  ?= $(HOME)/.local/isp/
STOCK_TOOLS ?= $(abspath $(ISP_PREFIX)/stock-tools)

ISP_RUNTIME := $(basename $(shell echo $(abspath $(MAKEFILE_LIST)) | grep -o " /.*/isp-runtime-sel4\.mk"))
# Currently, seL4 doesn't build with clang, so we just have to build
# with the stock RISC-V toolchain. This means that stock and normal seL4
# builds are identical for now.

RISCV_PATH    ?= $(STOCK_TOOLS)
# riscv32/bin should contain a stock RISC-V GNU toolchain supporting
# rv32ima / ilp32.
RISCV_PREFIX ?= $(abspath $(RISCV_PATH)/riscv32/bin/riscv32-unknown-elf-)

sel4-build: sel4-lib
	rm $(OBJECTS)
	mv target.a hope-seL4-app-template/projects/bootstrap_main/src/target.a
	cd hope-seL4-app-template; bash ./make-riscv-build.sh -b 32 -p spike -C $(RISCV_PREFIX)
