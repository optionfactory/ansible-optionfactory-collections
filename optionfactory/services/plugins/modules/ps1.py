from ansible.module_utils.basic import AnsibleModule
DOCUMENTATION = r'''
---
module: ps1
short_description: deploy a custom prompt
description:
    - This is an action plugin that provisions a custom prompt for the user.
'''

EXAMPLES = r'''
- name: Add a custom prompt to the user's shell
  optionfactory.services.ps1:
'''

RETURN = r'''
msg:
    description: A summary of the prompt deployment.
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
