.PHONY: all
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
PROJECTS += freedom-e-sdk
PROJECTS += riscv-newlib
PROJECTS += llvm-project
PROJECTS += qemu
PROJECTS += riscv-fesvr
PROJECTS += riscv-openocd
PROJECTS += llvm-project/compiler-rt

PRIVATE_PROJECTS := pex-firmware
PRIVATE_PROJECTS += pex-kernel

PROJECTS += $(foreach project, $(PRIVATE_PROJECTS), $(if $(wildcard ../$(project)/Makefile.isp),$(project)))

STOCK_TOOLCHAIN := stock-riscv-gnu-toolchain
STOCK_TOOLCHAIN += stock-llvm-project
STOCK_TOOLCHAIN += stock-qemu

CLEAN_PROJECTS := $(patsubst %,clean-%,$(PROJECTS))

.PHONY: $(PROJECTS)
.PHONY: $(CLEAN_PROJECTS)

all: runtime
	$(MAKE) $(PROJECTS)

policy-engine: policy-tool
qemu: policy-engine
riscv-newlib: llvm-project
llvm-project/compiler-rt: llvm-project riscv-newlib
FreeRTOS: llvm-project/compiler-rt runtime
pex-firmware: riscv-gnu-toolchain
pex-kernel: pex-firmware
stock-riscv-newlib: stock-llvm-project

path_check:
	(grep -q $(ISP_PREFIX)bin <<< $(PATH)) || (echo "Need to add $(ISP_PREFIX)/bin to your PATH" && false)

$(PROJECTS): $(ISP_PREFIX)
	$(MAKE) -f Makefile.isp -C ../$@
	$(MAKE) -f Makefile.isp -C ../$@ install

$(STOCK_TOOLCHAIN): $(ISP_PREFIX)
	$(MAKE) -f Makefile.isp -C ../$@
	$(MAKE) -f Makefile.isp -C ../$@ install

$(ISP_PREFIX):
	mkdir -p $(ISP_PREFIX)
	chown $(USER) $(ISP_PREFIX)

$(CLEAN_PROJECTS):
	$(MAKE) -f Makefile.isp -C ../$(@:clean-%=%) clean

runtime: $(ISP_PREFIX) llvm-project/compiler-rt
	$(MAKE) -C runtime install

documentation:
	$(MAKE) -C documentation

test-bare:
	$(MAKE) -C ../policies/policy_tests bare-qemu

test-frtos:
	$(MAKE) -C ../policies/policy_tests frtos-qemu

test-bare64:
	$(MAKE) -C ../policies/policy_tests bare64-qemu

test-frtos64:
	$(MAKE) -C ../policies/policy_tests frtos64-qemu

clean-runtime:
	$(MAKE) -C runtime clean

clean-test:
	$(MAKE) -C ../policies/policy_tests clean

clean: $(CLEAN_PROJECTS) clean-test clean-runtime

distclean: clean
	-rm -rf $(ISP_PREFIX)
	rm -rf $(VENV_DIR)
