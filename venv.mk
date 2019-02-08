ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

PYTHON := python3
VENV_DIR := $(ROOT_DIR)/venv
VENV_DONE := $(VENV_DIR)/.done
PYTHON_REQUIREMENTS := $(ROOT_DIR)/python-requirements.txt
VENV = bash -c "source $(VENV_DIR)/bin/activate" &&

$(VENV_DONE): $(PYTHON_REQUIREMENTS)
	rm -rf $(VENV_DIR)
	virtualenv -p $(PYTHON) $(VENV_DIR)
	$(VENV) pip install -r $(PYTHON_REQUIREMENTS)
	touch $@

clean-venv:
	rm -rf $(VENV_DIR)
.PHONY: clean-venv

all:
