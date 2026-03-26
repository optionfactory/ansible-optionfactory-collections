PROJECT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
VENV_BIN := $(PROJECT_DIR)/.venv/bin


deps:
	python3 -m venv .venv
	$(VENV_BIN)/pip install ansible-core molecule ansible-lint	

examples:
	for x in */*/examples.yml;\
		do ansible-playbook $$x --check ;\
	done

test:
	$(VENV_BIN)/ansible-galaxy collection install optionfactory/service_bundles/ --force
	$(VENV_BIN)/molecule test

lint:
	$(VENV_BIN)/ansible-lint */* -v

