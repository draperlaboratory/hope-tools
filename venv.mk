ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

PYTHON := python3
VENV_DIR := $(ISP_PREFIX)/venv
VENV_DONE := $(VENV_DIR)/.done
PYTHON_REQUIREMENTS := $(ROOT_DIR)/python-requirements.txt
VENV = . $(VENV_DIR)/bin/activate &&

all:

$(VENV_DONE): $(PYTHON_REQUIREMENTS)
	rm -rf $(VENV_DIR)
	virtualenv -p $(PYTHON) $(VENV_DIR)
	$(VENV) pip3 install -r $(PYTHON_REQUIREMENTS)
	touch $@

clean-venv:
	rm -rf $(VENV_DIR)
.PHONY: clean-venv
