# Ansible OptionFactory collections

This is a set of collections used by OptionFactory Ansible manifests.

## Requirements

Collections require Ansible >= 2.15.0

## Using collections

### Install a collection

To use a collection, you need to declare it in your ansible-galaxy.yml / requirements.yml declarations. 

If the collections are published on a known server (e.g. Ansible Galaxy), use its name:

```yml
collections:
  - name: optionfactory.services
    version: 5.0.0
```

The `version` is optional: when omitted, the latest release is installed. When using multiple servers, pin the source explicitly:

```yml
collections:
  - name: optionfactory.services
    source: https://galaxy.ansible.com
    version: 5.0.0
```

If the collections are not published on a known server, use its GitHub repository url:

```yml
collections:
  - name: https://github.com/optionfactory/ansible-optionfactory-collections.git#optionfactory
    type: git
    version: 5.0.0
```

Afterwards, run ansible-galaxy to install:

```bash
$ ansible-galaxy install -r ansible-galaxy.yml
```

For further clarifications please refer to the latest Ansible docs: https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#install-multiple-collections-with-a-requirements-file


### Usage

#### `optionfactory.services.bundle`
This action is a powerful tool for defining an entire service in a single operation. It manages directory creation, file and template distribution, and the configuration of the associated systemd unit.

**Example:**
```yml
- name: Provision a service bundle
  optionfactory.services.bundle:
    name: my-app
    container:
      image: "myregistry/my-app:1.0"
      network: mynet
      ip: 172.18.0.10
      env:
        TZ: Europe/Rome
      opts: "--restart unless-stopped"
      args: "--config /etc/my-app.conf"
    owner: myuser
    group: mygroup
    dirs:
      - dest: /opt/my-app/config
    files:
      - dest: /opt/my-app/config/app.conf
        content: "setting=value"
    templates:
      - src: my-app.j2
        dest: /etc/my-app.conf
```

**Main parameters:**
- `name`: (mandatory) Name of the systemd service.
- `container`, `command`: Engine blocks — exactly one is required.
  - `container`: containerized service. `engine` (`docker` (default) or `podman`), `image` (mandatory, prefetched via `community.docker.docker_image`), `opts`, `args`, `env` (a `KEY: value` mapping, rendered as `--env`), `network`, `ip` (rendered as `--network`/`--ip`), `publish` (rendered as `-p`, empty entries ignored), `mounts` (rendered as `--mount type=bind,...`, each supports `when`), `volumes` (rendered as `--volume`, empty entries ignored), `template` (default: `<engine>_service.j2`). Empty `opts`/`network`/`ip` values are ignored, enabling Jinja conditionals that yield empty strings.
  - `command`: runs a plain (non-container) command as a service after the network is online. `exec` (mandatory), `args`, `template` (default: `command_service.j2`).
- `dirs`, `files`, `templates`: Lists of resources to be created/distributed.
- `owner`, `group`: Default owners (default: `docker-machines`).

#### `optionfactory.services.docker`
Automates Docker installation and configuration, including system proxies and Docker networks.
*Notes: with `package: docker-ce` (default), the official Docker repository is configured automatically (Debian and RedHat families); fact gathering is required.*

**Example:**
```yml
- name: Configure Docker
  optionfactory.services.docker:
    package: docker-ce
    users: ["remote-user"]
    proxy:
      http: "http://proxy.example.com:8080"
    network:
      name: my-bridge
      subnet: "172.20.0.0/24"
```

#### `optionfactory.services.journald`
Manages `systemd-journald` configuration.

**Example:**
```yml
- name: Configure journald
  optionfactory.services.journald:
    persistent: true
    configuration: |
      [Journal]
      SystemMaxUse=1G
```

**Parameters:**
- `persistent`: (bool) If `true` (default), creates `/var/log/journal` to make logs persistent across reboots.
- `configuration`: (string) The content to be written to `/etc/systemd/journald.conf`.

#### `optionfactory.services.legopfa`
Configures a `legopfa` certificate renewal service via a systemd timer.

**Example:**
```yml
- name: Configure legopfa certificate renewal
  optionfactory.services.legopfa:
    container_name: my-lego-container
```

**Parameters:**
- `container_name`: (mandatory) The name of the docker container running `legopfa`.

#### `optionfactory.services.ps1`
Installs a script in `/etc/profile.d/ps1.sh` that provides an advanced shell prompt. It shows:
- Dynamic host color based on the hostname.
- Current branch for Git and Mercurial repositories.
- Visual indicator if the shell is inside a Docker container.
- Status of the last command (⚙/⚠).

**Example:**
```yml
- name: Install custom PS1
  optionfactory.services.ps1: {}
```

#### `optionfactory.services.service`
A simplified version of `bundle` focused only on creating a systemd unit from a template.

**Example:**
```yml
- name: Provision a simple service
  optionfactory.services.service:
    name: my-simple-service
    container:
      image: "optionfactory/debian13-jdk21-keycloak2:999"
      network: mynet
      args: "start --optimized"

- name: Provision a podman service
  optionfactory.services.service:
    name: my-podman-service
    container:
      engine: podman
      image: "registry.example.com/my-app:2"

- name: Provision a command service
  optionfactory.services.service:
    name: my-agent
    command:
      exec: /usr/bin/my-agent
      args: "--config /etc/my-agent.conf"
```

**Parameters:**
- `name`: (mandatory) Name of the service.
- `container`, `command`: Engine blocks — exactly one is required (same shape as `bundle`).


#### `optionfactory.services.wireguard_mesh`
Configures a full-mesh WireGuard VPN topology.

**Example:**
```yml
- name: Deploy WireGuard Mesh
  optionfactory.services.wireguard_mesh:
    host_ip: "10.1.1.1"
    peers:
      - host_ip: "10.1.1.1"
        wg_tunnel_cidr: "10.0.0.1/24"
        docker_mesh_subnet: "172.18.1.0/24"
        private_key: "{{ vault_node_a_priv }}"
        public_key: "PubKeyA="
      - host_ip: "10.1.1.2"
        wg_tunnel_cidr: "10.0.0.2/24"
        docker_mesh_subnet: "172.18.2.0/24"
        private_key: "{{ vault_node_b_priv }}"
        public_key: "PubKeyB="
      - host_ip: "10.1.1.3"
        wg_tunnel_cidr: "10.0.0.3/24"
        docker_mesh_subnet: "172.18.3.0/24"
        private_key: "{{ vault_node_c_priv }}"
        public_key: "PubKeyC="
```
