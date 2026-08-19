from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: timer
short_description: Deploy a oneshot service and its systemd timer.
description:
    - This is an action plugin that provisions a oneshot systemd service and an
      associated timer unit, then ensures the timer is started and enabled.
    - Exactly one engine block (I(container) or I(command)) must be provided.
    - At least one scheduling option (I(on_calendar), I(on_boot_sec) or I(on_unit_active_sec)) must be provided.
options:
    name:
        type: str
        required: true
        description: "The name of the systemd timer and its oneshot service."
    container:
        type: dict
        description: "Runs the command inside an existing, already running container via '<engine> exec'. Mutually exclusive with 'command'."
        suboptions:
            engine:
                type: str
                required: false
                default: docker
                choices: [docker, podman]
                description: "The container engine to use."
            container:
                type: str
                required: true
                description: "The name of the running container to execute the command against."
            exec:
                type: str
                required: true
                description: "The executable to run inside the container. Injected into the template context."
            args:
                type: str
                required: false
                default: ''
                description: "Command arguments injected into the template context."
            opts:
                type: str
                required: false
                default: ''
                description: "Extra engine exec options, placed between 'exec' and the container name (e.g. '-ti'). An empty value is ignored."
            template:
                type: str
                required: false
                description: "Jinja2 template for the oneshot systemd .service file. Defaults to '<engine>_oneshot_service.j2'."
    command:
        type: dict
        description: "Runs a plain (non-container) command as a oneshot service. Mutually exclusive with 'container'."
        suboptions:
            exec:
                type: str
                required: true
                description: "The executable to run. Injected into the template context."
            args:
                type: str
                required: false
                default: ''
                description: "Command arguments injected into the template context."
            template:
                type: str
                required: false
                default: "command_oneshot_service.j2"
                description: "Jinja2 template for the oneshot systemd .service file (searches in Ansible paths or plugin defaults)."
    on_boot_sec:
        type: str
        required: false
        description: "Systemd OnBootSec directive (e.g. '15min')."
    on_unit_active_sec:
        type: str
        required: false
        description: "Systemd OnUnitActiveSec directive (e.g. '1w')."
    on_calendar:
        type: str
        required: false
        description: "Systemd OnCalendar directive (e.g. 'Mon *-*-* 05:00:00')."
    persistent:
        type: bool
        required: false
        default: false
        description: "If true, the timer catches up on missed activations while the machine was off (systemd Persistent=true)."
    accuracy_sec:
        type: str
        required: false
        description: "Systemd AccuracySec directive (e.g. '1min'). Fuzzy the expiration time to coalesce timer events."
    randomized_delay_sec:
        type: str
        required: false
        description: "Systemd RandomizedDelaySec directive (e.g. '30min'). Delays the timer by a randomly chosen amount of time."
    unit:
        type: str
        required: false
        description: "The unit to activate when the timer elapses. Defaults to the timer's matching '<name>.service'."
    timer_template:
        type: str
        required: false
        default: "timer.j2"
        description: "Jinja2 template for the systemd .timer unit (searches in Ansible paths or plugin defaults)."
'''

EXAMPLES = r'''
- name: Renew certificates weekly in an existing nginx container
  optionfactory.services.timer:
    name: cert-renewal
    container:
      container: "nginx-myproject"
      exec: /legopfa-all
    on_boot_sec: 15min
    on_unit_active_sec: 1w

- name: Run a maintenance job in a container with extra exec options
  optionfactory.services.timer:
    name: db-maintenance
    container:
      engine: podman
      container: "my-database"
      exec: /usr/local/bin/vacuum
      args: "--full"
      opts: "--user postgres"
    on_calendar: "Sun *-*-* 02:00:00"

- name: Nightly backup via a plain command
  optionfactory.services.timer:
    name: backup
    command:
      exec: /usr/local/bin/backup
      args: "--all"
    on_calendar: "Mon *-*-* 05:00:00"
    persistent: true
    randomized_delay_sec: 30min
'''

RETURN = r'''
msg:
    description: A summary of the timer deployment.
    type: str
    returned: always
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(),
        bypass_checks=True,
        supports_check_mode=True
    )
    module.exit_json(
        changed=False,
        msg="This module executes via its corresponding Action plugin. If you see this, the action plugin was bypassed."
    )


if __name__ == '__main__':
    main()
