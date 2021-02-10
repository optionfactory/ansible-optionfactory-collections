# Ansible opfa collection

This ansible collection contains all roles.

# How to use a collection

For use a collection you need to retrieve the collections and after use the collection elements.

## Install a collection

With ansible 2.10 can download collection from git. (https://docs.ansible.com/ansible/2.10/user_guide/collections_using.html#installing-a-collection-from-a-git-repository)
With ansible 2.9 must be clone collection repo and put adjacent to the current playbook, under a collections/ansible_collections/ directory structure. (https://docs.ansible.com/ansible/2.9/user_guide/collections_using.html#installing-collections)

TODO: generate makefile task to download collection and install it

## Use a role in collection

To use a role present in collection you need to specify the namespace and the collection name before the role name.
Be aware, the directory name of the role is used as the role name. Role names are now limited to contain only lowercase alphanumeric characters, plus _ and start with an alpha character.
For more information: https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html#roles-directory

Example:
```
  roles:
    - role: opfa.blu_instanbul.role1
  tasks:
    - name: Execute role from collection
      include_role:
        name: opfa.blu_instanbul.role1
```

# Next steps
* change collection name
* change repo name
* check version and supported platforms in meta files
* update collection `galaxy.xml`
* mark as deprecated old roles repos
* use collection version

# Role census
TODO
