include ./venv.mk

.PHONY: all
.PHONY: setup
.PHONY: path_check
.PHONY: runtime
.PHONY: documentation
.PHONY: clean
.PHONY: distclean

SHELL:=/bin/bash

ISP_PREFIX ?= $(HOME)/.local/isp/

SDK_VERSION:=0.0.0

PROJECTS := riscv-gnu-toolchain
PROJECTS += policy-tool
PROJECTS += policy-engine
PROJECTS += FreeRTOS
PROJECTS += riscv-newlib
PROJECTS += llvm-project
PROJECTS += qemu
PROJECTS += riscv-openocd
PROJECTS += llvm-project/compiler-rt
PROJECTS += freedom-e-sdk

PRIVATE_PROJECTS := bsp
PRIVATE_PROJECTS += pex-firmware
PRIVATE_PROJECTS += pex-kernel

PROJECTS += $(foreach project, $(PRIVATE_PROJECTS), $(if $(wildcard ../$(project)/Makefile.isp),$(project)))

STOCK_TOOLCHAIN := stock-riscv-gnu-toolchain
STOCK_TOOLCHAIN += stock-llvm-project
STOCK_TOOLCHAIN += stock-qemu

CLEAN_PROJECTS := $(patsubst %,clean-%,$(PROJECTS))

.PHONY: $(PROJECTS) riscv-isa-sim freedom-elf2hex
.PHONY: $(CLEAN_PROJECTS) clean-riscv-isa-sim clean-freedom-elf2hex

all: setup runtime
	$(MAKE) freedom-elf2hex $(PROJECTS) riscv-isa-sim


setup: $(VENV_DONE)
	$(VENV) true

policy-engine: policy-tool
qemu: policy-engine
riscv-newlib: llvm-project
llvm-project/compiler-rt: llvm-project riscv-newlib
FreeRTOS: llvm-project/compiler-rt runtime
bsp: riscv-gnu-toolchain llvm-project setup
freedom-e-sdk: riscv-gnu-toolchain llvm-project
pex-firmware: riscv-gnu-toolchain bsp
pex-kernel: bsp pex-firmware freedom-elf2hex
stock-riscv-newlib: stock-llvm-project

path_check:
	(grep -q $(ISP_PREFIX)bin <<< $(PATH)) || (echo "Need to add $(ISP_PREFIX)/bin to your PATH" && false)

$(PROJECTS): freedom-elf2hex $(ISP_PREFIX)
	$(MAKE) -f Makefile.isp -C ../$@  > >(tee ../$@/make_stdout.log) 2> >(tee ../$@/make_stderr.log >&2)
	$(MAKE) -f Makefile.isp -C ../$@ install

riscv-isa-sim: $(ISP_PREFIX)
	mkdir -p ../$@/build
	cd ../$@/build && ../configure --prefix=$(ISP_PREFIX)
	$(MAKE) -C ../$@/build > >(tee ../$@/build/make_stdout.log) 2> >(tee ../$@/build/make_stderr.log >&2)
	$(MAKE) -C ../$@/build install

freedom-elf2hex: $(ISP_PREFIX)
	$(MAKE) -C ../$@
	INSTALL_PATH=$(ISP_PREFIX) $(MAKE) -C ../$@ install

$(STOCK_TOOLCHAIN): $(ISP_PREFIX)
	$(MAKE) -f Makefile.isp -C ../$@
	$(MAKE) -f Makefile.isp -C ../$@ install

$(ISP_PREFIX):
	mkdir -p $(ISP_PREFIX)
	chown $(USER) $(ISP_PREFIX)

$(CLEAN_PROJECTS):
	$(MAKE) -f Makefile.isp -C ../$(@:clean-%=%) clean

clean-riscv-isa-sim:
	rm -rf ../$(@:clean-%=%)/build

clean-freedom-elf2hex:
	$(MAKE) -C ../$(@:clean-%=%) clean

runtime: $(ISP_PREFIX) llvm-project/compiler-rt
	$(MAKE) -C runtime install

documentation:
	$(MAKE) -C documentation

clean-runtime:
	$(MAKE) -C runtime clean

clean-test:
	$(MAKE) -C ../policies/policy_tests clean

clean: $(CLEAN_PROJECTS) clean-riscv-isa-sim clean-test clean-runtime

distclean: clean
	-rm -rf $(ISP_PREFIX)
	rm -rf $(VENV_DIR)
