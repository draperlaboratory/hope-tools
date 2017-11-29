.PHONY: all
.PHONY: configure-dover-os

POLICIES=none

all:
	$(MAKE) configure-dover-os

configure-dover-os:
	make -C dover-os build/Makefile

# policytool -t RV32pex -o dover-os/build/policy RWXPolicy
