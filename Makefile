PROJECT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
VENV_BIN := $(PROJECT_DIR)/.venv/bin
GALAXY_API_KEY ?= ""

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
	$(VENV_BIN)/ansible-galaxy collection install optionfactory/services/ --force
	$(VENV_BIN)/ansible-lint */* -v
	
update-deps:
	$(VENV_BIN)/pip install --upgrade ansible-core molecule ansible-lint



publish:
	@mkdir -p builds/
	@$(VENV_BIN)/ansible-galaxy collection build optionfactory/services/ --output-path builds/ --force
	@$(VENV_BIN)/ansible-galaxy collection build optionfactory/inventory/ --output-path builds/ --force
	@if [ -z "$(GALAXY_API_KEY)" ]; then \
		echo "Error: GALAXY_API_KEY is not set."; \
		echo "Usage: make publish GALAXY_API_KEY=your_token_here"; \
		exit 1; \
	fi
	$(VENV_BIN)/ansible-galaxy collection publish builds/optionfactory-services-*.tar.gz --api-key $(GALAXY_API_KEY)
	$(VENV_BIN)/ansible-galaxy collection publish builds/optionfactory-inventory-*.tar.gz --api-key $(GALAXY_API_KEY)
