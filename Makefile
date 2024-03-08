lint:
	ansible-lint */* -v



examples:
	for x in */*/examples.yml;\
		do ansible-playbook $$x --check ;\
	done
	