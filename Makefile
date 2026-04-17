# Makefile – install all SMCP packages in this repository
# -------------------------------------------------------------
# Usage:
#   make install        # (default) install lib + all server packages
#   make venv           # create an isolated virtual-env first
#   make clean          # remove the virtual-env
#   make check          # verify that all packages are installed
#   make uninstall      # uninstall all SMCP packages

# ---- Configuration -------------------------------------------------
REQ_FILE ?= requirements.txt

# Name of the virtual-env directory (set to empty to skip venv creation)
#VENV_DIR ?= .venv

# Pip command – automatically picks up the venv if it exists
PIP := $(if $(VENV_DIR),$(VENV_DIR)/bin/pip3,pip3)

# Shared library package (must be installed first – all servers depend on it)
LIB_PKG := lib

# Server packages (each has its own pyproject.toml)
SERVER_PKGS := adls alpaca alphavantage ebay ecobee econet homekit influxdb \
               matrix moltbook mqtt postgres sharepoint

ALL_PKGS := $(LIB_PKG) $(SERVER_PKGS)

# -------------------------------------------------------------
.PHONY: all install venv clean check uninstall requirements $(ALL_PKGS)

# Default target
all: install

# -----------------------------------------------------------------
# Create a clean virtual-env (optional but recommended)
# -----------------------------------------------------------------
venv:
	@python3 -m venv $(VENV_DIR)
	@echo "Virtual environment created at $(VENV_DIR)"
	@$(VENV_DIR)/bin/pip3 install --upgrade pip setuptools wheel

# -----------------------------------------------------------------
# Install shared requirements (optional – pyproject.toml covers deps)
# -----------------------------------------------------------------
requirements:
	@if [ -f $(REQ_FILE) ]; then \
		echo "Installing shared requirements from $(REQ_FILE)..."; \
		$(PIP) install --upgrade -r $(REQ_FILE); \
	fi

# -----------------------------------------------------------------
# Install every package in the repo
#   1. lib first (provides the smcp module others import)
#   2. each server package in editable mode
# -----------------------------------------------------------------
install: $(ALL_PKGS)
	@echo "All SMCP packages installed."

$(LIB_PKG):
	@echo "Installing $@..."
	@$(PIP) install -e ./$@

$(SERVER_PKGS): $(LIB_PKG)
	@echo "Installing $@..."
	@$(PIP) install -e ./$@

# -----------------------------------------------------------------
# Verify that every requirement is satisfied
# -----------------------------------------------------------------
check:
	@echo "Checking installed packages..."
	@$(PIP) check || { echo "Some packages are missing or have conflicts."; exit 1; }
	@echo "All packages are present and compatible."

# -----------------------------------------------------------------
# Uninstall every package defined in this repo
# -----------------------------------------------------------------
uninstall:
	@for pkg in $(SERVER_PKGS); do \
		name=$$(grep -m1 '^name' ./$$pkg/pyproject.toml | sed -E 's/name *= *"([^"]+)"/\1/'); \
		echo "Uninstalling $$name..."; \
		$(PIP) uninstall -y $$name || true; \
	done
	@echo "Uninstalling smcp..."
	@$(PIP) uninstall -y smcp || true

# -----------------------------------------------------------------
# Clean up the virtual-env
# -----------------------------------------------------------------
clean:
	@rm -rf $(VENV_DIR)
	@echo "Removed virtual environment $(VENV_DIR)"
