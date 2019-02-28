include ../venv.mk

SYMLINK_DIR = $(ISP_PREFIX)/sources/
KERNEL_DIR = $(ISP_PREFIX)/kernels/
BIN_DIR = $(ISP_PREFIX)/bin/
GDB_DIR = $(ISP_PREFIX)/gdb-scripts/

ROOT = $(realpath ../../)

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
ISP_BACKEND += isp_qemu.py
ISP_BACKEND += isp_renode.py

HIFIVE_PREFIX := osv.hifive.main.
FRTOS_PREFIX := osv.frtos.main.

SYMLINK_SRCS := $(patsubst %,$(ROOT)/%,$(SYMLINKS))
SYMLINK_DSTS := $(patsubst %,$(SYMLINK_DIR)/%,$(SYMLINKS))

KERNELS := $(patsubst %,$(HIFIVE_PREFIX)%,$(POLICY_NAMES))
KERNELS += $(patsubst %,$(FRTOS_PREFIX)%,$(POLICY_NAMES))
KERNELS := $(patsubst %,$(KERNEL_DIR)/%,$(KERNELS))

INSTALLED_ISP_SCRIPTS := $(patsubst %,$(BIN_DIR)/%,$(ISP_SCRIPTS))
INSTALLED_GDB_SCRIPTS := $(patsubst %,$(GDB_DIR)/%,$(GDB_SCRIPTS))

POLICIES_DIR = $(SYMLINK_DIR)/policies/
TEMPLATE_DIR = $(POLICIES_DIR)/policy_tests/template/
POLICY_ENGINE_DIR = $(SYMLINK_DIR)/policy-engine/

.PHONY: all install clean uninstall kernels symlinks
all: $(ISP_SCRIPTS)

install: $(INSTALLED_ISP_SCRIPTS) $(INSTALLED_GDB_SCRIPTS) $(INSTALLED_GDB_SCRIPTS)

kernels: $(KERNELS)

symlinks: $(SYMLINK_DSTS)

$(INSTALLED_ISP_SCRIPTS): $(ISP_SCRIPTS) $(ISP_BACKEND)
	cp $(ISP_SCRIPTS) $(BIN_DIR)

$(ISP_SCRIPTS): %: %.py $(SYMLINK_DSTS) $(ISP_BACKEND) $(VENV_DONE)
	$(VENV) pyinstaller --onefile --distpath . $<

$(INSTALLED_GDB_SCRIPTS): $(GDB_SCRIPTS)
	mkdir -p $(GDB_DIR)
	cp -rf $(GDB_SCRIPTS) $(GDB_DIR)

$(KERNELS): $(SYMLINK_DSTS) $(INSTALLED_ISP_SCRIPTS)
	mkdir -p $(KERNEL_DIR)
	isp_kernel $(notdir $@) $(KERNEL_DIR)

$(SYMLINK_DSTS): $(SYMLINK_DIR)/%: $(ROOT)/%
	@echo $(SYMLINK_DSTS)
	mkdir -p $(SYMLINK_DIR)
	ln -s $< $@

clean:
	rm -rf $(ISP_SCRIPTS) $(KERNELS) *.pyc *.spec build/

uninstall:
	rm -rf $(INSTALLED_ISP_SCRIPTS) $(INSTALLED_GDB_SCRIPTS) $(KERNELS)
