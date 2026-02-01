# Makefile — venv + install requirements
SHELL := /bin/bash
PY ?= python3
VENV := .venv
PIP := $(VENV)/bin/pip

.PHONY: venv install requirements upgrade freeze clean

venv:
	@if [ ! -d "$(VENV)" ]; then \
		$(PY) -m venv $(VENV); \
		echo "Created $(VENV)"; \
	fi

install: venv
	. $(VENV)/bin/activate && python -m pip install -U pip
	$(PIP) install -r requirements.txt

# nice alias so you can type: make requirements
requirements: install

# optional helpers
upgrade: venv
	$(PIP) install -U -r requirements.txt

freeze: venv
	$(PIP) freeze > requirements.lock
	@echo "Wrote requirements.lock"

clean:
	rm -rf $(VENV)
