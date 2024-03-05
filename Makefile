lint:
	ansible-lint */* -v



examples:
	for x in */*/examples.yml;\
		do ansible-playbook $$x --check --extra-vars '{"ansible_user": "connection_user"}' --ask-become-pass;\
	done
	