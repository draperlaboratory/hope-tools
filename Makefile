.PHONY: all
.PHONY: path_check
.PHONY: documentation
.PHONY: clean

SHELL:=/bin/bash

ISP_PREFIX ?= /opt/isp/

SDK_VERSION:=0.0.0

PROJECTS := riscv-gnu-toolchain
PROJECTS += policy-tool
PROJECTS += policy-engine
PROJECTS += renode-plugins
PROJECTS += renode
PROJECTS += llvm-riscv
PROJECTS += qemu

CLEAN_PROJECTS := $(patsubst %,clean-%,$(PROJECTS))

.PHONY: $(PROJECTS)
.PHONY: $(CLEAN_PROJECTS)

all: path_check
	$(MAKE) $(PROJECTS)

policy-engine: policy-tool
renode-plugins: renode
llvm-riscv: riscv-gnu-toolchain
qemu: policy-engine

path_check:
	(grep -q $(ISP_PREFIX)bin <<< $(PATH)) || (echo "Need to add $(ISP_PREFIX)/bin to your PATH" && false)

$(PROJECTS): $(ISP_PREFIX)
	$(MAKE) -f Makefile.isp -C ../$@
	$(MAKE) -f Makefile.isp -C ../$@ install

$(ISP_PREFIX):
	sudo mkdir -p $(ISP_PREFIX)
	sudo chown $(USER) $(ISP_PREFIX)

$(CLEAN_PROJECTS):
	$(MAKE) -f Makefile.isp -C ../$(@:clean-%=%) clean

documentation:
	$(MAKE) -C documentation

clean: $(CLEAN_PROJECTS)
	sudo rm -rf $(ISP_PREFIX)
