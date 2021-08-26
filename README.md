# Ansible opfa collections

This is a set of collections used by OptionFactory Ansible manifests.

## Collections

- [Legacy](opfa/legacy): collects all legacy roles for ease of maintenance and to facilitate transition from roles to collections.

# Requirements

Collections can be used by Ansible &gt;= 2.9, but Ansible &gt;= 2.11 is recommended

# Naming conventions

Roles in a collection have to follow a stricter naming convention comparing to standard roles:

- folder names in a role path are used to define its fully qualified name, so a path like opfa/legacy/roles/os_base will result in opfa.legacy.os_base.
- all path elements (namespace, collection, role) are limited to lowercase alphanumeric characters plus underscore, and they must start with an alpha character

For more information: https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html#roles-directory

# Using collections

## Install a collection

To use a collection you need to declare it in your ansible-galaxy.yml / requirements.yml declarations. 

If the collections is not published on a known server, use its github repository url:

```yml
  roles:
  collections:
    - name: https://github.com/optionfactory/ansible-blu-istanbul
      type: git
      version: tag | branch
```

Afterwards, run ansible-galaxy to install:

```bash
$ ansible-galaxy install -r ansible-galaxy.yml
```

If you have Ansible &lt;=2.9 you need to install git collections manually; please refer to documentation at https://docs.ansible.com/ansible/2.9/user_guide/collections_using.html#installing-collections.


For further clarifications please refer to the latest Ansible docs: https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#install-multiple-collections-with-a-requirements-file

## Use roles in collections

To use a role in a collection you need to refer to it with its fully qualified name:

```yml
  roles:
    - role: opfa.legacy.journald
      vars:
        forward_to_syslog: no
```

```yml
  tasks:
    - name: configure journald
      include_role: 
        name: opfa.legacy.journald
      vars:
        forward_to_syslog: no
```

It is possible to declare a collection to use all its roles without prefixes:

```yml
  collections:
    - opfa.legacy
  roles:
    - role: journald
      vars:
        forward_to_syslog: no
```
