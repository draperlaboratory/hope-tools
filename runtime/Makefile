include ../venv.mk

HOPE_SRC_SYMLINK = $(ISP_PREFIX)/sources
KERNEL_DIR = $(ISP_PREFIX)/kernels/
BIN_DIR = $(ISP_PREFIX)/bin/
GDB_DIR = $(ISP_PREFIX)/gdb-scripts/
RUNTIME_DIR = $(ISP_PREFIX)/runtime/
MODULE_DIR = $(ISP_PREFIX)/runtime/modules/

CLANG_PATH := $(shell command -v clang 2> /dev/null;)

HOPE_SRC = $(realpath ../../)

SYMLINKS := policies
SYMLINKS += policy-engine
SYMLINKS += tools

POLICY_NAMES := $(shell python policy_names.py)

ISP_SCRIPTS := isp_install_runtime
ISP_SCRIPTS += isp_run_app
ISP_SCRIPTS += isp_debug
ISP_SCRIPTS += isp_kernel

GDB_SCRIPTS := qemu.gdb
GDB_SCRIPTS += renode.gdb

ISP_BACKEND := isp_run.py
ISP_BACKEND += isp_utils.py

MODULES := isp_qemu.py
MODULES += isp_renode.py

BARE_PREFIX := osv.bare.main.
FRTOS_PREFIX := osv.frtos.main.
SEL4_PREFIX := osv.sel4.main.

KERNELS := $(patsubst %,$(BARE_PREFIX)%,$(POLICY_NAMES))
KERNELS += $(patsubst %,$(FRTOS_PREFIX)%,$(POLICY_NAMES))
KERNELS += $(patsubst %,$(SEL4_PREFIX)%,$(POLICY_NAMES))
KERNELS := $(patsubst %,$(KERNEL_DIR)/%,$(KERNELS))

INSTALLED_ISP_SCRIPTS := $(patsubst %,$(BIN_DIR)/%,$(ISP_SCRIPTS))

PYTHON_SCRIPTS := $(patsubst %,%.py,$(ISP_SCRIPTS))
PYTHON_SCRIPTS += $(ISP_BACKEND)

.PHONY: all install clean uninstall kernels symlink install-isp-scripts install-gdb-scripts install-runtime
all: $(ISP_SCRIPTS)

install: install-runtime install-isp-scripts install-gdb-scripts install-modules $(VENV_DONE) $(HOPE_SRC_SYMLINK)

install-runtime:
	mkdir -p $(RUNTIME_DIR)
	install $(PYTHON_SCRIPTS) $(RUNTIME_DIR)

install-isp-scripts: $(ISP_SCRIPTS)
	mkdir -p $(BIN_DIR)
	install $(ISP_SCRIPTS) $(BIN_DIR)

install-gdb-scripts: $(GDB_SCRIPTS)
	mkdir -p $(GDB_DIR)
	install $(GDB_SCRIPTS) $(GDB_DIR)

install-modules: $(MODULES)
	mkdir -p $(MODULE_DIR)
	install $(MODULES) $(MODULE_DIR)

install-sel4-template:
	if [ ! -d $(ISP_PREFIX)/hope-seL4-app-template ]; then \
		git clone https://github.com/draperlaboratory/hope-seL4-app-template.git $(ISP_PREFIX)/hope-seL4-app-template; \
	fi
	bash $(ISP_PREFIX)/hope-seL4-app-template/setup.sh

install-stock-tools:
	if [ ! -d $(ISP_PREFIX)/stock-tools ]; then\
		mkdir -p $(ISP_PREFIX)/stock-tools/bin; \
		ln -s $(ISP_PREFIX)/bin/riscv32-unknown-elf-* $(ISP_PREFIX)/stock-tools/bin/; \
	fi

        ifndef CLANG_PATH
            $(info "No clang in $(PATH), unable to automatically link into stock-tools")
        else 
	    if [ ! -f $(ISP_PREFIX)/stock-tools/bin/clang ]; then \
		    ln -s $(CLANG_PATH) $(ISP_PREFIX)/stock-tools/bin/clang; \
            fi
        endif

kernels: $(KERNELS)

symlink: $(HOPE_SRC_SYMLINK)

$(ISP_SCRIPTS): %: %.py
	printf '#!/bin/sh\n$(VENV) python $(RUNTIME_DIR)/$< "$$@"' > $@
	chmod +x $@

$(KERNELS): $(SYMLINK_DSTS) $(KERNEL_DIR) isp_kernel
	./isp_kernel $(notdir $@) -o $(KERNEL_DIR)

$(HOPE_SRC_SYMLINK):
	ln -s $(HOPE_SRC) $@

clean:
	rm -rf $(ISP_SCRIPTS) $(KERNELS) *.pyc *.spec build/

uninstall:
	rm -rf $(INSTALLED_ISP_SCRIPTS) $(GDB_DIR) $(KERNEL_DIR) $(HOPE_SRC_SYMLINK) $(RUNTIME_DIR) $(MODULE_DIR)
