.PHONY: configure
.PHONY: configure-dover-os
.PHONY: policy

configure: configure-dover-os

policy:
ifndef POLICY_FILES
	$(error POLICY_FILES is not set)
endif
	policytool -t RV32pex -o dover-os/build/policy $(POLICY_FILES)
	$(MAKE) -C dover-os/build
	DOVER=$(PWD) $(MAKE) -C dover-os/build install-kernel

configure-dover-os:
	make -C dover-os build/Makefile
