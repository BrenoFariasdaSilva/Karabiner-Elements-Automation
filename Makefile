.PHONY: install dry-run rules status uninstall validate test check
PYTHON ?= python3
install:
	bash install.command
dry-run:
	bash install.command --dry-run
rules:
	$(PYTHON) scripts/manage_rules.py install
status:
	$(PYTHON) scripts/manage_rules.py status
uninstall:
	bash uninstall.command
validate:
	$(PYTHON) scripts/manage_rules.py validate
test:
	$(PYTHON) -m unittest discover -s tests -v
check: validate test
