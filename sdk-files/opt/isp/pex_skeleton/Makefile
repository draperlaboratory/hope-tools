.PHONY: configure
.PHONY: configure-dover-os
.PHONY: policy

SHELL:=/bin/bash

configure: configure-dover-os

policy:
ifndef POLICY_OS
	$(error variable POLICY_OS not defined)
endif
ifndef POLICY_DIR
	$(error variable POLICY_DIR not defined)
endif
ifndef ISP_PROJECT_DIR
	$(error variable POLICY_DIR not defined)
endif
	cd $(POLICY_DIR); policy-tool -t $(POLICY_OS).xml -o $(ISP_PROJECT_DIR)/dover-os/build/policy $(POLICIES)
	$(MAKE) -C dover-os/build
	DOVER=$(ISP_PROJECT_DIR) $(MAKE) -C dover-os/build install-kernel
	DOVER=$(ISP_PROJECT_DIR) $(MAKE) -C dover-os/build install-no-kernel

configure-dover-os:
	make -C dover-os build/Makefile
