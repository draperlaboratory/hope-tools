.PHONY: all
.PHONY: configure-dover-os
.PHONY: dover-os
.PHONY: policy


all:
	$(MAKE) configure-dover-os

dover-os: policy
	$(MAKE) -C dover-os/build
	DOVER=$(PWD) $(MAKE) -C dover-os/build install-kernel

policy:
ifndef POLICY_FILES
	$(error POLICY_FILES is not set)
endif
	policytool -t RV32pex -o dover-os/build/policy $(POLICY_FILES)

configure-dover-os:
	make -C dover-os build/Makefile
