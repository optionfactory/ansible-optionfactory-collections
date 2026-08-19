PROJECT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
VENV_BIN := $(PROJECT_DIR)/.venv/bin
GALAXY_API_KEY ?= ""

deps:
	python3 -m venv .venv
	$(VENV_BIN)/pip install ansible-core molecule ansible-lint pytest

examples:
	for x in */*/examples.yml;\
		do ansible-playbook $$x --check ;\
		done

unit:
	$(VENV_BIN)/python -m pytest optionfactory/services/tests -v

test: unit
	$(VENV_BIN)/ansible-galaxy collection install optionfactory/services/ --force
	@if [ "$$(id -u)" -ne 0 ]; then \
	  sudo -n true </dev/null >/dev/null 2>&1 || sudo -v; \
	  if ! sudo -n true </dev/null >/dev/null 2>&1; then \
	    echo "error: the molecule scenario needs sudo that works without a terminal."; \
	    echo "ansible runs 'sudo -n' with no tty, so the default tty-based timestamp cache never hits."; \
	    echo "fix it once with:"; \
	    echo "  echo \"Defaults:$$USER timestamp_type=global\" | sudo tee /etc/sudoers.d/timestamp-global && sudo chmod 440 /etc/sudoers.d/timestamp-global"; \
	    exit 1; \
	  fi; \
	fi
	$(VENV_BIN)/molecule test

lint:
	$(VENV_BIN)/ansible-galaxy collection install optionfactory/services/ --force
	$(VENV_BIN)/ansible-lint */* -v
	
update-deps:
	$(VENV_BIN)/pip install --upgrade ansible-core molecule ansible-lint

publish:
	@mkdir -p builds/
	@$(VENV_BIN)/ansible-galaxy collection build optionfactory/services/ --output-path builds/ --force
	@if [ -z "$(GALAXY_API_KEY)" ]; then \
		echo "Error: GALAXY_API_KEY is not set."; \
		echo "Usage: make publish GALAXY_API_KEY=your_token_here"; \
		exit 1; \
	fi
	$(VENV_BIN)/ansible-galaxy collection publish builds/optionfactory-services-*.tar.gz --api-key $(GALAXY_API_KEY)
