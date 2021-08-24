Caddy
=========

Configure a caddy instance running as an unprivileged user


Role Variables
--------------

- caddy_install_dir: directory for caddy binaries
- caddy_config_dir: directory for Caddyfile
- caddy_data_dir: directory for caddy state (certs, keys)
- caddyfile_content: content of Caddyfile

Example Playbook
----------------

Content of Caddyfile must be passed as a variable. If your Caddyfile configuration is generated with a template, use ansible lookup() function as shown in this example:

    - hosts: servers
      roles:
         - caddy
           caddyfile_content: "{{ lookup('template', 'templates/Caddyfile.j2') }}"

License
-------

MIT
