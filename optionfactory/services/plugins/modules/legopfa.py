from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: legopfa
short_description: Configures the legopfa renewal service and timer.
description:
    - Creates the systemd service and timer for legopfa certificates renewal.
    - Reloads the systemd daemon if files change.
    - Ensures the timer is started and enabled.
options:
    container_name:
        description:
            - The name of the Docker container to execute the renewal command against.
        required: true
        type: str
'''

EXAMPLES = r'''
- name: Setup legopfa certificates renewal
  optionfactory.services.legopfa:
    container_name: "nginx-myproject"
'''

RETURN = r'''
msg:
    description: A summary message of the operations performed.
    type: str
    returned: always
    sample: "legopfa-renewal service and timer successfully configured."
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
