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

## Development

```bash
make deps      # create .venv with ansible-core, molecule, ansible-lint, pytest
make unit      # unit tests
make lint      # ansible-lint
make test      # unit tests + molecule scenario (targets localhost, requires root)
```

The molecule scenario runs against C(localhost) with I(become: true) and exercises real systemd units and docker containers. Ansible invokes C(sudo -n) without a terminal, and sudo's default I(timestamp_type=tty) falls back to per-process records when no tty is present, so a ticket primed in your shell is never seen. C(make test) detects this and aborts with instructions; the one-time fix is a per-user sudoers drop-in enabling global timestamp caching:

```bash
echo "Defaults:$USER timestamp_type=global" | sudo tee /etc/sudoers.d/timestamp-global
sudo chmod 440 /etc/sudoers.d/timestamp-global
```

Afterwards C(make test) prompts for the sudo password once (cache valid 15 minutes by default) and the password is never stored. C(ANSIBLE_BECOME_PASSWORD_FILE=/path/to/file make test) also works in CI since the environment is passed through.

The scenario converges docker containers and systemd units on the host (C(testapp) network and service, C(testapp-command) service, C(testapp-timer) timer) and cleans up after itself: the C(cleanup) playbook runs both before the converge (removing leftovers of previous runs) and after the verify (units, container, network and files).


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
  - `container`: containerized service. `engine` (`docker` (default) or `podman`), `image` (mandatory, prefetched via `community.docker.docker_image`), `opts`, `args`, `env` (a `KEY: value` mapping, rendered as `--env`), `network`, `ip` (rendered as `--network`/`--ip`), `publish` (rendered as `-p`, empty entries ignored), `mounts` (rendered as `--mount type=<type>,source=<source>,target=<target>[,readonly][,<opts>]`; each entry supports `type` (default `bind`), `source` (mandatory), `target` (defaults to `source`), `readonly` (default `true`), `opts` (comma-separated extra mount options, appended verbatim, e.g. `bind-propagation=rshared`), and `when`), `volumes` (rendered as `--volume`, empty entries ignored), `template` (default: `<engine>_service.j2`). Empty `opts`/`network`/`ip` values are ignored, enabling Jinja conditionals that yield empty strings.
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

#### `optionfactory.services.ps1`
Installs a script in `/etc/profile.d/ps1.sh` that provides an advanced shell prompt. It shows:
- Dynamic true-color (24-bit) host color based on the hostname hash, cached per shell.
- Current git branch as `[branch]` (dimmed brackets, single fork, detached HEAD falls back to the short commit id).
- Visual indicator `[docker]` when the shell is inside a container (via `/.dockerenv`/`/run/.containerenv`, cgroup v2 safe).
- Status of the last command (✔/✘).

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


#### `optionfactory.services.timer`
Provisions a oneshot systemd service and its associated timer unit in one step, then ensures the timer is started and enabled. Supersedes the removed legopfa-specific timer.

**Example:**
```yml
- name: Renew certificates weekly inside an existing container
  optionfactory.services.timer:
    name: cert-renewal
    container:
      container: nginx-myproject
      exec: /legopfa-all
    on_boot_sec: 15min
    on_unit_active_sec: 1w

- name: Nightly backup via a plain command
  optionfactory.services.timer:
    name: backup
    command:
      exec: /usr/local/bin/backup
      args: "--all"
    on_calendar: "Mon *-*-* 05:00:00"
    persistent: true
    randomized_delay_sec: 30min
```

**Parameters:**
- `name`: (mandatory) Name of the timer and its oneshot service.
- `container`, `command`: Engine blocks — exactly one is required.
  - `container`: runs the command inside an existing, already running container via `<engine> exec`. `engine` (`docker` (default) or `podman`), `container` (mandatory, container name), `exec` (mandatory), `args`, `opts` (extra exec options, e.g. `-ti`), `template` (default: `<engine>_oneshot_service.j2`).
  - `command`: runs a plain (non-container) command. `exec` (mandatory), `args`, `template` (default: `command_oneshot_service.j2`).
- `on_boot_sec`, `on_unit_active_sec`, `on_calendar`: scheduling directives — at least one is required (empty values are ignored).
- `persistent`: (bool, default `false`) catches up on missed activations while the machine was off.
- `accuracy_sec`, `randomized_delay_sec`, `unit`: optional timer directives (`AccuracySec`, `RandomizedDelaySec`, `Unit`).
- `timer_template`: custom template for the `.timer` unit (default: `timer.j2`).


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
