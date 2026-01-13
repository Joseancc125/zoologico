SHELL := /bin/bash

.PHONY: lint-shell lint-bash lint install-hooks

lint-shell:
	@shellcheck scripts/sdkmanager_auto.sh

lint-bash:
	@bash -n scripts/sdkmanager_auto.sh

lint: lint-shell lint-bash

install-hooks:
	@python3 -m pip install --user pre-commit || true
	@~/.local/bin/pre-commit install || pre-commit install || true
