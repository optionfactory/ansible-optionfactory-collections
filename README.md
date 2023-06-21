# Ansible OptionFactory collections

This is a set of collections used by OptionFactory Ansible manifests.

## Collections

- [Legacy](optionfactory/legacy): collects all legacy roles for ease of maintenance and to facilitate transition from roles to collections.
- [Docker](optionfactory/docker): collects roles to handle docker installation and configuration.
- [Legacy](optionfactory/system): collects roles to handle system configuration.
 
# Requirements

Collections can be used by Ansible &gt;= 2.9, but Ansible &gt;= 2.11 is recommended

# Naming conventions

Roles in a collection have to follow a stricter naming convention comparing to standard roles:

- folder names in a role path are used to define its fully qualified name, so a path like optionfactory/legacy/roles/os_base will result in optionfactory.legacy.os_base.
- all path elements (namespace, collection, role) are limited to lowercase alphanumeric characters plus underscore, and they must start with an alpha character

For more information: https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html#roles-directory

# Using collections

## Install a collection

To use a collection you need to declare it in your ansible-galaxy.yml / requirements.yml declarations. 

If the collections is not published on a known server, use its github repository url:

```yml
  roles:
  collections:
    - name: https://github.com/optionfactory/ansible-optionfactory-collections
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
    - role: optionfactory.legacy.journald
      vars:
        forward_to_syslog: no
```

```yml
  tasks:
    - name: configure journald
      include_role: 
        name: optionfactory.legacy.journald
      vars:
        forward_to_syslog: no
```

It is possible to declare a collection to use all its roles without prefixes:

```yml
  collections:
    - optionfactory.legacy
  roles:
    - role: journald
      vars:
        forward_to_syslog: no
```


# Migration steps from roles to collections

* change requirement file to use collection instead roles
* install collections instead roles:
* in playbook file change role name convention (the character `-` is not supported anymore)
* in playbook file define namespace or declare collections terms.

## Example of migration
Makefile:
```
 install-roles:
-       ansible-galaxy install --roles-path ansible/roles -r ansible/ansible-galaxy.yml --force
+       ansible-galaxy collection install --collections-path ansible/collections -r ansible/ansible-galaxy.yml

```
requirement file (ansible-galaxy.yml):
```
 ---
-- src: https://bitbucket.org/optionfactory/docker.git
-  scm: git
-- src: https://bitbucket.org/optionfactory/docker-service.git
-  scm: git
-- src: https://bitbucket.org/optionfactory/ubuntu-aws.git
-  scm: git
-
+collections:
+  - name: https://github.com/optionfactory/ansible-optionfactory-collections.git#optionfactory/legacy
+    type: git
+    version: master

```
playbook:
```
 - all
   remote_user: ubuntu
   become: yes
+  collections: optionfactory.legacy
+
   roles:
-    - role: ubuntu-aws
+    - role: ubuntu_aws
     - role: docker
-    - role: docker-service
+    - role: docker_service
[...]
```
